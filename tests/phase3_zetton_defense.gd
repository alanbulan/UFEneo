extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,label: String) -> void:
	if not ok: failures.append(label)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var driver:=UfePhase3ZettonDefenseReview.new()
	var sim:=UfeContentDatabase.match_for()
	var twin:=UfeContentDatabase.match_for()
	var results: Dictionary={}
	for frame in range(driver.length_frames()):
		driver.review_frame=frame
		var part:=driver.section(frame)
		var id: String=driver.actions()[part]
		if part!=driver.last_section:
			sim=UfeContentDatabase.match_for();twin=UfeContentDatabase.match_for()
			driver.prepare_match(sim);driver.prepare_match(twin);driver.last_section=part
			results[id]={"clips":[],"events":[],"samples":[]}
		var inputs: Array=[driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"杰顿防御受击确定性 "+str(frame))
		var f:=sim.fighters[1];var b:=sim.fighters[0]
		if not results[id].clips.has(f.animation_key()):results[id].clips.append(f.animation_key())
		for e in sim.events:
			if e.kind in ["hit","block"]:results[id].events.append({"frame":frame,"player":e.player,"move":e.move,"kind":e.kind})
		results[id].samples.append({"frame":frame,"state":f.state,"clip":f.animation_key(),"height":f.height,"vy":f.vy,"x":f.x,"facing":f.facing,"move":f.move_id,"energy":f.stats.energy,"hp":f.stats.hp,"attacker_move":b.move_id,"attacker_state":b.state})
	for action in driver.actions():
		var rs: Dictionary=results[action]
		if action=="full_chain":
			var order: Array=[]
			for sample in rs.samples:
				if order.is_empty() or order[-1]!=sample.state:order.append(sample.state)
			check(order.has("launch") and order.has("bounce") and order.has("down") and order.has("roll_back"),"完整连段倒地后滚链 "+str(order))
			for move in ["launcher","chase_light1","chase_light2","chase_end"]:
				check(rs.events.any(func(e):return e.player==0 and e.kind=="hit" and e.move==move),"完整空连未命中 "+move)
		elif action not in ["walk_forward","walk_back"]:check(rs.clips.has(action),"杰顿未触发 "+action+str(rs.clips))
		if action in ["wake_low","wake_mid","guard_counter","burst"]:
			check(rs.events.any(func(e):return e.player==1 and e.kind=="hit" and e.move==action),"杰顿反击未命中 "+action)
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")
	for action in driver.actions():
		if action=="full_chain":continue
		check(manifest.clips.has(action),"缺正式动画 "+action)
		if not manifest.clips.has(action):continue
		var clip: Dictionary=manifest.clips[action]
		check(FileAccess.file_exists(clip.texture) and clip.rects.size()==clip.ticks.size(),"资源清单 "+action)
		if action in ["walk_forward","walk_back"]:continue # 重排显示时长不改变模拟受击框。
		var total:=0
		for duration in clip.ticks:total+=int(duration)
		if action in ["wake_low","wake_mid","guard_counter","burst"]:
			check(UfeMoveData.validate(sim.fighters[1].definition.moves[action]),"帧数据合法 "+action)
			check(total==sim.fighters[1].definition.moves[action].frames.size(),"招式显示时长 "+action)
		else:check(total==sim.fighters[1].definition.state_frames[action].size(),"状态显示时长 "+action)
	# 真实走路显示必须服从新的manifest时长，不能再被旧模拟sprite覆盖。
	var view:=UfeSideView.new()
	for fighter in ["ultraman","zetton"]:
		var trial:=UfeContentDatabase.match_for(fighter,"ultraman" if fighter=="zetton" else "zetton")
		var f:=trial.fighters[0]
		var m: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/"+fighter+"/animations/manifest.json")
		for action in ["walk_forward","walk_back"]:
			if not m.clips.has(action):continue
			var ticks: Array=m.clips[action].ticks
			var total:=0
			for t in ticks:total+=int(t)
			for t in ticks:check(float(t)>=0.6*total/ticks.size() and float(t)<=1.5*total/ticks.size(),"走路节奏范围 "+fighter+action)
			var age:=0
			f.enter("walk");f.resolver.previous_x=f.facing*(1 if action=="walk_forward" else -1)
			for i in range(ticks.size()):
				for local in range(int(ticks[i])):
					f.state_tick=age+local;check(int(view._animation(f,m).index)==i,"走路实播时长 "+fighter+action+str(age+local))
				age+=int(ticks[i])
	view.free()
	var report:=FileAccess.open("res://reports/phase3-zetton-defense-evidence.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"failures":failures,"actions":results},"\t"))
	print("PHASE3_ZETTON_DEFENSE "+JSON.stringify(failures))
	quit(0 if failures.is_empty() else 1)
