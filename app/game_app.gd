extends Control
var simulation: UfeMatchDirector
var recorder: UfeReplayRecorder
var replay: UfeReplayRecorder
var replay_cursor: int = 0
var viewport: SubViewport
var view: UfeSideView
var image: SubViewportContainer
var hud: UfeMatchUI
var audio: UfeSideAudio
var paused: bool = false
var training: bool = false
var local: bool = false
var demo: bool = false
var review: bool = false
var dummy: int = 0
var intro: int = 75
var message: String = ""
var capture_path: String = ""
var capture_tick: int = 0
var auto_quit: int = 0
var _shutting_down: bool = false
var capture_frame: int = 6
var review_driver := UfeReviewDriver.new()
var review_trace: String = "res://reports/review/2026-10-21-gate-a/review-trace.json"
var walk_review_clip: String = ""
var review_capture_frames: int = 0
var ending_tick: int = 0
var ko_finish := UfeKoFinishPresentation.new()
var selected_fighters: Array=["ultraman","zetton"]
var battle_preferences: Dictionary={}
var capture_ui: String=""
var front: UfeFrontEnd
var training_overlay: UfeTrainingOverlay
var direct_battle: bool=false
var dummy_tape: Array=[]
var dummy_recording: bool=false
var dummy_cursor: int=0
var match_seed: int=20261022
var computers: Array=[]
var ai_difficulty: String="normal"
var gate_b_driver: UfeGateBReview
var ui_fixes_debug: UfeUIFixesDebug

func _on_joy_connection_changed(_device: int, _connected: bool) -> void:
	UfeInputRouter.configure()

func _ready() -> void:
	get_tree().auto_accept_quit = false
	UfeInputRouter.configure()
	# 随主节点自动断开，避免Input单例在语言卸载后才释放匿名脚本引用。
	Input.joy_connection_changed.connect(_on_joy_connection_changed)
	for arg in OS.get_cmdline_user_args():
		if arg=="--review-ultraseven-air-special":
			review=true
			review_driver=UfeUltrasevenAirSpecialReview.new()
			selected_fighters=["ultraseven","zetton"]
		if arg=="--review-zetton-counter":
			review=true
			review_driver=UfeZettonCounterReview.new()
		if arg=="--review-ultraseven":
			review=true
			review_driver=UfeUltrasevenReview.new()
			selected_fighters=["ultraseven","zetton"]
		if arg=="--review-ultraseven-air":
			review=true
			review_driver=UfeUltrasevenAirReview.new()
			selected_fighters=["ultraseven","zetton"]
		if arg=="--review-ultraseven-defense":
			review=true
			review_driver=UfeUltrasevenDefenseReview.new()
			selected_fighters=["ultraseven","zetton"]
		if arg=="--review-ultraseven-fourth":
			review=true
			review_driver=UfeUltrasevenFourthReview.new()
			selected_fighters=["ultraseven","zetton"]
		if arg=="--review-ultraseven-body":
			review=true
			review_driver=UfeUltrasevenBodyReview.new()
			selected_fighters=["ultraseven","zetton"]
		if arg.begins_with("--review-ultraseven-only=") and review_driver is UfeUltrasevenReview:
			review_driver.selected_action=arg.trim_prefix("--review-ultraseven-only=")
		if arg=="--review-gate-b":gate_b_driver=UfeGateBReview.new()
		if arg.begins_with("--match-seed="):match_seed=int(arg.trim_prefix("--match-seed="))
		if arg in ["--battle","--local","--training"]:direct_battle=true
		if arg.begins_with("--demo"): demo = true
		if arg == "--local": local = true
		if arg == "--training": training = true
		if arg == "--review": review = true
		if arg == "--review-forward-walk":
			review = true
			review_driver.profile = "forward_walk"
		if arg == "--review-back-walk":
			review = true
			review_driver.profile = "back_walk"
		if arg == "--review-dash":
			review = true
			review_driver.profile = "dash_once"
		if arg == "--review-switches":
			review = true
			review_driver.profile = "locomotion_switches"
		if arg == "--review-color-switches":
			review = true
			review_driver.profile = "color_switches"
		if arg == "--review-phase3":
			review = true
			review_driver.profile = "phase3_standing"
		if arg == "--review-air":
			review = true
			review_driver = UfePhase3AirReview.new()
		if arg == "--review-reactions":
			review = true
			review_driver = UfePhase3ReactionReview.new()
		if arg == "--review-zetton":
			review = true
			review_driver = UfePhase3ZettonReview.new()
		if arg == "--review-zetton-defense":
			review = true
			review_driver = UfePhase3ZettonDefenseReview.new()
		if arg == "--review-zetton-air":
			review = true
			review_driver = UfePhase3ZettonAirReview.new()
		if arg == "--review-throws":
			review = true
			review_driver = UfePhase3ThrowReview.new()
		if arg == "--review-gate-b-patch":
			review = true
			review_driver = UfeGateBPatchReview.new()
		if arg == "--review-specials":
			review = true
			review_driver = UfePhase3SpecialReview.new()
		if arg in ["--review-supers","--review-feedback"]:
			review = true
			review_driver = UfePhase3SuperReview.new()
			review_driver.feedback_only=arg=="--review-feedback"
		if arg=="--review-audio":
			review=true
			review_driver=UfePhase3AudioReview.new()
		if arg=="--review-hud":
			review=true
			review_driver=UfePixelHudReview.new()
		if arg=="--review-pages":
			review=true
			review_driver=UfePixelPagesReview.new()
		if arg=="--review-flash":
			review=true
			review_driver=UfePixelFlashReview.new()
		if arg=="--review-hud-air":
			review=true
			review_driver=UfePixelHudAirReview.new()
		if arg=="--review-ui-controls":
			review=true
			review_driver=UfePixelUIControls.new()
		if arg.begins_with("--capture-ui="):capture_ui=arg.trim_prefix("--capture-ui=")
		if arg.begins_with("--capture-pair="):
			var pair: Array=Array(arg.trim_prefix("--capture-pair=").split(","))
			if pair.size()==2 and pair.all(func(id):return FileAccess.file_exists("res://content/fighters/%s/definition.json"%id)):selected_fighters=[pair[0],pair[1]]
		if arg == "--review-final":
			review = true
			review_driver.profile = "gate_a_final"
		if arg.begins_with("--review-forward-candidate="):
			review = true
			walk_review_clip = arg.trim_prefix("--review-forward-candidate=")
			var candidate: Dictionary=UfeContentDatabase.read_json(walk_review_clip)
			review_driver.profile = "back_walk" if candidate.get("action","")=="walk_back" else "forward_walk"
			selected_fighters[0]=candidate.get("fighter","ultraman")
		if arg.begins_with("--review-trace="): review_trace = arg.trim_prefix("--review-trace=")
		if arg.begins_with("--review-capture-frames="): review_capture_frames=int(arg.trim_prefix("--review-capture-frames="))
		if arg.begins_with("--capture="): capture_path = arg.trim_prefix("--capture=")
		if arg.begins_with("--auto-quit="): auto_quit = int(arg.trim_prefix("--auto-quit="))
		if arg.begins_with("--capture-frame="): capture_frame = int(arg.trim_prefix("--capture-frame="))
	if review: training = true
	start_match()
	if review_driver is UfePixelPagesReview:_show_page("title")
	if not review and not demo and not direct_battle:
		_show_page("title")
	if capture_ui in ["title","select","vs","archive","settings","commands","training"]:
		front.selections=selected_fighters.duplicate()
		if capture_ui=="training":training=true;front.hide();view.show();hud.show();paused=false
		else:
			front.long_names="--review-long-text" in OS.get_cmdline_user_args()
			_show_page(capture_ui)
	if capture_ui in ["select-bottom","select-long","archive-zetton"]:
		front.long_names=capture_ui=="select-long"
		front.archive_index=1 if capture_ui=="archive-zetton" else 0
		_show_page("archive" if capture_ui=="archive-zetton" else "select")
	if capture_ui=="menu":
		front.hide();view.show();hud.show();paused=false;_action("pause")
	if capture_ui.begins_with("commands-"):
		_show_page("commands")
		if "zetton" in capture_ui:
			(content_commands() as UfeCommandPages).set_fighter(UfeContentDatabase.fighter("zetton"))
		for i in range(8):
			if capture_ui.ends_with("-"+["standing","crouching","jumping","airchain","state","throws","specials","supers"][i]):content_commands().show_page(i)
	if capture_ui in ["training-last","battle"]:
		training=capture_ui=="training-last";front.hide();view.show();hud.show();paused=false;intro=0
	resized.connect(_fit)
	if OS.has_feature("debug") and training:
		var ui_mode: String=""
		var ui_output: String=""
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--ui-fixes-debug="):ui_mode=arg.trim_prefix("--ui-fixes-debug=")
			if arg.begins_with("--ui-out="):ui_output=arg.trim_prefix("--ui-out=")
		if ui_mode in ["hud","switch","showcase"] and not ui_output.is_empty():
			ui_fixes_debug=UfeUIFixesDebug.new()
			ui_fixes_debug.prepare(self,ui_mode,ui_output)
	print("UFEneo 2D | 60 tick | replay v6")

func content_commands() -> UfeCommandPages:
	return front.content.get_child(0) as UfeCommandPages

func start_match() -> void:
	ko_finish.reset()
	for child in get_children():
		remove_child(child)
		child.queue_free()
	simulation = _battle_match(selected_fighters[0],selected_fighters[1],training)
	if review_driver is UfePhase3SpecialReview or review_driver is UfeUltrasevenFourthReview:
		var ids: Array=review_driver.matchup()
		simulation=_battle_match(str(ids[0]),str(ids[1]))
	review_driver.prepare_match(simulation)
	recorder = UfeReplayRecorder.new()
	_reset_computers()
	replay = null
	paused = false
	intro = 75 if (review_driver is UfePhase3SpecialReview or review_driver is UfeUltrasevenFourthReview) and review_driver.wants_intro() else 0 if demo or review else 75
	ending_tick=0
	viewport = SubViewport.new()
	viewport.size = Vector2i(640,360)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	view = UfeSideView.new()
	battle_preferences=UfePlayerSettings.values()
	view.selected_stage=UfeBattleStageCatalog.valid_id(str(battle_preferences.get("battle_stage",UfeBattleStageCatalog.default_id())))
	view.bind_match(simulation)
	view.walk_review_clip = walk_review_clip
	viewport.add_child(view)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	image = SubViewportContainer.new()
	image.stretch = true
	image.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	center.add_child(image)
	image.add_child(viewport)
	var ui_layer := CanvasLayer.new()
	viewport.add_child(ui_layer)
	hud = UfeMatchUI.new()
	hud.review_long_text = "--review-long-text" in OS.get_cmdline_user_args()
	ui_layer.add_child(hud)
	hud.action_requested.connect(_action)
	training_overlay=UfeTrainingOverlay.new()
	ui_layer.add_child(training_overlay)
	training_overlay.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	training_overlay.offset_top=56
	training_overlay.offset_bottom=56
	front=UfeFrontEnd.new()
	ui_layer.add_child(front)
	front.action_requested.connect(_front_action)
	front.sound_requested.connect(func(id:String,owner:int):audio.cue(id,false,owner))
	front.hide()
	audio = UfeSideAudio.new()
	add_child(audio)
	audio.configure_battle_music(simulation.fighters.map(func(f):return f.definition.id),view.selected_stage,battle_preferences)
	UfePlayerSettings.apply(UfePlayerSettings.values(),false)
	_fit()

func _fit() -> void:
	if is_instance_valid(image):
		var factor := maxi(1,floori(minf(size.x/640,size.y/360)))
		image.custom_minimum_size = Vector2(640,360)*factor
		image.stretch_shrink = factor
		image.size = image.custom_minimum_size

func _action(action: String) -> void:
	# 回放播完会自动暂停；首次按暂停应显示菜单，避免反复恢复后又立即暂停。
	if action=="pause" and (hud.selection.visible or (replay != null and replay_cursor >= replay.frames.size() and not hud.menu.visible)):
		paused=true
		hud.show_pause(true)
		audio.set_context("menu")
		return
	match action:
		"pause":
			paused = not paused
			hud.show_pause(paused)
		"boxes": view.show_boxes = not view.show_boxes
		"back_pause":
			paused = true
			hud.show_pause(true)
		"settings":
			paused = true
			hud.close_overlays()
			hud.settings.show()
		"restart": reset_round()
		"training":
			training = not training
			reset_round()
		"local":
			local = true
			training = false
			reset_round()
		"dummy":
			dummy = (dummy+1)%5
			hud.toast.show_message("对手行为："+["站立","下蹲","跳跃","自动防御","对手录制回放"][dummy])
		"dummy_record","dummy_playback":
			training=true
			dummy=4
			dummy_recording=action=="dummy_record"
			dummy_cursor=0
			if dummy_recording:dummy_tape.clear()
			paused=false
			hud.close_overlays()
			hud.toast.show_message("录制陪练：使用2P键位，Enter停止" if dummy_recording else "循环播放陪练录制")
		"commands":
			hud.show_commands(simulation.fighters[0].definition)
			paused = hud.commands.visible
		"home":
			hud.close_overlays()
			_show_page("title")
		"replay": play_replay()
		"select":
			hud.close_overlays()
			front.selections=selected_fighters.duplicate()
			front.confirmed=[false,false]
			_show_page("select")
		"select_first","select_second":
			var index: int=0 if action=="select_first" else 1
			selected_fighters[index]="zetton" if selected_fighters[index]=="ultraman" else "ultraman"
			hud.show_selection(selected_fighters)
		"select_confirm":
			hud.selection.hide()
			reset_round()
	audio.set_context("select" if hud.selection.visible or (front.visible and front.page in ["select","stage","vs"]) else "menu" if front.visible else "paused" if paused else "battle")

func _show_page(page: String) -> void:
	audio.suspend_battle()
	ko_finish.reset()
	view.bind_match(simulation)
	paused=true
	front.open(page)
	view.hide()
	hud.hide()
	training_overlay.hide()
	audio.set_context("select" if page=="select" else "menu")

func _front_action(action: String) -> void:
	if action.begins_with("music_preview:"):
		audio.preview_music(action.trim_prefix("music_preview:"))
		return
	if action.begins_with("sound:"):
		audio.cue(action.trim_prefix("sound:"))
		return
	match action:
		"quit":shutdown()
		"back":_show_page("select" if front.page=="stage" else "title")
		"begin_match":
			selected_fighters=front.selections.duplicate()
			battle_preferences=front.stage_options.duplicate(true) if not front.stage_options.is_empty() else UfePlayerSettings.values()
			view.set_stage(str(battle_preferences.get("battle_stage",UfeBattleStageCatalog.default_id())))
			training=front.mode=="training"
			local=front.mode=="local"
			reset_round()
			if review_driver is UfePixelPagesReview:intro=75
			view.show();hud.show();front.hide()

func reset_round() -> void:
	audio.suspend_battle()
	ko_finish.reset()
	simulation = _battle_match(selected_fighters[0],selected_fighters[1],training)
	if review_driver is UfePhase3SpecialReview or review_driver is UfeUltrasevenFourthReview:
		var ids: Array=review_driver.matchup()
		simulation=_battle_match(str(ids[0]),str(ids[1]))
	review_driver.prepare_match(simulation)
	view.bind_match(simulation)
	recorder = UfeReplayRecorder.new()
	_reset_computers()
	replay = null
	paused = false
	intro = 0 if review else 75
	ending_tick=0
	audio.configure_battle_music(simulation.fighters.map(func(f):return f.definition.id),view.selected_stage,battle_preferences)
	audio.next_battle()
	if view.layered_stage!=null:view.layered_stage.restart()
	hud.input_history = [[],[]]
	hud.close_overlays()
	training_overlay.last_moves=[{},{}]

func _reset_computers() -> void:
	ai_difficulty=str(UfePlayerSettings.values().get("ai_difficulty","normal"))
	computers=[UfeComputerController.new(match_seed,ai_difficulty,0),UfeComputerController.new(match_seed,ai_difficulty,1)]
	recorder.match_seed=match_seed
	recorder.ai_difficulty=ai_difficulty

func play_replay() -> void:
	if not recorder.frames.is_empty() and replay == null: recorder.save_file("user://last_replay.json")
	var value := UfeReplayRecorder.load_file("user://last_replay.json", simulation.content_fingerprint)
	if value == null:
		message = UfeReplayRecorder.last_error
		return
	audio.suspend_battle()
	ko_finish.reset()
	simulation = _battle_match(str(value.fighter_ids[0]),str(value.fighter_ids[1]),true)
	view.bind_match(simulation)
	replay = value
	audio.configure_battle_music(simulation.fighters.map(func(f):return f.definition.id),view.selected_stage,battle_preferences)
	audio.next_battle()
	if view.layered_stage!=null:view.layered_stage.restart()
	replay_cursor = 0
	intro = 0
	ending_tick = 0
	paused = false
	hud.close_overlays()

func _input(event: InputEvent) -> void:
	if is_instance_valid(front) and front.has_method("capture_binding_input") and bool(front.call("capture_binding_input",event)):
		get_viewport().set_input_as_handled()
		return
	if PixelChoice.handle_active_input(event):
		get_viewport().set_input_as_handled()
		return
	if not event is InputEventKey or not event.pressed or event.echo: return
	if is_instance_valid(front) and front.visible:
		if event.keycode==KEY_ESCAPE:
			if front.page=="controls":front.open("settings")
			else:_front_action("back")
		elif front.handle_key(event.keycode):pass
		else:return
		get_viewport().set_input_as_handled()
		return
	match event.keycode:
		KEY_ENTER:
			if dummy_recording:dummy_recording=false
			var focused := viewport.gui_get_focus_owner()
			if paused and focused is Button and focused.is_visible_in_tree(): focused.pressed.emit()
			else: _action("pause")
		KEY_ESCAPE: _action("pause")
		KEY_F1: _action("boxes")
		KEY_F2: _action("commands")
		KEY_F3: _action("training")
		KEY_F4: _action("replay")
		KEY_F5: _action("dummy")
		KEY_F6: _action("select")
		KEY_R: _action("restart")
		_: return
	# 根窗口先消费全局快捷键，避免SubViewport转发后Enter再次激活“继续”。
	get_viewport().set_input_as_handled()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST: shutdown()

func shutdown(exit_code: int = 0) -> void:
	if _shutting_down: return
	_shutting_down = true
	set_physics_process(false)
	viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	await get_tree().process_frame
	ko_finish.reset()
	view.simulation = null
	simulation = null
	recorder = null
	replay = null
	for child in get_children(): child.free()
	view = null
	viewport = null
	image = null
	hud = null
	get_tree().quit(exit_code)

func _physics_process(_delta: float) -> void:
	if is_instance_valid(view) and view.layered_stage!=null:view.layered_stage.frozen=paused
	if ui_fixes_debug!=null:ui_fixes_debug.drive(capture_tick)
	if gate_b_driver!=null:gate_b_driver.drive(capture_tick,self)
	if review_driver is UfePixelPagesReview:review_driver.drive_controls(capture_tick,self)
	if review_driver is UfePixelFlashReview:review_driver.drive_controls(capture_tick,self)
	if is_instance_valid(front) and front.visible:
		if gate_b_driver!=null:gate_b_driver.observe(capture_tick,simulation)
		if capture_ui=="select-bottom" and capture_tick==20:front.grid.scroll_vertical=100000
		if capture_ui.begins_with("commands-") and "bottom" in capture_ui and capture_tick==20:content_commands().rows.scroll_vertical=100000
		if ui_fixes_debug!=null:ui_fixes_debug.observe(capture_tick)
		capture_tick+=1
		if not capture_path.is_empty() and capture_tick==capture_frame:_capture.call_deferred()
		if auto_quit>0 and capture_tick>=auto_quit:shutdown()
		return
	if capture_ui=="training-last":
		if capture_tick==2:Input.action_press("p1_right");Input.action_press("p1_ranged")
		if capture_tick==3:Input.action_release("p1_right");Input.action_release("p1_ranged")
	if Input.is_action_just_pressed("pause"): _action("pause")
	if review:
		if review_driver is UfePixelUIControls: review_driver.drive_controls(capture_tick,self)
		review_driver.review_frame = capture_tick
		var part := review_driver.section(capture_tick)
		if part != review_driver.last_section:
			if review_driver is UfePhase3SpecialReview or review_driver is UfeUltrasevenFourthReview: start_match()
			else: reset_round()
			review_driver.last_section = part
		message = ("阶段 4 · " if review_driver.profile.begins_with("stage4_") else "阶段 3 · " if review_driver.profile.begins_with("phase3_") else "验收门 A · ")+review_driver.label(capture_tick)
		if not walk_review_clip.is_empty(): message += " · 候选未通过自检"
		view.show_boxes = review_driver.boxes(capture_tick)
		if review_driver is UfePixelHudReview and not review_driver is UfePixelPagesReview:
			if capture_tick in [180,270]: _action("pause")
	if not paused:
		if intro > 0: intro -= 1
		elif replay != null:
			if replay_cursor < replay.frames.size():
				var pair: Array = replay.frames[replay_cursor]
				simulation.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
				replay_cursor += 1
			else:
				message = "回放验证一致" if replay.final_hash == simulation.state_hash() else "回放状态不一致"
				if ko_finish.can_pause_replay(simulation,ending_tick) and not audio.has_pending_ending_voice():paused = true
		elif not simulation.finished:
			var first: UfeInputFrame=computers[0].sample(simulation) if demo else UfeInputRouter.poll(0)
			var second: UfeInputFrame=UfeInputRouter.poll(1) if local else computers[1].sample(simulation)
			if training: second = _dummy_input()
			if ui_fixes_debug!=null:
				first=ui_fixes_debug.sample(0,capture_tick)
				second=ui_fixes_debug.sample(1,capture_tick)
			if gate_b_driver!=null:first=gate_b_driver.sample(capture_tick,simulation)
			if review:
				first = review_driver.sample(capture_tick,simulation)
				second = review_driver.second_sample(capture_tick)
				if review_driver is UfePixelPagesReview and dummy==4 and not dummy_recording:second=_dummy_input()
			if dummy_recording:dummy_tape.append(second.pack())
			var inputs: Array = [first,second]
			if review: review_driver.remember_inputs(inputs)
			simulation.step(inputs)
			recorder.append(inputs,simulation)
			hud.record_inputs(inputs)
			training_overlay.record(inputs)
			if simulation.finished: recorder.save_file("user://last_replay.json")
	var display_sim:=ko_finish.sample(simulation,paused)
	if not is_same(view.simulation,display_sim):
		audio.begin_finish(simulation,display_sim)
		view.bind_match(display_sim,true)
	view.intro_tick=75-intro if intro>0 else -1
	view.ending_tick=ending_tick
	if not paused and display_sim.finished: ending_tick+=1
	view.feedback.advance_effects(ko_finish.effect_steps)
	view.update_view()
	if review: review_driver.observe_walk(capture_tick,simulation,view)
	audio.sync(display_sim,paused,intro>0,simulation)
	if not paused:audio.ceremony(display_sim,intro,ending_tick)
	if review and review_driver is UfePhase3AudioReview and not review_driver.trace.is_empty():
		review_driver.trace[-1]["audio_played"]=audio.played.slice(review_driver.audio_cursor).duplicate(true)
		review_driver.audio_cursor=audio.played.size()
		review_driver.trace[-1]["finished"]=simulation.finished
		review_driver.trace[-1]["winner"]=simulation.winner
		review_driver.trace[-1]["intro_tick"]=view.intro_tick
		review_driver.trace[-1]["ending_tick"]=ending_tick
	var label: String = "训练："+["站立","下蹲","跳跃","自动防御","对手录制回放"][dummy] if training else ("本地双人" if local else "对战电脑")
	hud.dummy_name = ["站立","下蹲","跳跃","自动防御","对手录制回放"][dummy]
	hud.debug_visible = view.show_boxes
	hud.update_match(display_sim,label+"  | Enter 暂停  F1 判定框  F2 招式表  F3 训练  "+message,intro,training)
	training_overlay.visible=training and not paused and not view.show_boxes
	training_overlay.update_match(simulation)
	if ui_fixes_debug!=null:ui_fixes_debug.observe(capture_tick)
	if gate_b_driver!=null:gate_b_driver.observe(capture_tick,simulation)
	if review and review_driver is UfePixelHudReview and not review_driver.trace.is_empty():
		review_driver.trace[-1]["hud"] = {"paused":paused,"white_trails":[hud.health[0].delayed,hud.health[1].delayed],"combo":[hud.combos[0].text,hud.combos[1].text],"word":hud.word_key,"viewport":[viewport.size.x,viewport.size.y],"debug":hud.debug_visible}
	capture_tick += 1
	if review and (capture_tick == review_driver.length_frames()-1 or (review_capture_frames>0 and capture_tick==review_capture_frames-2)): review_driver.save_file(review_trace)
	if not capture_path.is_empty() and capture_tick == capture_frame: _capture.call_deferred()
	if auto_quit > 0 and capture_tick >= auto_quit: shutdown()

func _dummy_input() -> UfeInputFrame:
	match dummy:
		1: return UfeInputFrame.make(0,-1)
		2: return UfeInputFrame.make(0,1 if simulation.tick%45 == 0 else 0)
		3: return UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
		4:
			if dummy_recording:
				var frame:=UfeInputRouter.poll(1)
				return frame
			if not dummy_tape.is_empty():
				var frame:=UfeInputFrame.unpack(dummy_tape[dummy_cursor%dummy_tape.size()])
				dummy_cursor+=1
				return frame
	return UfeInputFrame.make()

func _capture() -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(capture_path)


func _battle_match(first: String, second: String, allow_pilot: bool = false) -> UfeMatchDirector:
	return UfeBattleFormCatalog.match_for(first, second, allow_pilot)
