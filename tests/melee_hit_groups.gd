extends SceneTree
## 仅验证模拟：分段防重、命中/防御/落空、混合弹体、清招、原输入回放与旧招基线。
const Groups = preload("res://core/combat/melee_hit_groups.gd")
const BASELINE := "res://reports/review/2026-10-31/melee-hit-groups-core-v1/verified-v2/legacy-before.json"
const ThrowDriver = preload("res://tests/review/fighters/ultraman-omega/codex_weapon_throws_review_driver.gd")
var errors: Array = []
var cases: Array = []
var output_dir := "user://melee-hit-groups/"
var frozen_output := false

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report-dir="):
			output_dir = argument.trim_prefix("--report-dir=")
			if not output_dir.ends_with("/"): output_dir += "/"
			frozen_output = true
	DirAccess.make_dir_recursive_absolute(output_dir)
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	if not ok:
		errors.append(message)
		printerr(message)

func write(name: String, data: Variant) -> void:
	var path := output_dir + name
	if frozen_output and FileAccess.file_exists(path):
		check(false, "拒绝覆盖证据 " + name)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	FileAccess.open(path, FileAccess.WRITE).store_string(JSON.stringify(data, "\t", true) + "\n")

func legacy() -> Dictionary:
	var result: Dictionary = {}
	for family in ["supers", "specials", "omega_throws"]:
		var count := 12 if family == "supers" else 13 if family == "specials" else 40
		for section in range(count):
			var driver: RefCounted = UfePhase3SuperReview.new() if family == "supers" else UfePhase3SpecialReview.new() if family == "specials" else ThrowDriver.new()
			var first: int = section * 240 if family == "supers" else int(driver.S_STARTS[section]) if family == "specials" else section * 120
			var span: int = 240 if family == "supers" else int(driver.S_STARTS[section + 1]) - first if family == "specials" else 120
			driver.review_frame = first
			var ids: Array = ["ultraman", "zetton"] if family == "supers" else driver.matchup()
			var sim := UfeContentDatabase.match_for(str(ids[0]), str(ids[1]), true)
			driver.prepare_match(sim)
			var digest := ""
			var normalized_events := ""
			var hashes: Array = []
			var contacts: Array = []
			for age in range(span):
				if family == "specials" and driver.wants_intro() and age < 75: continue
				sim.step([driver.sample(first + age, sim), driver.second_sample(first + age)])
				digest = (digest + sim.state_hash() + JSON.stringify(sim.events, "", true)).sha256_text()
				hashes.append(sim.state_hash())
				normalized_events = (normalized_events + JSON.stringify(JSON.parse_string(JSON.stringify(sim.events)), "", true)).sha256_text()
				for event in sim.events:
					if event.kind in ["hit", "block", "weapon_return"]: contacts.append(event.duplicate(true))
			result[family + "/" + str(section)] = {"digest": digest, "final_hash": sim.state_hash(), "content": sim.content_fingerprint,
				"state_hashes": hashes, "normalized_events": normalized_events, "contacts": contacts}
	return result

func original_omega_trace(current: Dictionary) -> void:
	var path := "res://reports/review/2026-10-30/omega-s6-weapon-throws-runtime-v1/runtime-v1/main-trace.json"
	var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	check(original.trace.size() == 4800, "原主游戏欧米伽掷返trace完整")
	for section in range(40):
		var hashes: Array = []
		var events_digest := ""
		for row in original.trace.slice(section * 120, (section + 1) * 120):
			hashes.append(row.state_hash)
			events_digest = (events_digest + JSON.stringify(row.events, "", true)).sha256_text()
		var key := "omega_throws/" + str(section)
		check(hashes == current[key].state_hashes and events_digest == current[key].normalized_events,
			"原主游戏掷返状态与事件逐tick保持/" + str(section))

func move_fixture(with_beam: bool = false, repeat_group: bool = false, advance_to_second: bool = false) -> Dictionary:
	var move: Dictionary = UfeContentDatabase.fighter("ultraman").moves.light1.duplicate(true)
	move.merge({"id": "light1", "damage": 110, "chip_damage": 7, "hitstun": 24, "blockstun": 20,
		"pushback": 0, "stun": 0, "energy_cost": 0, "stamina_cost": 0, "kind": "strike", "level": "mid",
		"launch": false, "bounce": false, "knockdown": true, "unblockable": false,
		"feedback": {"spark": "impact_heavy", "block_spark": "impact_guard", "hitstop": 0, "blockstop": 0, "shake": 0, "flash": 0},
		"hit_groups": {"1": {"damage": 35, "chip_damage": 2, "knockdown": false}, "2": {"damage": 45, "chip_damage": 3, "knockdown": false}}, "frames": []}, true)
	for tick in range(24):
		var frame := {"sprite": 0, "dx": 25 if advance_to_second and tick == 5 else 0, "dy": 0, "hitboxes": [],
			"hurtboxes": [[-18, 0, 36, 128]], "cancel": [], "events": []}
		if tick in [1, 2, 3, 4, 6, 7, 8, 9] or (repeat_group and tick in [14, 15, 16]):
			frame.hitboxes = [[18, 55, 70, 35]]
			frame.hit_group = 1 if tick <= 4 or tick >= 14 else 2
		if with_beam and tick == 11:
			frame.shots = [{"spawn": [35, 75], "anchor": [35, 75], "beam": true, "speed": 0, "life": 6,
				"box": [0, -15, 110, 30], "length": 110, "thickness": 30, "effect": "pulse"}]
		move.frames.append(frame)
	return move

func copy_definition(source: UfeFighterDefinition) -> UfeFighterDefinition:
	var result: UfeFighterDefinition = source.duplicate(true)
	# Resource.duplicate只复制导出属性；模拟字典必须显式从来源复制。
	result.moves = source.moves.duplicate(true)
	result.command_table = source.command_table.duplicate(true)
	result.state_frames = source.state_frames.duplicate(true)
	return result

func fixture(facing: int, with_beam: bool = false, repeat_group: bool = false, advance_to_second: bool = false) -> UfeMatchDirector:
	var original := UfeContentDatabase.match_for()
	var first := copy_definition(original.fighters[0].definition)
	var second := copy_definition(original.fighters[1].definition)
	first.moves.light1 = move_fixture(with_beam, repeat_group, advance_to_second)
	var sim := UfeMatchDirector.new(first, second, original.rules, original.states)
	sim.fighters[0].x = 600
	sim.fighters[1].x = 600 + facing * (160 if advance_to_second else 55)
	sim.fighters[0].facing = facing
	sim.fighters[1].facing = -facing
	return sim

func exercise(facing: int, kind: String) -> void:
	var beam := kind in ["beam_hit", "beam_guard", "beam_whiff"]
	var sim := fixture(facing, beam, kind == "repeat", kind == "late_contact")
	var a := sim.fighters[0]
	var b := sim.fighters[1]
	if kind in ["whiff", "beam_whiff"]: b.x = 600 + facing * 400
	if kind == "invulnerable": b.combat.invulnerable = 6
	if kind == "early_projectile":
		for tick in [1, 2]:
			a.definition.moves.light1.frames[tick].hitboxes = []
			a.definition.moves.light1.frames[tick].erase("hit_group")
		UfeProjectileResolver.spawn(sim, 0, {"spawn": [35, 75], "speed": 0, "life": 5, "box": [0, -10, 40, 20],
			"hit_overrides": {"damage": 10, "chip_damage": 0, "knockdown": false}}, "light1")
	if kind in ["frame_guard", "unblockable_group"]:
		var guard: Dictionary = b.definition.moves.motion_22.duplicate(true)
		guard.energy_cost = 0
		guard.stamina_cost = 0
		guard.frames = []
		for tick in range(90):
			guard.frames.append({"sprite": 0, "dx": 0, "dy": 0, "hitboxes": [], "hurtboxes": [[-18, 0, 36, 128]], "cancel": [], "events": [],
				"melee_guard": "block", "guard_box": [-35, 0, 70, 160]})
		b.definition.moves.motion_22 = guard
		sim._start(b, "motion_22")
		if kind == "unblockable_group": a.definition.moves.light1.hit_groups["2"].unblockable = true
	var contacts: Array = []
	var recorder := UfeReplayRecorder.new()
	var hashes: Array = []
	for tick in range(90):
		var guarding := kind in ["guard", "beam_guard"] or (kind == "guard_release" and tick < 4)
		var inputs := [UfeInputFrame.make(0, 0, UfeInputFrame.LIGHT if tick == 0 or (kind == "restart" and tick == 45) else 0),
			UfeInputFrame.make(0, 0, UfeInputFrame.GUARD if guarding else 0)]
		sim.step(inputs)
		recorder.append(inputs, sim)
		hashes.append(sim.state_hash())
		for event in sim.events:
			if event.kind in ["hit", "block"]: contacts.append(event.duplicate(true))
	if kind in ["whiff", "beam_whiff"]:
		check(contacts.is_empty() and b.stats.hp == 1000, "远落空不结算/" + kind)
	elif kind in ["guard", "beam_guard"]:
		check(contacts.size() == (3 if beam else 2) and contacts.all(func(e): return e.kind == "block"), "每段可防御一次/" + kind)
		check(b.stats.hp == 1000 - (12 if beam else 5), "分段削血不能重复/" + kind)
	elif kind == "guard_release":
		check(contacts.size() == 2 and contacts[0].kind == "block" and contacts[1].kind == "hit" and b.stats.hp == 953, "第一段防住后第二段重新判断防御")
	elif kind == "frame_guard":
		check(contacts.size() == 2 and contacts.all(func(e): return e.kind == "block") and b.stats.hp == 1000, "实体护屏每段只拦一次")
	elif kind == "unblockable_group":
		check(contacts.size() == 2 and contacts[0].kind == "block" and contacts[1].kind == "hit" and b.stats.hp == 955, "第二段的不可防御覆盖必须绕过实体护屏")
	elif kind == "early_projectile":
		check(contacts.size() == 3 and contacts[0].projectile and not contacts[1].projectile and not contacts[2].projectile and b.stats.hp == 910, "先行弹体不能消耗后续实体段")
	elif kind in ["late_contact", "invulnerable"]:
		check(contacts.size() == 1 and b.stats.hp == 955, "第一段落空/无敌不能吃掉后段/" + kind)
	else:
		var expected := 3 if beam else 4 if kind == "restart" else 2
		check(contacts.size() == expected and b.stats.hp == 1000 - (190 if beam else 160 if kind == "restart" else 80), "逐段实体伤害/" + kind)
		if beam: check(contacts.size() == 3 and not contacts[0].projectile and not contacts[1].projectile and contacts[2].projectile, "两次实体斩击后独立弹体结算")
	check(not a.combat.has("hit_groups"), "清招后移除分段记录/" + kind)
	if kind == "beam_hit":
		var filename := "replay-" + str(facing) + ".json"
		check(recorder.save_file(output_dir + filename) == OK, "保存分段原输入回放")
		var twin := fixture(facing, true)
		var loaded := UfeReplayRecorder.load_file(output_dir + filename, twin.content_fingerprint)
		check(loaded != null, "载入原输入回放")
		if loaded != null:
			for tick in range(loaded.frames.size()):
				twin.step([UfeInputFrame.unpack(loaded.frames[tick][0]), UfeInputFrame.unpack(loaded.frames[tick][1])])
				check(twin.state_hash() == hashes[tick], "分段逐tick回放/" + str(tick))
			check(twin.state_hash() == loaded.final_hash, "分段回放最终哈希")
	cases.append({"facing": facing, "case": kind, "contacts": contacts, "hp": b.stats.hp, "final_hash": sim.state_hash()})

func validation() -> void:
	var move := move_fixture(true)
	check(UfeMoveData.validate(move), "合法实体多段与独立飞行物组合")
	var changes: Array = [
		["missing_group", func(m): m.frames[1].erase("hit_group")],
		["fractional_group", func(m): m.frames[1].hit_group = 1.5],
		["zero_group", func(m): m.frames[1].hit_group = 0],
		["unknown_group", func(m): m.frames[1].hit_group = 3],
		["unused_group", func(m): m.hit_groups["3"] = {"damage": 1}],
		["noncanonical_key", func(m): m.hit_groups["01"] = {"damage": 1}],
		["empty_override", func(m): m.hit_groups["1"] = {}],
		["negative_damage", func(m): m.hit_groups["1"].damage = -1],
		["fractional_damage", func(m): m.hit_groups["1"].damage = 1.5],
		["unsafe_override", func(m): m.hit_groups["1"].kind = "throw"],
		["invalid_bool", func(m): m.hit_groups["1"].launch = 1],
		["invalid_level", func(m): m.hit_groups["1"].level = "unknown"],
		["projectile_groups", func(m): m.kind = "projectile"],
		["throw_groups", func(m): m.kind = "throw"],
		["inactive_group", func(m): m.frames[0].hit_group = 1],
		["no_declaration", func(m): m.erase("hit_groups")]
	]
	for change in changes:
		var invalid := move.duplicate(true)
		change[1].call(invalid)
		check(not UfeMoveData.validate(invalid), "拒绝不合法分段/" + str(change[0]))
	var legacy_move: Dictionary = UfeContentDatabase.fighter("ultraman").moves.light1
	check(UfeMoveData.validate(legacy_move), "旧单次招式仍合法")
	var first := fixture(1, true)
	var modified := fixture(1, true)
	modified.fighters[0].definition.moves.light1.hit_groups["1"].damage = 36
	var new_sim := UfeMatchDirector.new(modified.fighters[0].definition, modified.fighters[1].definition, modified.rules, modified.states)
	check(first.content_fingerprint != new_sim.content_fingerprint, "段伤害修改改变内容指纹")

func standalone_replay() -> void:
	for facing in [1, -1]:
		var sim := fixture(facing, true)
		var loaded := UfeReplayRecorder.load_file(output_dir + "replay-" + str(facing) + ".json", sim.content_fingerprint)
		check(loaded != null, "独立进程载入分段回放")
		if loaded == null: continue
		for pair in loaded.frames: sim.step([UfeInputFrame.unpack(pair[0]), UfeInputFrame.unpack(pair[1])])
		check(sim.state_hash() == loaded.final_hash, "独立进程还原分段回放/" + str(facing))
	write("standalone-replay.json", {"errors": errors, "passed": errors.is_empty()})

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if "--baseline" in args:
		write("legacy-before.json", legacy())
	elif "--replay" in args:
		standalone_replay()
	else:
		if "--check-legacy" in args:
			var previous: Variant = JSON.parse_string(FileAccess.get_file_as_string(BASELINE))
			var current := legacy()
			check(previous is Dictionary and previous.size() == 25 and current.size() == 65, "旧基线与原主游戏掷返分组完整")
			for key in previous:
				check(current.has(key) and previous[key].digest == current[key].digest and previous[key].final_hash == current[key].final_hash and previous[key].content == current[key].content,
					"旧招式状态、事件与内容指纹逐tick基线一致/" + key)
			original_omega_trace(current)
			write("legacy-after.json", current)
		validation()
		for facing in [1, -1]:
			for kind in ["hit", "repeat", "guard", "guard_release", "whiff", "late_contact", "invulnerable", "frame_guard", "unblockable_group", "early_projectile", "restart", "beam_hit", "beam_guard", "beam_whiff"]:
				exercise(facing, kind)
		write("result.json", {"passed": errors.is_empty(), "errors": errors, "cases": cases, "legacy_checked": "--check-legacy" in args,
			"scope": "纯模拟夹具；未安装或代替任何人物/特效资源，不能作为美术验收"})
	print("MELEE_HIT_GROUPS " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
