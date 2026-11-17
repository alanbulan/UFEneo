extends RefCounted
@warning_ignore_start("integer_division")
## 只复制正式杰顿定义的单个状态帧表；MatchDirector构造前完成，运行中零模拟写入。
const ACTION := "crouch_blockstun"
const CASES := ["low", "mid", "overhead", "release_down"]
const LENGTH := 180
const ATTACK_FRAME := 20

static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema)=="ufeneo.zetton.crouch-block-main-candidate.v1" and bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter)=="zetton" and str(cfg.attacker)=="ultraman")
	var bound: Dictionary = {}
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path))==str(resource.sha256),"杰顿蹲防硬直冻结依赖变化")
		bound[ProjectSettings.globalize_path(str(resource.path)).simplify_path()]=true
	for required in ["candidate_factory.gd","candidate_view.gd","main_driver.gd","main_entry.gd","main_game.gd","logic_check.gd"]:
		assert(bound.has(ProjectSettings.globalize_path("res://tests/review/fighters/zetton/crouch_block/"+required).simplify_path()))
	var original: Array = UfeContentDatabase.read_json("res://content/fighters/zetton/state_frames.json")[ACTION]
	assert(cfg.state_frames.size()==10 and original.size()==10)
	for tick in range(10):
		var expected: Dictionary=original[tick].duplicate(true)
		expected.hurtboxes=cfg.state_frames[tick].hurtboxes
		assert(expected==cfg.state_frames[tick],"仅允许候选新Alpha受击框，不许改变正式状态字段")
		assert(int(expected.sprite)==(0 if tick<4 else 1))
	var clip: Dictionary=cfg.clip
	assert(str(clip.source_fighter)=="zetton" and not bool(clip.loop))
	assert(equal_numbers(clip.ticks,[4,6]) and clip.rects.size()==2)
	assert(bound.has(ProjectSettings.globalize_path(str(clip.texture)).simplify_path()))
	assert(FileAccess.get_sha256(str(clip.texture))==str(clip.atlas_sha256))
	for anchor in clip.anchors:assert(equal_numbers(anchor,cfg.root))
	cfg["_candidate_contract_sha256"]=FileAccess.get_sha256(path)
	return cfg

static func temporary_definition(cfg: Dictionary) -> UfeFighterDefinition:
	var official := UfeContentDatabase.fighter("zetton",false)
	var baseline: Array=official.simulation_data().duplicate(true)
	# 数据库每次返回新Resource；仍显式深拷贝字典，防止与任何既有读者共享可写表。
	official.moves=official.moves.duplicate(true)
	official.command_table=official.command_table.duplicate(true)
	official.state_frames=official.state_frames.duplicate(true)
	official.state_frames[ACTION]=cfg.state_frames.duplicate(true)
	baseline[-1][ACTION]=cfg.state_frames.duplicate(true)
	assert(official.simulation_data()==baseline,"候选只能替换crouch_blockstun")
	return official

static func make_match(cfg: Dictionary, direction: int, kind: String) -> UfeMatchDirector:
	assert(direction in [-1,1] and kind in CASES)
	var attacker := UfeContentDatabase.fighter("ultraman",false)
	var defender := temporary_definition(cfg)
	var sim := UfeMatchDirector.new(attacker,defender,load("res://content/rules/neo.tres"),UfeContentDatabase.states(),{})
	assert(sim.tick==0)
	# 仅tick0训练站距和朝向；HP、体力、状态、招式均为正式初值。
	sim.fighters[0].x=640-direction*50
	sim.fighters[1].x=sim.fighters[0].x+direction*int(cfg.initial_gaps[kind])
	sim.fighters[0].facing=direction
	sim.fighters[1].facing=-direction
	return sim

static func move_for(kind: String) -> String:
	return "spin_heavy" if kind=="overhead" else "light1" if kind=="mid" else "crouch_light"

static func attacker_input(frame: int, kind: String, direction: int) -> UfeInputFrame:
	if kind in ["low","release_down"]:return UfeInputFrame.make(0,-1,UfeInputFrame.LIGHT if frame==ATTACK_FRAME else 0)
	if kind=="mid":return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if frame==ATTACK_FRAME else 0)
	return UfeInputFrame.make(-direction if frame==ATTACK_FRAME else 0,0,UfeInputFrame.HEAVY if frame==ATTACK_FRAME else 0)

static func equal_numbers(actual: Array, expected: Array) -> bool:
	if actual.size()!=expected.size():return false
	for i in range(actual.size()):
		if float(actual[i])!=float(expected[i]):return false
	return true

static func verify_input_shape(tape: Dictionary) -> Array:
	if str(tape.kind) not in CASES or int(tape.direction) not in [-1,1]:return [{"kind":"invalid_case"}]
	for key in ["original_pairs","state_hashes","events","projectiles"]:
		if tape.get(key,[]).size()!=LENGTH:return [{"kind":"invalid_tape_length","field":key}]
	var errors: Array=[]
	var first_block: int=-1
	for frame in range(LENGTH):
		var pair: Array=tape.original_pairs[frame]
		var expected: Array=attacker_input(frame,str(tape.kind),int(tape.direction)).pack()
		var release: bool=str(tape.kind)=="release_down" and first_block>=0 and frame>first_block
		if pair.size()!=2 or not equal_numbers(pair[0],expected) or not equal_numbers(pair[1],[0,0 if release else -1,UfeInputFrame.GUARD]):
			errors.append({"kind":"not_single_official_attack_and_guard_input","frame":frame})
		for event in tape.events[frame]:
			if str(event.get("kind",""))=="block" and int(event.get("player",-1))==0 and first_block<0:first_block=frame
	if str(tape.kind)=="release_down" and first_block<0:errors.append({"kind":"release_down_without_prior_real_block"})
	return errors

static func verify_original_inputs(cfg: Dictionary,tape: Dictionary) -> Dictionary:
	assert(str(tape.candidate_contract_sha256)==str(cfg._candidate_contract_sha256))
	var sim:=make_match(cfg,int(tape.direction),str(tape.kind))
	assert(sim.content_fingerprint==str(tape.simulation_fingerprint))
	var errors: Array=verify_input_shape(tape)
	if not errors.is_empty():return {"errors":errors,"tick_count":0}
	for tick in range(LENGTH):
		var pair: Array=tape.original_pairs[tick]
		sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
		if sim.state_hash()!=str(tape.state_hashes[tick]):errors.append({"tick":sim.tick,"kind":"hash_mismatch"})
		for key in ["events","projectiles"]:
			if JSON.stringify(JSON.parse_string(JSON.stringify(sim.get(key))),"",true)!=JSON.stringify(JSON.parse_string(JSON.stringify(tape[key][tick])),"",true):errors.append({"tick":sim.tick,"kind":key+"_mismatch"})
	return {"errors":errors,"final_hash":sim.state_hash(),"simulation_fingerprint":sim.content_fingerprint,"tick_count":sim.tick,"no_user_writes":true}

static func phase_at(state_tick: int,duration: int,frames: Array) -> int:
	return int(frames[mini(int(state_tick*frames.size()/maxi(1,duration)),frames.size()-1)].sprite)

static func verify_trace(cfg: Dictionary,kind: String,trace: Array) -> Array:
	var errors: Array=[]
	var contacts: Array=[]
	var moves: Dictionary={}
	var phases: Dictionary={}
	var ages: Dictionary={}
	var resumed_hold:=false
	var hold: Array=UfeContentDatabase.fighter("zetton",false).state_frames.crouch_guard
	var expected_move:=move_for(kind)
	var official: Dictionary=UfeContentDatabase.fighter("ultraman",false).moves[expected_move]
	for row in trace:
		var attacker: Dictionary=row.pair[0]
		var target: Dictionary=row.pair[1]
		if not str(attacker.move_id).is_empty():moves[str(attacker.move_id)]=true
		for event in row.events:
			if str(event.get("kind","")) in ["hit","block"]:contacts.append(event)
		if int(target.height)!=0 or str(target.state) in ["launch","down","wake"]:errors.append({"kind":"unexpected_airborne_or_knockdown_receiver"})
		if str(target.state)==ACTION:
			phases[int(target.frame_sprite)]=true
			ages[int(target.state_tick)]=true
			if kind=="overhead":errors.append({"kind":"overhead_was_blocked"})
			if int(target.duration)!=int(official.blockstun) or int(target.frame_sprite)!=phase_at(int(target.state_tick),int(target.duration),cfg.state_frames):errors.append({"kind":"changed_duration_or_proportional_sprite"})
			if str(target.animation.key)!=ACTION or str(target.animation.texture)!=str(cfg.clip.texture) or int(target.animation.index)!=int(target.frame_sprite):errors.append({"kind":"wrong_candidate_animation"})
		elif str(target.animation.get("texture",""))==str(cfg.clip.texture):errors.append({"kind":"candidate_clip_leaked_into_other_state"})
		if kind in ["low","mid"] and not phases.is_empty() and str(target.state)=="crouch_guard":
			resumed_hold=true
			if int(target.frame_sprite)!=int(hold[-1].sprite) or int(target.state_tick)<hold.size()-1:errors.append({"kind":"crouch_guard_resume_replayed_entry"})
		if kind=="overhead" and not contacts.is_empty() and str(target.state) in ["crouch","crouch_guard"]:
			if str(target.animation.key)!="crouch_guard" or int(target.frame_sprite)!=int(hold[-1].sprite):errors.append({"kind":"hit_crouch_recovery_pose_not_held"})
	if kind in ["low","mid"] and not resumed_hold:errors.append({"kind":"missing_resumed_crouch_hold"})
	if moves.size()!=1 or not moves.has(expected_move):errors.append({"kind":"unexpected_moves","moves":moves.keys()})
	var expected_contact: String="hit" if kind=="overhead" else "block"
	if contacts.size()!=1 or str(contacts[0].kind)!=expected_contact or str(contacts[0].move)!=expected_move or int(contacts[0].player)!=0:errors.append({"kind":"missing_or_repeated_real_contact","contacts":contacts})
	if kind!="overhead":
		if phases.size()!=2 or not phases.has(0) or not phases.has(1):errors.append({"kind":"missing_candidate_phase"})
		for age in range(int(official.blockstun)):
			if not ages.has(age):errors.append({"kind":"missing_stun_age","age":age})
	var expected_damage: int=int(official.damage) if kind=="overhead" else int(official.get("chip_damage",0))
	if int(trace[0].pair[1].hp)-int(trace[-1].pair[1].hp)!=expected_damage:errors.append({"kind":"wrong_receiver_damage"})
	if int(trace[-1].pair[0].hp)!=1000:errors.append({"kind":"attacker_damaged"})
	if str(trace[-1].pair[1].state)!=("guard" if kind=="release_down" else "crouch_guard"):errors.append({"kind":"receiver_did_not_naturally_return_to_guard"})
	return errors
@warning_ignore_restore("integer_division")
