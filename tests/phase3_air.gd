extends SceneTree
var failures: Array[String] = []
func check(ok: bool, label: String) -> void:
	if not ok: failures.append(label)
func _initialize() -> void: call_deferred("run")
func neutral() -> UfeInputFrame: return UfeInputFrame.make()
func test_air_special_landing() -> void:
	# 在发射/生效前一tick、当tick和后一tick落地；只截断非返航空中招式。
	var cases: Array = [
		["father-of-ultra", 10, "beam"], ["mother-of-ultra", 10, "beam"],
		["ultraman-gaia", 10, "beam"], ["ultraman-king", 10, "beam"],
		["ultraman-justice", 10, "beam"], ["ultraman-zero", 10, "beam"],
		["ultraman-ace", 7, "independent"], ["red_king", 12, "none"],
	]
	for row in cases:
		for facing in [-1, 1]:
			for boundary in [int(row[1]) - 1, int(row[1]), int(row[1]) + 1]:
				var sim := UfeContentDatabase.match_for(str(row[0]), "zetton")
				var f := sim.fighters[0]
				var label := "%s/%s/tick%s" % [row[0], facing, boundary]
				f.x = 1100 if facing < 0 else 150; f.facing = facing
				sim.fighters[1].x = 150 if facing < 0 else 1100
				f.height = 600; f.vy = 0; f.motion.jump_kind = "vertical"; f.enter("air")
				f.stats.energy = 1000
				check(not bool(f.definition.moves.air_special.get("finish_on_landing", false)), "非返航空中必杀按落地结束/" + label)
				sim.step([UfeInputFrame.make(0, 0, UfeInputFrame.SPECIAL), neutral()])
				check(f.move_id == "air_special", "真实P启动空中必杀/" + label)
				for _tick in range(1, int(boundary)): sim.step([neutral(), neutral()])
				check(f.move_id == "air_special" and f.move_tick == int(boundary), "落地前到达指定发射边界/" + label)
				var emitted := int(boundary) > int(row[1]) and str(row[2]) != "none"
				check(sim.projectiles.size() == (1 if emitted else 0), "落地前仅到发射帧才出弹/" + label)
				f.height = 1; f.vy = -1
				sim.step([neutral(), neutral()])
				check(f.height == 0 and f.move_id.is_empty() and f.state == "land" and f.animation_key() == "land", "同tick清空空中招式并显示落地/" + label)
				var surviving := emitted and str(row[2]) == "independent"
				check(sim.projectiles.size() == (1 if surviving else 0), "落地收束持续束但不误删已发独立弹/" + label)
				for _tick in range(6):
					sim.step([neutral(), neutral()])
					check(sim.projectiles.size() == (1 if surviving else 0), "发射前落地不得延迟偷射/" + label)
	# 赛文头镖确需落地继续返航/装回；不能用批量删除标志破坏合理分支。
	for facing in [-1, 1]:
		var sim := UfeContentDatabase.match_for("ultraseven", "zetton")
		var f := sim.fighters[0]
		f.x = 1000 if facing < 0 else 250; f.facing = facing
		f.height = 600; f.vy = 0; f.motion.jump_kind = "vertical"; f.enter("air")
		f.stats.energy = 1000
		check(bool(f.definition.moves.air_special.get("finish_on_landing", false)), "赛文返航保招声明保留")
		sim.step([UfeInputFrame.make(0, 0, UfeInputFrame.SPECIAL), neutral()])
		for _tick in range(7): sim.step([neutral(), neutral()])
		check(not sim.projectiles.is_empty() and sim.projectiles[0].has("integer_path"), "赛文真实P已发返航头镖")
		f.height = 1; f.vy = -1
		sim.step([neutral(), neutral()])
		check(f.height == 0 and f.move_id == "air_special" and not sim.projectiles.is_empty(), "赛文落地仍完成头镖返航")

func run() -> void:
	test_air_special_landing()
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
	var bounce_sim := UfeContentDatabase.match_for()
	var attacker := bounce_sim.fighters[0]
	var defender := bounce_sim.fighters[1]
	defender.height=100
	UfeHitResolver.apply(attacker,defender,attacker.definition.moves.chase_end,false,bounce_sim.rules)
	check(defender.state=="bounce" and defender.combat.bounced,"第一次空中砸地触发弹地")
	defender.vy=3
	UfeHitResolver.apply(attacker,defender,attacker.definition.moves.chase_end,false,bounce_sim.rules)
	check(defender.state!="bounce" and defender.vy==3,"同连段禁止第二次弹地")
	# 俯冲轨迹须独立于普通跳弧；斜下飞行物必须同时改变x和高度。
	var jump := UfeContentDatabase.match_for()
	var dive := UfeContentDatabase.match_for()
	for frame in range(20):
		jump.step([UfeInputFrame.make(0,0,UfeInputFrame.JUMP if frame==0 else 0),neutral()])
		dive.step([UfeInputFrame.make(0,1 if frame==0 else -1 if frame==4 else 0,UfeInputFrame.JUMP if frame==0 else UfeInputFrame.HEAVY if frame==4 else 0),neutral()])
	check(dive.fighters[0].x>jump.fighters[0].x and dive.fighters[0].height<jump.fighters[0].height,"俯冲未改变落点与竖直轨迹")
	check(int(attacker.definition.moves.air_pulse.projectile.vy)<0,"空中光弹缺少斜下速度")
	view.free()
	var report := FileAccess.open("res://reports/phase3-air-evidence.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"failures":failures,"actions":results,"combo_hits":combo_hits,"bounce_entries":bounce_entries},"\t"))
	print("PHASE3_AIR "+JSON.stringify({"failures":failures,"combo_hits":combo_hits,"actions":results.keys()}))
	quit(0 if failures.is_empty() else 1)
