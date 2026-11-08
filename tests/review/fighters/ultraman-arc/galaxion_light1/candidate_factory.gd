extends RefCounted
@warning_ignore_start("integer_division")
## 银河本人单直拳；原04护架复用为起手，原00–02接触保持；无三连。
const ID := "ultraman-arc__galaxion"
const CLOCKS := [2,2,2,2,12]

static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema)=="ufeneo.galaxion.light1-main-candidate.v1" and bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter)==ID and str(cfg.definition.id)==ID and str(cfg.opponent)=="zetton")
	for flag in ["implemented","playable","select_visible","transform_enabled"]:assert(not bool(cfg[flag]))
	var bound: Dictionary = {}
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path))==str(resource.sha256),"银河单拳冻结依赖变化")
		bound[ProjectSettings.globalize_path(str(resource.path)).simplify_path()]=true
	for required in ["candidate_factory.gd","main_driver.gd","main_entry.gd","main_game.gd","logic_check.gd"]:
		assert(bound.has(ProjectSettings.globalize_path("res://tests/review/fighters/ultraman-arc/galaxion_light1/"+required).simplify_path()))
	assert(bound.has(ProjectSettings.globalize_path("res://tests/review/fighters/ultraman-arc/galaxion_crouch/candidate_view.gd").simplify_path()))
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/%s/definition.json"%ID)
	for flag in ["implemented","playable","select_visible"]:assert(not bool(flags[flag]))
	assert(cfg.definition.moves.size()==1 and cfg.definition.moves.has("light1"))
	assert(cfg.definition.state_frames.size()==1 and cfg.definition.state_frames.has("idle"))
	assert(cfg.presentation.manifest_data.clips.size()==2)
	for action in ["idle","light1"]:
		var clip: Dictionary=cfg.presentation.manifest_data.clips[action]
		assert(str(clip.source_fighter)==ID and bool(clip.loop)==(action=="idle"))
		assert(bound.has(ProjectSettings.globalize_path(str(clip.texture)).simplify_path()))
		assert(FileAccess.get_sha256(str(clip.texture))==str(clip.atlas_sha256))
		var ticks: Array=[10,10,10,10,10,10] if action=="idle" else CLOCKS
		assert(equal_numbers(clip.ticks,ticks) and clip.rects.size()==ticks.size())
		for anchor in clip.anchors:assert(equal_numbers(anchor,[160,280]))
	var move: Dictionary=cfg.definition.moves.light1
	var original: Dictionary=UfeContentDatabase.read_json("res://content/fighters/ultraman-arc/moves/light1.json")
	for key in original:
		if key not in ["frames","production_source","display_name"]:assert(move[key]==original[key],"禁止修改正式单拳规则")
	assert(move.frames.size()==20)
	assert(cfg.fist_boxes.size()==3)
	for key in ["1","2","3"]:assert(cfg.fist_boxes.has(key) and cfg.fist_boxes[key].size()==4)
	assert(cfg.definition.state_frames.idle.size()==60)
	for tick in range(60):
		var frame: Dictionary=cfg.definition.state_frames.idle[tick]
		assert(int(frame.sprite)==int(tick/10) and int(frame.dx)==0 and int(frame.dy)==0)
		assert(frame.hitboxes.is_empty() and frame.cancel.is_empty() and frame.events.is_empty())
	var phases: Array=[]
	for phase in range(5):
		for _tick in range(CLOCKS[phase]):phases.append(phase)
	for tick in range(20):
		var frame: Dictionary=move.frames[tick]
		assert(int(frame.sprite)==int(phases[tick]) and frame.cancel.is_empty())
		var expected: Array=[cfg.fist_boxes[str(phases[tick])]] if cfg.fist_boxes.has(str(phases[tick])) else []
		assert(frame.hitboxes.size()==expected.size())
		for i in range(expected.size()):assert(equal_numbers(frame.hitboxes[i],expected[i]))
		for key in original.frames[tick]:
			if key not in ["sprite","hitboxes","hurtboxes","cancel"]:assert(frame[key]==original.frames[tick][key])
		assert(int(frame.dx)==0 and int(frame.dy)==0 and not bool(frame.get("invulnerable",false)))
	assert(cfg.definition.command_table.size()==1)
	assert(str(cfg.definition.command_table[0].move)=="light1" and int(cfg.definition.command_table[0].buttons)==UfeInputFrame.LIGHT)
	cfg["_candidate_contract_sha256"]=FileAccess.get_sha256(path)
	return cfg

static func temporary_definition(cfg: Dictionary) -> UfeFighterDefinition:
	var raw: Dictionary = cfg.definition
	var result := UfeFighterDefinition.new()
	result.id = ID
	result.display_name = str(raw.display_name)
	result.max_health = int(raw.max_health)
	result.walk_speed = int(raw.walk_speed)
	result.jump_speed = int(raw.jump_speed)
	result.body_radius = int(raw.body_radius)
	result.moves = raw.moves.duplicate(true)
	for move in result.moves.values():assert(UfeMoveData.validate(move))
	result.command_table = raw.command_table.duplicate(true)
	result.state_frames = raw.state_frames.duplicate(true)
	return result

static func make_match(cfg: Dictionary, direction: int, kind: String) -> UfeMatchDirector:
	assert(direction in [-1,1] and kind in ["hit","block","whiff"])
	assert(bool(cfg.get("root_runtime_ready", false)))
	# 银河定义和本人状态表在第一次UfeMatchDirector构造之前即已完整建立。
	var first := temporary_definition(cfg)
	var second := UfeContentDatabase.fighter(str(cfg.opponent), false)
	var sim := UfeMatchDirector.new(first, second, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), {})
	var gap: int = int(cfg.initial_gaps[kind])
	assert(sim.tick == 0)
	sim.fighters[0].x = 640 - direction * 50
	sim.fighters[1].x = sim.fighters[0].x + direction * gap
	sim.fighters[0].facing = direction
	sim.fighters[1].facing = -direction
	return sim


static func verify_original_inputs(cfg: Dictionary, tape: Dictionary) -> Dictionary:
	assert(str(tape.candidate_contract_sha256) == str(cfg._candidate_contract_sha256))
	var sim := make_match(cfg,int(tape.direction),str(tape.kind))
	assert(sim.content_fingerprint == str(tape.simulation_fingerprint))
	assert(tape.original_pairs.size() == tape.state_hashes.size())
	var errors: Array = verify_input_shape(tape)
	if not errors.is_empty():return {"errors":errors,"tick_count":0}
	for tick in range(tape.original_pairs.size()):
		var pair: Array = tape.original_pairs[tick]
		sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
		if sim.state_hash() != str(tape.state_hashes[tick]):errors.append({"tick":sim.tick,"kind":"hash_mismatch"})
		for key in ["events","projectiles"]:
			if JSON.stringify(JSON.parse_string(JSON.stringify(sim.get(key))),"",true) != JSON.stringify(JSON.parse_string(JSON.stringify(tape[key][tick])),"",true):errors.append({"tick":sim.tick,"kind":key+"_mismatch"})
	return {"errors":errors,"final_hash":sim.state_hash(),"simulation_fingerprint":sim.content_fingerprint,"tick_count":sim.tick,"no_user_writes":true}

static func verify_input_shape(tape: Dictionary) -> Array:
	var errors: Array = []
	if tape.original_pairs.size() != 120 or tape.state_hashes.size() != 120 or tape.get("events",[]).size()!=120 or tape.get("projectiles",[]).size()!=120:
		return [{"kind": "invalid_tape_length"}]
	for tick in range(120):
		var pair: Array = tape.original_pairs[tick]
		var first: Array = [0, 0, UfeInputFrame.LIGHT if tick == 20 else 0]
		var second: Array = [0, 0, UfeInputFrame.GUARD if str(tape.kind) == "block" else 0]
		if pair.size() != 2 or not equal_numbers(pair[0], first) or not equal_numbers(pair[1], second):
			errors.append({"kind": "not_single_light1_original_input", "tick": tick})
	return errors

static func verify_case(_cfg: Dictionary, kind: String, moves: Dictionary, contacts: Dictionary, counts: Dictionary, damage: int) -> Array:
	var errors: Array = []
	if moves.size() != 1 or not moves.has("light1"): errors.append({"kind": "unexpected_moves", "moves": moves.keys()})
	if kind in ["hit", "block"]:
		if contacts.size() != 1 or str(contacts.get("light1", "")) != kind or int(counts.get("light1", 0)) != 1:
			errors.append({"kind": "missing_or_repeated_real_contact", "expected": kind})
	elif not contacts.is_empty(): errors.append({"kind": "unexpected_whiff_contact"})
	var expected: int = 65 if kind == "hit" else 0
	if damage != expected: errors.append({"kind": "wrong_light1_damage", "expected": expected, "actual": damage})
	return errors

static func verify_phases(trace: Array) -> Array:
	var phases: Dictionary = {}
	var errors: Array = []
	for row in trace:
		var own: Dictionary = row.pair[0]
		if str(own.move_id) == "light1": phases[int(own.frame_sprite)] = true
	for phase in range(5):
		if not phases.has(phase): errors.append({"kind": "unreached_light1_phase", "phase": phase})
	if trace.is_empty() or str(trace[-1].pair[0].state) != "idle" or not str(trace[-1].pair[0].move_id).is_empty():
		errors.append({"kind": "light1_did_not_recover_to_idle"})
	return errors

static func equal_numbers(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size(): return false
	for index in range(actual.size()):
		if float(actual[index]) != float(expected[index]): return false
	return true
@warning_ignore_restore("integer_division")
