class_name InputGlyphs
extends HBoxContainer
const BUTTONS={1:"square",2:"triangle",4:"cross",8:"guard",16:"charge",32:"P",64:"circle",128:"I",256:"evade",1024:"skill",2048:"form"}
func _init() -> void:
	theme=PixelPanel.NEO_THEME
	add_theme_constant_override("separation",1)
	mouse_filter=Control.MOUSE_FILTER_IGNORE
func show_input(direction: int, buttons: int, motion: Array=[], alternatives: bool=false) -> void:
	for child in get_children():remove_child(child);child.queue_free()
	var directions: Array=motion if not motion.is_empty() else [direction]
	for i in range(directions.size()):
		var d: int=int(directions[i])
		if alternatives and i>0:
			var divider:=Label.new();divider.text="/";add_child(divider)
		if int(d)>0:add_child(PixelArt.new("d"+str(d),Vector2(16,16)))
	for mask in BUTTONS:
		if buttons & int(mask):
			var key: String=BUTTONS[mask]
			if key in ["guard","charge","evade","skill","form"]:
				var label:=Label.new();label.text={"guard":"防","charge":"蓄","evade":"闪","skill":"技","form":"形"}[key];add_child(label)
			else:add_child(PixelArt.new(key,Vector2(16,16)))
