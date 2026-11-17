class_name PortraitFrame
extends Control
var picture := TextureRect.new()
var fighter_id: String=""
func _init() -> void:
	theme = PixelPanel.NEO_THEME
	custom_minimum_size = Vector2(44,44)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
func _ready() -> void:
	var inset := MarginContainer.new()
	for side in ["left","top","right","bottom"]: inset.add_theme_constant_override("margin_"+side,4)
	inset.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(inset)
	inset.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	picture.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inset.add_child(picture)
	var frame := NinePatchRect.new()
	frame.texture = theme.get_icon("portrait","NeoKit")
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]: frame.set_patch_margin(side,6)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(frame)
	frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
func set_fighter(id: String, form_id: String="") -> void:
	id=UfeFighterDisplay.resolved_id(id,form_id)
	if fighter_id==id:return
	fighter_id=id
	picture.texture=UfeFighterDisplay.portrait(id)
	picture.material=UfeFighterDisplay.portrait_material(id)
