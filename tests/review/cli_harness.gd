extends UfeAppHarness
## 审片、页面截图与 UI 调试 CLI 挂载器（仅通过 --harness=res://tests/review/cli_harness.gd 加载）。

var gate_b_driver: UfeGateBReview = null
var ui_fixes_debug: UfeUIFixesDebug = null
var capture_ui: String = ""
var long_text: bool = false


func parse_args(app: Control, args: PackedStringArray) -> void:
	long_text = "--review-long-text" in args
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
		elif arg == "--review-throws":
			app.review = true
			app.review_driver = UfePhase3ThrowReview.new()
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
			if pair.size() == 2 and pair.all(func(id): return FileAccess.file_exists("res://content/fighters/%s/definition.json" % id)):
				app.selected_fighters = [pair[0], pair[1]]
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
	if app.review_driver is UfePixelPagesReview:
		app._show_page("title")
	if capture_ui in ["title", "select", "vs", "archive", "settings", "commands", "training"]:
		app.front.selections = app.selected_fighters.duplicate()
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
