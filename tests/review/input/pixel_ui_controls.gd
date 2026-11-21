class_name UfePixelUIControls
extends UfeReviewDriver
## 正式主游戏事件、设备轮询与训练/F1/F2切换；不直接指定招式或镜头。
const LAYOUT_FRAMES := [95,110,125,145,155,165]
const STILL_FRAMES := [95,110,125,155,235,300]
var checks: Dictionary = {}
var layout_samples: Array = []
var show_debug: bool = false
var current_app: Node
var initial_window := Vector2i.ZERO
var baseline_zoom: float = 1.0

func _init() -> void:
	profile = "phase4_ui_controls"

func length_frames() -> int:
	return 610

func section(_frame: int) -> int:
	return 0

func label(_frame: int) -> String:
	return "实际键盘与鼠标 · W只方向 / Space跳跃 · 训练/F1/F2"

func boxes(_frame: int) -> bool:
	return show_debug

func prepare_match(sim: UfeMatchDirector) -> void:
	# 仅设训练开局资源，使方向技能可由真实按键启动。
	for fighter in sim.fighters:
		fighter.stats.energy = 3000

func sample(_frame: int, _sim: UfeMatchDirector) -> UfeInputFrame:
	return UfeInputRouter.poll(0)

func second_sample(_frame: int) -> UfeInputFrame:
	return UfeInputRouter.poll(1)

func key(_app: Node, code: int, down: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code as Key
	event.physical_keycode = code as Key
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func drive_controls(frame: int, app: Node) -> void:
	current_app = app
	if initial_window == Vector2i.ZERO:
		initial_window = app.get_window().size
	if frame in [15,16]: key(app,KEY_ENTER,frame==15)
	if frame == 20: checks["enter_pauses"] = app.paused and app.hud.menu.visible
	if frame in [25,26]:
		var button: Button = app.hud.menu.get_child(0).get_child(1)
		var native_point := button.get_global_rect().get_center()
		var point: Vector2 = app.image.get_global_transform_with_canvas()*native_point
		var event := InputEventMouseButton.new()
		event.position = point
		event.global_position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = frame==25
		app.get_viewport().push_input(event)
	if frame == 30: checks["scaled_mouse_resume"] = not app.paused and not app.hud.menu.visible
	if frame in [40,41,50,51]: key(app,KEY_F2,frame in [40,50])
	if frame == 45: checks["f2_opens"] = app.paused and app.hud.commands.visible
	if frame == 55: checks["f2_closes"] = not app.paused and not app.hud.commands.visible
	if frame in [70,71,90,91,150,151,160,161]:
		key(app,KEY_F1,frame in [70,90,150,160])
		show_debug = app.view.show_boxes
	if frame == 80: checks["f1_debug_and_boxes"] = app.hud.debug_visible and app.view.show_boxes
	if frame in [105,106,140,141]: key(app,KEY_F3,frame in [105,140])
	if frame in [120,121,130,131]: key(app,KEY_F2,frame in [120,130])
	if frame in [280,360,440,520]: app.reset_round()
	if frame in [200,220,230,232]: key(app,KEY_W,frame in [200,230])
	if frame in [230,231]: key(app,KEY_I,frame==230)
	if frame in [290,291,370,371,450,451]: key(app,KEY_SPACE,frame in [290,370,450])
	if frame in [370,374]: key(app,KEY_D,frame==370)
	if frame in [450,454]: key(app,KEY_A,frame==450)
	if frame in [530,540]: key(app,KEY_UP,frame==530)
	if frame in [550,551]: key(app,KEY_KP_ADD,frame==550)

func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	var fighter := sim.fighters[0]
	var second := sim.fighters[1]
	trace.append({"movie_frame":frame,"tick":sim.tick,"inputs":last_inputs.duplicate(true),
		"state":fighter.state,"move":fighter.move_id,"height":fighter.height,
		"jump_kind":fighter.motion.jump_kind,"p2_height":second.height,
		"camera_zoom":view.camera_zoom,"state_hash":sim.state_hash()})
	if frame == 210:
		checks["w_is_up_only"] = UfeInputRouter.poll(0).y==1 and fighter.height==0 and fighter.state not in ["air","takeoff"]
	if frame == 235:
		checks["w_i_starts_direction_skill"] = fighter.move_id=="motion_22"
		checks["w_i_does_not_jump"] = fighter.height==0
	if frame == 300: checks["space_vertical_jump"] = fighter.height>0 and fighter.motion.jump_kind=="vertical"
	if frame == 380: checks["space_forward_jump"] = fighter.height>0 and fighter.motion.jump_kind=="diagonal"
	if frame == 460: checks["space_backward_jump"] = fighter.height>0 and fighter.motion.jump_kind=="backward"
	if frame == 535:
		checks["p2_up_is_direction_only"] = UfeInputRouter.poll(1).y==1 and second.height==0 and second.state not in ["air","takeoff"]
	if frame == 560: checks["p2_keypad_plus_jumps"] = second.height>0
	if frame in LAYOUT_FRAMES:
		if frame == 95: baseline_zoom = view.camera_zoom
		var window_size: Vector2i = current_app.get_window().size
		var native_size: Vector2i = current_app.viewport.size
		var outer_scale: Vector2 = current_app.image.scale
		checks["layout_%d_native_viewport"%frame] = native_size==Vector2i(640,360)
		checks["layout_%d_keeps_window"%frame] = window_size==initial_window
		checks["layout_%d_keeps_zoom"%frame] = is_equal_approx(view.camera_zoom,baseline_zoom)
		checks["layout_%d_outer_scale"%frame] = outer_scale.is_equal_approx(Vector2(window_size)/Vector2(640,360))
		layout_samples.append({"frame":frame,"training":current_app.training,"paused":current_app.paused,
			"boxes":view.show_boxes,"commands":current_app.hud.commands.visible,
			"training_overlay":current_app.training_overlay.visible,"zoom":view.camera_zoom,
			"window":[window_size.x,window_size.y],"native":[native_size.x,native_size.y],
			"outer_scale":[outer_scale.x,outer_scale.y]})

func capture_still(app: Node, frame: int, directory: String) -> void:
	if frame in STILL_FRAMES:
		_capture_still.call_deferred(app,"%s/ui-controls-%03d.png"%[directory,frame])

func _capture_still(app: Node, path: String) -> void:
	await RenderingServer.frame_post_draw
	var image := app.get_viewport().get_texture().get_image()
	assert(image.save_png(path)==OK,"主游戏输入/界面截图保存失败: "+path)

func save_file(path: String) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null,"无法保存主游戏实际输入检查: "+path)
	file.store_string(JSON.stringify({"profile":profile,"input_source":"主游戏InputEventKey→Input→InputRouter.poll；仅设置训练开局能量，按阶段重开对局，不指定招式/姿势/镜头",
		"checks":checks,"all_passed":not checks.is_empty() and not checks.values().has(false),
		"layout_samples":layout_samples,"trace":trace},"\t"))
