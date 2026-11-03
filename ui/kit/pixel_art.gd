class_name PixelArt
extends TextureRect
func _init(key: String="", target: Vector2=Vector2.ZERO) -> void:
	theme=PixelPanel.NEO_THEME
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	custom_minimum_size=target
	if not key.is_empty():texture=theme.get_icon(key,"NeoKit")

## 素材统一朝右；只镜像纹理，不对容器施加负缩放或改变标签布局。
func face_player(player: int) -> void:
	flip_h=player==1
	set_meta("display_player",player)

func displayed_foot_anchor() -> Vector2:
	var anchor: Vector2=get_meta("foot_anchor",Vector2(texture.get_width()/2.0,texture.get_height()))
	return Vector2(texture.get_width()-anchor.x if flip_h else anchor.x,anchor.y)
