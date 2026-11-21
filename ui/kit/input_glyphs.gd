class_name InputGlyphs
extends HBoxContainer
const BUTTONS={1:"square",2:"triangle",4:"cross",8:"guard",16:"charge",32:"P",64:"circle",128:"I",256:"evade",512:"jump",1024:"form"}
func _init() -> void:
	theme=PixelPanel.NEO_THEME
	add_theme_constant_override("separation",1)
	mouse_filter=Control.MOUSE_FILTER_IGNORE
## directions 为当前方向的候选项，不表示连续方向序列；兼容二参数与四参数调用。
func show_input(direction: int, buttons: int, directions: Array=[], alternatives: bool=false) -> void:
	for child in get_children():remove_child(child);child.queue_free()
	var shown_directions: Array=directions if not directions.is_empty() else [direction]
	for i in range(shown_directions.size()):
		var d: int=int(shown_directions[i])
		if alternatives and i>0:
			var divider:=Label.new();divider.text="/";add_child(divider)
		if int(d)>0:add_child(PixelArt.new("d"+str(d),Vector2(16,16)))
	for mask in BUTTONS:
		if buttons & int(mask):
			var key: String=BUTTONS[mask]
			if key in ["guard","charge","evade","jump","form"]:
				var label:=Label.new();label.text={"guard":"防","charge":"蓄","evade":"闪","jump":"跳","form":"形"}[key];add_child(label)
			else:add_child(PixelArt.new(key,Vector2(16,16)))
