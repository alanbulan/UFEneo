extends RefCounted
## 只读冲刺飞踢候选：复用已验证的正式模拟装配与原输入回放，不改三连工具。
const CONTACT_BOXES: Dictionary = {2: [[66, 52, 9, 12]], 3: [[63, 61, 10, 10]]}
const HIT_GAP: int = 140
const WHIFF_GAP: int = 320
const Shared = preload("res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd")
static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema) == "ufeneo.luna.dash_heavy-main-candidate.v1")
	assert(bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter) == "ultraman-arc__luna" and str(cfg.definition.id) == str(cfg.fighter))
	for flag in ["implemented", "playable", "select_visible", "transform_enabled"]: assert(not bool(cfg[flag]))
	assert(not cfg.bound_resources.is_empty())
	var bound: Dictionary = {}
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "月亮冲刺飞踢候选来源变化")
		bound[ProjectSettings.globalize_path(str(resource.path)).simplify_path()] = str(resource.sha256)
	for required in [
		"res://tests/review/fighters/ultraman-arc/luna_dash_heavy/candidate_factory.gd",
		"res://tests/review/fighters/ultraman-arc/luna_dash_heavy/main_driver.gd",
		"res://tests/review/fighters/ultraman-arc/luna_dash_heavy/main_entry.gd",
		"res://tests/review/fighters/ultraman-arc/luna_dash_heavy/main_game.gd",
		"res://tests/review/fighters/ultraman-arc/luna_dash_heavy/logic_check.gd",
		"res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd",
		"res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/candidate_view.gd",
		"res://content/fighters/ultraman-arc__luna/definition.json",
		"res://content/fighters/ultraman-arc/moves/dash_heavy.json"]:
		assert(bound.has(ProjectSettings.globalize_path(required).simplify_path()), "缺少候选依赖SHA绑定")
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc__luna/definition.json")
	for flag in ["implemented", "playable", "select_visible"]: assert(not bool(flags[flag]))
	assert(cfg.definition.moves.size() == 1 and cfg.definition.moves.has("dash_heavy"))
	assert(cfg.definition.state_frames.size() == 5)
	assert(cfg.presentation.manifest_data.clips.size() == 8)
	for action in ["dash_heavy", "idle", "turn", "walk_forward", "walk_back", "dash_start", "dash", "dash_stop"]:
		assert(cfg.presentation.manifest_data.clips.has(action))
		var clip: Dictionary = cfg.presentation.manifest_data.clips[action]
		assert(str(clip.source_fighter) == "ultraman-arc__luna")
		assert(bound.has(ProjectSettings.globalize_path(str(clip.texture)).simplify_path()))
		assert(FileAccess.get_sha256(str(clip.texture)) == str(clip.atlas_sha256))
	for action in ["idle", "turn", "walk_forward", "walk_back", "dash"]: assert(cfg.definition.state_frames.has(action))
	assert(not CONTACT_BOXES.is_empty(), "尚未确认冲刺飞踢实体接触框")
	var move: Dictionary = cfg.definition.moves.dash_heavy
	var original: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc/moves/dash_heavy.json")
	assert(int(move.damage) == 65 and move.frames.size() == original.frames.size())
	# 本人实体接触框需与已审注册结果一致；保留正式逐tick位移和时序。
	assert(int(move.startup) == 4 and int(move.active) == 7 and int(move.recovery) == 11)
	assert(not str(move.production_source).is_empty())
	for key in original:
		if key not in ["frames", "production_source"]:
			assert(move[key] == original[key], "禁止修改未授权冲刺飞踢规则")
	for index in range(original.frames.size()):
		var expected_boxes: Array = CONTACT_BOXES.get(int(original.frames[index].sprite), [])
		assert(move.frames[index].hitboxes.size() == expected_boxes.size(), "冲刺飞踢必须命中本人实际接触框")
		if not expected_boxes.is_empty(): assert(equal_numbers(move.frames[index].hitboxes[0], expected_boxes[0]), "本人接触框坐标不符")
		for key in original.frames[index]:
			if key not in ["hurtboxes", "hitboxes"]:
				assert(move.frames[index][key] == original.frames[index][key], "禁止修改原逐tick时序、位移和取消")
	assert(cfg.presentation.manifest_data.clips.dash_heavy.rects.size() == 6)
	assert(cfg.presentation.manifest_data.clips.dash_heavy.anchors.size() == 6)
	for anchor in cfg.presentation.manifest_data.clips.dash_heavy.anchors:
		assert(equal_numbers(anchor, [160, 280]))
	assert(cfg.definition.command_table.size() == 1)
	assert(str(cfg.definition.command_table[0].move) == "dash_heavy" and int(cfg.definition.command_table[0].buttons) == UfeInputFrame.HEAVY)
	assert(equal_numbers(cfg.definition.command_table[0].directions, [0]))
	assert(cfg.definition.command_table[0].states == ["dash"])
	assert(not bool(cfg.dependency_review.strict_size_accepted))
	assert(not bool(cfg.dependency_review.complete_dash_cycle_accepted))
	assert(equal_numbers(cfg.dependency_review.exercised_dash_phases, [0,1,2,3,4]))
	assert(equal_numbers(cfg.dependency_review.unexercised_dash_phases, [5,6,7,8]))
	assert(int(cfg.dependency_review.initial_gap.hit) == HIT_GAP and int(cfg.dependency_review.initial_gap.block) == HIT_GAP)
	assert(int(cfg.dependency_review.initial_gap.whiff) == WHIFF_GAP)
	cfg["_candidate_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg

static func make_match(cfg: Dictionary, direction: int, kind: String) -> UfeMatchDirector:
	var sim: UfeMatchDirector = Shared.make_match(cfg, direction, kind)
	sim.fighters[1].x = sim.fighters[0].x + direction * (WHIFF_GAP if kind == "whiff" else HIT_GAP)
	return sim

static func verify_input_shape(tape: Dictionary) -> Array:
	var errors: Array = []
	if int(tape.direction) not in [-1, 1] or str(tape.kind) not in ["hit", "block", "whiff"]:
		return [{"kind": "invalid_tape_case"}]
	if tape.original_pairs.size() != 120 or tape.state_hashes.size() != 120:
		return [{"kind": "invalid_tape_length"}]
	for tick in range(120):
		var pair: Array = tape.original_pairs[tick]
		var first: Array = [int(tape.direction) if tick in [20, 22] else 0, 0, UfeInputFrame.HEAVY if tick == 34 else 0]
		var second: Array = [0, 0, UfeInputFrame.GUARD if str(tape.kind) == "block" else 0]
		if pair.size() != 2 or not equal_numbers(pair[0], first) or not equal_numbers(pair[1], second):
			errors.append({"kind": "not_double_forward_then_heavy_original_input", "tick": tick})
	return errors

static func verify_original_inputs(cfg: Dictionary, tape: Dictionary) -> Dictionary:
	var errors: Array = verify_input_shape(tape)
	if not errors.is_empty(): return {"errors": errors, "tick_count": 0}
	assert(str(tape.candidate_contract_sha256) == str(cfg._candidate_contract_sha256))
	var sim := make_match(cfg, int(tape.direction), str(tape.kind))
	assert(sim.content_fingerprint == str(tape.simulation_fingerprint))
	for tick in range(tape.original_pairs.size()):
		var pair: Array = tape.original_pairs[tick]
		sim.step([UfeInputFrame.unpack(pair[0]), UfeInputFrame.unpack(pair[1])])
		if sim.state_hash() != str(tape.state_hashes[tick]): errors.append({"tick":tick,"kind":"state_hash"})
	return {"errors":errors,"final_hash":sim.state_hash(),"tick_count":sim.tick}

static func verify_case(_cfg: Dictionary, kind: String, moves: Dictionary, contacts: Dictionary, counts: Dictionary, damage: int) -> Array:
	var errors: Array = []
	if moves.size() != 1 or not moves.has("dash_heavy"): errors.append({"kind": "unexpected_moves", "moves": moves.keys()})
	if kind in ["hit", "block"]:
		if contacts.size() != 1 or str(contacts.get("dash_heavy", "")) != kind or int(counts.get("dash_heavy", 0)) != 1:
			errors.append({"kind": "missing_or_repeated_real_contact", "expected": kind})
	elif not contacts.is_empty(): errors.append({"kind": "unexpected_whiff_contact"})
	var expected: int = 65 if kind == "hit" else 0
	if damage != expected: errors.append({"kind": "wrong_dash_heavy_damage", "expected": expected, "actual": damage})
	return errors

static func verify_phases(trace: Array) -> Array:
	var phases: Dictionary = {}
	var phase_order: Array = []
	var saw_dash := false
	var dash_phases: Dictionary = {}
	var dash_before_attack := false
	var errors: Array = []
	for row in trace:
		var own: Dictionary = row.pair[0]
		if str(own.state) == "dash":
			saw_dash = true
			dash_phases[int(own.frame_sprite)] = true
		if str(own.move_id) == "dash_heavy":
			phases[int(own.frame_sprite)] = true
			if phase_order.is_empty() or int(phase_order[-1]) != int(own.frame_sprite): phase_order.append(int(own.frame_sprite))
			dash_before_attack = saw_dash
	if not equal_numbers(phase_order, [0,1,2,3,4,5]): errors.append({"kind": "wrong_six_phase_order", "actual": phase_order})
	if not dash_before_attack: errors.append({"kind":"missing_real_dash_before_heavy"})
	for phase in range(5):
		if not dash_phases.has(phase): errors.append({"kind": "missing_dash_prerequisite_phase", "phase": phase})
	if dash_phases.size() != 5: errors.append({"kind": "unexpected_dash_phase_scope", "actual": dash_phases.keys()})
	for phase in range(6):
		if not phases.has(phase): errors.append({"kind": "unreached_dash_heavy_phase", "phase": phase})
	if trace.is_empty() or str(trace[-1].pair[0].state) != "idle" or not str(trace[-1].pair[0].move_id).is_empty():
		errors.append({"kind": "dash_heavy_did_not_recover_to_idle"})
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
	if advance != 103: errors.append({"kind": "wrong_real_forward_displacement", "expected": 103, "actual": advance})
	var expected_pushback: int = 8 if kind == "hit" else 0
	if pushback != expected_pushback: errors.append({"kind": "wrong_real_pushback", "expected": expected_pushback, "actual": pushback})
	var airborne := false
	var landed_during_recovery := false
	var max_height: int = 0
	for row in trace:
		var own: Dictionary = row.pair[0]
		max_height = maxi(max_height, int(own.height))
		if int(own.height) > 0: airborne = true
		if airborne and int(own.height) == 0 and str(own.move_id) == "dash_heavy" and int(own.frame_sprite) in [4, 5]: landed_during_recovery = true
		if int(row.pair[1].height) != 0: errors.append({"kind": "target_unexpected_airborne"})
		for fighter in row.pair:
			if str(fighter.state) in ["launch", "bounce", "down"]:
				errors.append({"kind": "unexpected_knockdown", "state": fighter.state})
	if not airborne or max_height != 10: errors.append({"kind": "original_jump_arc_missing", "max_height": max_height})
	if not landed_during_recovery: errors.append({"kind": "finish_on_landing_truncated_recovery"})
	if str(last[1].state) != ("guard" if kind == "block" else "idle"):
		errors.append({"kind": "target_did_not_recover", "state": last[1].state})
	return errors

static func animation_matches(animation: Dictionary, sprite: int, cfg: Dictionary) -> bool:
	if animation.is_empty(): return false
	var clip: Dictionary = cfg.presentation.manifest_data.clips[str(animation.key)]
	return int(animation.index) + int(clip.get("simulation_sprite_offset", 0)) == sprite
