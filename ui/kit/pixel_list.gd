class_name PixelList
extends ScrollContainer
signal item_selected(index: int)
var rows := VBoxContainer.new()
func _init() -> void:
	theme = PixelPanel.NEO_THEME
	horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_child(rows)
func set_items(values: Array) -> void:
	for child in rows.get_children(): child.queue_free()
	for i in range(values.size()):
		var item := PixelButton.new(str(values[i]))
		item.theme_type_variation = "PixelListItem"
		item.alignment = HORIZONTAL_ALIGNMENT_LEFT
		item.clip_text = true
		item.tooltip_text = str(values[i])
		item.pressed.connect(func(): item_selected.emit(i))
		rows.add_child(item)
