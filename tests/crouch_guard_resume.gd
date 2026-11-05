extends SceneTree
## 正式输入回归：只在tick0配置训练站距/朝向；缺表检查另列为直接状态单元测试。
const CASES := ["initial_idle", "initial_stand_guard", "low", "mid", "overhead", "repeat_low", "direction_guard", "release_guard", "release_down", "release_all"]
const LENGTH := 140
var output: String=""
var legacy_path: String=""
var errors: Array=[]
var cases: Array=[]
var compatibility: Array=[]
var checks: int=0
var probe: UfeSideView

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):output=ProjectSettings.globalize_path(arg.trim_prefix("--out=")).simplify_path()
		elif arg.begins_with("--legacy-report="):legacy_path=ProjectSettings.globalize_path(arg.trim_prefix("--legacy-report=")).simplify_path()
		else:assert(false,"未知蹲防恢复测试参数")
	assert(output.begins_with(ProjectSettings.globalize_path("res://reports/crouch-guard-resume/")))
	assert(not DirAccess.dir_exists_absolute(output),"测试输出禁止覆盖")
	assert(DirAccess.make_dir_recursive_absolute(output)==OK)
	call_deferred("run")

func check(ok: bool,kind: String,context: Dictionary={}) -> void:
	checks+=1
	if not ok:
		var item: Dictionary={"kind":kind}
		item.merge(context)
		errors.append(item)

func canonical_inputs(frames: Array) -> Array:
	return frames.map(func(pair):return [UfeInputFrame.unpack(pair[0]).pack(),UfeInputFrame.unpack(pair[1]).pack()])

func write_new(path: String,value: Dictionary) -> void:
	assert(not FileAccess.file_exists(path))
	var file:=FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify(value,"\t"));file.close()

func make_match(target: String,direction: int,kind: String) -> UfeMatchDirector:
	var sim:=UfeContentDatabase.match_for("ultraman",target)
	assert(sim.tick==0)
	sim.fighters[0].x=640-direction*50
	sim.fighters[1].x=sim.fighters[0].x+direction*(95 if kind=="overhead" else 65)
	sim.fighters[0].facing=direction
	sim.fighters[1].facing=-direction
	return sim

func attack_input(frame: int,kind: String,direction: int) -> UfeInputFrame:
	if kind.begins_with("initial_"):return UfeInputFrame.make()
	var pressed: bool=frame==20 or (kind=="repeat_low" and frame==55)
	if kind=="mid":return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if pressed else 0)
	if kind=="overhead":return UfeInputFrame.make(-direction if pressed else 0,0,UfeInputFrame.HEAVY if pressed else 0)
	return UfeInputFrame.make(0,-1,UfeInputFrame.LIGHT if pressed else 0)

func defender_input(frame: int,kind: String,direction: int,saw_block: bool) -> UfeInputFrame:
	if kind=="initial_stand_guard":return UfeInputFrame.make(0,0 if frame<10 else -1,UfeInputFrame.GUARD)
	if kind=="direction_guard":return UfeInputFrame.make(direction,-1)
	if saw_block and kind=="release_guard":return UfeInputFrame.make(0,-1)
	if saw_block and kind=="release_down":return UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
	if saw_block and kind=="release_all":return UfeInputFrame.make()
	return UfeInputFrame.make(0,-1,UfeInputFrame.GUARD)

func record(f: UfeFighter,manifest: Dictionary) -> Dictionary:
	return {"state":f.state,"state_tick":f.state_tick,"duration":int(f.motion.duration),"move":f.move_id,"move_tick":f.move_tick,
		"hp":int(f.stats.hp),"stamina":int(f.stats.stamina),"x":f.x,"height":f.height,"facing":f.facing,
		"frame":f.frame().duplicate(true),"animation":probe._animation(f,manifest)}

func run_case(target: String,direction: int,kind: String) -> void:
	var sim:=make_match(target,direction,kind)
	var manifests: Array=[]
	for id in ["ultraman",target]:manifests.append(UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%id))
	var hold_frames: Array=sim.fighters[1].definition.state_frames.crouch_guard
	var hold: Dictionary=hold_frames[-1]
	var id: String=target+"/"+str(direction)+"/"+kind
	var trace: Array=[]
	var contacts: Array=[]
	var returns: Array=[]
	var previous_state: String="idle"
	var saw_block: bool=false
	var saw_hit: bool=false
	var resumed: bool=false
	var initial_age: int=0
	var initial_checked: int=0
	var recorder:=UfeReplayRecorder.new()
	for frame in range(LENGTH):
		var pair: Array=[attack_input(frame,kind,direction),defender_input(frame,kind,direction,saw_block)]
		sim.step(pair)
		recorder.append(pair,sim)
		var f:=sim.fighters[1]
		var row: Dictionary={"frame":frame,"tick":sim.tick,"inputs":[pair[0].pack(),pair[1].pack()],"hash":sim.state_hash(),"hitstop":sim.hitstop,
			"fighters":[record(sim.fighters[0],manifests[0]),record(f,manifests[1])],"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)}
		trace.append(row)
		for event in sim.events:
			if str(event.get("kind","")) in ["hit","block"]:
				contacts.append({"frame":frame,"event":event.duplicate(true)})
				saw_block=saw_block or str(event.kind)=="block"
				saw_hit=saw_hit or str(event.kind)=="hit"
		# 初次站入蹲防必须仍从自身表0开始；不能全局跳过入架来掩盖恢复错误。
		if not saw_block and not saw_hit and f.state=="crouch_guard" and initial_age<hold_frames.size():
			check(f.state_tick==initial_age and f.frame()==hold_frames[initial_age],"initial_entry_unchanged",{"case":id,"frame":frame,"age":initial_age})
			initial_age+=1;initial_checked+=1
		if previous_state=="crouch_blockstun" and f.state!="crouch_blockstun":
			returns.append({"frame":frame,"state":f.state,"state_tick":f.state_tick,"sprite":int(f.frame().sprite)})
			if kind in ["low","mid","repeat_low","direction_guard"]:
				check(f.state=="crouch_guard" and f.state_tick==hold_frames.size()-1 and f.frame()==hold,"resume_starts_at_own_hold",{"case":id,"frame":frame,"state_tick":f.state_tick,"sprite":int(f.frame().sprite)})
				resumed=true
			elif kind=="release_guard":check(f.state=="crouch" and f.state_tick==0,"released_guard_keeps_crouch",{"case":id})
			elif kind in ["release_down","release_all"]:check(f.state=="idle" and f.state_tick==0,"released_down_keeps_original_idle_transition",{"case":id})
		if resumed and f.state=="crouch_guard":
			check(f.frame()==hold and int(row.fighters[1].animation.index)==int(hold.sprite),"resumed_guard_never_replays_entry",{"case":id,"frame":frame,"sprite":int(f.frame().sprite)})
		if f.state=="crouch_blockstun":check(int(f.motion.duration)==12,"block_duration_unchanged",{"case":id,"frame":frame})
		check(f.height==0 and int(sim.fighters[0].stats.hp)==1000,"grounded_no_counter_damage",{"case":id,"frame":frame})
		previous_state=f.state
	check(initial_checked==8,"initial_entry_fully_observed",{"case":id,"observed":initial_checked})
	var expected_contacts: int=0 if kind.begins_with("initial_") else 2 if kind=="repeat_low" else 1
	check(contacts.size()==expected_contacts,"actual_contact_count",{"case":id,"actual":contacts.size(),"expected":expected_contacts})
	for contact in contacts:
		check(int(contact.event.player)==0 and str(contact.event.kind)==("hit" if kind=="overhead" else "block"),"official_high_low_result",{"case":id,"contact":contact})
	check(returns.size()==(0 if kind.begins_with("initial_") or kind=="overhead" else expected_contacts),"natural_stun_return_count",{"case":id})
	check(int(sim.fighters[1].stats.hp)==(900 if kind=="overhead" else 1000),"official_damage_unchanged",{"case":id})
	var expected_final: String="crouch" if kind=="release_guard" else "guard" if kind=="release_down" else "idle" if kind=="release_all" else "crouch_guard"
	check(sim.fighters[1].state==expected_final,"current_input_controls_recovery",{"case":id})
	# 新实例仅吃原始输入，不能重新执行基于接触的自适应采样。
	var replay:=make_match(target,direction,kind)
	for row in trace:
		replay.step([UfeInputFrame.unpack(row.inputs[0]),UfeInputFrame.unpack(row.inputs[1])])
		check(replay.state_hash()==row.hash and replay.events==row.events and replay.projectiles==row.projectiles,"independent_original_input_replay",{"case":id,"frame":row.frame})
	var replay_file: String=output.path_join(target+"-"+str(direction)+"-"+kind+"-new-replay.json")
	check(recorder.save_file(replay_file)==OK,"save_isolated_new_replay",{"case":id})
	var loaded:=UfeReplayRecorder.load_file(replay_file,sim.content_fingerprint)
	check(loaded!=null and loaded.final_hash==sim.state_hash() and canonical_inputs(loaded.frames)==canonical_inputs(recorder.frames),"new_format6_replay_accepted",{"case":id})
	cases.append({"id":id,"target":target,"direction":direction,"kind":kind,"fingerprint":sim.content_fingerprint,"trace":trace,"contacts":contacts,"returns":returns,"new_replay":replay_file,"final_hash":sim.state_hash()})

func verify_missing_tables() -> void:
	var state=load("res://core/states/crouch_blockstun.gd").new()
	for present in [false,true]:
		var definition:=UfeFighterDefinition.new()
		if present:definition.state_frames.crouch_guard=[]
		var f:=UfeFighter.new(definition,0)
		f.enter("crouch_blockstun",1);f.state_tick=1
		state.step(f,UfeInputFrame.make(0,-1,UfeInputFrame.GUARD),{})
		check(f.state=="crouch_guard" and f.state_tick==0,"missing_or_empty_guard_table_keeps_zero_fallback",{"empty_present":present,"unit_only":true})

func verify_legacy() -> void:
	if legacy_path.is_empty():return
	var legacy: Dictionary=UfeContentDatabase.read_json(legacy_path)
	check(legacy.cases.size()==cases.size(),"legacy_report_same_matrix")
	for current in cases:
		var matches: Array=legacy.cases.filter(func(row):return str(row.id)==str(current.id))
		check(matches.size()==1,"legacy_case_found",{"case":current.id})
		if matches.size()!=1:continue
		var before: Dictionary=matches[0]
		check(before.fingerprint!=current.fingerprint,"semantic_change_updates_content_fingerprint",{"case":current.id})
		var old_file: String=output.path_join(str(current.target)+"-"+str(current.direction)+"-"+str(current.kind)+"-legacy-replay.json")
		write_new(old_file,{"format":6,"tick_rate":60,"rules":"neo","fighters":["ultraman",current.target],"content":before.fingerprint,
			"frames":before.trace.map(func(row):return row.inputs),"final_hash":before.final_hash})
		var parsed:=UfeReplayRecorder.read_candidate(old_file)
		check(parsed!=null,"legacy_format6_structure_still_supported",{"case":current.id})
		check(UfeReplayRecorder.load_file(old_file,current.fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放","old_content_rejected_without_format_bump",{"case":current.id})
		var boundary: int=LENGTH
		if str(current.kind) in ["low","mid","repeat_low","direction_guard"] and not before.returns.is_empty():boundary=int(before.returns[0].frame)
		for frame in range(boundary):check(before.trace[frame].hash==current.trace[frame].hash,"pre_recovery_hash_unchanged",{"case":current.id,"frame":frame})
		compatibility.append({"case":current.id,"old_content":before.fingerprint,"new_content":current.fingerprint,"format":6,"old_rejected":true,"new_accepted":true,"unchanged_prefix_frames":boundary})

func run() -> void:
	probe=UfeSideView.new();probe.intro_tick=-1
	for target in ["zetton","ultraman"]:
		for direction in [1,-1]:
			for kind in CASES:run_case(target,direction,kind)
	verify_missing_tables()
	var constants: Dictionary=load("res://core/combat/match_director.gd").get_script_constant_map()
	check(int(constants.get("CROUCH_GUARD_RESUME_RULE_REVISION",0))==1,"resume_semantics_versioned")
	check(UfeReplayRecorder.FORMAT==6,"replay_format_stays_6")
	verify_legacy()
	probe.free()
	write_new(output.path_join("result.json"),{"cases":cases,"errors":errors,"checks":checks,"compatibility":compatibility,"legacy_report":legacy_path,
		"no_post_tick_simulation_writes":true,"missing_table_isolated_state_units":2,"art_accepted":false,"candidate_art_installed":false,"graphical_review":false})
	print("CROUCH_GUARD_RESUME "+JSON.stringify({"cases":cases.size(),"errors":errors.size(),"checks":checks,"legacy_cases":compatibility.size()}))
	quit(0 if errors.is_empty() else 1)
