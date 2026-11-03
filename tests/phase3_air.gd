extends SceneTree
var failures: Array[String] = []
func check(ok: bool, label: String) -> void:
	if not ok: failures.append(label)
func _initialize() -> void: call_deferred("run")
func neutral() -> UfeInputFrame: return UfeInputFrame.make()
func run() -> void:
	var driver := UfePhase3AirReview.new()
	var sim := UfeContentDatabase.match_for()
	var twin := UfeContentDatabase.match_for()
	var view := UfeSideView.new()
	var manifest: Dictionary = UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json")
	var results: Dictionary = {}
	var hits: Dictionary = {}
	var combo_hits: Array = []
	var bounce_entries := 0
	var last_target := "idle"
	for movie_frame in range(driver.length_frames()):
		driver.review_frame = movie_frame
		var section := driver.section(movie_frame)
		var action: String = driver.ACTIONS[section]
		if section!=driver.last_section:
			sim = UfeContentDatabase.match_for()
			twin = UfeContentDatabase.match_for()
			driver.prepare_match(sim)
			driver.prepare_match(twin)
			driver.last_section = section
			results[action] = {"hits":[],"frames":[],"states":[],"trajectory":[]}
		var pair := [driver.sample(movie_frame,sim),driver.second_sample(movie_frame)]
		sim.step(pair)
		twin.step(pair)
		check(sim.state_hash()==twin.state_hash(),"跳跃/移动/斜下飞行物确定性 "+str(movie_frame))
		var f := sim.fighters[0]
		var b := sim.fighters[1]
		var a := view._animation(f,manifest)
		if action=="full_combo":results[action].trajectory.append({"frame":movie_frame,"state":f.state,"move":f.move_id,"move_tick":f.move_tick,"height":f.height,"x":f.x,"vy":f.vy,"target_x":b.x,"target_height":b.height,"target_vy":b.vy,"target_state":b.state,"land_window":f.motion.land_window,"chain_stage":driver.chain_stage,"events":sim.events.duplicate(true)})
		if not results[action].states.has(f.state):results[action].states.append(f.state)
		if f.move_id==action or (action in ["vertical_jump","flip_back"] and f.state=="air") or f.state==action:
			check(not a.is_empty(),action+"动画未接入")
			if not a.is_empty() and not results[action].frames.has(a.index):results[action].frames.append(a.index)
			results[action].trajectory.append({"frame":movie_frame,"height":f.height,"vy":f.vy,"x":f.x,"sprite":a.get("index",-1)})
		for event in sim.events:
			if event.kind=="hit" and event.player==0:
				hits[event.move] = true
				var record := {"frame":movie_frame,"move":event.move,"target_hp":b.stats.hp,"state":f.state,"land_window":f.motion.land_window}
				results[action].hits.append(record)
				if action=="full_combo":combo_hits.append(event.move)
		if action=="full_combo" and b.state=="bounce" and last_target!="bounce":bounce_entries+=1
		last_target = b.state
	for action in driver.ACTIONS:
		if action=="full_combo":continue
		check(manifest.clips.has(action),action+"缺正式清单")
		if not manifest.clips.has(action):continue
		var clip: Dictionary = manifest.clips[action]
		if action not in ["vertical_jump","flip_back","backstep","dodge"]:
			check(hits.has(action),action+"实际输入未命中杰顿")
			var d: Dictionary = sim.fighters[0].definition.moves[action]
			check(UfeMoveData.validate(d),action+"帧数据无效")
			check(view._clip_ticks(clip)==d.frames.size(),action+"动画与招式tick不一致")
		check(not results[action].frames.is_empty(),action+"没有实际播放")
	check(combo_hits==["launcher","chase_light1","chase_light2","chase_end","sweep"],"完整空连未实际逐招命中："+str(combo_hits))
	check(bounce_entries==1,"完整空连弹地次数不是一次")
	# 不依赖画面：落地的前两个tick允许追击，第三tick必须仍在落地硬直。
	for delay in [0,1,2]:
		for button in [UfeInputFrame.HEAVY,UfeInputFrame.CRUSH]:
			var trial := UfeContentDatabase.match_for()
			var f := trial.fighters[0]
			f.height = 1;f.vy = -1;f.enter("air");f.motion.bounce_followup = true
			trial.step([neutral(),neutral()])
			for i in range(delay):trial.step([neutral(),neutral()])
			trial.step([UfeInputFrame.make(0,-1 if button==UfeInputFrame.HEAVY else 0,button),neutral()])
			check((f.move_id==("sweep" if button==UfeInputFrame.HEAVY else "crush"))==(delay<2),"落地2tick边界 delay="+str(delay))
	# 同一连段第二次不能重新弹地。
	var trial := UfeContentDatabase.match_for()
	var f := trial.fighters[0]
	var b := trial.fighters[1]
	b.height=100
	UfeHitResolver.apply(f,b,f.definition.moves.chase_end,false,trial.rules)
	check(b.state=="bounce" and b.combat.bounced,"第一次空中砸地触发弹地")
	b.vy=3
	UfeHitResolver.apply(f,b,f.definition.moves.chase_end,false,trial.rules)
	check(b.state!="bounce" and b.vy==3,"同连段禁止第二次弹地")
	# 俯冲轨迹须独立于普通跳弧；斜下飞行物必须同时改变x和高度。
	var jump := UfeContentDatabase.match_for()
	var dive := UfeContentDatabase.match_for()
	for frame in range(20):
		jump.step([UfeInputFrame.make(0,1 if frame==0 else 0),neutral()])
		dive.step([UfeInputFrame.make(0,1 if frame==0 else -1 if frame==4 else 0,UfeInputFrame.HEAVY if frame==4 else 0),neutral()])
	check(dive.fighters[0].x>jump.fighters[0].x and dive.fighters[0].height<jump.fighters[0].height,"俯冲未改变落点与竖直轨迹")
	check(int(f.definition.moves.air_pulse.projectile.vy)<0,"空中光弹缺少斜下速度")
	view.free()
	var report := FileAccess.open("res://reports/phase3-air-evidence.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"failures":failures,"actions":results,"combo_hits":combo_hits,"bounce_entries":bounce_entries},"\t"))
	print("PHASE3_AIR "+JSON.stringify({"failures":failures,"combo_hits":combo_hits,"actions":results.keys()}))
	quit(0 if failures.is_empty() else 1)
