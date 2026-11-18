class_name UfeCandidateHarness
extends RefCounted
## 通用数据驱动候选对局审片与逻辑验证底座。
## 负责读取 JSON 合同、构造候选对局、按 tick 喂输入磁带、校验 HUD 安全区与输出结构化 trace。


static func load_contract(path: String, expected_schema: String = "") -> Dictionary:
	assert(FileAccess.file_exists(path), "缺少候选合同文件: %s" % path)
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	if not expected_schema.is_empty():
		assert(str(cfg.get("schema", "")) == expected_schema, "候选合同 schema 不匹配: %s" % str(cfg.get("schema", "")))
	for resource in cfg.get("bound_resources", []):
		var res_path := str(resource.get("path", ""))
		var expected_sha := str(resource.get("sha256", ""))
		assert(not res_path.is_empty() and FileAccess.file_exists(res_path), "候选依赖文件缺失: %s" % res_path)
		assert(FileAccess.get_sha256(res_path) == expected_sha, "候选依赖 SHA256 不匹配: %s" % res_path)
	cfg["_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg


static func build_definition(raw: Dictionary) -> UfeFighterDefinition:
	var result := UfeFighterDefinition.new()
	result.id = str(raw.get("id", ""))
	result.display_name = str(raw.get("display_name", result.id))
	result.max_health = int(raw.get("max_health", 1000))
	result.walk_speed = int(raw.get("walk_speed", 2))
	result.jump_speed = int(raw.get("jump_speed", 16))
	result.body_radius = int(raw.get("body_radius", 30))
	var moves_raw: Variant = raw.get("moves", {})
	result.moves = (moves_raw as Dictionary).duplicate(true) if moves_raw is Dictionary else {}
	for move_id in result.moves:
		assert(UfeMoveData.validate(result.moves[move_id]), "候选招式数据不合法: %s/%s" % [result.id, move_id])
	var commands_raw: Variant = raw.get("command_table", [])
	result.command_table = (commands_raw as Array).duplicate(true) if commands_raw is Array else []
	var frames_raw: Variant = raw.get("state_frames", {})
	result.state_frames = (frames_raw as Dictionary).duplicate(true) if frames_raw is Dictionary else {}
	return result


static func build_match(cfg: Dictionary, direction: int = 1, gap_override: int = -1, allow_pilot: bool = false) -> UfeMatchDirector:
	assert(direction in [-1, 1], "无效初始朝向: %d" % direction)
	var first: UfeFighterDefinition = build_definition(cfg.definition) if cfg.has("definition") else UfeContentDatabase.fighter(str(cfg.get("fighter", "ultraman")), allow_pilot)
	var second: UfeFighterDefinition = build_definition(cfg.opponent_definition) if cfg.has("opponent_definition") else UfeContentDatabase.fighter(str(cfg.get("opponent", "zetton")), allow_pilot)
	var sim := UfeMatchDirector.new(first, second, load("res://content/rules/neo.tres"), UfeContentDatabase.states())
	var gap: int = gap_override if gap_override >= 0 else int(cfg.get("gap", 120))
	@warning_ignore("integer_division")
	var half_gap: int = gap / 2
	sim.fighters[0].x = UfeStateRules.clamp_stage_x(640 - direction * half_gap)
	sim.fighters[1].x = UfeStateRules.clamp_stage_x(sim.fighters[0].x + direction * gap)
	sim.fighters[0].facing = direction
	sim.fighters[1].facing = -direction
	var initial_hp: Array = cfg.get("initial_hp", [])
	var initial_energy: Array = cfg.get("initial_energy", [])
	var initial_stamina: Array = cfg.get("initial_stamina", [])
	for i in range(2):
		if i < initial_hp.size():
			sim.fighters[i].stats.hp = int(initial_hp[i])
		if i < initial_energy.size():
			sim.fighters[i].stats.energy = int(initial_energy[i])
		if i < initial_stamina.size():
			sim.fighters[i].stats.stamina = int(initial_stamina[i])
	return sim


static func unpack_pair(pair_data: Array, direction: int = 1, mirror_x: bool = false) -> Array:
	assert(pair_data.size() == 2, "输入磁带每 tick 必须包含双方输入")
	var result: Array = []
	for index in range(2):
		var raw: Array = (pair_data[index] as Array).duplicate()
		if mirror_x and raw.size() >= 1:
			raw[0] = int(raw[0]) * direction
		result.append(UfeInputFrame.unpack(raw))
	return result


static func rect_array(rect: Rect2) -> Array:
	return [rect.position.x, rect.position.y, rect.size.x, rect.size.y]


static func check_safe_rect(view: UfeSideView, hud: UfeBattleHUD, frame_index: int, tolerance: float = 0.1) -> Array:
	var violations: Array = []
	if view == null or hud == null:
		return violations
	var safe: Rect2 = hud.battle_safe_rect()
	var allowed: Rect2 = safe.grow(tolerance)
	for i in range(view.fighters.size()):
		var sprite: Sprite2D = view.fighters[i]
		if sprite == null or not sprite.visible or sprite.texture == null:
			continue
		var bounds: Rect2 = view.get_global_transform() * view._sprite_bounds(sprite)
		if not allowed.encloses(bounds):
			violations.append({
				"frame": frame_index,
				"kind": "fighter_outside_safe_rect",
				"player": i,
				"bounds": rect_array(bounds),
				"safe": rect_array(safe),
			})
	for node in view.framing_entities:
		if node == null or not node.visible or node.texture == null:
			continue
		var bounds: Rect2 = view.get_global_transform() * view._sprite_bounds(node)
		if not allowed.encloses(bounds):
			violations.append({
				"frame": frame_index,
				"kind": "entity_outside_safe_rect",
				"texture": node.texture.resource_path,
				"bounds": rect_array(bounds),
				"safe": rect_array(safe),
			})
	return violations


static func capture_fighter_row(fighter: UfeFighter, view: UfeSideView = null, manifest: Dictionary = {}) -> Dictionary:
	var pose: Dictionary = fighter.visual_pose()
	var frame_data: Dictionary = fighter.frame()
	var animation: Dictionary = {}
	if view != null and not manifest.is_empty():
		animation = view._animation(fighter, manifest)
	return {
		"id": fighter.definition.id,
		"state": fighter.state,
		"state_tick": fighter.state_tick,
		"move": fighter.move_id,
		"move_tick": fighter.move_tick,
		"x": fighter.x,
		"height": fighter.height,
		"vx": fighter.vx,
		"vy": fighter.vy,
		"facing": fighter.facing,
		"hp": fighter.stats.hp,
		"energy": fighter.stats.energy,
		"stamina": fighter.stats.stamina,
		"connected": fighter.combat.connected,
		"confirmed": fighter.combat.confirmed,
		"blocked": fighter.combat.blocked,
		"combo": fighter.combat.combo,
		"frame_sprite": int(frame_data.get("sprite", 0)),
		"pose": pose,
		"animation": animation,
	}


static func run_tape(sim: UfeMatchDirector, inputs: Array, options: Dictionary = {}) -> Dictionary:
	var view: UfeSideView = options.get("view", null)
	var hud: UfeBattleHUD = options.get("hud", null)
	var manifests: Array = options.get("manifests", [])
	var direction: int = int(options.get("direction", 1))
	var mirror_x: bool = bool(options.get("mirror_x", false))
	var tolerance: float = float(options.get("tolerance", 0.1))
	var trace: Array = []
	var original_pairs: Array = []
	var state_hashes: Array = []
	var all_violations: Array = []
	for tick_index in range(inputs.size()):
		var pair := unpack_pair(inputs[tick_index] as Array, direction, mirror_x)
		var packed := [pair[0].pack(), pair[1].pack()]
		original_pairs.append(packed)
		sim.step(pair)
		var state_hash := sim.state_hash()
		state_hashes.append(state_hash)
		if hud != null:
			hud.update_match(sim, "", 0, false)
		if view != null:
			view.update_view()
		var violations: Array = []
		if view != null and hud != null:
			violations = check_safe_rect(view, hud, tick_index, tolerance)
			all_violations.append_array(violations)
		var pair_rows: Array = []
		for i in range(sim.fighters.size()):
			var manifest: Dictionary = manifests[i] if i < manifests.size() else (view.manifests[i] if view != null and i < view.manifests.size() else {})
			pair_rows.append(capture_fighter_row(sim.fighters[i], view, manifest))
		var row: Dictionary = {
			"frame": tick_index,
			"tick": sim.tick,
			"state_hash": state_hash,
			"original_inputs": packed,
			"pair": pair_rows,
			"events": sim.events.duplicate(true),
			"projectiles": sim.projectiles.duplicate(true),
		}
		if hud != null:
			row["safe_rect"] = rect_array(hud.battle_safe_rect())
		if view != null:
			row["camera_zoom"] = view.camera_zoom
			row["framed_bounds"] = rect_array(view.framed_bounds)
		if not violations.is_empty():
			row["safe_violations"] = violations
		trace.append(row)
	return {
		"content_fingerprint": sim.content_fingerprint,
		"final_hash": sim.state_hash(),
		"original_pairs": original_pairs,
		"state_hashes": state_hashes,
		"safe_violations": all_violations,
		"trace": trace,
	}


static func verify_replay(cfg: Dictionary, tape: Dictionary, gap_override: int = -1, allow_pilot: bool = false) -> Dictionary:
	var direction: int = int(tape.get("direction", 1))
	var sim := build_match(cfg, direction, gap_override, allow_pilot)
	var errors: Array = []
	var expected_fp := str(tape.get("simulation_fingerprint", tape.get("content_fingerprint", "")))
	if not expected_fp.is_empty() and sim.content_fingerprint != expected_fp:
		errors.append({"kind": "content_fingerprint_mismatch", "expected": expected_fp, "actual": sim.content_fingerprint})
	var pairs: Array = tape.get("original_pairs", [])
	var hashes: Array = tape.get("state_hashes", [])
	if pairs.size() != hashes.size():
		errors.append({"kind": "tape_length_mismatch", "pairs": pairs.size(), "hashes": hashes.size()})
	var count := mini(pairs.size(), hashes.size())
	for tick_index in range(count):
		var pair := unpack_pair(pairs[tick_index] as Array)
		sim.step(pair)
		var actual_hash := sim.state_hash()
		if actual_hash != str(hashes[tick_index]):
			errors.append({"tick": tick_index, "kind": "state_hash_mismatch", "expected": str(hashes[tick_index]), "actual": actual_hash})
	return {
		"errors": errors,
		"final_hash": sim.state_hash(),
		"tick_count": sim.tick,
	}


static func write_json(path: String, payload: Dictionary, overwrite: bool = false) -> Error:
	if not overwrite and FileAccess.file_exists(path):
		return ERR_ALREADY_EXISTS
	var out_file := FileAccess.open(path, FileAccess.WRITE)
	if out_file == null:
		return FileAccess.get_open_error()
	out_file.store_string(JSON.stringify(payload, "\t"))
	out_file.close()
	return OK
