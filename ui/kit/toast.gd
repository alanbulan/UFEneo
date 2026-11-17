class_name Toast
extends PixelPanel
var label := Label.new()
var remaining: float = 0
func _init() -> void:
	super("toast")
	mouse_filter = Control.MOUSE_FILTER_IGNORE
func _ready() -> void:
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(label)
	hide()
func show_message(value: String, seconds: float = 2.0) -> void:
	label.text = value
	remaining = seconds
	show()
func _process(delta: float) -> void:
	if remaining > 0:
		remaining -= delta
		if remaining <= 0: hide()
