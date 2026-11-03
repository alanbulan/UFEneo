class_name UfePixelUIControls
extends UfeReviewDriver
## 主游戏实际事件分发验证：Enter/F2/F1及整数缩放后的鼠标按钮。
var checks: Dictionary={}
var result_path: String="res://reports/ui-controls.json"
var show_debug: bool=false
func _init() -> void: profile="phase4_ui_controls"
func length_frames() -> int: return 110
func section(_frame: int) -> int: return 0
func boxes(_frame: int) -> bool: return show_debug
func key(app: Node, code: int, down: bool) -> void:
	var event:=InputEventKey.new()
	event.keycode=code
	event.physical_keycode=code
	event.pressed=down
	app.get_viewport().push_input(event)
func drive_controls(frame: int, app: Node) -> void:
	if frame in [15,16]: key(app,KEY_ENTER,frame==15)
	if frame==20: checks["enter_pauses"]=app.paused and app.hud.menu.visible
	if frame in [25,26]:
		var button: Button=app.hud.menu.get_child(0).get_child(1)
		var native_point:=button.get_global_rect().get_center()
		var point: Vector2=app.image.get_global_rect().position+native_point*app.image.stretch_shrink
		var event:=InputEventMouseButton.new()
		event.position=point
		event.global_position=point
		event.button_index=MOUSE_BUTTON_LEFT
		event.pressed=frame==25
		app.get_viewport().push_input(event)
	if frame==30: checks["scaled_mouse_resume"]=not app.paused and not app.hud.menu.visible
	if frame in [40,41,50,51]: key(app,KEY_F2,frame in [40,50])
	if frame==45: checks["f2_opens"]=app.paused and app.hud.commands.visible
	if frame==55: checks["f2_closes"]=not app.paused and not app.hud.commands.visible
	if frame in [70,71]:
		key(app,KEY_F1,frame==70)
		show_debug=app.view.show_boxes
	if frame==80:
		checks["f1_debug_and_boxes"]=app.hud.debug_visible and app.view.show_boxes
		checks["native_viewport"]=app.viewport.size==Vector2i(640,360)
	if frame==100:
		var out:=FileAccess.open(result_path,FileAccess.WRITE)
		out.store_string(JSON.stringify({"checks":checks,"resolution":[app.size.x,app.size.y],"all_passed":not checks.values().has(false)},"\t"))
