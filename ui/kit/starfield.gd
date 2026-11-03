class_name PixelStarfield
extends Control
var layers: Array=[]
var age: float=0
func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	clip_contents=true
	var backdrop:=PixelArt.new("",Vector2(640,360))
	backdrop.texture=preload("res://assets/ui/backgrounds/neo.png")
	add_child(backdrop)
	for key in ["stars_far","stars_near"]:
		var strip:=HBoxContainer.new()
		strip.add_theme_constant_override("separation",0)
		strip.mouse_filter=Control.MOUSE_FILTER_IGNORE
		add_child(strip)
		for i in range(2):strip.add_child(PixelArt.new(key,Vector2(640,360)))
		layers.append(strip)
func _process(delta: float) -> void:
	age+=delta
	for i in range(layers.size()):layers[i].position.x=-floori(fmod(age*(i+1)*3,640))
