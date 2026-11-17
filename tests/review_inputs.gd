extends SceneTree
@warning_ignore_start("integer_division")
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var driver := UfeReviewDriver.new()
	var sim := UfeContentDatabase.match_for()
	var hits_seen: Dictionary = {}
	var missing: Array = []
	var manifest: Dictionary = UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json")
	for id in ["idle","walk_forward","walk_back","dash_start","dash","dash_stop","light1","light2","light3","takeoff","flip_forward","land","diagonal_heavy","launcher","chase_takeoff","chase_light1"]:
		if not manifest.clips.has(id):
			missing.append(id+"图集未入清单")
			continue
		var clip: Dictionary = manifest.clips[id]
		# 经导入资源读取图集；Image.load_from_file 直接读 res:// 下的 PNG 在导出后
		# 不可用，引擎会报黄色警告。
		var texture := load(str(clip.texture)) as Texture2D
		var atlas: Image = texture.get_image() if texture != null else null
		if atlas == null or clip.rects.size() != clip.ticks.size():
			missing.append(id+"图集或时长清单无效")
			continue
		var bounds := Rect2i(0,0,atlas.get_width(),atlas.get_height())
		for rect in clip.rects:
			if not bounds.encloses(Rect2i(rect[0],rect[1],rect[2],rect[3])): missing.append(id+"切帧越界")
		for ticks in clip.ticks:
			if ticks <= 0: missing.append(id+"帧时长无效")
	# 真实冲刺只有22 tick；起步2、四张跑步关键帧和刹停3都必须能播放到。
	var side := UfeSideView.new()
	var actor := sim.fighters[0]
	actor.enter("dash",22)
	var shown: Dictionary = {}
	for tick in range(22):
		actor.state_tick = tick
		var animation := side._animation(actor,manifest)
		var id := str(animation.get("texture",""))
		if not shown.has(id): shown[id] = {}
		shown[id][int(animation.get("index",-1))] = true
	for id in ["dash_start","dash","dash_stop"]:
		var clip: Dictionary = manifest.clips[id]
		if clip.loop: missing.append(id+"一次性冲刺不能循环")
		for index in range(clip.rects.size()):
			if not shown.get(clip.texture,{}).has(index): missing.append(id+"漏播帧"+str(index))
			if int(clip.ticks[index]) < 2 or int(clip.ticks[index]) > 4: missing.append(id+"时长超出2..4tick")
		if clip.rects.size() != (2 if id == "dash_start" else 4 if id == "dash" else 3): missing.append(id+"不符合九帧方案")
	if side._clip_ticks(manifest.clips.dash_start)+side._clip_ticks(manifest.clips.dash)+side._clip_ticks(manifest.clips.dash_stop) != 22:
		missing.append("冲刺三段时长之和不等于22tick")
	# 两个完整走路周期都不能在接头跳过或延长某一格。
	for id in ["walk_forward","walk_back"]:
		actor.enter("walk")
		actor.resolver.previous_x = 1 if id == "walk_forward" else -1
		var counts: Dictionary = {}
		var cycle_ticks := side._clip_ticks(manifest.clips[id])
		for tick in range(cycle_ticks*2):
			actor.state_tick = tick
			var animation := side._animation(actor,manifest)
			var index := int(animation.index)
			counts[index] = int(counts.get(index,0))+1
		for index in range(8):
			if counts.get(index,0) != int(manifest.clips[id].ticks[index])*2: missing.append(id+"循环时序异常")
	side.free()
	# 前后走审片都必须由真实输入连续移动6秒；检查符号、位移与非均匀时长。
	for profile in ["forward_walk","back_walk"]:
		var walk_driver := UfeReviewDriver.new()
		walk_driver.profile = profile
		var walk_sim := UfeContentDatabase.match_for()
		walk_driver.prepare_match(walk_sim)
		var start_x: int = walk_sim.fighters[0].x
		var direction := 1 if profile == "forward_walk" else -1
		var clip: Dictionary = manifest.clips.walk_forward if direction == 1 else manifest.clips.walk_back
		var walk_ticks := 0
		var walk_counts: Dictionary = {}
		var walk_view := UfeSideView.new()
		for frame in range(walk_driver.length_frames()):
			var pair := [walk_driver.sample(frame,walk_sim),walk_driver.second_sample(frame)]
			var previous_x: int = walk_sim.fighters[0].x
			walk_sim.step(pair)
			if walk_driver.held_walk(frame):
				walk_ticks += 1
				var f := walk_sim.fighters[0]
				if f.state != "walk" or f.facing != 1 or f.x-previous_x != direction*2 or walk_sim.fighters[1].x-f.x != 280:
					missing.append(profile+"审片输入未保持连续移动与间距")
				var animation := walk_view._animation(f,manifest)
				var index := int(animation.get("index",-1))
				if animation.get("texture","") != clip.texture: missing.append(profile+"动画方向错误")
				walk_counts[index] = int(walk_counts.get(index,0))+1
		if walk_ticks != 360 or walk_sim.fighters[0].x-start_x != direction*720:
			missing.append(profile+"审片不足6秒或位移不符")
		var walk_cycles := floori(float(walk_ticks)/walk_view._clip_ticks(clip))
		for index in range(8):
			var duration: int = clip.ticks[index]
			if walk_counts.get(index,0) < duration*walk_cycles or walk_counts.get(index,0) > duration*(walk_cycles+1):
				missing.append(profile+"审片循环丢帧或时长不符")
		walk_view.free()

	var dash_driver := UfeReviewDriver.new()
	dash_driver.profile = "dash_once"
	var dash_sim := UfeContentDatabase.match_for()
	dash_driver.prepare_match(dash_sim)
	var dash_entries := 0
	var dash_steps := 0
	var dash_displacement := 0
	for movie_frame in range(dash_driver.length_frames()):
		var f := dash_sim.fighters[0]
		var was_dash := f.state == "dash"
		var previous_x := f.x
		dash_sim.step([dash_driver.sample(movie_frame,dash_sim),dash_driver.second_sample(movie_frame)])
		if f.state == "dash" and f.state_tick == 0: dash_entries += 1
		if was_dash:
			dash_steps += 1
			dash_displacement += f.x-previous_x
			if f.x-previous_x != 6: missing.append("真实冲刺每tick位移不是6")
		if (movie_frame >= 86 and movie_frame < 116) or (movie_frame >= 142 and movie_frame < 172):
			if f.state != "idle" or dash_driver.dash_input(movie_frame) != 0: missing.append("两次冲刺之间未静止半秒")
	if dash_entries != 3 or dash_steps != 66 or dash_displacement != 396: missing.append("三次冲刺未各自执行22tick/132px")
	sim = UfeContentDatabase.match_for()
	for frame in range(1800):
		var part := driver.section(frame)
		if part != driver.last_section:
			sim = UfeContentDatabase.match_for()
			driver.last_section = part
		sim.step([driver.sample(frame,sim),UfeInputFrame.make()])
		for event in sim.events:
			if event.kind == "hit": hits_seen[sim.fighters[0].move_id] = true
	for id in ["light1","light2","light3","diagonal_heavy","launcher","chase_light1"]:
		if not driver.moves_seen.has(id): missing.append(id)
		if not hits_seen.has(id): missing.append(id+"未命中")
	for id in ["walk","dash","takeoff","air","land"]:
		if not driver.states_seen.has(id): missing.append(id)
	if not driver.launched or not driver.aerial_struck: missing.append("升击追击跳衔接")
	# 最终40秒真实输入必须在每组两半都覆盖动作，F1仅在后半打开。
	var final_driver := UfeReviewDriver.new()
	final_driver.profile = "gate_a_final"
	var final_sim := UfeContentDatabase.match_for()
	var final_moves: Dictionary = {}
	for frame in range(final_driver.length_frames()):
		var part := final_driver.section(frame)
		if part != final_driver.last_section:
			final_sim = UfeContentDatabase.match_for()
			final_driver.last_section = part
		var half := 1 if final_driver.boxes(frame) else 0
		var finish: int = final_driver.FINAL_STARTS[part+1] if part<5 else 2400
		if final_driver.boxes(frame) != (frame >= (int(final_driver.FINAL_STARTS[part])+finish)/2): missing.append("最终审片F1半段错误")
		final_sim.step([final_driver.sample(frame,final_sim),final_driver.second_sample(frame)])
		var key := str(part)+"/"+str(half)
		if not final_moves.has(key): final_moves[key] = {}
		final_moves[key][final_sim.fighters[0].move_id] = true
	for part in [3,4,5]:
		for half in [0,1]:
			var required: Array = ["light1","light2","light3"] if part==3 else ["diagonal_heavy"] if part==4 else ["launcher","chase_light1"]
			for id in required:
				if not final_moves.get(str(part)+"/"+str(half),{}).has(id): missing.append("最终审片第"+str(part)+"组半段"+str(half)+"缺"+id)
	print("REVIEW_INPUTS "+JSON.stringify({"missing":missing,"moves":driver.moves_seen.keys(),"states":driver.states_seen.keys(),"chase":driver.launched}))
	quit(0 if missing.is_empty() else 1)
@warning_ignore_restore("integer_division")
