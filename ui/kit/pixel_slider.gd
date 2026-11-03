class_name PixelSlider
extends HSlider
func _init() -> void:
	theme=PixelPanel.NEO_THEME
	min_value=0
	max_value=100
	step=1
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
