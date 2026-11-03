class_name PixelButton
extends Button
var caption: Label
func _init(value: String = "") -> void:
	theme = PixelPanel.NEO_THEME
	theme_type_variation = "PixelButton"
	text = value
	custom_minimum_size.y = 28
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

func _ready() -> void:
	# Button的focus纹理最后绘制；子Label在所有纹理之上，原文字保持布局/可访问名称。
	caption=Label.new()
	caption.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	PixelTextBounds.layout(self,caption)
	caption.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	caption.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
	caption.mouse_filter=Control.MOUSE_FILTER_IGNORE
	caption.add_theme_color_override("font_color",Color.WHITE)
	caption.add_theme_color_override("font_outline_color",Color("101827"))
	caption.add_theme_constant_override("outline_size",2)
	add_child(caption)
	for state in ["font_color","font_hover_color","font_pressed_color","font_focus_color","font_disabled_color","font_hover_pressed_color"]:
		add_theme_color_override(state,Color.TRANSPARENT)
	_refresh_caption()

func _process(_delta: float) -> void: _refresh_caption()
func _refresh_caption() -> void:
	if caption==null:return
	caption.text=text
	caption.horizontal_alignment=alignment
	caption.modulate=Color("8794a6") if disabled else Color.WHITE
	caption.text_overrun_behavior=TextServer.OVERRUN_NO_TRIMMING
	if not text.is_empty():
		var margin:=PixelTextBounds.insets(self)
		custom_minimum_size.x=maxf(custom_minimum_size.x,caption.get_minimum_size().x+margin.x+margin.z+4)
		custom_minimum_size.y=maxf(custom_minimum_size.y,caption.get_minimum_size().y+margin.y+margin.w+4)
