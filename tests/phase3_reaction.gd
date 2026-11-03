extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,label: String) -> void:
	if not ok: failures.append(label)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var driver:=UfePhase3ReactionReview.new()
	var sim:=UfeContentDatabase.match_for()
	var twin:=UfeContentDatabase.match_for()
	var results: Dictionary={}
	for frame in range(driver.length_frames()):
		driver.review_frame=frame
		var part:=driver.section(frame)
		var id: String=driver.ACTIONS[part]
		if part!=driver.last_section:
			sim=UfeContentDatabase.match_for()
			twin=UfeContentDatabase.match_for()
			driver.prepare_match(sim)
			driver.prepare_match(twin)
			driver.last_section=part
			results[id]={"states":[],"clips":[],"moves":[],"events":[],"samples":[]}
		var inputs: Array=[driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(inputs)
		twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"防御受击确定性 "+str(frame))
		var f:=sim.fighters[0]
		for pair in [["states",f.state],["clips",f.animation_key()],["moves",f.move_id]]:
			if not results[id][pair[0]].has(pair[1]):results[id][pair[0]].append(pair[1])
		for e in sim.events:
			if e.kind in ["hit","block"]:results[id].events.append({"frame":frame,"player":e.player,"move":e.move,"kind":e.kind})
		results[id].samples.append({"frame":frame,"state":f.state,"clip":f.animation_key(),"sprite":f.frame().sprite,"height":f.height,"vy":f.vy,"x":f.x,"facing":f.facing,"move":f.move_id,"energy":f.stats.energy,"hp":f.stats.hp,"p2_hp":sim.fighters[1].stats.hp,"p2_state":sim.fighters[1].state,"p2_move":sim.fighters[1].move_id,"p2_height":sim.fighters[1].height,"p2_tick":sim.fighters[1].move_tick})
	for action in driver.ACTIONS:
		if action=="full_chain":
			var sequence: Array=[]
			for sample in results[action].samples:
				if sequence.is_empty() or sequence[-1]!=sample.state:sequence.append(sample.state)
			check(sequence.has("launch") and sequence.has("bounce") and sequence.has("down") and sequence.has("roll_forward"),"完整击飞→弹地→倒地→前滚未触发 "+str(sequence))
		else: check(results[action].clips.has(action),"实际输入未触发 "+action+" "+str(results[action].clips))
		if action in ["wake_low","wake_mid","guard_counter","burst"]:
			check(results[action].events.any(func(e):return e.player==0 and e.kind=="hit" and e.move==action),action+"未实际命中陪练")
	# 防御高低判定和已受击后不能重新按防御吞掉连段。
	for posture in ["guard","crouch_guard"]:
		for level in ["mid","low","overhead"]:
			var trial:=UfeContentDatabase.match_for()
			var a:=trial.fighters[1]
			var b:=trial.fighters[0]
			b.enter(posture)
			var move: Dictionary=a.definition.moves.heavy.duplicate(true)
			move.level=level
			var result:=UfeHitResolver.apply(a,b,move,true,trial.rules)
			var expected: bool=level=="mid" or level=="low" and posture=="crouch_guard" or level=="overhead" and posture=="guard"
			check((result=="block")==expected,"高低防御 "+posture+" "+level)
	# 不足能量不能使用；足额恰好消耗一/二格。
	for id in ["guard_counter","burst"]:
		for enough in [false,true]:
			var trial:=UfeContentDatabase.match_for()
			var f:=trial.fighters[0]
			var cost:=1000 if id=="guard_counter" else 2000
			f.stats.energy=cost if enough else cost-1
			f.enter("guard" if id=="guard_counter" else "hit",20)
			f.combat.buffer=id;f.combat.buffer_ticks=7
			trial.step([UfeInputFrame.make(0,0,UfeInputFrame.GUARD),UfeInputFrame.make()])
			check((f.move_id==id)==enough,"能量门槛 "+id+str(enough))
			if enough:check(f.stats.energy==0,"能量扣除 "+id)
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json")
	for action in driver.ACTIONS:
		if action=="full_chain":continue
		check(manifest.clips.has(action),action+"缺正式动画清单")
		if not manifest.clips.has(action):continue
		var clip: Dictionary=manifest.clips[action]
		var total:=0
		for duration in clip.ticks:
			check(int(duration)>0,action+"帧时长必须正整数")
			total+=int(duration)
		check(FileAccess.file_exists(clip.texture),action+"纹理缺失")
		check(clip.rects.size()==clip.ticks.size(),action+"矩形与时长数量不符")
		check(bool(clip.loop)==(action in ["stun","charge"]),action+"循环属性不符")
		if action in ["wake_low","wake_mid","guard_counter","burst"]:
			check(UfeMoveData.validate(sim.fighters[0].definition.moves[action]),action+"逐tick招式数据无效")
			check(total==sim.fighters[0].definition.moves[action].frames.size(),action+"显示与招式时长不符")
		else:
			check(total==sim.fighters[0].definition.state_frames[action].size(),action+"显示与受击框时长不符")
	# 从正面受击后根点向后移动，背面受击先记录来向，画面不能倒向打击方。
	for attack_x in [300,700]:
		var trial:=UfeContentDatabase.match_for()
		var a:=trial.fighters[1];var b:=trial.fighters[0]
		a.x=attack_x;a.facing=1 if attack_x<470 else -1
		UfeHitResolver.apply(a,b,a.definition.moves.heavy,false,trial.rules)
		check(b.facing==(1 if attack_x>470 else -1),"受击来向")
		check((b.x-470)*b.facing<0,"受击后退方向")
	var report:=FileAccess.open("res://reports/phase3-reaction-evidence.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"failures":failures,"actions":results},"\t"))
	print("PHASE3_REACTION "+JSON.stringify({"failures":failures,"actions":results.keys()}))
	quit(0 if failures.is_empty() else 1)
