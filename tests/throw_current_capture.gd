extends SceneTree
const Capture = preload("res://core/combat/throw_current_capture.gd")
var errors: Array=[]
func _initialize() -> void:
	create_timer(25).timeout.connect(func():printerr("CAPTURE_TEST_TIMEOUT");quit(2))
	call_deferred("run")
func check(value: bool,label: String) -> void:
	if not value:errors.append(label);printerr(label)
func fixture(facing: int=1, enabled: bool=true) -> UfeMatchDirector:
	var a:=UfeContentDatabase.fighter("ultraman",true)
	var b:=UfeContentDatabase.fighter("ultraseven",true)
	var move: Dictionary=a.moves.throw_forward
	move.throw_target_air=true
	move.feedback.hitstop=4
	move.whiff_branch_tick=3;move.whiff_recovery_tick=17
	move.frames=[]
	for tick in range(24):
		var target: Dictionary
		if tick<3:target={"mode":"capture_current"}
		elif tick<8:target={"mode":"hold","pose":"grabbed","sprite":0,"facing":1,"grip":[52,100],"root":[999,999],"root_overrides":{"ultraseven":[0,0]},"hold_point_overrides":{"ultraseven":{"grabbed":{"0":[0,40]}}}}
		else:target={"mode":"release","pose":"thrown_back","sprite":0,"facing":1,"root":[200,0],"progress":[mini(8,tick-7),8],"ground":true,"impact":tick>=15}
		move.frames.append({"sprite":0,"dx":0,"dy":0,"hurtboxes":[[-8,0,16,64]],"hitboxes":[[40,40,24,100]] if tick<3 else [],"target":target,"cancel":[],"events":[]})
	if enabled:move.throw_current_capture={"target_ids":["ultraseven"],"states":["air"],"body_hurtbox_index":0,"first_tick":0,"entry_tick":3,"max_entry_root_delta":[14,14]}
	else:
		for tick in range(3):move.frames[tick].erase("target")
	b.state_frames.grabbed=[{"sprite":0,"dx":0,"dy":0,"hurtboxes":[[-8,0,16,64]],"hitboxes":[],"grab_points":{"waist":[0,40]},"cancel":[],"events":[]}]
	for frame in b.state_frames.vertical_air:frame.hurtboxes=[[-8,0,16,64]]
	var sim:=UfeMatchDirector.new(a,b,load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	sim.fighters[0].x=600;sim.fighters[0].facing=facing
	sim.fighters[1].x=600+52*facing;sim.fighters[1].height=60;sim.fighters[1].vy=1;sim.fighters[1].facing=facing;sim.fighters[1].enter("air")
	return sim
func scenario(facing: int,kind: String) -> void:
	var sim:=fixture(facing);var twin:=fixture(facing)
	if kind=="miss":
		for item in [sim,twin]:item.fighters[1].x+=100*facing
	var recorder:=UfeReplayRecorder.new();var hashes: Array=[]
	var captured:=false;var count:=0;var slams:=0;var techs:=0;var preserved:=0
	for tick in range(70):
		var pair:=[UfeInputFrame.make(),UfeInputFrame.make()]
		if tick==0:pair[0]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		if captured:
			count+=1
			if kind.begins_with("tech") and count==int(kind.trim_prefix("tech")):pair[1]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		sim.step(pair);twin.step(pair.map(func(i):return UfeInputFrame.unpack(i.pack())))
		check(sim.state_hash()==twin.state_hash(),"确定性/%s"%kind)
		recorder.append(pair,sim);hashes.append(sim.state_hash())
		var b:=sim.fighters[1]
		if b.state=="thrown":captured=true
		if Capture.active(b):
			preserved+=1
			var saved: Dictionary=b.motion.throw_current_capture
			check(b.frame()==saved.frame and b.facing==facing and b.x==int(saved.x) and b.height==int(saved.height),"原相朝向根点保留")
			var view:=UfeSideView.new();var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/ultraseven/animations/manifest.json")
			check(view._animation(b,manifest)==view._animation(Capture.visual_fighter(b),manifest),"保相表现复用原动画")
			view.free()
		if b.state!="thrown":check(not b.motion.has("throw_current_capture"),"退出清快照")
		for event in sim.events:
			if event.kind=="throw_slam":slams+=1;check(b.height==0,"唯一伤害在落地")
			if event.kind=="throw_tech":techs+=1
	var broken:=kind in ["tech1","tech2","tech3"]
	check(captured==(kind!="miss"),"实际捕获/%s"%kind)
	check(slams==(0 if broken or kind=="miss" else 1),"唯一伤害/%s"%kind)
	check(techs==(1 if broken else 0),"拆投边界/%s"%kind)
	check(sim.fighters[1].stats.hp==1000-(int(sim.fighters[0].definition.moves.throw_forward.damage) if slams==1 else 0),"伤害守恒")
	if kind!="miss":check(preserved>0,"实际保相消费")
	var path:="user://capture-%s-%s.json"%[facing,kind]
	check(recorder.save_file(path)==OK,"保存回放")
	var loaded:=UfeReplayRecorder.load_file(path,sim.content_fingerprint)
	check(loaded!=null,"回放读取")
	if loaded!=null:
		var replay:=fixture(facing)
		if kind=="miss":replay.fighters[1].x+=100*facing
		for tick in range(loaded.frames.size()):
			replay.step(loaded.frames[tick].map(func(i):return UfeInputFrame.unpack(i)))
			check(replay.state_hash()==hashes[tick],"独立文件逐tick重放")
func run() -> void:
	var sim:=fixture();var a:=sim.fighters[0];var b:=sim.fighters[1];var move: Dictionary=a.definition.moves.throw_forward
	check(UfeMoveData.validate(move),"合法opt-in schema")
	a.move_id="throw_forward";a.move_tick=0
	check(Capture.eligible(a,b,move),"入口使用root覆盖而非999默认")
	var old:=move.duplicate(true);old.erase("throw_current_capture")
	check(not Capture.valid_move(old),"未opt-in不能使用capture_current")
	for value in [null,{},false,{"states":[]}]:
		var bad:=move.duplicate(true);bad.throw_current_capture=value
		check(not Capture.valid_move(bad),"非法schema拒绝")
	for field in ["frames_type","frames","hitboxes","target","grip","sprite","root","pose"]:
		var bad:=move.duplicate(true)
		if field=="frames_type":bad.frames=null
		elif field=="frames":bad.frames=[null]
		elif field=="hitboxes":bad.frames[0].erase("hitboxes")
		elif field=="target":bad.frames[0].target=[]
		else:bad.frames[3].target[field]=null
		check(not UfeMoveData.validate(bad),"畸形入口拒绝/"+field)
	for field in ["dx","dy","throw_height"]:
		var moving:=move.duplicate(true)
		if field == "throw_height":
			moving.frames[3][field] = [1, 2]
		else:
			moving.frames[3][field] = 1
		check(not Capture.valid_move(moving),"拒绝保相至entry攻击方位移/"+field)
	a.height=1;check(not Capture.eligible(a,b,move),"拒绝空中攻击方");a.height=0
	b.definition.state_frames.grabbed[0].throw_hold_floor_variants=[0]
	check(not Capture.eligible(a,b,move),"拒绝可换相入口")
	b.definition.state_frames.grabbed[0].erase("throw_hold_floor_variants")
	b.x+=15;check(not Capture.eligible(a,b,move),"不吸附越界根点");b.x-=15
	var view:=UfeSideView.new()
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/ultraseven/animations/manifest.json")
	var original_animation:=view._animation(b,manifest)
	var original_frame:=b.frame().duplicate(true)
	Capture.remember(b,move);b.enter("thrown");UfeThrowResolver.begin(sim,0,move)
	check(view._animation(b,manifest)==original_animation and b.frame()==original_frame,"捕获前后真实整相一致")
	view.free()
	check(Capture.active(b),"保存有效")
	a.move_tick=3;UfeThrowResolver.sync(sim);check(not b.motion.has("throw_current_capture"),"hold停用")
	b.enter("air");Capture.remember(b,move);b.enter("thrown")
	a.frame().target={"mode":"root","pose":"thrown_back","sprite":0,"root":[20,60]}
	UfeThrowResolver.sync(sim);check(not b.motion.has("throw_current_capture"),"root停用")
	b.enter("air");Capture.remember(b,move);b.enter("thrown");a.clear_move();UfeThrowResolver.sync(sim)
	check(not Capture.active(b) and not b.motion.has("throw_current_capture"),"中断清快照")
	# 人工对照：当前全局规则仅省capture扩展，不是历史版本回放。
	var baseline:=fixture(1,false)
	var forms: Array=[]
	for fighter in baseline.fighters:forms.append(UfeBattleTransform.simulation_data(fighter.battle_form))
	var payload: Array=[6,60,baseline.rules.simulation_data(),baseline.fighters[0].definition.simulation_data(),baseline.fighters[1].definition.simulation_data(),forms,["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION],["hit_pushback_bounds",UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],["throw_target_air",UfeHitResolver.THROW_TARGET_RULE_REVISION],["chase_interrupt",UfeMatchDirector.CHASE_INTERRUPT_RULE_REVISION],["projectile_contact_direction",UfeHitResolver.PROJECTILE_DIRECTION_RULE_REVISION],["projectile_move_isolation",UfeHitResolver.PROJECTILE_MOVE_ISOLATION_RULE_REVISION], ["projectile_beam_reflection", UfeProjectileResolver.BEAM_REFLECTION_RULE_REVISION],["crouch_guard_resume_hold",UfeMatchDirector.CROUCH_GUARD_RESUME_RULE_REVISION],["hit_crouch_guard_resume_pose",UfeMatchDirector.HIT_CROUCH_GUARD_RESUME_RULE_REVISION],["feel_rules",UfeFeelRules.REVISION]]
	if UfeThrowResolver.RootOffsets.used_in(payload):payload.append(["throw_root_overrides",UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION])
	check(baseline.content_fingerprint==JSON.stringify(payload,"",true).sha256_text(),"未opt-in时当前规则省capture人工基线相等")
	check(not Capture.used_in(payload),"未opt-in内容不含capture扩展语义")
	check(Capture.used_in(move),"opt-in参与语义")
	var opted:=fixture()
	payload[3]=opted.fighters[0].definition.simulation_data()
	payload[4]=opted.fighters[1].definition.simulation_data()
	payload.append(["throw_current_capture",Capture.REVISION])
	check(opted.content_fingerprint==JSON.stringify(payload,"",true).sha256_text(),"仅opt-in绑定新语义版本")
	for facing in [-1,1]:
		for kind in ["land","tech1","tech2","tech3","tech4","miss"]:scenario(facing,kind)
	print("THROW_CURRENT_CAPTURE ",JSON.stringify({"errors":errors,"input_cases":12,"scope":"generic opt-in, not Gomora installation or visual acceptance"}));quit(0 if errors.is_empty() else 1)
