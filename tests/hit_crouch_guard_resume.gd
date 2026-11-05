extends SceneTree
## 真实输入红绿测试。训练初始站距之外不写模拟；缺表/中断为独立单元。
const FLAG := "hit_crouch_guard_resume"
const CASES := ["hold", "direction", "release_guard", "release_down", "release_all", "jump", "taunt", "forward_heavy", "attack", "repeat", "stand_hit", "initial", "release_before_end"]
const LENGTH := 150
var output := ""
var legacy_path := ""
var errors: Array=[]
var cases: Array=[]
var checks := 0
var probe: UfeSideView
var sound: UfeSideAudio
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):output=ProjectSettings.globalize_path(arg.trim_prefix("--out=")).simplify_path()
		elif arg.begins_with("--legacy-report="):legacy_path=arg.trim_prefix("--legacy-report=")
		else:assert(false,"未知参数")
	assert(output.begins_with(ProjectSettings.globalize_path("res://reports/hit-crouch-guard-resume/")))
	assert(not DirAccess.dir_exists_absolute(output))
	assert(DirAccess.make_dir_recursive_absolute(output)==OK)
	call_deferred("run")
func check(ok: bool, kind: String, context: Dictionary={}) -> void:
	checks+=1
	if not ok:
		var row={"kind":kind};row.merge(context);errors.append(row)
func write_new(path: String, value: Dictionary) -> void:
	assert(not FileAccess.file_exists(path))
	var file=FileAccess.open(path,FileAccess.WRITE);assert(file!=null)
	file.store_string(JSON.stringify(value));file.close()
func make_match(target: String, direction: int) -> UfeMatchDirector:
	var sim=UfeContentDatabase.match_for("ultraman",target)
	sim.fighters[0].x=640-direction*50;sim.fighters[1].x=sim.fighters[0].x+direction*95
	sim.fighters[0].facing=direction;sim.fighters[1].facing=-direction
	return sim
func key(f: UfeFighter) -> String:
	return str(sound.call("_state_entry_key",f)) if sound.has_method("_state_entry_key") else f.animation_key()
func row_f(f: UfeFighter, manifest: Dictionary) -> Dictionary:
	return {"snapshot":f.snapshot().duplicate(true),"state":f.state,"state_tick":f.state_tick,"frame":f.frame().duplicate(true),"animation":probe._animation(f,manifest),"audio_entry_key":key(f)}
func defense(frame: int, kind: String, direction: int, saw_hit: bool, recovery: int, f: UfeFighter) -> UfeInputFrame:
	if kind=="stand_hit" and not saw_hit:return UfeInputFrame.make()
	if kind=="direction":return UfeInputFrame.make(direction,-1)
	if kind=="release_before_end" and saw_hit:return UfeInputFrame.make(0,-1)
	var delta=frame-recovery if recovery>=0 else -1
	if delta>=1:
		if kind=="release_guard":return UfeInputFrame.make(0,-1)
		if kind=="release_down":return UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
		if kind=="release_all":return UfeInputFrame.make()
		if kind=="jump":return UfeInputFrame.make(0,-1,UfeInputFrame.GUARD|UfeInputFrame.JUMP)
		if kind=="forward_heavy":return UfeInputFrame.make(-direction,0,UfeInputFrame.HEAVY if delta==1 else 0)
		if kind=="attack":return UfeInputFrame.make(0,-1,UfeInputFrame.GUARD|(UfeInputFrame.LIGHT if delta==1 else 0))
		if kind=="taunt":return UfeInputFrame.make(0,-1,UfeInputFrame.GUARD|(UfeInputFrame.THROW if delta in [1,3] else 0))
	# 让GUARD+投组合落在正式3tick同时输入窗；hit中短松防不改变受击姿态。
	if kind=="taunt" and f.state=="hit" and f.state_tick<int(f.motion.duration)-1:return UfeInputFrame.make(0,-1)
	return UfeInputFrame.make(0,-1,UfeInputFrame.GUARD)
func run_case(target: String, direction: int, kind: String) -> void:
	var sim=make_match(target,direction)
	var manifests=[]
	for id in ["ultraman",target]:manifests.append(UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%id))
	var id=target+"/"+str(direction)+"/"+kind
	var trace=[];var contacts=[];var returns=[]
	var recovery=-1;var saw_hit=false;var prior="idle";var hold_expected=false
	var recorder=UfeReplayRecorder.new()
	for frame in range(LENGTH):
		var f=sim.fighters[1]
		var incoming=defense(frame,kind,direction,saw_hit,recovery,f)
		var fire=kind!="initial" and (frame==20 or (kind=="repeat" and frame==85))
		var pair=[UfeInputFrame.make(-direction if fire else 0,0,UfeInputFrame.HEAVY if fire else 0),incoming]
		var was_pose=str(f.motion.get("hit_pose",""))
		sim.step(pair);recorder.append(pair,sim)
		var row={"tick":sim.tick,"inputs":[pair[0].pack(),pair[1].pack()],"hash":sim.state_hash(),"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"hitstop":sim.hitstop,"fighters":[row_f(sim.fighters[0],manifests[0]),row_f(f,manifests[1])]}
		trace.append(row)
		for event in sim.events:
			if str(event.get("kind","")) in ["hit","block"]:
				contacts.append({"tick":sim.tick,"event":event.duplicate(true)})
				if int(event.player)==0 and str(event.kind)=="hit":saw_hit=true
		if prior=="hit" and f.state=="crouch":
			recovery=frame;returns.append(frame)
			hold_expected=was_pose=="hit_crouch" and incoming.y<0 and (incoming.held(UfeInputFrame.GUARD) or incoming.x*f.facing<0)
			check(f.state_tick==0,"original_crouch_recovery_tick",{"case":id,"frame":frame})
			check(key(f)=="crouch","original_crouch_audio_key",{"case":id,"frame":frame})
		if f.state not in ["crouch","crouch_guard"] or incoming.y>=0 or not (incoming.held(UfeInputFrame.GUARD) or incoming.x*f.facing<0):hold_expected=false
		if hold_expected:
			var hold: Dictionary=f.definition.state_frames.crouch_guard[-1]
			check(f.animation_key()=="crouch_guard" and f.frame().sprite==hold.sprite and f.frame().hurtboxes==hold.hurtboxes,"recovery_uses_own_low_hold",{"case":id,"frame":frame})
			check(int(row.fighters[1].animation.index)==int(hold.sprite),"visual_matches_simulation",{"case":id,"frame":frame})
		if not hold_expected:check(not f.motion.has(FLAG),"context_not_leaked",{"case":id,"frame":frame})
		if prior=="crouch" and f.state=="crouch_guard":check(f.state_tick==0 and key(f)=="crouch_guard","original_guard_entry_tick_and_audio",{"case":id,"frame":frame})
		prior=f.state
	check(kind=="initial" or saw_hit,"real_overhead_hit_observed",{"case":id})
	if not returns.is_empty():
		var r: int=returns[0]
		if kind=="jump":check(trace[r+1].fighters[1].state=="crouch_guard" and trace[r+2].fighters[1].state=="takeoff","jump_keeps_original_priority",{"case":id})
		if kind=="taunt":check(trace[r+1].fighters[1].snapshot[8]=="" and trace[r+3].fighters[1].snapshot[8]=="taunt","taunt_not_advanced_to_crouch_tick",{"case":id})
		if kind=="forward_heavy":check(trace[r+1].fighters[1].snapshot[8]=="launcher","crouch_context_not_guard_counter",{"case":id})
		if kind=="attack":check(trace[r+1].fighters[1].snapshot[8]=="crouch_light","normal_attack_timing_unchanged",{"case":id})
	if kind=="repeat":check(returns.size()==2,"two_real_hit_recoveries",{"case":id})
	var replay=make_match(target,direction)
	for row in trace:
		replay.step([UfeInputFrame.unpack(row.inputs[0]),UfeInputFrame.unpack(row.inputs[1])])
		check(replay.state_hash()==row.hash and replay.events==row.events and replay.projectiles==row.projectiles,"independent_input_replay",{"case":id,"tick":row.tick})
	var path=output.path_join(target+"-"+str(direction)+"-"+kind+".json")
	check(recorder.save_file(path)==OK,"new_replay_saved",{"case":id})
	var loaded=UfeReplayRecorder.load_file(path,sim.content_fingerprint)
	check(loaded!=null and loaded.final_hash==sim.state_hash(),"new_replay_loads",{"case":id})
	cases.append({"id":id,"target":target,"direction":direction,"kind":kind,"fingerprint":sim.content_fingerprint,"trace":trace,"returns":returns,"contacts":contacts,"replay":path,"final_hash":sim.state_hash()})
func comparable(row: Dictionary) -> Dictionary:
	var result=row.duplicate(true);result.erase("hash")
	for f in result.fighters:
		f.snapshot[12].erase(FLAG)
		f.frame.erase("sprite");f.frame.erase("hurtboxes");f.erase("animation")
	return JSON.parse_string(JSON.stringify(result))
func legacy_check() -> void:
	if legacy_path.is_empty():return
	var legacy=UfeContentDatabase.read_json(legacy_path)
	for current in cases:
		var found=legacy.cases.filter(func(c):return c.id==current.id)
		check(found.size()==1,"legacy_case_exists",{"case":current.id})
		if found.size()!=1:continue
		var before: Dictionary=found[0]
		check(before.fingerprint!=current.fingerprint,"new_semantic_fingerprint",{"case":current.id})
		check(UfeReplayRecorder.load_file(str(before.replay),current.fingerprint)==null,"old_content_rejected",{"case":current.id})
		for i in range(LENGTH):
			# JSON规范化数字，避免磁盘float与内存int的伪差异。
			check(JSON.stringify(comparable(before.trace[i]),"",true)==JSON.stringify(comparable(current.trace[i]),"",true),"all_non_pose_fields_unchanged",{"case":current.id,"frame":i})
func units() -> void:
	var hit=load("res://core/states/hit.gd").new()
	var crouch=load("res://core/states/crouch.gd").new()
	for present in [false,true]:
		var data=UfeFighterDefinition.new()
		if present:data.state_frames.crouch_guard=[]
		var f=UfeFighter.new(data,0);f.motion.hit_pose="hit_crouch";f.enter("hit",1);f.state_tick=1
		hit.step(f,UfeInputFrame.make(0,-1,UfeInputFrame.GUARD),{})
		check(f.state=="crouch" and f.state_tick==0 and not f.motion.has(FLAG),"missing_empty_fallback",{"unit":true,"empty":present})
	for next_state in ["hit","attack","air","crouch_turn","crouch_rise","idle","crouch_blockstun"]:
		var f=make_match("zetton",1).fighters[1];f.enter("crouch");f.motion[FLAG]=true
		f.enter(next_state);check(not f.motion.has(FLAG),"unrelated_enter_clears",{"state":next_state,"unit":true})
	var f=make_match("zetton",1).fighters[1];f.enter("crouch");f.motion[FLAG]=true
	crouch.step(f,UfeInputFrame.make(0,-1),{"jump":false})
	check(not f.motion.has(FLAG) and f.state=="crouch","release_without_enter_clears",{"unit":true})
	f.motion[FLAG]=true;f.clear_move();check(not f.motion.has(FLAG),"clear_move_clears",{"unit":true})
	f.enter("idle");f.enter("crouch_guard")
	check(f.state_tick==0 and f.frame()==f.definition.state_frames.crouch_guard[0],"later_initial_guard_entry_still_zero",{"unit":true})
	for h in [0,20]:
		for pose in ["hit_high","hit_mid","hit_air"]:
			f.enter("hit",1);f.motion.hit_pose=pose;f.height=h;f.state_tick=1
			hit.step(f,UfeInputFrame.make(0,-1,UfeInputFrame.GUARD),{})
			check(not f.motion.has(FLAG) and f.state==("air" if h>0 else "crouch"),"standing_or_air_hit_never_maps",{"height":h,"pose":pose,"unit":true})
	var audio_source=FileAccess.get_file_as_string("res://presentation/side_audio.gd")
	check(audio_source.contains("var key: String=_state_entry_key(f)"),"actual_audio_sync_uses_entry_key_helper",{"unit":true})
func run() -> void:
	probe=UfeSideView.new();probe.intro_tick=-1;sound=UfeSideAudio.new()
	for target in ["zetton","ultraman"]:
		for direction in [1,-1]:
			for kind in CASES:run_case(target,direction,kind)
	units();legacy_check()
	check(int(load("res://core/combat/match_director.gd").get_script_constant_map().get("HIT_CROUCH_GUARD_RESUME_RULE_REVISION",0))==1,"semantic_rule_version")
	probe.free();sound.free()
	write_new(output.path_join("result.json"),{"cases":cases,"checks":checks,"errors":errors,"legacy":legacy_path,"no_post_tick_simulation_writes":true,"audio_listened":false,"art_installed":false})
	print("HIT_CROUCH_GUARD_RESUME "+JSON.stringify({"cases":cases.size(),"checks":checks,"errors":errors.size()}))
	quit(0 if errors.is_empty() else 1)
