extends SceneTree
## 招式/反馈/蓄气引用的effect id必须在运行时特效表有条目。
## presentation查不到时会静默跳过，弹体与蓄气整段不可见而逻辑测试仍通过，故单列此门。
var failures: Array[String] = []
var fighters := ["zoffy", "mother-of-ultra", "ultraman-gaia", "father-of-ultra", "ultraman-king", "ultraman-zero", "ultraman-justice"]
var effects: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("FAIL " + label)

func _add(value: Variant, ids: Dictionary) -> void:
	if value is String and not str(value).is_empty(): ids[str(value)] = true

func _scan_shot(shot: Variant, ids: Dictionary) -> void:
	if not shot is Dictionary: return
	for key in ["effect", "return_effect", "trail_effect"]:
		_add(shot.get(key, ""), ids)

func _scan_move(move: Dictionary, ids: Dictionary) -> void:
	_scan_shot(move.get("projectile", {}), ids)
	for frame in move.get("frames", []):
		for shot in frame.get("shots", []): _scan_shot(shot, ids)
		_scan_shot(frame.get("counter_shot", {}), ids)
		for attachment in frame.get("attachments", []):
			_add(attachment.get("effect", ""), ids)
	var feedback: Dictionary = move.get("feedback", {})
	for key in ["spark", "block_spark"]:
		_add(feedback.get(key, ""), ids)
	var impacts: Variant = feedback.get("projectile_impacts", {})
	if impacts is Dictionary:
		for key in impacts:
			_add(key, ids)
			_add(impacts[key], ids)

func run() -> void:
	effects = UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	# 已实装形态各自有独立招式表，与本体同口径核对。
	for row in UfeContentDatabase.read_json("res://content/roster/selection.json").entries:
		for form in row.get("forms", []):
			if not bool(form.get("implemented", false)) or str(form.get("id", "")) in fighters: continue
			if FileAccess.file_exists("res://content/fighters/%s/definition.json" % str(form.id)):
				fighters.append(str(form.id))
	for id in fighters:
		var definition := UfeContentDatabase.fighter(id, true)
		var ids: Dictionary = {}
		for move_id in definition.moves:
			_scan_move(definition.moves[move_id], ids)
		for move_id in ids:
			check(effects.has(move_id), "%s/%s 特效已登记" % [id, move_id])
	# 专属特效不能只是别的角色/形态图集的副本；换 id 照抄等于复用他人特效。
	var seen_atlas: Dictionary = {}
	for id in fighters:
		var definition := UfeContentDatabase.fighter(id, true)
		var ids: Dictionary = {}
		for move_id in definition.moves:
			_scan_move(definition.moves[move_id], ids)
		for move_id in ids:
			var entry: Dictionary = effects.get(move_id, {})
			var dedicated := str(entry.get("dedicated_to", ""))
			var texture := str(entry.get("texture", ""))
			if dedicated.is_empty() or texture.is_empty() or dedicated == id: continue
			check(dedicated == id, "%s/%s 特效属于%s而非%s" % [id, move_id, dedicated, id])
	for move_id in effects:
		var entry: Dictionary = effects[move_id]
		var dedicated := str(entry.get("dedicated_to", ""))
		var texture := str(entry.get("texture", ""))
		if dedicated.is_empty() or texture.is_empty(): continue
		# 路径不同、内容相同的副本也算复用；按图集 SHA 归并。
		var key := str(entry.get("atlas_sha256", texture))
		if seen_atlas.has(key) and seen_atlas[key] != dedicated:
			check(false, "%s 与 %s 共用同一图集" % [dedicated, seen_atlas[key]])
		seen_atlas[key] = dedicated
	# 只有落点、没有状态帧占位附件的角色也必须真的显示Q蓄气；离开Q不能遗留。
	for id in ["ultraman-zero", "father-of-ultra", "ultraman-justice"]:
		var layout: Dictionary = UfeChargeEffectPolicy.data().placements[id]
		for state in ["charge_start", "charge", "charge_stop"]:
			var charged := UfeFighter.new(UfeContentDatabase.fighter(id, true), 470)
			charged.enter(state)
			var aura := UfeChargeEffectPolicy.filter(charged, {}, [], false)
			var expected := str(layout[state].effect)
			check(aura.any(func(item): return str(item.get("effect", "")) == expected), "%s/%s q_charge_injected_without_attachments" % [id, state])
	var charged := UfeFighter.new(UfeContentDatabase.fighter("ultraman-zero", true), 470)
	charged.enter("idle")
	check(UfeChargeEffectPolicy.filter(charged, {}, [], false).is_empty(), "q_charge_absent_outside_charge")
	# 状态帧挂件同样经 presentation 渲染，id 不在表里就整段不显示；扫全部已实装角色，不只本批七人。
	# state_frames.json 单份可达数万行，逐份解析会超时；只从原文取 effect 字段。
	for id in DirAccess.get_directories_at("res://content/fighters"):
		var posture := "res://content/fighters/%s/state_frames.json" % id
		var definition_path := "res://content/fighters/%s/definition.json" % id
		if not FileAccess.file_exists(posture) or not FileAccess.file_exists(definition_path): continue
		if not bool(UfeContentDatabase.read_json(definition_path).get("playable", false)): continue
		var text := FileAccess.get_file_as_string(posture)
		var cursor := 0
		while true:
			var at := text.find("\"effect\"", cursor)
			if at < 0: break
			cursor = at + 8
			var colon := text.find(":", cursor)
			var quote := text.find("\"", colon + 1)
			if colon < 0 or quote < 0: break
			var end := text.find("\"", quote + 1)
			if end < 0: break
			var effect := text.substr(quote + 1, end - quote - 1)
			cursor = end + 1
			if effect.is_empty() or effect.contains("/") or effect.length() > 64: continue
			check(effects.has(effect), "%s 状态挂件已登记 %s" % [id, effect])
	var placements: Dictionary = UfeContentDatabase.read_json("res://content/presentation/charge_overlay_policy.json").get("placements", {})
	for id in placements:
		for state in placements[id]:
			var effect := str(placements[id][state].get("effect", ""))
			if not effect.is_empty():
				check(effects.has(effect), "%s/%s Q蓄气特效已登记" % [id, effect])
	print("EFFECT_REGISTRATION " + ("PASS" if failures.is_empty() else str(failures)))
	quit(0 if failures.is_empty() else 1)
