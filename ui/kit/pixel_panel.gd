class_name PixelPanel
extends PanelContainer
const NEO_THEME = preload("res://ui/theme/neo_pixel_theme.tres")
func _init(style: String = "panel") -> void:
	theme = NEO_THEME
	theme_type_variation = "PixelPanel" if style == "panel" else "PixelDialog" if style == "dialog" else "PixelToast"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	mouse_filter = Control.MOUSE_FILTER_STOP
