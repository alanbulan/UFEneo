extends RefCounted
## 只读扫腿候选：复用已验证的正式模拟装配与原输入回放，不改三连工具。
const CONTACT_BOXES: Dictionary = {2: [[58, 5, 12, 12]], 3: [[60, 12, 12, 12]]}
const Shared = preload("res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd")
static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema) == "ufeneo.luna.sweep-main-candidate.v1")
	assert(bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter) == "ultraman-arc__luna" and str(cfg.definition.id) == str(cfg.fighter))
	for flag in ["implemented", "playable", "select_visible", "transform_enabled"]: assert(not bool(cfg[flag]))
	assert(not cfg.bound_resources.is_empty())
	var bound: Dictionary = {}
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "月亮扫腿候选来源变化")
		bound[ProjectSettings.globalize_path(str(resource.path)).simplify_path()] = str(resource.sha256)
	for required in [
		"res://tests/review/fighters/ultraman-arc/luna_sweep/candidate_factory.gd",
		"res://tests/review/fighters/ultraman-arc/luna_sweep/main_driver.gd",
		"res://tests/review/fighters/ultraman-arc/luna_sweep/main_entry.gd",
		"res://tests/review/fighters/ultraman-arc/luna_sweep/main_game.gd",
		"res://tests/review/fighters/ultraman-arc/luna_sweep/logic_check.gd",
		"res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/candidate_view.gd",
		"res://content/fighters/ultraman-arc__luna/definition.json",
		"res://content/fighters/ultraman-arc/moves/sweep.json"]:
		assert(bound.has(ProjectSettings.globalize_path(required).simplify_path()), "缺少候选依赖SHA绑定")
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc__luna/definition.json")
	for flag in ["implemented", "playable", "select_visible"]: assert(not bool(flags[flag]))
	assert(cfg.definition.moves.size() == 1 and cfg.definition.moves.has("sweep"))
	assert(cfg.definition.state_frames.size() == 5)
	assert(cfg.presentation.manifest_data.clips.size() == 6)
	for action in ["sweep", "idle", "turn", "crouch_start", "crouch", "crouch_rise"]:
		assert(cfg.presentation.manifest_data.clips.has(action))
		var clip: Dictionary = cfg.presentation.manifest_data.clips[action]
		assert(str(clip.source_fighter) == "ultraman-arc__luna")
		assert(bound.has(ProjectSettings.globalize_path(str(clip.texture)).simplify_path()))
		assert(FileAccess.get_sha256(str(clip.texture)) == str(clip.atlas_sha256))
	for action in ["idle", "turn", "crouch_start", "crouch", "crouch_rise"]: assert(cfg.definition.state_frames.has(action))
	for action in ["crouch_start", "crouch", "crouch_rise"]:
		var clip: Dictionary = cfg.presentation.manifest_data.clips[action]
		assert(clip.anchors.size() == 2 and clip.rects.size() == 2)
		for anchor in clip.anchors: assert(equal_numbers(anchor, [160, 280]))
	assert(not CONTACT_BOXES.is_empty(), "尚未确认扫腿实体接触框")
	var move: Dictionary = cfg.definition.moves.sweep
	var original: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc/moves/sweep.json")
	assert(int(move.damage) == 65 and move.frames.size() == original.frames.size())
	# 本人实体接触框需与已审注册结果一致；保留正式逐tick位移和时序。
	assert(int(move.startup) == 6 and int(move.active) == 7 and int(move.recovery) == 15)
	assert(not str(move.production_source).is_empty())
	for key in original:
		if key not in ["frames", "production_source"]:
			assert(move[key] == original[key], "禁止修改未授权扫腿规则")
	for index in range(original.frames.size()):
		var expected_boxes: Array = CONTACT_BOXES.get(int(original.frames[index].sprite), [])
		assert(move.frames[index].hitboxes.size() == expected_boxes.size(), "扫腿必须命中本人实际接触框")
		if not expected_boxes.is_empty(): assert(equal_numbers(move.frames[index].hitboxes[0], expected_boxes[0]), "本人接触框坐标不符")
		for key in original.frames[index]:
			if key not in ["hurtboxes", "hitboxes"]:
				assert(move.frames[index][key] == original.frames[index][key], "禁止修改原逐tick时序、位移和取消")
	assert(cfg.presentation.manifest_data.clips.sweep.rects.size() == 7)
	assert(cfg.presentation.manifest_data.clips.sweep.anchors.size() == 7)
	for anchor in cfg.presentation.manifest_data.clips.sweep.anchors:
		assert(equal_numbers(anchor, [160, 280]))
	assert(cfg.definition.command_table.size() == 1)
	assert(str(cfg.definition.command_table[0].move) == "sweep" and int(cfg.definition.command_table[0].buttons) == UfeInputFrame.HEAVY)
	assert(equal_numbers(cfg.definition.command_table[0].directions, [1, 2, 3]))
	assert(cfg.definition.command_table[0].states.size() == 1 and str(cfg.definition.command_table[0].states[0]) == "crouch")
	assert(str(move.level) == "low" and bool(move.knockdown))
	cfg["_candidate_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg

static func make_match(cfg: Dictionary, direction: int, kind: String) -> UfeMatchDirector:
	return Shared.make_match(cfg, direction, "hit" if kind == "standing_guard" else kind)

static func verify_input_shape(tape: Dictionary) -> Array:
	var errors: Array = []
	if int(tape.direction) not in [-1, 1] or str(tape.kind) not in ["hit", "block", "whiff", "standing_guard"]:
		return [{"kind": "invalid_tape_case"}]
	if tape.original_pairs.size() != 120 or tape.state_hashes.size() != 120:
		return [{"kind": "invalid_tape_length"}]
	for tick in range(120):
		var pair: Array = tape.original_pairs[tick]
		var first: Array = [0, -1 if tick >= 10 and tick < 80 else 0, UfeInputFrame.HEAVY if tick == 32 else 0]
		var second: Array = [0, -1 if str(tape.kind) == "block" else 0, UfeInputFrame.GUARD if str(tape.kind) in ["block", "standing_guard"] else 0]
		if pair.size() != 2 or not equal_numbers(pair[0], first) or not equal_numbers(pair[1], second):
			errors.append({"kind": "not_single_sweep_original_input", "tick": tick})
	return errors

static func verify_original_inputs(cfg: Dictionary, tape: Dictionary) -> Dictionary:
	var errors: Array = verify_input_shape(tape)
	if not errors.is_empty(): return {"errors": errors, "tick_count": 0}
	var sim := make_match(cfg, int(tape.direction), str(tape.kind))
	assert(str(tape.candidate_contract_sha256) == str(cfg._candidate_contract_sha256))
	assert(sim.content_fingerprint == str(tape.simulation_fingerprint))
	for tick in range(tape.original_pairs.size()):
		var pair: Array = tape.original_pairs[tick]
		sim.step([UfeInputFrame.unpack(pair[0]), UfeInputFrame.unpack(pair[1])])
		if sim.state_hash() != str(tape.state_hashes[tick]): errors.append({"tick": tick, "kind": "state_hash"})
	return {"errors": errors, "final_hash": sim.state_hash(), "tick_count": sim.tick}

static func verify_case(_cfg: Dictionary, kind: String, moves: Dictionary, contacts: Dictionary, counts: Dictionary, damage: int) -> Array:
	var errors: Array = []
	if moves.size() != 1 or not moves.has("sweep"): errors.append({"kind": "unexpected_moves", "moves": moves.keys()})
	var expected_contact: String = "hit" if kind == "standing_guard" else kind
	if kind in ["hit", "block", "standing_guard"]:
		if contacts.size() != 1 or str(contacts.get("sweep", "")) != expected_contact or int(counts.get("sweep", 0)) != 1:
			errors.append({"kind": "missing_or_repeated_real_contact", "expected": expected_contact})
	elif not contacts.is_empty(): errors.append({"kind": "unexpected_whiff_contact"})
	var expected: int = 65 if kind in ["hit", "standing_guard"] else 0
	if damage != expected: errors.append({"kind": "wrong_sweep_damage", "expected": expected, "actual": damage})
	return errors

static func verify_phases(trace: Array) -> Array:
	var phases: Dictionary = {}
	var errors: Array = []
	for row in trace:
		var own: Dictionary = row.pair[0]
		if str(own.move_id) == "sweep": phases[int(own.frame_sprite)] = true
	for phase in range(7):
		if not phases.has(phase): errors.append({"kind": "unreached_sweep_phase", "phase": phase})
	if trace.is_empty() or str(trace[-1].pair[0].state) != "idle" or not str(trace[-1].pair[0].move_id).is_empty():
		errors.append({"kind": "sweep_did_not_recover_to_idle"})
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
	if advance != 0: errors.append({"kind": "wrong_real_forward_displacement", "expected": 0, "actual": advance})
	var hit: bool = kind in ["hit", "standing_guard"]
	if pushback != (8 if hit else 0): errors.append({"kind": "wrong_real_pushback", "actual": pushback})
	var own_states: Dictionary = {}
	var target_states: Dictionary = {}
	var own_phases: Dictionary = {}
	var transitions: Array = []
	for row in trace:
		var own: Dictionary = row.pair[0]
		var target: Dictionary = row.pair[1]
		own_states[str(own.state)] = true
		own_phases[str(own.state)+":"+str(int(own.frame_sprite))] = true
		target_states[str(target.state)] = true
		if transitions.is_empty() or transitions[-1] != str(target.state): transitions.append(str(target.state))
		for fighter in row.pair:
			if int(fighter.height) != 0 or str(fighter.state) in ["launch", "bounce"]:
				errors.append({"kind": "unexpected_airborne", "state": fighter.state})
	for required in ["crouch_start", "crouch", "crouch_rise"]:
		if not own_states.has(required): errors.append({"kind": "missing_real_crouch_transition", "state": required})
		for phase in range(2):
			if not own_phases.has(required+":"+str(phase)): errors.append({"kind": "missing_real_crouch_phase", "state": required, "phase": phase})
	if str(trace[31].pair[0].state) != "crouch": errors.append({"kind": "sweep_not_started_from_real_crouch"})
	if hit:
		var down_index: int = transitions.find("down")
		var wake_index: int = transitions.find("wake")
		if down_index < 0 or wake_index <= down_index: errors.append({"kind": "missing_real_down_wake_sequence", "states": transitions})
	elif target_states.has("down") or target_states.has("wake"):
		errors.append({"kind": "unexpected_knockdown", "states": transitions})
	if kind == "block" and not target_states.has("crouch_blockstun"):
		errors.append({"kind": "missing_low_guard_blockstun"})
	if kind == "standing_guard" and not target_states.has("guard"):
		errors.append({"kind": "missing_standing_guard_before_hit"})
	var final_state: String = "crouch_guard" if kind == "block" else "guard" if kind == "standing_guard" else "idle"
	if str(last[1].state) != final_state: errors.append({"kind": "target_did_not_recover", "expected": final_state, "state": last[1].state})
	return errors
