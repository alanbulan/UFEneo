class_name UfeSuperCinematic
extends Node2D
## 只播放GPT或经用户授权烘焙的PixelFX像素资源，不修改模拟。
var background: Sprite2D
var portrait: Sprite2D
var config: Dictionary = {}
var beam_parts: Array[Sprite2D] = []
var beam_texture: Texture2D
var active: bool=false
var beam_clip: Dictionary={}
var effect_clips: Dictionary={}
func _ready() -> void:
	if FileAccess.file_exists("res://content/presentation/supers.json"):config=UfeContentDatabase.read_json("res://content/presentation/supers.json")
	background=Sprite2D.new()
	background.centered=false
	background.z_index=1
	add_child(background)
	background.set_as_top_level(true)
	portrait=Sprite2D.new()
	portrait.z_index=6
	add_child(portrait)
	portrait.set_as_top_level(true)
	effect_clips=UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	beam_clip=effect_clips.beam_loop
	for i in range(24):
		var s:=Sprite2D.new()
		var material:=ShaderMaterial.new()
		material.shader=preload("res://presentation/effect_palette.gdshader")
		s.material=material
		s.region_enabled=true
		s.centered=false
		s.z_index=4
		add_child(s)
		beam_parts.append(s)
func sync(sim: UfeMatchDirector,camera_x: int,camera_y: int) -> void:
	background.visible=false
	portrait.visible=false
	active=false
	for s in beam_parts:s.visible=false
	for f in sim.fighters:
		if f.move_id not in ["special3","super_special3"] or not config.has(f.definition.id):continue
		background.texture=load(config[f.definition.id].background)
		background.z_index=int(config[f.definition.id].get("background_z_index",1))
		background.visible=true
		active=true
		var stage:=str(f.frame().get("cinematic_stage",""))
		if stage=="portrait":
			portrait.texture=load(config[f.definition.id].portrait)
			if f.move_id=="super_special3": portrait.texture=load("res://assets/effects/ultraman-taro/super_portrait/atlas.png")
			portrait.position=Vector2(148 if f.facing>0 else 492,158)
			portrait.flip_h=f.facing<0
			portrait.visible=true
	var slot:=0
	for p in sim.projectiles:
		if not bool(p.get("beam",false)) or sim.finished:continue
		var length:=int(p.length)
		var source: Dictionary=effect_clips.get(str(p.get("effect","beam_loop")),beam_clip)
		# 本人/原生跨度/档位的显式表现绑定；共享缺省和其它长度继续原资源。
		if p.has("owner"):
			var owner_id: String=sim.fighters[int(p.owner)].definition.id
			source=source.get("beam_fighter_variants",{}).get(owner_id,{}).get("%d:%d" % [int(p.length),int(p.get("level",1))],source)
		var clip:=UfeEffectGeometry.variant(source,int(p.get("level",1)))
		var emission_anchor:bool=bool(source.get("emission_anchor",false))
		var phase:=UfeEffectTimeline.phase(clip,int(p.age),bool(clip.get("loop",true)))
		var r: Array=clip.rects[phase]
		var tile_width:=int(r[2])
		var tint: Array=p.get("color",[1,1,1,1])
		if bool(clip.get("full_frame",source.get("full_frame",false))):
			# 显式完整束：原生整相只用一枚Sprite，不按模拟length裁片或平铺。
			assert(emission_anchor and clip.has("anchor"),"完整束必须声明emission_anchor与实测根点")
			var full_scale:=UfeEffectGeometry.scale_for(clip)
			assert(full_scale==Vector2.ONE,"完整束只允许原生1:1，不拉伸PNG")
			assert(not bool(p.get("clip_below_ground",false)),"完整横束不能绑定地线裁行协议")
			if slot>=beam_parts.size():break
			var full_sprite:=beam_parts[slot]
			full_sprite.texture=load(clip.texture)
			full_sprite.region_rect=Rect2(int(r[0]),int(r[1]),int(r[2]),int(r[3]))
			full_sprite.scale=full_scale
			full_sprite.rotation=0.0
			UfeEffectGeometry.apply_anchor(full_sprite,clip,r,int(p.facing))
			full_sprite.position=UfeEffectGeometry.beam_position(p,0,camera_x,camera_y)
			(full_sprite.material as ShaderMaterial).set_shader_parameter("palette_tint",Color.WHITE)
			full_sprite.modulate.a=float(p.get("end_alpha",1000))/1000.0
			full_sprite.visible=true
			slot+=1
			continue
		for offset in range(0,length,tile_width):
			if slot>=beam_parts.size():break
			var s:=beam_parts[slot]
			s.texture=load(clip.texture)
			(s.material as ShaderMaterial).set_shader_parameter("palette_tint",Color(float(tint[0]),float(tint[1]),float(tint[2]),float(tint[3])))
			var width:=mini(tile_width,length-offset)
			s.region_rect=Rect2(int(r[0]),int(r[1]),width,int(r[3]))
			s.scale=UfeEffectGeometry.scale_for(clip)
			s.flip_h=int(p.facing)<0
			if emission_anchor:
				# 仅显式启用的发射图集：像素锚随裁片镜像，scale由Sprite2D统一应用。
				var pivot:Array=clip.get("anchor",[0,int(r[3])/2])
				s.offset=Vector2(-int(pivot[0]) if int(p.facing)>0 else int(pivot[0])-width,-int(pivot[1]))
				s.position=UfeEffectGeometry.beam_position(p,offset,camera_x,camera_y)
			else:
				s.offset=Vector2.ZERO
				s.position=UfeEffectGeometry.beam_position(p,offset+(0 if int(p.facing)>0 else width),camera_x,camera_y)-Vector2(0,int(r[3])/2)
			if str(p.effect)=="transform_cosmo_beam": s.position.x-=int(p.facing)*16
			s.visible=true
			s.modulate.a=float(p.get("end_alpha",1000))/1000.0
			if bool(p.get("clip_below_ground",false)):
				# 只裁原图底行，含世界高度0的地线像素；原点、锚、缩放与横向轮廓保持。
				var rows:=clampi(floori((304+camera_y-s.position.y)/s.scale.y-s.offset.y)+1,0,int(r[3]))
				s.region_rect.size.y=rows
				s.visible=rows>0
			slot+=1
