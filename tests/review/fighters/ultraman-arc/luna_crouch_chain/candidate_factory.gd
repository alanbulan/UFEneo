extends RefCounted
## 月亮实际蹲姿→近侧左拳→同蹲姿，三端点试排；第二拳仅RAM载入。
const ID := "ultraman-arc__luna"
const CLOCKS := [3,3,12]

static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema)=="ufeneo.luna.crouch_chain-main-candidate.v1" and bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter)==ID and str(cfg.definition.id)==ID and str(cfg.opponent)=="zetton")
	for flag in ["implemented","playable","select_visible","transform_enabled"]:assert(not bool(cfg[flag]))
	var bound: Dictionary = {}
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path))==str(resource.sha256),"月亮蹲拳二连冻结依赖变化")
		bound[ProjectSettings.globalize_path(str(resource.path)).simplify_path()]=true
	for required in ["candidate_factory.gd","candidate_view.gd","main_driver.gd","main_entry.gd","main_game.gd","logic_check.gd"]:
		assert(bound.has(ProjectSettings.globalize_path("res://tests/review/fighters/ultraman-arc/luna_crouch_chain/"+required).simplify_path()))
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/%s/definition.json"%ID)
	for flag in ["implemented","playable","select_visible"]:assert(not bool(flags[flag]))
	assert(cfg.definition.moves.size()==2 and cfg.definition.moves.has("crouch_light2"))
	assert(cfg.definition.command_table.size()==2)
	for action in ["crouch_light","crouch_light2"]:
		var move: Dictionary=cfg.definition.moves[action]
		var original: Dictionary=UfeContentDatabase.read_json("res://content/fighters/ultraman-arc/moves/"+action+".json")
		for key in original:
			if key not in ["frames","production_source","display_name"]:assert(move[key]==original[key])
		assert(move.frames.size()==original.frames.size())
		for tick in range(move.frames.size()):
			for key in original.frames[tick]:
				if key not in ["sprite","hitboxes","hurtboxes"]:assert(move.frames[tick][key]==original.frames[tick][key])
	for action in cfg.presentation.manifest_data.clips:
		var clip: Dictionary=cfg.presentation.manifest_data.clips[action]
		assert(bound.has(ProjectSettings.globalize_path(str(clip.texture)).simplify_path()))
		assert(FileAccess.get_sha256(str(clip.texture))==str(clip.atlas_sha256))
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
	assert(direction in [-1,1] and kind in ["hit","stand_guard","block","whiff"])
	assert(bool(cfg.get("root_runtime_ready", false)))
	# 月亮定义和本人状态表在第一次UfeMatchDirector构造之前即已完整建立。
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
	if tape.original_pairs.size() != 180 or tape.state_hashes.size() != 180 or tape.get("events",[]).size()!=180 or tape.get("projectiles",[]).size()!=180:
		return [{"kind": "invalid_tape_length"}]
	for tick in range(180):
		var pair: Array = tape.original_pairs[tick]
		var first: Array = [0, -1, UfeInputFrame.LIGHT if tick in [20,27] else 0]
		var second: Array = [0, -1 if str(tape.kind) == "block" else 0, UfeInputFrame.GUARD if str(tape.kind) in ["block", "stand_guard"] else 0]
		if pair.size() != 2 or not equal_numbers(pair[0], first) or not equal_numbers(pair[1], second):
			errors.append({"kind": "not_chain_original_input", "tick": tick})
	return errors

static func verify_case(_cfg: Dictionary, kind: String, moves: Dictionary, contacts: Dictionary, counts: Dictionary, damage: int) -> Array:
	var errors: Array=[]
	var expected_moves: int=2 if kind in ["hit","stand_guard"] else 1
	if moves.size()!=expected_moves or not moves.has("crouch_light") or (expected_moves==2 and not moves.has("crouch_light2")):errors.append({"kind":"unexpected_cancel_result","moves":moves.keys()})
	if kind in ["hit","stand_guard","block"]:
		if str(contacts.get("crouch_light",""))!=("block" if kind=="block" else "hit") or int(counts.get("crouch_light",0))!=1:errors.append({"kind":"first_contact_wrong"})
	elif not contacts.is_empty():errors.append({"kind":"whiff_contact"})
	for action in counts:
		if int(counts[action])!=1:errors.append({"kind":"repeat_contact","action":action})
	var expected: int=0
	for action in contacts:
		if contacts[action]=="hit":expected+=int(_cfg.definition.moves[action].damage)
	if damage!=expected:errors.append({"kind":"wrong_damage","actual":damage,"expected":expected})
	return errors

static func verify_phases(trace: Array) -> Array:
	var errors: Array=[]
	var phases: Dictionary={}
	for row in trace:
		var f: Dictionary=row.pair[0]
		if not str(f.move_id).is_empty():phases[str(f.move_id)+":"+str(int(f.frame_sprite))]=true
	for key in ["crouch_light:0","crouch_light:1"]:
		if not phases.has(key):errors.append({"kind":"missing_first_phase","key":key})
	if phases.has("crouch_light2:0"):
		for phase in range(3):
			if not phases.has("crouch_light2:"+str(phase)):errors.append({"kind":"missing_second_phase","phase":phase})
	if trace.is_empty() or str(trace[-1].pair[0].state)!="crouch" or not str(trace[-1].pair[0].move_id).is_empty():errors.append({"kind":"not_recovered"})
	return errors

static func equal_numbers(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size(): return false
	for index in range(actual.size()):
		if float(actual[index]) != float(expected[index]): return false
	return true

static func verify_grounded_receiver(trace: Array, kind: String) -> Array:
	var errors: Array=[]
	for row in trace:
		var other: Dictionary=row.pair[1]
		if int(other.height)!=0 or str(other.state) in ["launch","down","wake"]:
			errors.append({"kind":"unexpected_airborne_or_knockdown_receiver"})
	if trace.is_empty() or str(trace[-1].pair[1].state)!=("crouch_guard" if kind=="block" else "guard" if kind=="stand_guard" else "idle"):
		errors.append({"kind":"receiver_did_not_recover_to_crouch"})
	return errors
