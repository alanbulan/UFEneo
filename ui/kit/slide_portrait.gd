class_name SlidePortrait
extends Control
## 单个常驻图层：纹理从缓存即时更新，保持不透明并短距滑入。
var art:=PixelArt.new("",Vector2(64,64))
var current_id: String=""
var tween: Tween
func _init() -> void:
	custom_minimum_size=Vector2(64,64)
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	clip_contents=true
	add_child(art)
	art.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
func face_player(player: int) -> void:
	art.face_player(player)
func show_fighter(id: String) -> void:
	if current_id==id:return
	var next:=UfeFighterDisplay.portrait(id)
	if tween!=null and tween.is_running():tween.kill()
	art.texture=next
	art.modulate.a=1
	if not current_id.is_empty():
		art.position.x=2 if not art.flip_h else -2
		tween=create_tween()
		tween.tween_property(art,"position:x",0.0,0.12).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	current_id=id
