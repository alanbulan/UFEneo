class_name UfeSuperStateView
extends Node2D
## 只读形态状态；运行时精确查表、GPT光晕裁剪和变身挂件。
var config: Dictionary = {}
var effects: Dictionary = {}
var palettes: Array = [null,null]
var ordinary_materials: Array = [null,null]
var auras: Array[Sprite2D] = []
var layers: Array = [[],[]]
var aura_renderer: UfeSuperStateAura

func setup(view: UfeSideView) -> void:
	config = UfeContentDatabase.read_json("res://content/fighters/ultraman-taro/super_state.json")
	for key in config.effects: effects[key] = UfeContentDatabase.read_json(str(config.effects[key]))
	aura_renderer = UfeSuperStateAura.new(effects.super_aura)
	view.cinematic.effect_clips["transform_cosmo_beam"] = effects.cosmo_beam
	view.feedback.clips["transform_cosmo_hit"] = effects.cosmo_hit
	for i in range(2):
		var aura := Sprite2D.new()
		aura.centered=false; aura.offset=Vector2(-128,-248); aura.z_index=3; aura.visible=false
		var additive := CanvasItemMaterial.new(); additive.blend_mode=CanvasItemMaterial.BLEND_MODE_ADD
		aura.material=additive; add_child(aura); auras.append(aura)
		for j in range(3):
			var layer:=Sprite2D.new(); layer.centered=false; layer.region_enabled=true; layer.visible=false; layer.z_index=4+j
			add_child(layer); layers[i].append(layer)

func super_material(i: int) -> ShaderMaterial:
	if palettes[i] != null: return palettes[i]
	var material := ShaderMaterial.new()
	material.shader=preload("res://presentation/super_state_palette.gdshader")
	var sources := PackedVector3Array(); var targets := PackedVector3Array()
	for entry in config.palette_mapping:
		sources.append(Vector3(entry.source[0],entry.source[1],entry.source[2])/255.0)
		targets.append(Vector3(entry.target[0],entry.target[1],entry.target[2])/255.0)
	while sources.size()<32: sources.append(Vector3.ZERO); targets.append(Vector3.ZERO)
	material.set_shader_parameter("mapping_count",config.palette_mapping.size())
	material.set_shader_parameter("palette_sources",sources)
	material.set_shader_parameter("palette_targets",targets)
	palettes[i]=material
	return material

func show_effect(node: Sprite2D, key: String, age: int, root: Vector2, facing: int) -> void:
	var clip: Dictionary = effects[key]
	var phase := UfeEffectTimeline.phase(clip,age,bool(clip.get("loop",false)))
	var r: Array=clip.rects[phase]
	node.texture=load(str(clip.texture)); node.region_rect=Rect2(r[0],r[1],r[2],r[3])
	node.offset=Vector2(-int(clip.anchor[0]),-int(clip.anchor[1]))
	node.position=root; node.flip_h=facing<0; node.visible=true

func sync(view: UfeSideView) -> void:
	for i in range(2):
		var f := view.simulation.fighters[i]
		var sprite := view.fighters[i]
		for layer in layers[i]: layer.visible=false
		auras[i].visible=false
		var active := f.form_id=="super-taro"
		if active:
			if ordinary_materials[i]==null: ordinary_materials[i]=sprite.material
			var material := super_material(i)
			material.set_shader_parameter("hit_flash",(sprite.material as ShaderMaterial).get_shader_parameter("hit_flash"))
			sprite.material=material
			var phase := UfeEffectTimeline.phase(effects.super_aura,view.simulation.tick,true)
			auras[i].texture=aura_renderer.texture_for(sprite,phase)
			auras[i].position=sprite.position; auras[i].flip_h=f.facing<0
			auras[i].modulate.a=float(config.aura.emission_gain)*(float(88-f.move_tick)/8.0 if f.move_id=="super_special3" and f.move_tick>=80 else 1.0)
			auras[i].visible=true
		elif ordinary_materials[i]!=null:
			(ordinary_materials[i] as ShaderMaterial).set_shader_parameter("hit_flash",(sprite.material as ShaderMaterial).get_shader_parameter("hit_flash"))
			sprite.material=ordinary_materials[i]; ordinary_materials[i]=null
		if f.state=="transform" and f.base_definition.id=="ultraman-taro":
			if f.move_tick>=12 and f.move_tick<60: show_effect(layers[i][0],"brothers_inflow",f.move_tick-12,sprite.position,f.facing)
			if f.move_tick>=42 and f.move_tick<54: show_effect(layers[i][1],"transform_veil",f.move_tick-42,sprite.position,f.facing)
		if f.move_id=="super_special3" and f.move_tick<32 and not bool(f.frame().get("cosmo_start_attached",false)):
			show_effect(layers[i][2],"cosmo_start",f.move_tick,sprite.position+Vector2(f.facing*91,-124),f.facing)
