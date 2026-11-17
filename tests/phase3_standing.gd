extends SceneTree
var failures: Array[String] = []
func check(ok: bool, label: String) -> void:
	if not ok: failures.append(label)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var driver := UfeReviewDriver.new()
	driver.profile = "phase3_standing"
	var sim := UfeContentDatabase.match_for()
	var twin := UfeContentDatabase.match_for()
	var view := UfeSideView.new()
	var manifest: Dictionary = UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json")
	var sounds: Dictionary = UfeContentDatabase.read_json("res://content/presentation/action_sounds.json")
	var results: Dictionary = {}
	var states_seen: Dictionary = {}
	var seen: Dictionary = {}
	var hits: Dictionary = {}
	for frame in range(driver.length_frames()):
		driver.review_frame = frame
		var section := driver.section(frame)
		var action: String = driver.PHASE3_ACTIONS[section]
		if section != driver.last_section:
			sim = UfeContentDatabase.match_for()
			twin = UfeContentDatabase.match_for()
			driver.prepare_match(sim)
			driver.prepare_match(twin)
			driver.last_section = section
			results[action] = {"hits":[],"sprites":[],"states":[]}
		var pair := [driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(pair)
		twin.step(pair)
		check(sim.state_hash()==twin.state_hash(),"新动作/飞行物确定性 "+str(frame))
		var f := sim.fighters[0]
		states_seen[f.state] = true
		if not f.move_id.is_empty():
			seen[f.move_id] = true
			var animation := view._animation(f,manifest)
			check(not animation.is_empty(),"正式动画缺失 "+f.move_id)
			if f.move_id == action and not results[action].sprites.has(int(animation.index)): results[action].sprites.append(int(animation.index))
		for event in sim.events:
			if event.kind == "hit" and int(event.player)==0:
				hits[event.move] = true
				results[action].hits.append({"move":event.move,"frame":frame,"hp":sim.fighters[1].stats.hp,"projectile":event.projectile})
			if event.kind == "sound": check(sounds.sounds.has(event.id),"音效事件未映射 "+str(event.id))
	for action in driver.PHASE3_ACTIONS:
		check(seen.has(action),action+"指令没有触发")
		check(hits.has(action),action+"审片没有命中杰顿")
		var clip: Dictionary = manifest.clips[action]
		check(clip.rects.size()==clip.ticks.size(),action+"清单帧数时长不一致")
		var move: Dictionary = sim.fighters[0].definition.moves[action]
		check(UfeMoveData.validate(move),action+"帧数据不合法")
		check(view._clip_ticks(clip)==move.frames.size(),action+"动画时长与招式不一致")
		for frame in move.frames: check(int(frame.sprite)>=0 and int(frame.sprite)<clip.rects.size(),action+"sprite越界")
		if action != "crouch_light":
			check(results[action].sprites.size()==clip.rects.size(),action+"主游戏审片漏播帧")
	for state in ["crouch_start","crouch","crouch_rise"]:
		check(states_seen.has(state),state+"主游戏审片未演示")
		check(sim.fighters[0].definition.state_frames.has(state),state+"缺少低姿受击框")
	# 数据定义飞行盒必须依朝向镜像；贴地光弹与站立发射有自己的高度。
	var p := {"x":100,"height":50,"facing":1,"box":[-12,-8,30,16]}
	check(UfeMatchDirector.projectile_box(p)==Rect2i(88,42,30,16),"飞行物右向世界框")
	p.facing = -1
	check(UfeMatchDirector.projectile_box(p)==Rect2i(82,42,30,16),"飞行物左向镜像世界框")
	var moves := sim.fighters[0].definition.moves
	check(int(moves.low_pulse.projectile.spawn[1])<int(moves.pulse.projectile.spawn[1]),"低姿光弹发射高度")
	check(moves.ranged_forward.projectile.effect=="slash","八分光轮特效绑定")
	check(moves.crouch_light.frames[7].cancel.has("crouch_light2") and moves.crouch_light2.frames[7].cancel.has("sweep"),"下轻二连与扫腿取消")
	# 站防不能挡下段；蹲防挡下段但不能挡回旋中段；超重击破防。
	for setup in [["idle","sweep","hit"],["crouch","sweep","block"],["crouch","spin_heavy","hit"],["guard","crush","hit"]]:
		var guard_sim := UfeContentDatabase.match_for()
		var a := guard_sim.fighters[0]
		var b := guard_sim.fighters[1]
		b.enter(setup[0])
		check(UfeHitResolver.apply(a,b,moves[setup[1]],true,guard_sim.rules)==setup[2],"高低与破防 "+str(setup))
	view.free()
	var report := FileAccess.open("res://reports/phase3-standing-evidence.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"failures":failures,"actions":results,"states":states_seen.keys()},"\t"))
	print("PHASE3_LOGIC "+JSON.stringify({"failures":failures,"actions":results}))
	quit(0 if failures.is_empty() else 1)
