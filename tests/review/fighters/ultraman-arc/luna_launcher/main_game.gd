extends "res://app/game_app.gd"
## 仍实例化正式main，替换首次训练工厂；无正式角色/资源开关修改。
const Factory = preload("res://tests/review/fighters/ultraman-arc/luna_launcher/candidate_factory.gd")
const CandidateView = preload("res://tests/review/fighters/ultraman-arc/luna_launcher/candidate_view.gd")
var candidate_contract: Dictionary = {}
var candidate_contract_path: String = ""
var direction: int = 1
var case_kind: String = "hit"
var output_directory: String = ""
var still_keys: Dictionary = {}
var pending_stills: int = 0
var finishing: bool = false

func _battle_match(_first: String, _second: String, _allow_pilot: bool = false) -> UfeMatchDirector:
	return Factory.make_match(candidate_contract,direction,case_kind)

func start_match() -> void:
	assert(bool(candidate_contract.get("root_runtime_ready",false)))
	training = true
	local = true
	ko_finish.reset()
	for child in get_children():
		remove_child(child)
		child.queue_free()
	# 第一份sim即候选月亮定义；后续没有definition字段替换。
	simulation = _battle_match("ultraman-arc__luna",str(candidate_contract.opponent),false)
	review_driver.prepare_match(simulation)
	recorder = UfeReplayRecorder.new()
	_reset_computers()
	replay = null
	paused = false
	intro = 0
	ending_tick = 0
	viewport = SubViewport.new()
	viewport.size = Vector2i(640,360)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	view = CandidateView.new()
	view.set("candidate_contract",candidate_contract)
	view.set("candidate_contract_path",candidate_contract_path)
	battle_preferences = UfePlayerSettings.values()
	view.selected_stage = UfeBattleStageCatalog.valid_id(str(battle_preferences.get("battle_stage",UfeBattleStageCatalog.default_id())))
	view.bind_match(simulation)
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
	ui_layer.add_child(hud)
	hud.action_requested.connect(_action)
	view.framing_safe_provider=hud.battle_safe_rect
	training_overlay = UfeTrainingOverlay.new()
	ui_layer.add_child(training_overlay)
	training_overlay.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	training_overlay.offset_top = 56
	training_overlay.offset_bottom = 56
	hud.framing_top_overlays.append(training_overlay)
	front = UfeFrontEnd.new()
	ui_layer.add_child(front)
	front.action_requested.connect(_front_action)
	front.hide()
	audio = UfeSideAudio.new()
	add_child(audio)
	audio.configure_battle_music(simulation.fighters.map(func(f):return f.definition.id),view.selected_stage,battle_preferences)
	_fit()

func reset_round() -> void:
	push_error("S2候选固定单局不允许重建；请用新输出目录重启入口")

func _input(_event: InputEvent) -> void:
	pass # 避免F3/F4/R进入正式保存/回放路径；输入只由独立驱动提供。

func _action(_action_name: String) -> void:
	pass

func _front_action(_action_name: String) -> void:
	pass

func play_replay() -> void:
	push_error("候选回放只允许独立入口载原输入带，不写last_replay")

func _finish() -> void:
	for _wait_frame in range(4):
		if pending_stills == 0:break
		await get_tree().process_frame
	var failures: Array = review_driver.get("failures")
	if pending_stills != 0:failures.append({"kind":"pending_screenshot_not_flushed","count":pending_stills})
	review_driver.save_file(review_trace)
	shutdown(0 if failures.is_empty() else 1)

var capture_window_size:=Vector2i(1280,720)
var capture_requests: Dictionary = {}
var capture_previous_process: bool = false
func _physics_process(delta: float) -> void:
	if capture_tick >= review_driver.length_frames():
		if not finishing:
			finishing=true
			set_physics_process(false)
			_finish.call_deferred()
		return
	super._physics_process(delta)
	# 保留正式HUD和训练板，最终真实布局共同取景。
	if review_driver.trace.is_empty() or finishing:return
	var row: Dictionary=review_driver.trace[-1]
	row["training_overlay_visible"]=training_overlay.visible
	var own: Dictionary=row.pair[0]
	var keys: Array=[]
	if str(own.move_id)=="launcher" and int(own.move_tick) in [1,2,3,5,6,8,9,13,14,16,17,19,20,22]:
		keys.append("launcher-tick-%02d-phase-%02d"%[int(own.move_tick),int(own.frame_sprite)])
	elif int(row.movie_frame)==0:keys.append("before-input-idle")
	elif str(own.state)=="idle" and int(row.movie_frame)>20:keys.append("returned-idle")
	if case_kind=="hit":
		var other: Dictionary=row.pair[1]
		if str(other.state)=="launch":keys.append("opponent-launch")
		if int(other.height)>0:keys.append("opponent-airborne")
		if int(other.height)>0 and int(other.vy)<=0:keys.append("opponent-apex")
		if review_driver.trace.size()>1:
			var previous: Dictionary=review_driver.trace[-2].pair[1]
			if int(other.height)>0 and int(other.height)<int(previous.height):keys.append("opponent-descending")
			if int(other.height)==0 and int(previous.height)>0:keys.append("opponent-landed")
		if still_keys.has("opponent-landed") and str(other.state)=="idle":keys.append("opponent-recovered")
	var fresh: Array=[]
	for key in keys:
		if not still_keys.has(key):fresh.append(key)
	if fresh.is_empty():return
	capture_previous_process=is_processing()
	set_process(false)
	set_physics_process(false)
	for key in fresh:
		still_keys[key]=true
		capture_requests[key]={"tick":simulation.tick,"movie_frame":int(row.movie_frame),"sprite":int(own.frame_sprite),"state":str(own.state),"animation_key":str(own.animation.key),"state_hash":simulation.state_hash(),"render_rect":own.animation.rect.duplicate(),"pair":row.pair.duplicate(true)}
		pending_stills+=1
		_save_still.call_deferred(int(row.movie_frame),key)

func _resume_after_capture() -> void:
	pending_stills-=1
	if pending_stills==0 and not finishing:
		set_process(capture_previous_process)
		set_physics_process(true)

func _save_still(frame: int, key: String) -> void:
	if DisplayServer.get_name() == "headless":
		var skipped: Array = review_driver.get("stills")
		var request: Dictionary=capture_requests[key]
		if simulation.tick!=int(request.tick) or simulation.state_hash()!=str(request.state_hash):
			review_driver.failures.append({"kind":"headless_capture_gate_advanced_simulation","request":request,"observed_tick":simulation.tick})
		skipped.append({"movie_frame": frame, "key": key, "captured": false, "reason": "headless_no_graphical_evidence","request":request,"observed_tick":simulation.tick})
		_resume_after_capture()
		return
	await RenderingServer.frame_post_draw
	var expected: Dictionary=capture_requests[key]
	var fighter:=simulation.fighters[0]
	var actual_phase:=int(fighter.frame().sprite)
	var failures: Array=review_driver.get("failures")
	if simulation.tick!=int(expected.tick) or actual_phase!=int(expected.sprite) or fighter.state!=str(expected.state) or simulation.state_hash()!=str(expected.state_hash):
		failures.append({"kind":"capture_phase_changed_while_waiting","expected":expected,"actual_tick":simulation.tick,"actual_sprite":actual_phase})
		_resume_after_capture()
		return
	var sprite: Sprite2D=view.fighters[0]
	var r: Array=expected.render_rect
	var expected_rect:=Rect2(float(r[0]),float(r[1]),float(r[2]),float(r[3]))
	if not sprite.region_enabled or sprite.region_rect!=expected_rect:
		failures.append({"kind":"render_region_does_not_match_requested_phase","expected":r})
		_resume_after_capture()
		return
	for i in range(2):
		var current:=simulation.fighters[i]
		var planned: Dictionary=expected.pair[i]
		var body: Sprite2D=view.fighters[i]
		var rect: Array=[body.region_rect.position.x,body.region_rect.position.y,body.region_rect.size.x,body.region_rect.size.y]
		if current.state!=str(planned.state) or int(current.frame().sprite)!=int(planned.frame_sprite) or not body.region_enabled or rect!=planned.animation.rect:
			failures.append({"kind":"either_fighter_phase_or_region_changed","player":i,"movie_frame":frame})
	# 候选同样核绘制前最终HUD安全区，不能仅用旧trace的屏幕边界冒充避让。
	var safe: Rect2=hud.battle_safe_rect()
	var final_bounds: Array=[]
	for node in view.fighters+view.framing_entities:
		var b: Rect2=view.get_global_transform()*view._sprite_bounds(node)
		final_bounds.append([b.position.x,b.position.y,b.size.x,b.size.y])
		if not safe.grow(0.1).encloses(b):failures.append({"kind":"final_alpha_outside_hud_safe_area","movie_frame":frame,"bounds":final_bounds[-1]})
	if not safe.is_equal_approx(view.framing_safe_rect):failures.append({"kind":"candidate_hud_provider_not_applied","movie_frame":frame})
	expected["final_render_bounds"]=final_bounds
	expected["final_safe_rect"]=[view.framing_safe_rect.position.x,view.framing_safe_rect.position.y,view.framing_safe_rect.size.x,view.framing_safe_rect.size.y]
	expected["hud_safe_rect"]=[safe.position.x,safe.position.y,safe.size.x,safe.size.y]
	expected["hud_visible"]=hud.visible
	expected["training_overlay_visible"]=training_overlay.visible
	var picture: Image = get_viewport().get_texture().get_image()
	var dimensions := Vector2i(picture.get_width(),picture.get_height())
	var window_dimensions: Vector2i = DisplayServer.window_get_size()
	if dimensions!=capture_window_size or dimensions != window_dimensions:
		failures.append({"kind":"unexpected_native_capture_size","image":[dimensions.x,dimensions.y],"window":[window_dimensions.x,window_dimensions.y]})
	var path: String = output_directory.path_join(key+".png")
	assert(not FileAccess.file_exists(path))
	assert(picture.save_png(path) == OK)
	var rows: Array = review_driver.get("stills")
	rows.append({"movie_frame":frame,"key":key,"path":path,"dimensions":[dimensions.x,dimensions.y],
		"window_dimensions":[window_dimensions.x,window_dimensions.y],"resized":false,"format":"PNG",
		"sha256":FileAccess.get_sha256(path),"request":expected,"captured_tick":simulation.tick,"captured_sprite":actual_phase,"simulation_frozen_during_capture":true})
	_resume_after_capture()
