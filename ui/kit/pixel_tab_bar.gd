class_name PixelTabBar
extends HBoxContainer
signal tab_changed(index: int)
var tabs: Array[Button] = []
func set_tabs(values: Array) -> void:
	for child in get_children(): child.queue_free()
	tabs.clear()
	var group := ButtonGroup.new()
	for i in range(values.size()):
		var button := PixelButton.new(str(values[i]))
		button.theme_type_variation = "PixelTab"
		button.toggle_mode = true
		button.button_group = group
		button.button_pressed = i == 0
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.pressed.connect(func(): tab_changed.emit(i))
		add_child(button)
		tabs.append(button)
