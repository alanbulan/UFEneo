class_name PixelCombo
extends HBoxContainer
var text: String="":
	set(value):
		if text==value:return
		text=value
		for child in get_children():remove_child(child);child.queue_free()
		for digit in value.get_slice(" ",0):
			if digit.is_valid_int():add_child(PixelArt.new("digit_"+digit,Vector2(16,24)))
		if not value.is_empty():
			var label:=Label.new()
			label.text="连击"
			label.add_theme_constant_override("outline_size",2)
			label.add_theme_color_override("font_outline_color",Color("101827"))
			add_child(label)
