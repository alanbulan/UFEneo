extends "res://app/game_app.gd"
## 仍实例化正式main，替换首次训练工厂；无正式角色/资源开关修改。
const Factory = preload("res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/candidate_factory.gd")
const CandidateView = preload("res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/candidate_view.gd")
var candidate_contract: Dictionary = {}
var candidate_contract_path: String = ""
var direction: int = 1
var output_directory: String = ""
var still_keys: Dictionary = {}
var pending_stills: int = 0
var finishing: bool = false

func _battle_match(_first: String, _second: String, _allow_pilot: bool = false) -> UfeMatchDirector:
	return Factory.make_match(candidate_contract,direction)

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
	training_overlay = UfeTrainingOverlay.new()
	ui_layer.add_child(training_overlay)
	training_overlay.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	training_overlay.offset_top = 56
	training_overlay.offset_bottom = 56
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

func _physics_process(delta: float) -> void:
	if capture_tick >= review_driver.length_frames():
		if not finishing:
			finishing = true
			set_physics_process(false)
			_finish.call_deferred()
		return
	super._physics_process(delta)
	if review_driver.trace.is_empty():return
	var row: Dictionary = review_driver.trace[-1]
	var fighter: Dictionary = row.pair[0]
	var key: String = ""
	if str(fighter.state) == "walk":
		var cycle: int = int(fighter.state_tick) / 32
		key = "cycle-%d-phase-%02d" % [cycle,int(fighter.animation.index)]
	elif int(row.movie_frame) in [0,23,112,135]:
		key = "idle-%03d" % int(row.movie_frame)
	if not key.is_empty() and not still_keys.has(key):
		still_keys[key] = true
		pending_stills += 1
		_save_still.call_deferred(int(row.movie_frame),key)

func _save_still(frame: int, key: String) -> void:
	await RenderingServer.frame_post_draw
	var picture: Image = get_viewport().get_texture().get_image()
	if picture.get_width() > 768:
		picture.resize(768,roundi(picture.get_height()*768.0/picture.get_width()),Image.INTERPOLATE_LANCZOS)
	var bytes := picture.save_jpg_to_buffer(0.8)
	while bytes.size() > 150000:
		picture.resize(roundi(picture.get_width()*0.9),roundi(picture.get_height()*0.9),Image.INTERPOLATE_LANCZOS)
		bytes = picture.save_jpg_to_buffer(0.8)
	var path := output_directory.path_join(key+".jpg")
	assert(not FileAccess.file_exists(path))
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file != null)
	file.store_buffer(bytes)
	var still_rows: Array = review_driver.get("stills")
	still_rows.append({"movie_frame":frame,"key":key,"path":path,
		"dimensions":[picture.get_width(),picture.get_height()],"bytes":bytes.size(),"quality":80})
	pending_stills -= 1

func _finish() -> void:
	for _wait_frame in range(4):
		if pending_stills == 0:break
		await get_tree().process_frame
	var failures: Array = review_driver.get("failures")
	if pending_stills != 0:failures.append({"kind":"pending_screenshot_not_flushed","count":pending_stills})
	review_driver.save_file(review_trace)
	shutdown(0 if failures.is_empty() else 1)
