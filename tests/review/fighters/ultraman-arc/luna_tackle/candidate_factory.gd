extends RefCounted
## 只读突进候选：复用已验证的正式模拟装配与原输入回放，不改三连工具。
const CONTACT_BOXES: Dictionary = {2: [[54, 77, 10, 16]], 3: [[59, 90, 10, 16]], 4: [[53, 77, 10, 16]]}
const Shared = preload("res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd")
static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema) == "ufeneo.luna.tackle-main-candidate.v1")
	assert(bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter) == "ultraman-arc__luna" and str(cfg.definition.id) == str(cfg.fighter))
	for flag in ["implemented", "playable", "select_visible", "transform_enabled"]: assert(not bool(cfg[flag]))
	assert(not cfg.bound_resources.is_empty())
	var bound: Dictionary = {}
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "月亮突进候选来源变化")
		bound[ProjectSettings.globalize_path(str(resource.path)).simplify_path()] = str(resource.sha256)
	for required in [
		"res://tests/review/fighters/ultraman-arc/luna_tackle/candidate_factory.gd",
		"res://tests/review/fighters/ultraman-arc/luna_tackle/main_driver.gd",
		"res://tests/review/fighters/ultraman-arc/luna_tackle/main_entry.gd",
		"res://tests/review/fighters/ultraman-arc/luna_tackle/main_game.gd",
		"res://tests/review/fighters/ultraman-arc/luna_tackle/logic_check.gd",
		"res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/candidate_view.gd",
		"res://content/fighters/ultraman-arc__luna/definition.json",
		"res://content/fighters/ultraman-arc/moves/tackle.json"]:
		assert(bound.has(ProjectSettings.globalize_path(required).simplify_path()), "缺少候选依赖SHA绑定")
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc__luna/definition.json")
	for flag in ["implemented", "playable", "select_visible"]: assert(not bool(flags[flag]))
	assert(cfg.definition.moves.size() == 1 and cfg.definition.moves.has("tackle"))
	assert(cfg.definition.state_frames.size() == 2)
	assert(cfg.presentation.manifest_data.clips.size() == 3)
	for action in ["tackle", "idle", "turn"]:
		assert(cfg.presentation.manifest_data.clips.has(action))
		var clip: Dictionary = cfg.presentation.manifest_data.clips[action]
		assert(str(clip.source_fighter) == "ultraman-arc__luna")
		assert(bound.has(ProjectSettings.globalize_path(str(clip.texture)).simplify_path()))
		assert(FileAccess.get_sha256(str(clip.texture)) == str(clip.atlas_sha256))
	for action in ["idle", "turn"]: assert(cfg.definition.state_frames.has(action))
	assert(not CONTACT_BOXES.is_empty(), "尚未确认突进实体接触框")
	var move: Dictionary = cfg.definition.moves.tackle
	var original: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc/moves/tackle.json")
	assert(int(move.damage) == 100 and move.frames.size() == original.frames.size())
	# 本人实体接触框需与已审注册结果一致；保留正式逐tick位移和时序。
	assert(int(move.startup) == 4 and int(move.active) == 9 and int(move.recovery) == 13)
	assert(not str(move.production_source).is_empty())
	for key in original:
		if key not in ["frames", "production_source"]:
			assert(move[key] == original[key], "禁止修改未授权突进规则")
	for index in range(original.frames.size()):
		var expected_boxes: Array = CONTACT_BOXES.get(int(original.frames[index].sprite), [])
		assert(move.frames[index].hitboxes.size() == expected_boxes.size(), "突进必须命中本人实际接触框")
		if not expected_boxes.is_empty(): assert(equal_numbers(move.frames[index].hitboxes[0], expected_boxes[0]), "本人接触框坐标不符")
		for key in original.frames[index]:
			if key not in ["hurtboxes", "hitboxes"]:
				assert(move.frames[index][key] == original.frames[index][key], "禁止修改原逐tick时序、位移和取消")
	assert(cfg.presentation.manifest_data.clips.tackle.rects.size() == 8)
	assert(cfg.presentation.manifest_data.clips.tackle.anchors.size() == 8)
	for anchor in cfg.presentation.manifest_data.clips.tackle.anchors:
		assert(equal_numbers(anchor, [160, 280]))
	assert(cfg.definition.command_table.size() == 1)
	assert(str(cfg.definition.command_table[0].move) == "tackle" and int(cfg.definition.command_table[0].buttons) == UfeInputFrame.CRUSH)
	assert(equal_numbers(cfg.definition.command_table[0].directions, [6]))
	cfg["_candidate_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg

static func make_match(cfg: Dictionary, direction: int, kind: String) -> UfeMatchDirector:
	return Shared.make_match(cfg, direction, kind)

static func verify_input_shape(tape: Dictionary) -> Array:
	var errors: Array = []
	if int(tape.direction) not in [-1, 1] or str(tape.kind) not in ["hit", "block", "whiff"]:
		return [{"kind": "invalid_tape_case"}]
	if tape.original_pairs.size() != 120 or tape.state_hashes.size() != 120:
		return [{"kind": "invalid_tape_length"}]
	for tick in range(120):
		var pair: Array = tape.original_pairs[tick]
		var first: Array = [int(tape.direction) if tick == 20 else 0, 0, UfeInputFrame.CRUSH if tick == 20 else 0]
		var second: Array = [0, 0, UfeInputFrame.GUARD if str(tape.kind) == "block" else 0]
		if pair.size() != 2 or not equal_numbers(pair[0], first) or not equal_numbers(pair[1], second):
			errors.append({"kind": "not_single_tackle_original_input", "tick": tick})
	return errors

static func verify_original_inputs(cfg: Dictionary, tape: Dictionary) -> Dictionary:
	var errors: Array = verify_input_shape(tape)
	if not errors.is_empty(): return {"errors": errors, "tick_count": 0}
	return Shared.verify_original_inputs(cfg, tape)

static func verify_case(_cfg: Dictionary, kind: String, moves: Dictionary, contacts: Dictionary, counts: Dictionary, damage: int) -> Array:
	var errors: Array = []
	if moves.size() != 1 or not moves.has("tackle"): errors.append({"kind": "unexpected_moves", "moves": moves.keys()})
	if kind in ["hit", "block"]:
		if contacts.size() != 1 or str(contacts.get("tackle", "")) != kind or int(counts.get("tackle", 0)) != 1:
			errors.append({"kind": "missing_or_repeated_real_contact", "expected": kind})
	elif not contacts.is_empty(): errors.append({"kind": "unexpected_whiff_contact"})
	var expected: int = 100 if kind == "hit" else 0
	if damage != expected: errors.append({"kind": "wrong_tackle_damage", "expected": expected, "actual": damage})
	return errors

static func verify_phases(trace: Array) -> Array:
	var phases: Dictionary = {}
	var errors: Array = []
	for row in trace:
		var own: Dictionary = row.pair[0]
		if str(own.move_id) == "tackle": phases[int(own.frame_sprite)] = true
	for phase in range(8):
		if not phases.has(phase): errors.append({"kind": "unreached_tackle_phase", "phase": phase})
	if trace.is_empty() or str(trace[-1].pair[0].state) != "idle" or not str(trace[-1].pair[0].move_id).is_empty():
		errors.append({"kind": "tackle_did_not_recover_to_idle"})
	return errors

static func equal_numbers(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size(): return false
	for index in range(actual.size()):
		if float(actual[index]) != float(expected[index]): return false
	return true

static func verify_motion(trace: Array, direction: int, kind: String) -> Array:
	var errors: Array = []
	if trace.is_empty(): return [{"kind": "empty_motion_trace"}]
	var first: Array = trace[0].pair
	var last: Array = trace[-1].pair
	var advance: int = (int(last[0].x)-int(first[0].x))*direction
	var pushback: int = (int(last[1].x)-int(first[1].x))*direction
	if advance != 27: errors.append({"kind": "wrong_real_forward_displacement", "expected": 27, "actual": advance})
	var expected_pushback: int = 8 if kind == "hit" else 0
	if pushback != expected_pushback: errors.append({"kind": "wrong_real_pushback", "expected": expected_pushback, "actual": pushback})
	for row in trace:
		for fighter in row.pair:
			if int(fighter.height) != 0 or str(fighter.state) in ["launch", "bounce", "down"]:
				errors.append({"kind": "unexpected_airborne_or_knockdown", "state": fighter.state})
	if str(last[1].state) != ("guard" if kind == "block" else "idle"):
		errors.append({"kind": "target_did_not_recover", "state": last[1].state})
	return errors
