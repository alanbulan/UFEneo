extends RefCounted
## 只读重击候选：复用已验证的正式模拟装配与原输入回放，不改三连工具。
const Shared = preload("res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd")
static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema) == "ufeneo.luna.heavy-main-candidate.v1")
	assert(bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter) == "ultraman-arc__luna" and str(cfg.definition.id) == str(cfg.fighter))
	for flag in ["implemented", "playable", "select_visible", "transform_enabled"]: assert(not bool(cfg[flag]))
	assert(not cfg.bound_resources.is_empty())
	var bound: Dictionary = {}
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "月亮重击候选来源变化")
		bound[ProjectSettings.globalize_path(str(resource.path)).simplify_path()] = str(resource.sha256)
	for required in [
		"res://tests/review/fighters/ultraman-arc/luna_heavy/candidate_factory.gd",
		"res://tests/review/fighters/ultraman-arc/luna_heavy/main_driver.gd",
		"res://tests/review/fighters/ultraman-arc/luna_heavy/main_entry.gd",
		"res://tests/review/fighters/ultraman-arc/luna_heavy/main_game.gd",
		"res://tests/review/fighters/ultraman-arc/luna_heavy/logic_check.gd",
		"res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/candidate_view.gd",
		"res://content/fighters/ultraman-arc__luna/definition.json",
		"res://content/fighters/ultraman-arc/moves/heavy.json"]:
		assert(bound.has(ProjectSettings.globalize_path(required).simplify_path()), "缺少候选依赖SHA绑定")
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc__luna/definition.json")
	for flag in ["implemented", "playable", "select_visible"]: assert(not bool(flags[flag]))
	assert(cfg.definition.moves.size() == 1 and cfg.definition.moves.has("heavy"))
	assert(cfg.definition.state_frames.size() == 2)
	assert(cfg.presentation.manifest_data.clips.size() == 3)
	for action in ["heavy", "idle", "turn"]:
		assert(cfg.presentation.manifest_data.clips.has(action))
		var clip: Dictionary = cfg.presentation.manifest_data.clips[action]
		assert(str(clip.source_fighter) == "ultraman-arc__luna")
		assert(bound.has(ProjectSettings.globalize_path(str(clip.texture)).simplify_path()))
		assert(FileAccess.get_sha256(str(clip.texture)) == str(clip.atlas_sha256))
	for action in ["idle", "turn"]: assert(cfg.definition.state_frames.has(action))
	var move: Dictionary = cfg.definition.moves.heavy
	var original: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc/moves/heavy.json")
	assert(int(move.damage) == 100 and move.frames.size() == original.frames.size())
	# 本人实体拳面只在第3相；第4相已收拳，不沿用本体空气判定。
	assert(int(move.startup) == 9 and int(move.active) == 4 and int(move.recovery) == 15)
	assert(not str(move.production_source).is_empty())
	for key in original:
		if key not in ["frames", "active", "recovery", "production_source"]:
			assert(move[key] == original[key], "禁止修改未授权重击规则")
	for index in range(original.frames.size()):
		var expected_boxes: Array = [[40, 49, 10, 10]] if int(original.frames[index].sprite) == 3 else []
		assert(move.frames[index].hitboxes.size() == expected_boxes.size(), "重击必须命中本人实际拳面")
		if not expected_boxes.is_empty(): assert(equal_numbers(move.frames[index].hitboxes[0], expected_boxes[0]), "本人拳面坐标不符")
		for key in original.frames[index]:
			if key not in ["hurtboxes", "hitboxes"]:
				assert(move.frames[index][key] == original.frames[index][key], "禁止修改原逐tick时序、位移和取消")
	assert(cfg.presentation.manifest_data.clips.heavy.rects.size() == 7)
	assert(cfg.definition.command_table.size() == 1)
	assert(str(cfg.definition.command_table[0].move) == "heavy" and int(cfg.definition.command_table[0].buttons) == UfeInputFrame.HEAVY)
	cfg["_candidate_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg

static func make_match(cfg: Dictionary, direction: int, kind: String) -> UfeMatchDirector:
	return Shared.make_match(cfg, direction, kind)

static func verify_input_shape(tape: Dictionary) -> Array:
	var errors: Array = []
	if tape.original_pairs.size() != 120 or tape.state_hashes.size() != 120:
		return [{"kind": "invalid_tape_length"}]
	for tick in range(120):
		var pair: Array = tape.original_pairs[tick]
		var first: Array = [0, 0, UfeInputFrame.HEAVY if tick == 20 else 0]
		var second: Array = [0, 0, UfeInputFrame.GUARD if str(tape.kind) == "block" else 0]
		if pair.size() != 2 or not equal_numbers(pair[0], first) or not equal_numbers(pair[1], second):
			errors.append({"kind": "not_single_heavy_original_input", "tick": tick})
	return errors

static func verify_original_inputs(cfg: Dictionary, tape: Dictionary) -> Dictionary:
	var errors: Array = verify_input_shape(tape)
	if not errors.is_empty(): return {"errors": errors, "tick_count": 0}
	return Shared.verify_original_inputs(cfg, tape)

static func verify_case(_cfg: Dictionary, kind: String, moves: Dictionary, contacts: Dictionary, counts: Dictionary, damage: int) -> Array:
	var errors: Array = []
	if moves.size() != 1 or not moves.has("heavy"): errors.append({"kind": "unexpected_moves", "moves": moves.keys()})
	if kind in ["hit", "block"]:
		if contacts.size() != 1 or str(contacts.get("heavy", "")) != kind or int(counts.get("heavy", 0)) != 1:
			errors.append({"kind": "missing_or_repeated_real_contact", "expected": kind})
	elif not contacts.is_empty(): errors.append({"kind": "unexpected_whiff_contact"})
	var expected: int = 100 if kind == "hit" else 0
	if damage != expected: errors.append({"kind": "wrong_heavy_damage", "expected": expected, "actual": damage})
	return errors

static func verify_phases(trace: Array) -> Array:
	var phases: Dictionary = {}
	var errors: Array = []
	for row in trace:
		var own: Dictionary = row.pair[0]
		if str(own.move_id) == "heavy": phases[int(own.frame_sprite)] = true
	for phase in range(7):
		if not phases.has(phase): errors.append({"kind": "unreached_heavy_phase", "phase": phase})
	if trace.is_empty() or str(trace[-1].pair[0].state) != "idle" or not str(trace[-1].pair[0].move_id).is_empty():
		errors.append({"kind": "heavy_did_not_recover_to_idle"})
	return errors

static func equal_numbers(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size(): return false
	for index in range(actual.size()):
		if float(actual[index]) != float(expected[index]): return false
	return true
