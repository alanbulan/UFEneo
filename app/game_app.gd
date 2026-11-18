extends Control
const TrainingInputAudit = preload("res://app/training_input_audit.gd")
var training_input_audit: TrainingInputAudit
var simulation: UfeMatchDirector
var recorder: UfeReplayRecorder
var replay: UfeReplayRecorder
var replay_cursor: int = 0
var viewport: SubViewport
var view: UfeSideView
var image: SubViewportContainer
var frame_holder: Control
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
var harness: UfeAppHarness = null
var review_driver: RefCounted = null
var review_trace: String = "res://reports/review/2026-10-21-gate-a/review-trace.json"
var walk_review_clip: String = ""
var review_capture_frames: int = 0
var ending_tick: int = 0
var ko_finish := UfeKoFinishPresentation.new()
var selected_fighters: Array=["ultraman","zetton"]
# 选人界面选定的出场形态；"default"为基础形态。回放按录像内形态复原。
var selected_forms: Array=["default","default"]
# 最近一次_battle_match要用的出场形态（子类重写签名保持三参数）。
var match_start_forms: Array=["default","default"]
var battle_preferences: Dictionary={}
var front: UfeFrontEnd
var training_overlay: UfeTrainingOverlay
var direct_battle: bool=false
var dummy_tape: Array=[]
var dummy_facings: Array=[]
var dummy_relative: bool=false
var dummy_recording: bool=false
var dummy_cursor: int=0
var match_seed: int=20261022
var computers: Array=[]
var ai_difficulty: String="normal"

func _on_joy_connection_changed(_device: int, _connected: bool) -> void:
	UfeInputRouter.configure()

func _ready() -> void:
	_size_window()
	get_tree().auto_accept_quit = false
	var args := OS.get_cmdline_user_args()
	training_input_audit=TrainingInputAudit.from_arguments(args)
	UfeInputRouter.configure()
	# 随主节点自动断开，避免Input单例在语言卸载后才释放匿名脚本引用。
	Input.joy_connection_changed.connect(_on_joy_connection_changed)
	for arg in args:
		if arg.begins_with("--harness="):
			var harness_path := arg.trim_prefix("--harness=")
			if not harness_path.is_empty():
				var loaded_harness := load(harness_path)
				if loaded_harness is Script:
					harness = loaded_harness.new() as UfeAppHarness
		if arg.begins_with("--match-seed="):match_seed=int(arg.trim_prefix("--match-seed="))
		if arg in ["--battle","--local","--training"]:direct_battle=true
		if arg.begins_with("--demo"): demo = true
		if arg == "--local": local = true
		if arg == "--training": training = true
		if arg.begins_with("--capture="): capture_path = arg.trim_prefix("--capture=")
		if arg.begins_with("--auto-quit="): auto_quit = int(arg.trim_prefix("--auto-quit="))
		if arg.begins_with("--capture-frame="): capture_frame = int(arg.trim_prefix("--capture-frame="))
	if harness != null:
		harness.parse_args(self, args)
	if review: training = true
	start_match()
	if not review and not demo and not direct_battle:
		_show_page("title")
	if harness != null:
		harness.after_ready(self)
	resized.connect(_fit)
	print("UFEneo 2D | 60 tick | replay v6")

func content_commands() -> UfeCommandPages:
	return front.content.get_child(0) as UfeCommandPages

func start_match() -> void:
	dummy_recording=false
	dummy_cursor=0
	ko_finish.reset()
	for child in get_children():
		remove_child(child)
		child.queue_free()
	match_start_forms = selected_forms.duplicate()
	simulation = _battle_match(selected_fighters[0],selected_fighters[1],training)
	if harness != null:
		var ids := harness.override_matchup(self)
		if ids.size() == 2:
			simulation = _battle_match(str(ids[0]), str(ids[1]))
	if review_driver != null:
		review_driver.call("prepare_match", simulation)
	recorder = UfeReplayRecorder.new()
	_reset_computers()
	replay = null
	paused = false
	var wants_intro := harness != null and harness.wants_intro(self)
	intro = 75 if wants_intro else 0 if demo or review else 75
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
	# 外层按缩放后的尺寸参与布局；SubViewportContainer 自己始终是 640×360，
	# 只靠 scale 放大。这样内部渲染分辨率不变，画面又能铺满窗口。
	frame_holder = Control.new()
	frame_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(frame_holder)
	image = SubViewportContainer.new()
	image.stretch = true
	image.stretch_shrink = 1
	image.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	image.size = Vector2(640, 360)
	frame_holder.add_child(image)
	image.add_child(viewport)
	var ui_layer := CanvasLayer.new()
	viewport.add_child(ui_layer)
	hud = UfeMatchUI.new()
	ui_layer.add_child(hud)
	hud.action_requested.connect(_action)
	view.framing_safe_provider=hud.battle_safe_rect
	training_overlay=UfeTrainingOverlay.new()
	ui_layer.add_child(training_overlay)
	training_overlay.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	training_overlay.offset_top=56
	training_overlay.offset_bottom=56
	hud.framing_top_overlays.append(training_overlay)
	front=UfeFrontEnd.new()
	ui_layer.add_child(front)
	front.action_requested.connect(_front_action)
	front.sound_requested.connect(func(id:String,owner_index:int):audio.cue(id,false,owner_index))
	front.hide()
	audio = UfeSideAudio.new()
	add_child(audio)
	audio.configure_battle_music(simulation.fighters.map(func(f):return f.definition.id),view.selected_stage,battle_preferences)
	UfePlayerSettings.apply(UfePlayerSettings.values(),false)
	if harness != null:
		harness.after_start_match(self)
	_fit()

func _size_window() -> void:
	"""启动时把窗口撑到屏幕放得下的最大整数倍，避免一开就是半屏黑边。"""
	UfeWindowFitter.size_window(self)

func _fit() -> void:
	# 640×360 的原生画面等比铺满窗口。窗口尺寸是 640×360 整数倍时像素仍然整齐；
	# 其它尺寸允许小数倍，宁可不留黑边——之前只取整数倍，窗口一大就缩成半屏。
	UfeWindowFitter.fit(size, image, frame_holder)

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
		"dummy_facing":
			dummy_relative=not dummy_relative
			dummy_cursor=0
			hud.toast.show_message("陪练按当前朝向复现，从头播放" if dummy_relative else "陪练按原始左右复现，从头播放")
		"dummy_record","dummy_playback":
			if not _prepare_dummy_session():return
			training=true
			dummy=4
			dummy_recording=action=="dummy_record"
			dummy_cursor=0
			if dummy_recording:
				dummy_tape.clear()
				dummy_facings.clear()
			paused=false
			hud.close_overlays()
			hud.toast.show_message("录制陪练：使用2P键位，Enter停止" if dummy_recording else "循环播放陪练录制")
		"commands":
			hud.show_commands(simulation.fighters[0].definition,simulation.fighters)
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
	dummy_recording=false
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
			selected_forms=front.selected_forms.duplicate()
			battle_preferences=front.stage_options.duplicate(true) if not front.stage_options.is_empty() else UfePlayerSettings.values()
			view.set_stage(str(battle_preferences.get("battle_stage",UfeBattleStageCatalog.default_id())))
			training=front.mode=="training"
			local=front.mode=="local"
			reset_round()
			if harness != null:
				harness.on_begin_match_from_front(self)
			view.show();hud.show();front.hide()

# 完整回放/终局不能直接接实时输入；先成功装配新局，再提交模式变更。
func _prepare_dummy_session() -> bool:
	if replay==null and not simulation.finished:return true
	var ids: Array=replay.fighter_ids.duplicate() if replay!=null else [simulation.fighters[0].base_definition.id,simulation.fighters[1].base_definition.id]
	if ids.size()!=2:return false
	match_start_forms = selected_forms.duplicate()
	var next_match:=_battle_match(str(ids[0]),str(ids[1]),true)
	if next_match==null:
		hud.toast.show_message("无法建立训练对局，陪练录制已保留")
		return false
	selected_fighters=ids
	training=true
	_install_round(next_match)
	return true

func reset_round() -> void:
	match_start_forms = selected_forms.duplicate()
	var next_match:=_battle_match(selected_fighters[0],selected_fighters[1],training)
	if harness != null:
		var ids := harness.override_matchup(self)
		if ids.size() == 2:
			next_match = _battle_match(str(ids[0]), str(ids[1]))
	if review_driver != null:
		review_driver.call("prepare_match", next_match)
	_install_round(next_match)

func _install_round(next_match: UfeMatchDirector) -> void:
	audio.suspend_battle()
	ko_finish.reset()
	dummy_recording=false
	dummy_cursor=0
	simulation=next_match
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
	var value := UfeReplayRecorder.read_candidate("user://last_replay.json")
	if value == null:
		message = UfeReplayRecorder.last_error
		return
	# 不以当前选人组合校验另一组人物；也不把文件自报指纹当作可信规则。
	for id in value.fighter_ids:
		if not UfeRosterModel.implemented(id):
			UfeReplayRecorder.last_error="回放角色不存在或尚不可用："+id
			message=UfeReplayRecorder.last_error
			return
	match_start_forms = value.forms.duplicate() if value.forms.size()==2 else ["default","default"]
	var next_match:=_battle_match(value.fighter_ids[0],value.fighter_ids[1],true)
	if next_match==null:
		UfeReplayRecorder.last_error="无法建立回放对局"
		message=UfeReplayRecorder.last_error
		return
	if not value.matches_content(next_match.content_fingerprint):
		message=UfeReplayRecorder.last_error
		return
	audio.suspend_battle()
	ko_finish.reset()
	simulation = next_match
	selected_fighters=value.fighter_ids.duplicate()
	selected_forms=value.forms.duplicate() if value.forms.size()==2 else ["default","default"]
	message=""
	view.bind_match(simulation)
	# 验证并成功装配后才清显示；失败加载不能破坏当前输入与上一招。
	hud.input_history=[[],[]]
	hud.debug_label.text=""
	training_overlay.reset_display()
	replay = value
	dummy_recording=false
	dummy_cursor=0
	audio.configure_battle_music(simulation.fighters.map(func(f):return f.definition.id),view.selected_stage,battle_preferences)
	audio.next_battle()
	if view.layered_stage!=null:view.layered_stage.restart()
	replay_cursor = 0
	intro = 0
	ending_tick = 0
	paused = false
	hud.close_overlays()

func _input(event: InputEvent) -> void:
	if training_input_audit!=null:training_input_audit.record_event(event)
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

## 同步停播并断开音频流引用；任何退出路径（菜单、窗口关闭、--quit-after）都会
## 经过 _exit_tree。AudioServer 在独立线程按真实时间回收 playback，headless 帧
## 循环极快，必须让出真实时间，否则退出时报 AudioStream/Playback 泄漏。
func _release_audio_sync() -> void:
	if is_instance_valid(audio): audio.release_audio()

func _exit_tree() -> void:
	_release_audio_sync()
	OS.delay_msec(120)

## quit_tree=false 时只拆解自身资源、不结束进程，供同一进程内的多实例测试收尾。
func shutdown(exit_code: int = 0, quit_tree: bool = true) -> void:
	if _shutting_down: return
	_shutting_down = true
	if training_input_audit!=null:training_input_audit.close()
	set_physics_process(false)
	viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	# 停播并断开流引用：播放中的 AudioStreamPlayer 若在音频线程回收前被
	# free，会留下 AudioStream/Playback 残留。
	_release_audio_sync()
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
	if quit_tree:get_tree().quit(exit_code)

func _physics_process(_delta: float) -> void:
	if training_input_audit!=null:training_input_audit.begin_frame(self)
	if is_instance_valid(view) and view.layered_stage!=null:view.layered_stage.frozen=paused
	if harness != null:
		harness.before_physics(self, capture_tick)
	if is_instance_valid(front) and front.visible:
		if harness != null:
			harness.on_front_visible(self, capture_tick)
		capture_tick+=1
		if not capture_path.is_empty() and capture_tick==capture_frame:_capture.call_deferred()
		if training_input_audit!=null:training_input_audit.end_frame(self)
		if auto_quit>0 and capture_tick>=auto_quit:shutdown()
		return
	if harness != null:
		harness.before_simulation_step(self, capture_tick)
	if Input.is_action_just_pressed("pause"): _action("pause")
	if review and review_driver != null:
		review_driver.set("review_frame", capture_tick)
		var part: int = int(review_driver.call("section", capture_tick))
		if part != int(review_driver.get("last_section")):
			if harness != null and harness.should_restart_match_on_section(self):
				start_match()
			else:
				reset_round()
			review_driver.set("last_section", part)
		var driver_profile := str(review_driver.get("profile"))
		message = ("阶段 4 · " if driver_profile.begins_with("stage4_") else "阶段 3 · " if driver_profile.begins_with("phase3_") else "验收门 A · ") + str(review_driver.call("label", capture_tick))
		if not walk_review_clip.is_empty(): message += " · 候选未通过自检"
		view.show_boxes = bool(review_driver.call("boxes", capture_tick))
	if not paused:
		if intro > 0: intro -= 1
		elif replay != null:
			if replay_cursor < replay.frames.size():
				var pair: Array = replay.frames[replay_cursor]
				var inputs: Array=[UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])]
				if training_input_audit!=null:training_input_audit.sampled(inputs[1],"replay")
				simulation.step(inputs)
				hud.record_inputs(inputs)
				training_overlay.record(inputs)
				replay_cursor += 1
			else:
				message = "回放验证一致" if replay.final_hash == simulation.state_hash() else "回放状态不一致"
				if ko_finish.can_pause_replay(simulation,ending_tick) and not audio.has_pending_ending_voice():paused = true
		elif not simulation.finished:
			var first: UfeInputFrame=computers[0].sample(simulation) if demo else UfeInputRouter.poll(0)
			var second: UfeInputFrame=UfeInputRouter.poll(1) if local else computers[1].sample(simulation)
			if training: second = _dummy_input()
			if review and review_driver != null:
				first = review_driver.call("sample", capture_tick, simulation) as UfeInputFrame
				second = review_driver.call("second_sample", capture_tick) as UfeInputFrame
			if harness != null:
				var overridden := harness.override_inputs(self, capture_tick, first, second)
				if overridden.size() == 2:
					first = overridden[0] as UfeInputFrame
					second = overridden[1] as UfeInputFrame
			_record_dummy_input(second)
			var inputs: Array = [first,second]
			if review and review_driver != null:
				review_driver.call("remember_inputs", inputs)
			if training_input_audit!=null:training_input_audit.sampled(second,"live")
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
	view.feedback.advance_effects(ko_finish.effect_steps, simulation.hitstop>0)
	var label: String = "训练："+["站立","下蹲","跳跃","自动防御","对手录制回放"][dummy] if training else ("本地双人" if local else "对战电脑")
	hud.dummy_relative = dummy_relative
	hud.dummy_name = ["站立","下蹲","跳跃","自动防御","对手录制回放"][dummy]
	hud.debug_visible = view.show_boxes
	hud.update_match(display_sim,label+"  | Enter 暂停  F1 判定框  F2 招式表  F3 训练  "+message,intro,training)
	training_overlay.visible=training and not paused and not view.show_boxes
	training_overlay.update_match(simulation)
	view.update_view()
	if review and review_driver != null:
		review_driver.call("observe_walk", capture_tick, simulation, view)
	audio.sync(display_sim,paused,intro>0,simulation)
	if not paused:audio.ceremony(display_sim,intro,ending_tick)
	if harness != null:
		harness.after_step(self, capture_tick)
	capture_tick += 1
	if review and review_driver != null:
		var driver_len: int = int(review_driver.call("length_frames"))
		if capture_tick == driver_len - 1 or (review_capture_frames > 0 and capture_tick == review_capture_frames - 2):
			review_driver.call("save_file", review_trace)
	if not capture_path.is_empty() and capture_tick == capture_frame: _capture.call_deferred()
	if training_input_audit!=null:training_input_audit.end_frame(self)
	if auto_quit > 0 and capture_tick >= auto_quit: shutdown()

func _record_dummy_input(frame: UfeInputFrame) -> void:
	UfeDummySession.record_input(self, frame)

func _dummy_input() -> UfeInputFrame:
	return UfeDummySession.sample_input(self)

func _capture() -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(capture_path)

func _battle_match(first: String, second: String, allow_pilot: bool = false) -> UfeMatchDirector:
	# 用成员传出场形态，保持测试子类对_battle_match的重写签名不变。
	return UfeBattleFormCatalog.match_for(first, second, allow_pilot, {}, match_start_forms)
