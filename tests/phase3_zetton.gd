extends SceneTree
var out := "user://phase3-zetton/"
var failures: Array[String]=[]
func check(ok: bool,label: String) -> void:
	if not ok:failures.append(label)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--test-out="):out=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(out)
	var driver:=UfePhase3ZettonReview.new()
	var sim:=UfeContentDatabase.match_for()
	var twin:=UfeContentDatabase.match_for()
	var results: Dictionary={}
	var saw_groundball:=false
	for frame in range(driver.length_frames()):
		driver.review_frame=frame
		var id: String=driver.ACTIONS[driver.section(frame)]
		if driver.section(frame)!=driver.last_section:
			sim=UfeContentDatabase.match_for();twin=UfeContentDatabase.match_for()
			driver.prepare_match(sim);driver.prepare_match(twin);driver.last_section=driver.section(frame)
			results[id]={"moves":[],"events":[],"samples":[]}
		var inputs: Array=[driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"杰顿确定性 "+str(frame))
		for p in sim.projectiles:
			if p.owner==1 and p.move=="low_pulse":
				check(int(p.height)>=14,"贴地火球不能穿地")
				if p.height==14 and p.vy==0:saw_groundball=true
		var f:=sim.fighters[1]
		if not results[id].moves.has(f.move_id):results[id].moves.append(f.move_id)
		for event in sim.events:
			if event.kind in ["hit","block"]:results[id].events.append({"frame":frame,"kind":event.kind,"move":event.move,"player":event.player})
		results[id].samples.append({"frame":frame,"x":f.x,"state":f.state,"state_tick":f.state_tick,"sprite":f.frame().sprite,"move":f.move_id,"move_tick":f.move_tick,"p1_hp":sim.fighters[0].stats.hp,"events":sim.events.duplicate(true)})
	var required: Array=["light1","light2","light3","heavy","launcher","spin_heavy","crush","tackle","pulse","ranged_forward","crouch_light","crouch_light2","sweep","slide","low_pulse"]
	var hits: Array=[]
	for result in results.values():
		for event in result.events:
			if event.player==1 and event.kind=="hit":hits.append(event.move)
	for action in required:
		check(hits.has(action),"玩家二真实输入未命中 "+action)
		check(UfeMoveData.validate(sim.fighters[1].definition.moves[action]),"杰顿逐tick数据 "+action)
	var m: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")
	for key in m.clips:
		var clip: Dictionary=m.clips[key]
		check(FileAccess.file_exists(clip.texture),"杰顿纹理 "+key)
		check(clip.rects.size()==clip.ticks.size(),"杰顿帧数 "+key)
		for duration in clip.ticks:check(int(duration)>0,"杰顿时长 "+key)
	for action in required:
		var total:=0
		for duration in m.clips[action].ticks:total+=int(duration)
		check(total==sim.fighters[1].definition.moves[action].frames.size(),"招式/动画时长一致 "+action)
	var dash_total:=0
	for key in ["dash_start","dash","dash_stop"]:
		check(not bool(m.clips[key].loop),"冲刺一次性 "+key)
		for duration in m.clips[key].ticks:dash_total+=int(duration)
	check(dash_total==22,"杰顿冲刺22tick")
	check(sim.fighters[1].definition.walk_speed==2,"杰顿走速不变")
	check(saw_groundball,"脸部火球下降后应沿地面飞行")
	# 同角色相同输入跨多个周期，模拟位移与动画播放时长互不推导。
	for direction in [-1,1]:
		var trial:=UfeContentDatabase.match_for();trial.fighters[1].x=500;trial.fighters[0].x=900;trial.fighters[1].facing=1
		for tick in range(120):trial.step([UfeInputFrame.make(direction),UfeInputFrame.make(direction)])
		check(trial.fighters[1].x==500+direction*240,"走速每tick2像素 "+str(direction))
	var report:=FileAccess.open(out+"phase3-zetton-evidence.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"failures":failures,"actions":results},"\t"))
	print("PHASE3_ZETTON "+JSON.stringify({"failures":failures,"hits":hits}))
	quit(0 if failures.is_empty() else 1)
