extends SceneTree
@warning_ignore_start("integer_division")
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--skill-trace="):
			var failures: Array = []
			replay_skill_trace(arg.trim_prefix("--skill-trace="), failures)
			print("SKILL_TRACE_REPLAY "+JSON.stringify({"missing":failures}))
			quit(0 if failures.is_empty() else 1)
			return
		if arg.begins_with("--throw-trace="):
			var failures: Array = []
			replay_zoffy_throw_trace(arg.trim_prefix("--throw-trace="), failures)
			print("ZOFFY_THROW_TRACE_REPLAY "+JSON.stringify({"missing":failures}))
			quit(0 if failures.is_empty() else 1)
			return
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
	check_zoffy_inputs(missing)
	check_king_projectile_continuity(missing)
	print("REVIEW_INPUTS "+JSON.stringify({"missing":missing,"moves":driver.moves_seen.keys(),"states":driver.states_seen.keys(),"chase":driver.launched}))
	quit(0 if missing.is_empty() else 1)
@warning_ignore_restore("integer_division")

func zoffy_check(ok: bool, label: String, missing: Array) -> void:
	var detail := "佐菲/" + label
	if not ok and not missing.has(detail): missing.append(detail)

func check_zoffy_inputs(missing: Array) -> void:
	var manifest: Dictionary = UfeContentDatabase.read_json("res://assets/fighters/zoffy/animations/manifest.json")
	var view := UfeSideView.new()
	check_zoffy_locomotion(view, manifest, missing)
	check_zoffy_jumps(view, manifest, missing)
	check_zoffy_cancel_chain(missing)
	check_zoffy_legacy_holds(view, manifest, missing)
	check_zoffy_authored_holds(missing)
	check_zoffy_skills(view, manifest, missing)
	view.free()

func check_zoffy_locomotion(view: UfeSideView, manifest: Dictionary, missing: Array) -> void:
	for facing in [1, -1]:
		for direction in [1, -1]:
			var sim := UfeContentDatabase.match_for("zoffy", "ultraman")
			var actor := sim.fighters[0]
			actor.x = 640; actor.facing = facing
			sim.fighters[1].x = 640 + facing * 500; sim.fighters[1].facing = -facing
			var key := "walk_forward" if direction == 1 else "walk_back"
			var clip: Dictionary = manifest.clips[key]
			var rows: Array = actor.definition.state_frames.get(key, [])
			var counts: Dictionary = {}
			var total := view._clip_ticks(clip)
			zoffy_check(total > 0 and rows.size() == total, key + "完整计时表", missing)
			if rows.is_empty() or total <= 0: continue
			for _tick in range(total * 2):
				var previous_x := actor.x
				sim.step([UfeInputFrame.make(facing * direction), UfeInputFrame.make()])
				var animation := view._animation(actor, manifest)
				var frame := actor.frame()
				var expected: Dictionary = rows[actor.state_tick % rows.size()]
				zoffy_check(actor.state == "walk" and actor.facing == facing and actor.x - previous_x == facing * direction * actor.definition.walk_speed, key + "双向真实移动", missing)
				zoffy_check(animation.get("key", "") == key and int(animation.get("index", -1)) == int(frame.sprite) and frame.hurtboxes == expected.hurtboxes, key + "显示与模拟受击姿势逐 tick 对应", missing)
				var sprite := int(animation.get("index", -1))
				counts[sprite] = int(counts.get(sprite, 0)) + 1
			for sprite in range(clip.rects.size()):
				zoffy_check(int(counts.get(sprite, 0)) == int(clip.ticks[sprite]) * 2, key + "两周期每格停留准确", missing)
		# 双击前进入真实 dash，检查完整 22 tick，而不是手工 enter 后跳采样。
		var dash_sim := UfeContentDatabase.match_for("zoffy", "ultraman")
		var runner := dash_sim.fighters[0]
		runner.x = 640; runner.facing = facing
		dash_sim.fighters[1].x = 640 + facing * 500; dash_sim.fighters[1].facing = -facing
		var expected_dash: Array = []
		var offset := 0
		for key in ["dash_start", "dash", "dash_stop"]:
			var clip: Dictionary = manifest.clips[key]
			for sprite in range(clip.rects.size()):
				for _tick in range(int(clip.ticks[sprite])):
					expected_dash.append({"key": key, "index": sprite, "sprite": offset + sprite})
			offset += clip.rects.size()
		var dash_counts: Dictionary = {}
		var dash_samples := 0
		var dash_distance := 0
		for tick in range(35):
			var was_dash := runner.state == "dash"
			var previous_x := runner.x
			dash_sim.step([UfeInputFrame.make(facing if tick in [0, 2] else 0), UfeInputFrame.make()])
			if was_dash: dash_distance += (runner.x - previous_x) * facing
			if runner.state != "dash": continue
			dash_samples += 1
			zoffy_check(runner.motion.duration == 22 and runner.state_tick < expected_dash.size(), "dash真实状态仍为22tick", missing)
			if runner.state_tick >= expected_dash.size(): continue
			var expected: Dictionary = expected_dash[runner.state_tick]
			var animation := view._animation(runner, manifest)
			var sprite := int(runner.frame().sprite)
			zoffy_check(sprite == int(expected.sprite) and animation.get("key", "") == expected.key and int(animation.get("index", -1)) == int(expected.index), "dash全局0..8与三段局部图逐tick对应", missing)
			dash_counts[sprite] = int(dash_counts.get(sprite, 0)) + 1
		zoffy_check(dash_samples == 22 and dash_distance == 132 and runner.state == "idle", "dash真实输入完整22tick/132px后结束", missing)
		zoffy_check(dash_counts.size() == 9, "dash九图全部可达", missing)
		for sprite in range(9):
			var duration := 0
			for expected in expected_dash:
				if int(expected.sprite) == sprite: duration += 1
			zoffy_check(int(dash_counts.get(sprite, 0)) == duration and duration >= 2 and duration <= 4, "dash每张图实际停留等于清单时长", missing)

func check_zoffy_jumps(view: UfeSideView, manifest: Dictionary, missing: Array) -> void:
	# 普通三种跳跃按 jump_speed-vy 查表；不把空中追击套入同一断言。
	for facing in [1, -1]:
		for jump in [["vertical", 0, "vertical_jump"], ["diagonal", 1, "flip_forward"], ["backward", -1, "flip_back"]]:
			var sim := UfeContentDatabase.match_for("zoffy", "ultraman")
			var actor := sim.fighters[0]
			actor.x = 640; actor.facing = facing
			sim.fighters[1].x = 640 + facing * 500; sim.fighters[1].facing = -facing
			var key := str(jump[2])
			var rows: Array = actor.definition.state_frames.get(str(jump[0]) + "_air", [])
			zoffy_check(rows.size() == 32, key + "轨迹表存在且32tick", missing)
			var shown: Dictionary = {}
			var rising := false
			var falling := false
			var landed := false
			for tick in range(45):
				sim.step([UfeInputFrame.make(int(jump[1]) * facing if tick == 0 else 0, 0, UfeInputFrame.JUMP if tick == 0 else 0), UfeInputFrame.make()])
				if actor.state == "land": landed = true
				if actor.state != "air" or rows.is_empty(): continue
				var phase := clampi(actor.definition.jump_speed - actor.vy, 0, rows.size() - 1)
				var frame := actor.frame()
				var expected: Dictionary = rows[phase]
				var animation := view._animation(actor, manifest)
				zoffy_check(actor.motion.jump_kind == str(jump[0]) and actor.facing == facing, key + "真实起跳类型与朝向", missing)
				zoffy_check(frame.hurtboxes == expected.hurtboxes and int(frame.sprite) == int(expected.sprite), key + "受击框来自jump_speed-vy轨迹表", missing)
				zoffy_check(animation.get("key", "") == key and int(animation.get("index", -1)) == int(expected.sprite), key + "显示与轨迹帧一致", missing)
				shown[int(animation.get("index", -1))] = true
				rising = rising or actor.vy > 0
				falling = falling or actor.vy < 0
			zoffy_check(shown.size() > 1 and shown.size() == manifest.clips[key].rects.size() and rising and falling and landed, key + "双向完整升落且不锁sprite0", missing)

func check_zoffy_cancel_chain(missing: Array) -> void:
	for opponent in ["ultraman", "zoffy"]:
		check_zoffy_cancel_against(str(opponent), missing)

func check_zoffy_cancel_against(opponent: String, missing: Array) -> void:
	# 8/9预按及原窗口10..18逐tick真实送6K；未确认或停顿中只缓冲，首个合法tick立即取消。
	for facing in [1, -1]:
		for cancel_tick in range(8, 19):
			var sim := UfeContentDatabase.match_for("zoffy", opponent)
			var actor := sim.fighters[0]
			actor.x = 640 - facing * 80; actor.facing = facing
			sim.fighters[1].x = 640 + facing * 80
			sim.fighters[1].facing = -facing
			for _tick in range(100): sim.step([UfeInputFrame.make(facing), UfeInputFrame.make()])
			for _tick in range(8): sim.step([UfeInputFrame.make(), UfeInputFrame.make()])
			var second_sent := false
			var launcher_sent := false
			var cancelled := false
			var starts: Array[String] = []
			var hits: Array[String] = []
			var label := "轻一→轻二→launcher/%s/%d/%d" % [opponent, facing, cancel_tick]
			for tick in range(120):
				var input := UfeInputFrame.make(0, 0, UfeInputFrame.LIGHT if tick == 0 else 0)
				if not second_sent and actor.move_id == "light1" and actor.combat.confirmed and sim.hitstop == 0:
					input = UfeInputFrame.make(0, 0, UfeInputFrame.LIGHT)
					second_sent = true
				var request_launcher := not launcher_sent and actor.move_id == "light2" and actor.move_tick == cancel_tick
				if request_launcher:
					input = UfeInputFrame.make(facing, 0, UfeInputFrame.HEAVY)
					launcher_sent = true
				var previous_move := actor.move_id
				var previous_tick := actor.move_tick
				var legal_cancel := launcher_sent and previous_move == "light2" and actor.combat.confirmed and sim.hitstop == 0
				sim.step([input, UfeInputFrame.make()])
				if legal_cancel:
					cancelled = actor.move_id == "launcher"
					zoffy_check(cancelled and previous_tick in range(10, 19), label + "原窗口首个合法tick直接取消", missing)
				elif request_launcher:
					zoffy_check(actor.move_id == "light2", label + "未确认或停顿中不提前取消", missing)
				if not actor.move_id.is_empty() and actor.move_id != previous_move: starts.append(actor.move_id)
				for event in sim.events:
					if event.kind == "hit" and int(event.player) == 0: hits.append(str(event.move))
			zoffy_check(second_sent and launcher_sent and cancelled and starts == ["light1", "light2", "launcher"], label + "真实按键启动顺序", missing)
			zoffy_check(hits.slice(0, 2) == ["light1", "light2"], label + "前两段真实命中确认", missing)
			# 只要求最早执行的取消构成三次实际命中；不扩大判定或硬直强保晚连段。
			if cancel_tick <= 10: zoffy_check(hits == ["light1", "light2", "launcher"], label + "逐招实际命中", missing)

func check_zoffy_legacy_holds(view: UfeSideView, manifest: Dictionary, missing: Array) -> void:
	# 初代旧式 hold 无覆盖抓点，也不走 capture_current；佐菲作为受方覆盖四种投法。
	for facing in [1, -1]:
		for move_id in ["throw_forward", "throw_back", "air_throw", "dash_throw"]:
			var sim := UfeContentDatabase.match_for("ultraman", "zoffy")
			var actor := sim.fighters[0]
			var victim := sim.fighters[1]
			actor.x = 640; actor.facing = facing
			victim.x = 640 + facing * (actor.definition.body_radius + victim.definition.body_radius); victim.facing = -facing
			var move: Dictionary = actor.definition.moves[move_id]
			var label := "旧式hold/%s/%d" % [move_id, facing]
			var safe := true
			var legacy_frames := 0
			# 先报告缺点而不让已知缺字段直接中断整个测试进程。
			for row in move.frames:
				var target: Dictionary = row.get("target", {})
				if target.get("mode", "") != "hold": continue
				legacy_frames += 1
				var pose := UfeThrowResolver.pose_frame(victim, str(target.pose), int(target.get("sprite", 0)))
				var point: Array = pose.get("grab_points", {}).get(str(target.get("grab_point", "waist")), [])
				safe = safe and not target.has("hold_point_overrides") and int(pose.get("sprite", -1)) == int(target.get("sprite", 0)) and UfeThrowResolver.HoldPoints.point_valid(point)
			zoffy_check(safe and legacy_frames > 0, label + "所有旧式受投抓点可直接读取", missing)
			if not safe or legacy_frames == 0: continue
			var hold_ticks := 0
			var sent := false
			var release_heights: Array[int] = []
			var hits: Array[String] = []
			var slams: Array[String] = []
			for tick in range(100):
				var input := UfeInputFrame.make()
				var victim_input := UfeInputFrame.make()
				if move_id == "air_throw":
					if tick == 0:
						input = UfeInputFrame.make(0, 0, UfeInputFrame.JUMP); victim_input = UfeInputFrame.make(0, 0, UfeInputFrame.JUMP)
					elif not sent and actor.state == "air" and victim.state == "air":
						input = UfeInputFrame.make(0, 0, UfeInputFrame.THROW); sent = true
				elif move_id == "dash_throw":
					input = UfeInputFrame.make(facing if tick in [0, 2] else 0, 0, UfeInputFrame.THROW if tick == 3 else 0)
				elif tick == 0:
					input = UfeInputFrame.make(-facing if move_id == "throw_back" else 0, 0, UfeInputFrame.THROW)
				sim.step([input, victim_input])
				for event in sim.events:
					zoffy_check(event.kind != "throw_hold_abort", label + "无hold中断", missing)
					if event.kind == "hit": hits.append(str(event.move))
					if event.kind == "throw_slam": slams.append(str(event.move))
				if victim.state != "thrown": continue
				var animation := view._animation(victim, manifest)
				var pose := victim.frame()
				zoffy_check(animation.get("key", "") == victim.motion.pose and int(animation.get("index", -1)) == victim.motion.pose_sprite and int(pose.sprite) == victim.motion.pose_sprite, label + "受投姿势索引不被tick展开破坏", missing)
				var target: Dictionary = actor.frame().get("target", {})
				if move_id == "air_throw" and target.get("mode", "") == "release": release_heights.append(actor.height)
				if target.get("mode", "") != "hold": continue
				hold_ticks += 1
				var point: Array = pose.get("grab_points", {}).get(str(target.get("grab_point", "waist")), [])
				var offset := UfeThrowResolver.RootOffsets.offset(victim, target)
				var valid := UfeThrowResolver.HoldPoints.point_valid(point) and offset.size() == 2
				zoffy_check(valid, label + "运行期抓点合法", missing)
				if not valid: continue
				var grip: Array = target.grip
				var owner_point := Vector2i(actor.x + actor.facing * (int(grip[0]) + int(offset[0])), actor.height + int(grip[1]) + int(offset[1]))
				var victim_point := Vector2i(victim.x + victim.facing * int(point[0]), victim.height + int(point[1]))
				zoffy_check(owner_point == victim_point, label + "整数世界抓点零误差贴合", missing)
			zoffy_check(hold_ticks > 0 and hits == [move_id] and slams == [move_id] and victim.stats.hp == victim.definition.max_health - int(move.damage), label + "真实输入抓住并仅结算一次投技伤害", missing)
			if move_id == "air_throw":
				var descent_ok := release_heights.size() >= 5 and release_heights[0] > 0
				for height_index in range(1, release_heights.size()):
					descent_ok = descent_ok and release_heights[height_index] <= release_heights[height_index - 1]
				zoffy_check(descent_ok and release_heights.back() == 0, label + "空投攻击方随释放连续下降至地面", missing)

func position_zoffy_throw_audit(sim: UfeMatchDirector, driver: UfePhase3ThrowReview, location: String) -> void:
	driver.prepare_match(sim)
	var actor := sim.fighters[0]
	var victim := sim.fighters[1]
	var gap := absi(actor.x-victim.x)
	var left := 28 if location=="left_wall" else 1252-gap if location=="right_wall" else mini(actor.x,victim.x)
	actor.x = left if actor.facing>0 else left+gap
	victim.x = actor.x+actor.facing*gap

func check_zoffy_authored_holds(missing: Array) -> void:
	# 只验实际输入、持握协议和确定性；高度/Alpha净空另在主游戏审片，不把协议PASS冒充美术PASS。
	var cases := 0
	for opponent in ["ultraman", "zoffy", "ultraman-king"]:
		for part in range(UfePhase3ThrowReview.FIGHTER_ACTIONS.size()*2):
			for location in ["left_wall", "center", "right_wall"]:
				var driver := UfePhase3ThrowReview.new()
				driver.fighter_audit = true
				driver.review_frame = part*180
				var sim := UfeContentDatabase.match_for("zoffy", opponent)
				var replay := UfeContentDatabase.match_for("zoffy", opponent)
				position_zoffy_throw_audit(sim,driver,location)
				position_zoffy_throw_audit(replay,driver,location)
				var actor := sim.fighters[0]
				var victim := sim.fighters[1]
				var move_id := driver.action_at(driver.review_frame)
				var label := "佐菲持握/%s/%s/%d/%s/" % [opponent,move_id,actor.facing,location]
				var hits: Array[String] = []
				var slams: Array[String] = []
				var held := 0
				var held_sprites: Array[int] = []
				var release_heights: Array[int] = []
				var victim_release_heights: Array[int] = []
				for tick in range(180):
					var frame := part*180+tick
					var inputs := [driver.sample(frame,sim),driver.second_sample(frame)]
					sim.step(inputs)
					var replay_inputs: Array=inputs.map(func(input):return UfeInputFrame.unpack(input.pack()))
					replay.step(replay_inputs)
					zoffy_check(sim.state_hash()==replay.state_hash() and sim.events==replay.events,label+"逐tick输入重放一致",missing)
					for event in sim.events:
						zoffy_check(event.kind!="throw_hold_abort",label+"无持握中断",missing)
						if event.kind=="hit":hits.append(str(event.move))
						if event.kind=="throw_slam":slams.append(str(event.move))
					for fighter in sim.fighters:
						zoffy_check(fighter.x>=28 and fighter.x<=1252,label+"墙边双方不越界",missing)
					var target: Dictionary=actor.frame().get("target",{})
					if victim.state=="thrown" and move_id=="air_throw" and str(target.get("mode",""))=="release":
						if release_heights.is_empty() or release_heights.back()!=actor.height:release_heights.append(actor.height)
						if victim_release_heights.is_empty() or victim_release_heights.back()!=victim.height:victim_release_heights.append(victim.height)
					if victim.state!="thrown" or str(target.get("mode",""))!="hold":continue
					if opponent=="ultraman-king" and move_id in ["throw_forward","throw_back","air_throw","dash_throw"]:held_sprites.append(int(victim.motion.pose_sprite))
					held+=1
					var pose := victim.frame()
					var point: Array = UfeThrowResolver.HoldPoints.point(victim,target,pose) if target.has("hold_point_overrides") else pose.get("grab_points",{}).get(str(target.get("grab_point","waist")),[])
					var offset:=UfeThrowResolver.RootOffsets.offset(victim,target)
					var valid:=UfeThrowResolver.HoldPoints.point_valid(point) and offset.size()==2
					zoffy_check(valid,label+"实际受方抓点有效",missing)
					if not valid:continue
					var grip: Array=target.grip
					var owner_point:=Vector2i(actor.x+actor.facing*(int(grip[0])+int(offset[0])),actor.height+int(grip[1])+int(offset[1]))
					var victim_point:=Vector2i(victim.x+victim.facing*int(point[0]),victim.height+int(point[1]))
					zoffy_check(owner_point==victim_point,label+"真实双向抓点零误差",missing)
				zoffy_check(held>0 and hits==[move_id] and slams==[move_id],label+"实际捕获且只撞地一次",missing)
				zoffy_check(victim.stats.hp==victim.definition.max_health-int(actor.definition.moves[move_id].damage),label+"仅结算本人招式伤害",missing)
				if opponent=="ultraman-king" and move_id in ["throw_forward","throw_back","air_throw","dash_throw"]:
					zoffy_check(held_sprites.has(1) and held_sprites.has(2),label+"奥王受投有连续翻摔姿势",missing)
				if move_id=="air_throw":
					for heights in [release_heights,victim_release_heights]:
						var descent_ok: bool=heights.size()==5 and heights[0]>0 and heights.back()==0
						for height_index in range(1,heights.size()):
							descent_ok=descent_ok and heights[height_index]<heights[height_index-1]
						zoffy_check(descent_ok,label+"空投双方释放分五步严格下降至地面",missing)
				cases+=1
	zoffy_check(cases==90,"佐菲五投×三受方×双朝向×三站位全部执行",missing)

func zoffy_replay_hurtbox_bottom(fighter: UfeFighter) -> int:
	var hurtboxes: Array=fighter.frame().get("hurtboxes",[])
	if hurtboxes.is_empty():return fighter.height
	var bottom:=int(hurtboxes[0][1])
	for box in hurtboxes:bottom=mini(bottom,int(box[1]))
	return fighter.height+bottom

func zoffy_json_matches_recorded(actual: Variant, recorded: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(actual))==recorded

func check_zoffy_throw_trace_pair(row: Dictionary, sim: UfeMatchDirector, driver: UfePhase3ThrowReview, view: UfeSideView, manifests: Dictionary, missing: Array, index: int) -> void:
	var pair: Array=row.get("pair",[])
	zoffy_check(pair.size()==2,"主游戏双方姿势记录/%d"%index,missing)
	if pair.size()!=2:return
	for player in range(2):
		var fighter: UfeFighter=sim.fighters[player]
		var entry: Dictionary=pair[player]
		var label:="主游戏双方姿势/%d/%d/"%[index,player]
		zoffy_check(entry.get("fighter","")==fighter.definition.id and entry.get("x",-999999)==fighter.x and entry.get("height",-999999)==fighter.height and entry.get("facing",0)==fighter.facing,label+"身份、位置、朝向",missing)
		zoffy_check(entry.get("state","")==fighter.state and entry.get("state_tick",-1)==fighter.state_tick and entry.get("move","")==fighter.move_id and entry.get("move_tick",-1)==fighter.move_tick and entry.get("hp",-1)==fighter.stats.hp,label+"状态与招式相位",missing)
		var hurt_bottom:=zoffy_replay_hurtbox_bottom(fighter)
		zoffy_check(entry.get("hurtbox_bottom",-999999)==hurt_bottom and entry.get("body_bottom",-999999)==hurt_bottom,label+"受击框底缘",missing)
		var manifest: Dictionary=manifests[fighter.definition.id]
		var animation: Dictionary=view._animation(fighter,manifest)
		zoffy_check(entry.get("clip","")==animation.get("key","") and entry.get("sprite",-1)==animation.get("index",-2),label+"正式动画姿势索引",missing)
		zoffy_check(entry.get("texture","")==animation.get("texture","") and zoffy_json_matches_recorded(animation.get("rect",[]),entry.get("rect",[])) and zoffy_json_matches_recorded(animation.get("anchor",[]),entry.get("anchor",[])),label+"正式图集帧、格和根点",missing)
		var alpha:=driver.pixel_bottom(animation)
		zoffy_check(not alpha.is_empty(),label+"正式图集Alpha轮廓可读",missing)
		if alpha.is_empty():continue
		zoffy_check(entry.get("pixel_bottom",-999999)==fighter.height+int(alpha.offset) and zoffy_json_matches_recorded(alpha.bounds,entry.get("alpha_bounds",[])),label+"实际像素底缘",missing)
	var actor: UfeFighter=sim.fighters[0]
	var victim: UfeFighter=sim.fighters[1]
	var target: Dictionary=actor.frame().get("target",{})
	if victim.state=="thrown" and str(target.get("mode",""))=="hold":
		var victim_frame:=victim.frame()
		var point: Array=UfeThrowResolver.HoldPoints.point(victim,target,victim_frame) if target.has("hold_point_overrides") else victim_frame.get("grab_points",{}).get(str(target.get("grab_point","waist")),[])
		var offset:=UfeThrowResolver.RootOffsets.offset(actor,target)
		if UfeThrowResolver.HoldPoints.point_valid(point) and offset.size()==2:
			var grip: Array=target.grip
			var world_grip:=Vector2i(actor.x+actor.facing*(int(grip[0])+int(offset[0])),actor.height+int(grip[1])+int(offset[1]))
			var world_grab:=Vector2i(victim.x+victim.facing*int(point[0]),victim.height+int(point[1]))
			zoffy_check(world_grip==world_grab and pair[0].get("grip_world",[])==pair[1].get("grab_world",[]),"主游戏双方逐tick抓点零误差/%d"%index,missing)

func replay_skill_trace(path: String, missing: Array) -> void:
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not raw is Dictionary or raw.get("profile", "") != "fighter_skills":
		missing.append("技能实录trace格式不符")
		return
	var trace: Array = raw.get("trace", [])
	if trace.size() != 360:
		missing.append("单技能双向实录必须完整360tick")
		return
	var pair: Array = trace[0].get("pair", [])
	if pair.size() != 2:
		missing.append("技能实录缺少双方身份")
		return
	var skills: Dictionary = {}
	for row: Dictionary in trace:
		if not str(row.get("move", "")).is_empty():skills[str(row.move)] = true
	var skill := str(skills.keys()[0]) if skills.size() == 1 else "charge" if skills.is_empty() and trace.any(func(row): return row.get("state", "") == "charge") else ""
	if skills.is_empty() and trace.all(func(row): return row.get("state", "") == "idle"):
		skill = "idle"
	if skill.is_empty():
		missing.append("单技能实录没有唯一实际动作")
		return
	var view := UfeSideView.new()
	var manifests: Array = []
	for fighter: Dictionary in pair:
		manifests.append(UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json" % fighter.fighter))
	var sim: UfeMatchDirector
	for index in range(trace.size()):
		var row: Dictionary = trace[index]
		var section := floori(float(index) / 180.0)
		if index % 180 == 0:
			sim = UfeBattleFormCatalog.match_for(str(pair[0].fighter), str(pair[1].fighter), true)
			var facing := 1 if section == 0 else -1
			var gap := 72 if skill == "motion_41236" else 80 if skill == "motion_236" else 280
			sim.fighters[0].x = 640 - facing * (gap >> 1)
			sim.fighters[1].x = sim.fighters[0].x + facing * gap
			sim.fighters[0].facing = facing
			sim.fighters[1].facing = -facing
			sim.fighters[0].stats.energy = 1000 if skill == "special" else 2000 if skill == "special2" else 3000
		var inputs: Array = row.get("inputs", [])
		if inputs.size() != 2 or int(row.get("movie_frame", -1)) != index or int(row.get("section", -1)) != section:
			missing.append("技能实录输入或分段缺失/%d" % index)
			break
		sim.step(inputs.map(func(value): return UfeInputFrame.unpack(value)))
		if sim.state_hash() != str(row.get("state_hash", "")) or JSON.parse_string(JSON.stringify(sim.events)) != row.get("events", []):
			missing.append("技能原InputFrame状态或事件回放不符/%d" % index)
			break
		var observed: Array = row.get("pair", [])
		if observed.size() != 2:
			missing.append("技能实录双人姿势缺失/%d" % index)
			break
		for player in range(2):
			var shown := view._animation(sim.fighters[player], manifests[player])
			if shown.get("key", "") != observed[player].get("clip", "") or int(shown.get("index", -1)) != int(observed[player].get("sprite", -1)):
				missing.append("技能实录姿势回放不符/%d/%d" % [index, player])
	view.free()

func replay_zoffy_throw_trace(path: String, missing: Array) -> void:
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	zoffy_check(raw is Dictionary and raw.get("profile","")=="phase3_throws","主游戏佐菲投技trace结构",missing)
	if not raw is Dictionary:return
	var trace: Array=raw.get("trace",[])
	zoffy_check(trace.size()==1800,"主游戏佐菲投技trace逐tick完整",missing)
	if trace.is_empty():return
	var first_pair: Array=trace[0].get("pair",[])
	if first_pair.size()!=2:return
	var opponent:=str(first_pair[1].get("fighter",""))
	var view:=UfeSideView.new()
	var manifests: Dictionary={}
	for fighter_id in ["zoffy",opponent]:manifests[fighter_id]=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%fighter_id)
	var current_section:=-1
	var sim: UfeMatchDirector
	var driver: UfePhase3ThrowReview
	var replayed:=0
	for index in range(mini(trace.size(),1800)):
		var row: Dictionary=trace[index]
		var next_section:=int(row.get("section",-1))
		if next_section!=current_section:
			current_section=next_section
			driver=UfePhase3ThrowReview.new()
			driver.fighter_audit=true
			driver.review_frame=current_section*180
			sim=UfeBattleFormCatalog.match_for("zoffy",opponent,true)
			driver.prepare_match(sim)
		var inputs: Array=row.get("inputs",[]).map(func(value):return UfeInputFrame.unpack(value))
		if inputs.size()!=2:continue
		sim.step(inputs)
		zoffy_check(str(sim.state_hash())==str(row.get("state_hash","")),"主游戏原InputFrame状态回放/%d"%index,missing)
		zoffy_check(JSON.parse_string(JSON.stringify(sim.events))==row.get("events",[]),"主游戏逐tick事件回放/%d"%index,missing)
		check_zoffy_throw_trace_pair(row,sim,driver,view,manifests,missing,index)
		replayed+=1
	zoffy_check(replayed==1800,"主游戏五投实际输入回放完整",missing)
	view.capture_view=null
	view.free()

func zoffy_clip_sprite(clip: Dictionary, tick: int) -> int:
	var durations: Array = clip.get("ticks", [])
	var total := 0
	for duration in durations: total += int(duration)
	if total <= 0: return -1
	var age := tick % total if bool(clip.get("loop", false)) else mini(tick, total - 1)
	for index in range(durations.size()):
		if age < int(durations[index]): return index
		age -= int(durations[index])
	return -1

func zoffy_shot_touches_pose(animation: Dictionary, shot: Dictionary, tick: int) -> bool:
	# 检查正式图集的发射点附近确有手部像素，不锁图号、总图数或本地 art 源稿。
	var rect: Array = animation.get("rect", [])
	var anchor: Array = animation.get("anchor", [])
	var origins: Dictionary = shot.get("origin_by_frame", {})
	var origin: Array = origins.get(str(tick), shot.get("anchor", shot.get("spawn", [])))
	if rect.size() != 4 or anchor.size() != 2 or origin.size() != 2: return false
	var texture := load(str(animation.get("texture", ""))) as Texture2D
	var image: Image = texture.get_image() if texture != null else null
	if image == null: return false
	var point := Vector2i(int(anchor[0]) + int(origin[0]), int(anchor[1]) - int(origin[1]))
	for dy in range(-2, 3):
		for dx in range(-2, 3):
			if dx * dx + dy * dy > 4: continue
			var local := point + Vector2i(dx, dy)
			var pixel := local + Vector2i(int(rect[0]), int(rect[1]))
			if local.x < 0 or local.y < 0 or local.x >= int(rect[2]) or local.y >= int(rect[3]): continue
			if pixel.x >= 0 and pixel.y >= 0 and pixel.x < image.get_width() and pixel.y < image.get_height() and image.get_pixelv(pixel).a >= 200.0 / 255.0: return true
	return false

func check_zoffy_skills(view: UfeSideView, manifest: Dictionary, missing: Array) -> void:
	var required: Array[String] = ["pulse", "ranged_forward", "low_pulse", "air_pulse", "motion_236", "motion_623", "motion_214", "motion_22", "motion_41236", "special", "special2", "special3", "air_special", "charge"]
	var driver := UfeReviewDriver.new()
	driver.profile = "fighter_skills"
	var coverage: Dictionary = {}
	var group_ticks := floori(float(driver.length_frames()) / float(maxi(1, driver.skill_count() * 2)))
	zoffy_check(group_ticks > 0, "fighter_skills分组时长有效", missing)
	for part in range(driver.skill_count() * 2):
		var first_frame := part * group_ticks
		driver.review_frame = first_frame
		var id := driver.skill_id(first_frame)
		var facing := 1 if part < driver.skill_count() else -1
		var label := "技能profile/%s/%d/" % [id, facing]
		var sim := UfeContentDatabase.match_for("zoffy", "ultraman")
		driver.prepare_match(sim)
		var actor := sim.fighters[0]
		var starts: Array[String] = []
		var charge_states: Array[String] = []
		var shot_ticks: Array[int] = []
		var emitted := 0
		for age in range(group_ticks):
			var movie_frame := first_frame + age
			driver.review_frame = movie_frame
			var advance := sim.hitstop == 0
			# 发射在 _advance 的 move_tick 自增前发生，不能拿步进后的下一格误判。
			if advance and actor.move_id == id and id in ["special", "special3"]:
				var row := actor.frame()
				for shot in row.get("shots", []):
					shot_ticks.append(actor.move_tick)
					var animation := view._animation(actor, manifest)
					var clip: Dictionary = manifest.clips[id]
					zoffy_check(animation.get("key", "") == id and int(animation.get("index", -1)) == zoffy_clip_sprite(clip, actor.move_tick) and int(row.sprite) == int(animation.get("index", -1)), label + "发射tick人物与clip时间表一致", missing)
					zoffy_check(zoffy_shot_touches_pose(animation, shot, actor.move_tick), label + "发射tick已伸手至发射点2px内", missing)
			var previous_move := actor.move_id
			sim.step([driver.sample(movie_frame, sim), driver.second_sample(movie_frame)])
			if not actor.move_id.is_empty() and actor.move_id != previous_move: starts.append(actor.move_id)
			if actor.move_id == id:
				zoffy_check(actor.facing == facing, label + "实际出招朝向正确", missing)
			if advance:
				for projectile in sim.projectiles:
					if int(projectile.owner) != 0 or str(projectile.move) != id: continue
					if int(projectile.age) == 1: emitted += 1
					if id in ["special", "special3"] and bool(projectile.get("beam", false)) and int(projectile.life) > 0:
						var animation := view._animation(actor, manifest)
						zoffy_check(zoffy_shot_touches_pose(animation, projectile, actor.move_tick), label + "持续束结束前保持掌缘2px贴合/tick%d" % actor.move_tick, missing)
			if id == "charge" and actor.state in ["charge_start", "charge", "charge_stop"]:
				if charge_states.is_empty() or charge_states.back() != actor.state: charge_states.append(actor.state)
				var animation := view._animation(actor, manifest)
				var clip: Dictionary = manifest.clips[actor.state]
				zoffy_check(actor.move_id.is_empty() and actor.facing == facing and animation.get("key", "") == actor.state and int(animation.get("index", -1)) == zoffy_clip_sprite(clip, actor.state_tick) and int(actor.frame().sprite) == int(animation.get("index", -1)), label + "Q按真实charge状态与计时表显示", missing)
		if id == "charge":
			coverage["%s/%d" % [id, facing]] = charge_states == ["charge_start", "charge", "charge_stop"] and actor.state == "idle" and starts.is_empty()
		else:
			coverage["%s/%d" % [id, facing]] = starts.count(id) == 1
		zoffy_check(bool(coverage["%s/%d" % [id, facing]]), label + "本组真实输入独立触发而非顶层moves_seen", missing)
		if id in ["special", "special3"]:
			var expected_tick := 24 if id == "special" else 46
			zoffy_check(shot_ticks == [expected_tick] and emitted == 1, label + "指定shot tick实际仅发射一次", missing)
	for facing in [1, -1]:
		for id in required:
			zoffy_check(bool(coverage.get("%s/%d" % [id, facing], false)), "技能profile/%s/%d逐组覆盖" % [id, facing], missing)
	check_zoffy_air_special_landings(missing)
	check_zoffy_remote_skill_hits(missing)

func king_check(ok: bool, label: String, missing: Array) -> void:
	var detail := "奥王投射连续性/" + label
	if not ok and not missing.has(detail): missing.append(detail)

func check_king_projectile_continuity(missing: Array) -> void:
	var definition: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-king/definition.json")
	var move: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-king/moves/ranged_forward.json")
	var manifest: Dictionary = UfeContentDatabase.read_json("res://assets/fighters/ultraman-king/animations/manifest.json")
	var effects: Dictionary = UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	var clip: Dictionary = manifest.clips.get("ranged_forward", {})
	var frames: Array = move.get("frames", [])
	var shot_frame := -1
	var shot: Dictionary = {}
	for index in range(frames.size()):
		var shots: Array = frames[index].get("shots", [])
		if not shots.is_empty():
			shot_frame = index
			shot = shots[0]
			break
	var source_texture := load(str(clip.get("texture", ""))) as Texture2D
	var source_atlas: Image = source_texture.get_image() if source_texture != null else null
	var effect: Dictionary = effects.get(str(shot.get("effect", "")), {})
	var effect_texture := load(str(effect.get("texture", ""))) as Texture2D
	var effect_atlas: Image = effect_texture.get_image() if effect_texture != null else null
	king_check(shot_frame >= 0 and clip.size() > 0 and source_atlas != null and effect_atlas != null, "招式、人物帧与特效均已登记", missing)
	if shot_frame < 0 or clip.is_empty() or source_atlas == null or effect_atlas == null: return
	var sprite_index := zoffy_clip_sprite(clip, shot_frame + 1)
	var rect: Array = clip.rects[sprite_index]
	var pose: Image = source_atlas.get_region(Rect2i(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])))
	var hand_x := -1
	var hand_top := -1
	var hand_bottom := -1
	for y in range(140, 154):
		if pose.get_pixel(177, y).a >= 200.0 / 255.0:
			hand_x = 177
			if hand_top < 0: hand_top = y
			hand_bottom = y
	var hand_y := floori(float(hand_top + hand_bottom) / 2.0) if hand_top >= 0 else -1
	var actor_anchor: Array = clip.get("anchors", [clip.get("anchor", [128, 248])])[sprite_index]
	var spawn: Array = shot.get("spawn", [])
	var declared_anchor: Array = shot.get("anchor", [])
	var speed := int(shot.get("speed", 0))
	var emitter_x := int(actor_anchor[0]) + int(spawn[0]) + speed if spawn.size() == 2 else -10000
	var emitter_y := int(actor_anchor[1]) - int(spawn[1]) if spawn.size() == 2 else -10000
	king_check(hand_x >= 0 and abs(emitter_x - hand_x) <= 1 and abs(emitter_y - hand_y) <= 1, "同tick弹体起点贴合伸出的指尖", missing)
	king_check(declared_anchor.size() == 2 and abs(int(declared_anchor[0]) - (hand_x - int(actor_anchor[0]))) <= 1 and abs(int(declared_anchor[1]) - (int(actor_anchor[1]) - hand_y)) <= 1, "招式发射锚点登记为指尖世界偏移", missing)
	var effect_bounds: Array = []
	for effect_rect in effect.get("rects", []):
		var cell: Image = effect_atlas.get_region(Rect2i(int(effect_rect[0]), int(effect_rect[1]), int(effect_rect[2]), int(effect_rect[3])))
		effect_bounds.append(cell.get_used_rect())
	king_check(effect_bounds.size() == effect.get("rects", []).size() and not effect_bounds.is_empty(), "发射特效各相有可见像素", missing)
	if effect_bounds.size() == effect.get("rects", []).size() and effect_bounds.size() > 0:
		var effect_anchor: Array = effect.get("anchor", [float(effect.rects[0][2]) / 2.0, float(effect.rects[0][3]) / 2.0])
		var continuous := true
		for facing in [1, -1]:
			for index in range(effect_bounds.size()):
				var previous: Rect2i = effect_bounds[index]
				var following: Rect2i = effect_bounds[(index + 1) % effect_bounds.size()]
				var previous_front := previous.end.x - 1 - int(effect_anchor[0]) if facing > 0 else int(effect_anchor[0]) - previous.position.x
				var next_back := following.position.x - int(effect_anchor[0]) if facing > 0 else int(effect_anchor[0]) - (following.end.x - 1)
				if previous_front < speed + next_back: continuous = false
		king_check(continuous, "左右朝向逐tick弹体位移与相邻特效轮廓无视觉断档", missing)
	var view := UfeSideView.new()
	for facing in [1, -1]:
		var sim := UfeContentDatabase.match_for("ultraman-king", "ultraman")
		var actor := sim.fighters[0]
		var victim := sim.fighters[1]
		actor.x = 640 - facing * 140
		actor.facing = facing
		victim.x = actor.x + facing * 280
		victim.facing = -facing
		var launched := false
		var hit_count := 0
		var last_x := 0
		var last_age := -1
		for tick in range(90):
			var input := UfeInputFrame.make(facing, 0, UfeInputFrame.RANGED) if tick == 0 else UfeInputFrame.make()
			sim.step([input, UfeInputFrame.make()])
			for projectile in sim.projectiles:
				if int(projectile.owner) != 0 or str(projectile.move) != "ranged_forward": continue
				if int(projectile.age) == 1:
					launched = true
					var animation := view._animation(actor, manifest)
					var local_x: int = facing * (int(projectile.x) - actor.x)
					king_check(int(projectile.facing) == facing and abs(local_x - (hand_x - int(actor_anchor[0]))) <= 1 and abs(int(projectile.height) - actor.height - (int(actor_anchor[1]) - hand_y)) <= 1, "左右朝向实际首个可见弹体均从指尖发出", missing)
					king_check(animation.get("key", "") == "ranged_forward" and int(animation.get("index", -1)) == sprite_index, "发射时人物显示帧与发射帧同步", missing)
				if last_age >= 0 and int(projectile.age) == last_age + 1:
					king_check(facing * (int(projectile.x) - last_x) == speed, "弹体逐tick沿出手方向连续移动", missing)
				last_x = int(projectile.x)
				last_age = int(projectile.age)
			for event in sim.events:
				if str(event.get("kind", "")) != "hit" or int(event.get("player", -1)) != 0 or str(event.get("move", "")) != "ranged_forward": continue
				hit_count += 1
				var predicted_x: int = last_x + facing * speed
				king_check(abs(int(event.x) - predicted_x) <= (int(shot.box[2]) >> 1) + 1 and abs(int(event.height) - (actor.height + int(spawn[1]))) <= (int(shot.box[3]) >> 1) + 1, "命中特效锚点与弹体接触框相接", missing)
				king_check(facing * (int(event.x) - actor.x) > 0 and actor.facing == facing, "命中方向与发射方向一致", missing)
			if hit_count > 0: break
		king_check(launched and hit_count == 1 and victim.stats.hp < victim.definition.max_health, "左右朝向从指尖发射并连续抵达有效接触点", missing)
	view.free()

func check_zoffy_air_special_landings(missing: Array) -> void:
	for facing in [1, -1]:
		for after_shot in [false, true]:
			var sim := UfeContentDatabase.match_for("zoffy", "ultraman")
			var actor := sim.fighters[0]
			actor.x = 640 - facing * 350; actor.facing = facing; actor.stats.energy = 1000
			sim.fighters[1].x = 640 + facing * 350; sim.fighters[1].facing = -facing
			var label := "空中必杀/%d/%s/" % [facing, "发射后落地" if after_shot else "发射前落地"]
			var sent := false
			var start_tick := -1
			var landing_tick := -1
			var emitted := 0
			for tick in range(90):
				var input := UfeInputFrame.make(0, 0, UfeInputFrame.JUMP if tick == 0 else 0)
				var ready: bool = actor.vy <= 0 if after_shot else actor.vy < 0 and actor.height <= actor.definition.jump_speed * 2
				if not sent and actor.state == "air" and ready:
					input = UfeInputFrame.make(0, 0, UfeInputFrame.SPECIAL)
					sent = true
				var previous_height := actor.height
				var advance := sim.hitstop == 0
				sim.step([input, UfeInputFrame.make()])
				if actor.move_id == "air_special" and start_tick < 0: start_tick = tick
				if start_tick >= 0 and landing_tick < 0 and previous_height > 0 and actor.height == 0:
					landing_tick = tick
					zoffy_check(actor.state == "land" and actor.move_id.is_empty(), label + "触地当tick清空空中招并进入land", missing)
				if advance:
					for projectile in sim.projectiles:
						if int(projectile.owner) != 0 or str(projectile.move) != "air_special" or int(projectile.age) != 1: continue
						emitted += 1
						zoffy_check(landing_tick < 0, label + "触地后不补凭空shot", missing)
			zoffy_check(sent and start_tick >= 0 and landing_tick > start_tick and landing_tick - start_tick < actor.definition.moves.air_special.frames.size(), label + "真实跳跃输入覆盖动作未结束时触地", missing)
			zoffy_check(emitted == (1 if after_shot else 0), label + "落地前后实际发射次数正确", missing)

func check_zoffy_remote_skill_hits(missing: Array) -> void:
	# 水平射线保留280px远端命中；前下束改为下降时瞄准地面目标，不强求同跳同高度必中。
	for config in [{"id":"ranged_forward", "gap":280, "hit":true}, {"id":"air_special", "gap":190, "hit":true}, {"id":"air_special", "gap":700, "hit":false}]:
		var id := str(config.id)
		var gap := int(config.gap)
		var expected_hit := bool(config.hit)
		var results: Dictionary = {}
		for facing in [1, -1]:
			var sim := UfeContentDatabase.match_for("zoffy", "ultraman")
			var actor := sim.fighters[0]
			var victim := sim.fighters[1]
			actor.x = 640 - facing * (gap >> 1); actor.facing = facing; actor.stats.energy = 1000
			victim.x = actor.x + facing * gap; victim.facing = -facing
			var sent := false
			var started := false
			var hits := 0
			var shot_height := -1
			var boxes: Array = []
			var label := "远端判定/%s/%dpx/%d/" % [id, gap, facing]
			for tick in range(100):
				var input := UfeInputFrame.make()
				if id == "air_special":
					if tick == 0:
						input = UfeInputFrame.make(0, 0, UfeInputFrame.JUMP)
					elif not sent and actor.state == "air" and actor.vy <= -3:
						input = UfeInputFrame.make(0, 0, UfeInputFrame.SPECIAL); sent = true
				elif tick == 0:
					input = UfeInputFrame.make(facing, 0, UfeInputFrame.RANGED); sent = true
				sim.step([input, UfeInputFrame.make()])
				started = started or actor.move_id == id
				for event in sim.events:
					if event.kind == "hit" and int(event.player) == 0 and str(event.move) == id and bool(event.get("projectile", false)): hits += 1
				if boxes.is_empty():
					for projectile in sim.projectiles:
						if int(projectile.owner) != 0 or str(projectile.move) != id: continue
						shot_height = actor.height
						zoffy_check(int(projectile.facing) == facing, label + "弹体实际朝向", missing)
						for world_box in UfeProjectileResolver.world_hitboxes(projectile):
							var world: Rect2i = world_box
							var local_x := world.position.x - actor.x if facing > 0 else actor.x - world.end.x
							boxes.append([local_x, world.position.y - actor.height, world.size.x, world.size.y])
			var damage := victim.definition.max_health - victim.stats.hp
			zoffy_check(sent and started and not boxes.is_empty(), label + "真实输入启动并产生正式世界判定", missing)
			zoffy_check(hits == (1 if expected_hit else 0) and (damage > 0 if expected_hit else damage == 0), label + ("合理落点仅结算一次" if expected_hit else "超出束长确实落空"), missing)
			if id == "air_special": zoffy_check(shot_height >= 35 and shot_height <= 60, label + "真实下降轨迹在离地35..60px发射", missing)
			results[facing] = {"boxes": boxes, "hits": hits, "damage": damage, "shot_height": shot_height}
		zoffy_check(results[1] == results[-1], "远端判定/%s/%dpx/世界框镜像与实际伤害双向一致" % [id, gap], missing)
