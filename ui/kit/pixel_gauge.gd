class_name PixelGauge
extends Control
## 填充只采样套件内芯；外框最后覆盖，左右共用同一条完整轨道。
var bar:=TextureProgressBar.new()
var ghost:=TextureProgressBar.new()
var glow:=NinePatchRect.new()
var delayed: float=1.0
var last_value: float=1.0
var hold: float=0.0
var kind: String
var reverse: bool
var fills: Dictionary={}
func _init(role: String="health", reversed: bool=false) -> void:
	theme=PixelPanel.NEO_THEME
	kind=role
	reverse=reversed
	custom_minimum_size=Vector2(40,16 if role=="health" else 12)
	mouse_filter=Control.MOUSE_FILTER_IGNORE
func inner_texture(key: String) -> Texture2D:
	if not fills.has(key):
		var source: Texture2D=theme.get_icon(key,"NeoKit")
		var interior:=AtlasTexture.new()
		interior.atlas=source
		var horizontal_inset: int=2 if source.get_width()>4 else 0
		var vertical_inset: int=2 if source.get_height()>4 else 0
		interior.region=Rect2(horizontal_inset,vertical_inset,source.get_width()-horizontal_inset*2,source.get_height()-vertical_inset*2)
		interior.filter_clip=true
		fills[key]=interior
	return fills[key]
func _ready() -> void:
	var inset:=MarginContainer.new()
	for side in ["left","right"]:inset.add_theme_constant_override("margin_"+side,6 if kind=="health" else 3)
	for side in ["top","bottom"]:inset.add_theme_constant_override("margin_"+side,3)
	inset.mouse_filter=Control.MOUSE_FILTER_IGNORE
	add_child(inset)
	inset.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var stack:=Control.new()
	stack.clip_contents=true
	stack.mouse_filter=Control.MOUSE_FILTER_IGNORE
	inset.add_child(stack)
	var empty:=TextureRect.new()
	empty.texture=inner_texture("gauge_empty")
	empty.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	empty.stretch_mode=TextureRect.STRETCH_SCALE
	empty.mouse_filter=Control.MOUSE_FILTER_IGNORE
	stack.add_child(empty)
	empty.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for node in [ghost,bar]:
		node.mouse_filter=Control.MOUSE_FILTER_IGNORE
		node.max_value=1.0
		node.step=0
		node.nine_patch_stretch=true
		for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:node.set_stretch_margin(side,0)
		node.fill_mode=TextureProgressBar.FILL_RIGHT_TO_LEFT if reverse else TextureProgressBar.FILL_LEFT_TO_RIGHT
		stack.add_child(node)
		node.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ghost.texture_progress=inner_texture("health_ghost")
	bar.texture_progress=inner_texture(kind+"_fill")
	var frame:=NinePatchRect.new()
	frame.texture=theme.get_icon("health_track_frame" if kind=="health" else kind+"_frame","NeoKit")
	frame.draw_center=false
	for side in [SIDE_LEFT,SIDE_RIGHT]:frame.set_patch_margin(side,6 if kind=="health" else 3)
	for side in [SIDE_TOP,SIDE_BOTTOM]:frame.set_patch_margin(side,3)
	frame.mouse_filter=Control.MOUSE_FILTER_IGNORE
	add_child(frame)
	frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	glow.texture=theme.get_icon("energy_glow","NeoKit")
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:glow.set_patch_margin(side,4)
	glow.mouse_filter=Control.MOUSE_FILTER_IGNORE
	add_child(glow)
	glow.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	glow.hide()
func update_value(value: float, delta: float, tick: int) -> void:
	value=clampf(value,0,1)
	if value<last_value:hold=0.4
	if value>last_value:delayed=value
	if hold>0:hold=maxf(0,hold-delta)
	else:delayed=move_toward(delayed,value,delta*0.65)
	last_value=value
	bar.value=value
	ghost.value=delayed
	ghost.visible=kind=="health" and delayed>value
	glow.visible=kind=="energy" and value>=1.0 and tick%30<21
	if kind=="health":bar.texture_progress=inner_texture("health_red" if value>0 and value<=0.3 and tick%30<15 else "health_fill")
