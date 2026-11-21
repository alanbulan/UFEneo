extends UfeAppHarness
## 审片、页面截图与 UI 调试 CLI 挂载器（仅通过 --harness=res://tests/review/cli_harness.gd 加载）。

var gate_b_driver: UfeGateBReview = null
var ui_fixes_debug: UfeUIFixesDebug = null
var capture_ui: String = ""
var long_text: bool = false
var review_stills: String = ""
var last_still_key: String = ""
var force_review_draw: bool = false
var review_draw_count: int = 0
var review_pending_tick: int = -1
var review_render_trace: Array = []


func parse_args(app: Control, args: PackedStringArray) -> void:
	long_text = "--review-long-text" in args
	force_review_draw = "--review-force-draw" in args
	for arg in args:
		if arg == "--review-ultraseven-air-special":
			app.review = true
			app.review_driver = UfeUltrasevenAirSpecialReview.new()
			app.selected_fighters = ["ultraseven", "zetton"]
		elif arg == "--review-zetton-counter":
			app.review = true
			app.review_driver = UfeZettonCounterReview.new()
		elif arg == "--review-ultraseven":
			app.review = true
			app.review_driver = UfeUltrasevenReview.new()
			app.selected_fighters = ["ultraseven", "zetton"]
		elif arg == "--review-ultraseven-air":
			app.review = true
			app.review_driver = UfeUltrasevenAirReview.new()
			app.selected_fighters = ["ultraseven", "zetton"]
		elif arg == "--review-ultraseven-defense":
			app.review = true
			app.review_driver = UfeUltrasevenDefenseReview.new()
			app.selected_fighters = ["ultraseven", "zetton"]
		elif arg == "--review-ultraseven-fourth":
			app.review = true
			app.review_driver = UfeUltrasevenFourthReview.new()
			app.selected_fighters = ["ultraseven", "zetton"]
		elif arg == "--review-ultraseven-body":
			app.review = true
			app.review_driver = UfeUltrasevenBodyReview.new()
			app.selected_fighters = ["ultraseven", "zetton"]
		elif arg.begins_with("--review-ultraseven-only=") and app.review_driver is UfeUltrasevenReview:
			app.review_driver.selected_action = arg.trim_prefix("--review-ultraseven-only=")
		elif arg == "--review-gate-b":
			gate_b_driver = UfeGateBReview.new()
		elif arg == "--review":
			app.review = true
			_ensure_driver(app)
		elif arg == "--review-forward-walk":
			app.review = true
			_ensure_driver(app).profile = "forward_walk"
		elif arg == "--review-back-walk":
			app.review = true
			_ensure_driver(app).profile = "back_walk"
		elif arg == "--review-dash":
			app.review = true
			_ensure_driver(app).profile = "dash_once"
		elif arg == "--review-switches":
			app.review = true
			_ensure_driver(app).profile = "locomotion_switches"
		elif arg == "--review-color-switches":
			app.review = true
			_ensure_driver(app).profile = "color_switches"
		elif arg == "--review-phase3":
			app.review = true
			_ensure_driver(app).profile = "phase3_standing"
		elif arg == "--review-air":
			app.review = true
			app.review_driver = UfePhase3AirReview.new()
		elif arg == "--review-reactions":
			app.review = true
			app.review_driver = UfePhase3ReactionReview.new()
		elif arg == "--review-zetton":
			app.review = true
			app.review_driver = UfePhase3ZettonReview.new()
		elif arg == "--review-zetton-defense":
			app.review = true
			app.review_driver = UfePhase3ZettonDefenseReview.new()
		elif arg == "--review-zetton-air":
			app.review = true
			app.review_driver = UfePhase3ZettonAirReview.new()
		elif arg in ["--review-throws","--review-fighter-throws"]:
			app.review = true
			var driver := UfePhase3ThrowReview.new()
			driver.fighter_audit = arg=="--review-fighter-throws"
			app.review_driver = driver
		elif arg == "--review-gate-b-patch":
			app.review = true
			app.review_driver = UfeGateBPatchReview.new()
		elif arg == "--review-specials":
			app.review = true
			app.review_driver = UfePhase3SpecialReview.new()
		elif arg in ["--review-supers", "--review-feedback"]:
			app.review = true
			var super_driver := UfePhase3SuperReview.new()
			super_driver.feedback_only = arg == "--review-feedback"
			app.review_driver = super_driver
		elif arg == "--review-audio":
			app.review = true
			app.review_driver = UfePhase3AudioReview.new()
		elif arg == "--review-hud":
			app.review = true
			app.review_driver = UfePixelHudReview.new()
		elif arg == "--review-pages":
			app.review = true
			app.review_driver = UfePixelPagesReview.new()
		elif arg == "--review-flash":
			app.review = true
			app.review_driver = UfePixelFlashReview.new()
		elif arg == "--review-hud-air":
			app.review = true
			app.review_driver = UfePixelHudAirReview.new()
		elif arg == "--review-ui-controls":
			app.review = true
			app.review_driver = UfePixelUIControls.new()
		elif arg.begins_with("--capture-ui="):
			capture_ui = arg.trim_prefix("--capture-ui=")
		elif arg.begins_with("--capture-pair="):
			var pair: Array = Array(arg.trim_prefix("--capture-pair=").split(","))
			if pair.size() != 2 or not pair.all(_capture_fighter_available):
				push_error("审片角色必须是两个存在且已开放的角色id，禁止路径或默认回退：" + arg)
				app.set_physics_process(false)
				app.get_tree().quit(1)
				return
			app.selected_fighters = [pair[0], pair[1]]
		elif arg == "--review-skills" or arg.begins_with("--review-skill="):
			app.review = true
			var driver := _ensure_driver(app)
			driver.profile = "fighter_skills"
			if arg.begins_with("--review-skill="):
				var requested := arg.trim_prefix("--review-skill=")
				assert(requested == "idle" or requested in UfeReviewDriver.SKILL_ACTIONS,"未登记的动作审片输入: "+requested)
				driver.selected_skill = requested
		elif arg.begins_with("--review-stills="):
			review_stills = arg.trim_prefix("--review-stills=")
			assert(not review_stills.is_empty(),"技能截图输出目录不能为空")
			assert(DirAccess.make_dir_recursive_absolute(review_stills)==OK,"无法创建技能截图目录")
		elif arg == "--review-final":
			app.review = true
			_ensure_driver(app).profile = "gate_a_final"
		elif arg.begins_with("--review-forward-candidate="):
			app.review = true
			app.walk_review_clip = arg.trim_prefix("--review-forward-candidate=")
			var candidate: Dictionary = UfeContentDatabase.read_json(app.walk_review_clip)
			_ensure_driver(app).profile = "back_walk" if candidate.get("action", "") == "walk_back" else "forward_walk"
			app.selected_fighters[0] = candidate.get("fighter", "ultraman")
		elif arg.begins_with("--review-trace="):
			app.review_trace = arg.trim_prefix("--review-trace=")
		elif arg.begins_with("--review-capture-frames="):
			app.review_capture_frames = int(arg.trim_prefix("--review-capture-frames="))
	if force_review_draw:
		assert(app.review_capture_frames > 0 and not str(app.review_trace).is_empty(), "强制录制必须指定帧数与trace路径")
		app.auto_quit = 0


func _capture_fighter_available(id: String) -> bool:
	var pattern := RegEx.create_from_string("^[a-z0-9][a-z0-9_-]*$")
	var matched := pattern.search(id)
	if matched == null or matched.get_string() != id:
		return false
	var path := "res://content/fighters/%s/definition.json" % id
	if not FileAccess.file_exists(path):
		return false
	var definition: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not definition is Dictionary or definition.get("id", "") != id:
		return false
	var playable: Variant = definition.get("playable", true)
	var pilot: Variant = definition.get("pilot_playable", false)
	return (playable is bool and playable) or (pilot is bool and pilot)


func _ensure_driver(app: Control) -> UfeReviewDriver:
	if app.review_driver == null:
		app.review_driver = UfeReviewDriver.new()
	return app.review_driver as UfeReviewDriver


func override_matchup(app: Control) -> Array:
	if app.review_driver is UfePhase3SpecialReview or app.review_driver is UfeUltrasevenFourthReview:
		return app.review_driver.call("matchup") as Array
	return []


func wants_intro(app: Control) -> bool:
	if app.review_driver is UfePhase3SpecialReview or app.review_driver is UfeUltrasevenFourthReview:
		return bool(app.review_driver.call("wants_intro"))
	return false


func after_start_match(app: Control) -> void:
	if app.hud != null:
		app.hud.review_long_text = long_text


func after_ready(app: Control) -> void:
	if force_review_draw:
		RenderingServer.frame_post_draw.connect(_on_review_draw)
	if app.review_driver is UfePixelPagesReview:
		app._show_page("title")
	if capture_ui in ["title", "select", "vs", "archive", "settings", "commands", "training"]:
		app.front.selections = app.selected_fighters.duplicate()
		for player: int in range(2):
			var options: Array = UfeFighterDisplay.select_forms(str(app.front.selections[player]))
			var chosen: String = str((options[0] as Dictionary).get("id", "default")) if not options.is_empty() and options[0] is Dictionary else "default"
			for raw_form: Variant in options:
				if raw_form is Dictionary:
					var form_dict: Dictionary = raw_form
					if bool(form_dict.get("implemented", false)):
						chosen = str(form_dict.get("id", chosen))
						break
			app.front.selected_forms[player] = chosen
		if capture_ui == "training":
			app.training = true
			app.front.hide()
			app.view.show()
			app.hud.show()
			app.paused = false
		else:
			app.front.long_names = long_text
			app._show_page(capture_ui)
	if capture_ui in ["select-bottom", "select-long", "archive-zetton"]:
		app.front.long_names = capture_ui == "select-long"
		app.front.archive_index = 1 if capture_ui == "archive-zetton" else 0
		app._show_page("archive" if capture_ui == "archive-zetton" else "select")
	if capture_ui == "menu":
		app.front.hide()
		app.view.show()
		app.hud.show()
		app.paused = false
		app._action("pause")
	if capture_ui.begins_with("commands-"):
		app._show_page("commands")
		if "zetton" in capture_ui:
			(app.content_commands() as UfeCommandPages).set_fighter(UfeContentDatabase.fighter("zetton"))
		for i in range(8):
			if capture_ui.ends_with("-" + ["standing", "crouching", "jumping", "airchain", "state", "throws", "specials", "supers"][i]):
				app.content_commands().show_page(i)
	if capture_ui in ["training-last", "battle"]:
		app.training = capture_ui == "training-last"
		app.front.hide()
		app.view.show()
		app.hud.show()
		app.paused = false
		app.intro = 0
	if OS.has_feature("debug") and app.training:
		var ui_mode := ""
		var ui_output := ""
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--ui-fixes-debug="):
				ui_mode = arg.trim_prefix("--ui-fixes-debug=")
			if arg.begins_with("--ui-out="):
				ui_output = arg.trim_prefix("--ui-out=")
		if ui_mode in ["hud", "switch", "showcase"] and not ui_output.is_empty():
			ui_fixes_debug = UfeUIFixesDebug.new()
			ui_fixes_debug.prepare(app, ui_mode, ui_output)


func on_begin_match_from_front(app: Control) -> void:
	if app.review_driver is UfePixelPagesReview:
		app.intro = 75


func before_physics(app: Control, tick: int) -> void:
	if force_review_draw:
		assert(review_pending_tick == -1 and tick == review_render_trace.size(), "一个呈现帧内推进多个模拟tick，不能覆盖待绘制姿势")
		review_pending_tick = tick
		app.get_tree().create_timer(0.0, true, false, true).timeout.connect(_queue_review_draw.bind(app, tick), CONNECT_ONE_SHOT)
	if ui_fixes_debug != null:
		ui_fixes_debug.drive(tick)
	if gate_b_driver != null:
		gate_b_driver.drive(tick, app)
	if app.review_driver is UfePixelPagesReview:
		app.review_driver.call("drive_controls", tick, app)
	if app.review_driver is UfePixelFlashReview:
		app.review_driver.call("drive_controls", tick, app)


func on_front_visible(app: Control, tick: int) -> void:
	if gate_b_driver != null:
		gate_b_driver.observe(tick, app.simulation)
	if capture_ui == "select-bottom" and tick == 20:
		app.front.grid.scroll_vertical = 100000
	if capture_ui.begins_with("commands-") and "bottom" in capture_ui and tick == 20:
		app.content_commands().rows.scroll_vertical = 100000
	if ui_fixes_debug != null:
		ui_fixes_debug.observe(tick)


func before_simulation_step(app: Control, tick: int) -> void:
	if capture_ui == "training-last":
		if tick == 2:
			Input.action_press("p1_right")
			Input.action_press("p1_ranged")
		if tick == 3:
			Input.action_release("p1_right")
			Input.action_release("p1_ranged")
	if app.review and app.review_driver != null:
		if app.review_driver is UfePixelUIControls:
			app.review_driver.call("drive_controls", tick, app)
		if app.review_driver is UfePixelHudReview and not app.review_driver is UfePixelPagesReview:
			if tick in [180, 270]:
				app._action("pause")


func should_restart_match_on_section(app: Control) -> bool:
	return app.review_driver is UfePhase3SpecialReview or app.review_driver is UfeUltrasevenFourthReview


func override_inputs(app: Control, tick: int, first: UfeInputFrame, second: UfeInputFrame) -> Array:
	if not app.review:
		if ui_fixes_debug != null:
			first = ui_fixes_debug.sample(0, tick)
			second = ui_fixes_debug.sample(1, tick)
		if gate_b_driver != null:
			first = gate_b_driver.sample(tick, app.simulation)
	elif app.review_driver is UfePixelPagesReview and int(app.dummy) == 4 and not bool(app.dummy_recording):
		second = app._dummy_input()
	return [first, second]


func after_step(app: Control, tick: int) -> void:
	if not review_stills.is_empty() and app.review and app.review_driver is UfeReviewDriver:
		var driver := app.review_driver as UfeReviewDriver
		if driver is UfePixelUIControls:
			driver.capture_still(app,tick,review_stills)
		var throw_audit := driver is UfePhase3ThrowReview and (driver as UfePhase3ThrowReview).fighter_audit
		if (driver.profile=="fighter_skills" or throw_audit) and tick%180>=18 and tick%180<=150:
			var fighter: UfeFighter = app.simulation.fighters[0]
			var victim: UfeFighter = app.simulation.fighters[1]
			var key := "%d:%s:%d:%s:%d:%d" % [driver.section(tick),fighter.move_id,int(fighter.frame().get("sprite",0)),victim.state,victim.motion.pose_sprite,floori((tick%180)/6.0)]
			if key!=last_still_key:
				last_still_key = key
				_capture_skill_still.call_deferred(app,"%s/%02d-%04d.png" % [review_stills,driver.section(tick),tick])
	if app.review and app.review_driver is UfePhase3AudioReview:
		var audio_driver := app.review_driver as UfePhase3AudioReview
		if not audio_driver.trace.is_empty():
			audio_driver.trace[-1]["audio_played"] = app.audio.played.slice(audio_driver.audio_cursor).duplicate(true)
			audio_driver.audio_cursor = app.audio.played.size()
			audio_driver.trace[-1]["finished"] = app.simulation.finished
			audio_driver.trace[-1]["winner"] = app.simulation.winner
			audio_driver.trace[-1]["intro_tick"] = app.view.intro_tick
			audio_driver.trace[-1]["ending_tick"] = app.ending_tick
	if ui_fixes_debug != null:
		ui_fixes_debug.observe(tick)
	if gate_b_driver != null:
		gate_b_driver.observe(tick, app.simulation)
	if app.review and app.review_driver is UfePixelHudReview:
		var hud_driver := app.review_driver as UfePixelHudReview
		if not hud_driver.trace.is_empty():
			hud_driver.trace[-1]["hud"] = {
				"paused": app.paused,
				"white_trails": [app.hud.health[0].delayed, app.hud.health[1].delayed],
				"combo": [app.hud.combos[0].text, app.hud.combos[1].text],
				"word": app.hud.word_key,
				"viewport": [app.viewport.size.x, app.viewport.size.y],
				"debug": app.hud.debug_visible,
			}


func _queue_review_draw(app: Control, tick: int) -> void:
	_complete_review_draw.call_deferred(app, tick)
	if tick + 1 == int(app.review_capture_frames):
		app.set_physics_process(false)
		app.get_tree().quit()


func _complete_review_draw(app: Control, tick: int) -> void:
	assert(review_pending_tick == tick and int(app.capture_tick) == tick + 1, "待绘制tick已被覆盖或未完成模拟")
	var previous_count := review_draw_count
	RenderingServer.force_sync()
	RenderingServer.force_draw(true, 1.0 / 60.0)
	RenderingServer.force_sync()
	assert(review_draw_count == previous_count + 1, "主游戏录制没有完成本tick重绘")
	var root_image: Image = app.get_viewport().get_texture().get_image()
	var scene_image: Image = app.viewport.get_texture().get_image()
	assert(root_image != null and not root_image.is_empty() and scene_image != null and not scene_image.is_empty(), "重绘后无法读取实际像素")
	var rendered: Dictionary = {
		"capture_tick": tick,
		"source_movie_frame": Engine.get_process_frames(),
		"render_pass": review_draw_count,
		"front_visible": is_instance_valid(app.front) and bool(app.front.visible),
		"root_size": [root_image.get_width(), root_image.get_height()],
		"root_format": root_image.get_format(),
		"root_sha256": _review_image_sha256(root_image),
		"viewport_size": [scene_image.get_width(), scene_image.get_height()],
		"viewport_format": scene_image.get_format(),
		"viewport_sha256": _review_image_sha256(scene_image),
		"rendered_sprites": app.view.fighters.map(func(sprite): return {"flip_h":sprite.flip_h,"x":sprite.position.x,"y":sprite.position.y}),
	}
	review_render_trace.append(rendered)
	if app.review and app.review_driver is UfeReviewDriver:
		var driver := app.review_driver as UfeReviewDriver
		if not driver.trace.is_empty() and int(driver.trace[-1].get("movie_frame", -1)) == tick:
			for key: String in ["source_movie_frame", "render_pass", "rendered_sprites", "root_sha256", "viewport_sha256"]:
				driver.trace[-1][key] = rendered[key]
	review_pending_tick = -1
	if tick + 1 == int(app.review_capture_frames):
		_save_review_render_trace(app)


func _review_image_sha256(image: Image) -> String:
	var context := HashingContext.new()
	var error := context.start(HashingContext.HASH_SHA256)
	assert(error == OK, "无法初始化录制像素哈希")
	error = context.update(image.get_data())
	assert(error == OK, "无法计算录制像素哈希")
	return context.finish().hex_encode()


func _save_review_render_trace(app: Control) -> void:
	var report: Dictionary = {}
	var path := str(app.review_trace)
	if app.review and app.review_driver is UfeReviewDriver:
		app.review_driver.call("save_file", path)
		var saved: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		assert(saved is Dictionary, "无法读取录制模拟trace")
		report = saved
	report.render_trace = review_render_trace
	report.render_mapping = "capture_tick为主游戏输入tick；source_movie_frame为MovieWriter原片从0开始的实际帧号；SHA来自该次frame_post_draw之后的完整像素。"
	var output := FileAccess.open(path, FileAccess.WRITE)
	assert(output != null, "无法保存逐帧重绘证据")
	output.store_string(JSON.stringify(report, "\t"))


func _on_review_draw() -> void:
	review_draw_count += 1


func _capture_skill_still(app: Control, path: String) -> void:
	await RenderingServer.frame_post_draw
	var image := app.get_viewport().get_texture().get_image()
	# 整数倍窗口还原到原生640宽，避免逐招截图占满本机磁盘；不改游戏渲染。
	if image.get_width()>640 and image.get_width()%640==0:
		image.resize(640,roundi(640.0*image.get_height()/image.get_width()),Image.INTERPOLATE_NEAREST)
	var error := image.save_png(path)
	assert(error==OK,"技能截图保存失败: "+path)
