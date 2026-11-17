class_name SelectCursor
extends NinePatchRect
func _init(player: int = 0) -> void:
	theme = PixelPanel.NEO_THEME
	texture = theme.get_icon("cursor_red" if player == 0 else "cursor_blue","NeoKit")
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]: set_patch_margin(side,8)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
