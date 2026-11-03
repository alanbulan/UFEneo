class_name UfeSideView
extends Node2D
const GROUND := 304
var simulation: UfeMatchDirector
var show_boxes: bool = false
var camera_x: int = 320
var camera_lift: float = 0.0
var camera_y: int = 0
var camera_zoom: float = 1.0
var framed_bounds := Rect2()
var frame_bounds: Dictionary = {}
var camera_config:Dictionary={}
var fighters: Array[Sprite2D] = []
var manifests: Array = []
var textures: Dictionary = {}
var models: Array = []
var view_configs: Array = []
var loaded_fighter_ids: Array=[]
var backdrop: Sprite2D
var stage_layers: Array = []
var selected_stage: String="coastal-sunset"
var layered_stage: UfeLayeredBattleStage
var debug_overlay: Node2D
var walk_review_clip: String = ""
var projectile_sprites: Array[Sprite2D] = []
var projectile_clips: Dictionary = {}
var weapon_trails: Array[Sprite2D] = []
var projectile_history:=UfeProjectileHistory.new()
var attachment_trail_records:Dictionary={}
var attached_effects: Array[Sprite2D] = []
var attached_slots: Array = [[],[]]
var intro_tick: int = -1
var ending_tick: int = 0
var capture_view := UfeCaptureView.new()
var feedback: UfeCombatFeedback
var cinematic: UfeSuperCinematic
var super_state: UfeSuperStateView
var form_manifests: Dictionary = {}

func _process(_delta: float) -> void:
	if feedback==null:return
	var visible:=feedback.advance_flash(false)
	for i in range(fighters.size()):
		(fighters[i].material as ShaderMaterial).set_shader_parameter("hit_flash",int(visible[i])>0)

func _ready() -> void:
	if FileAccess.file_exists("res://content/presentation/camera_follow.json"):
		camera_config=UfeContentDatabase.read_json("res://content/presentation/camera_follow.json")
	if FileAccess.file_exists("res://content/presentation/phase3_projectiles.json"):
		projectile_clips = UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	layered_stage=UfeLayeredBattleStage.new()
	add_child(layered_stage)
	layered_stage.set_as_top_level(true)
	layered_stage.set_stage(selected_stage)
	backdrop=layered_stage.sky
	for f in simulation.fighters:
		loaded_fighter_ids.append(f.definition.id)
		var data: Dictionary = UfeContentDatabase.read_json("res://content/fighters/%s/definition.json" % f.definition.id)
		var sprite := Sprite2D.new()
		sprite.z_index = 2
		sprite.texture = load(data.presentation.model)
		models.append(sprite.texture)
		view_configs.append(data.presentation)
		sprite.centered = false
		var palette := ShaderMaterial.new()
		palette.shader = preload("res://presentation/timer_palette.gdshader")
		sprite.material = palette
		add_child(sprite)
		fighters.append(sprite)
		var path: String = data.presentation.manifest
		var manifest: Dictionary = UfeContentDatabase.read_json(path) if FileAccess.file_exists(path) else {}
		if fighters.size()==1 and not walk_review_clip.is_empty():
			# 显式主游戏审片入口可读取工程外/开发目录候选；不复制到assets或替换生产清单。
			var candidate: Dictionary=UfeContentDatabase.read_json(walk_review_clip)
			var candidate_action: String=candidate.get("action","walk_forward")
			assert(candidate_action in ["walk_forward","walk_back"],"候选审片仅允许前走和后走")
			manifest.clips[candidate_action] = candidate
		manifests.append(manifest)
		var held_effect := Sprite2D.new()
		var effect_material:=ShaderMaterial.new()
		effect_material.shader=preload("res://presentation/effect_palette.gdshader")
		held_effect.material=effect_material
		held_effect.visible = false
		add_child(held_effect)
		attached_effects.append(held_effect)
		attached_slots[fighters.size()-1].append(held_effect)
	debug_overlay = Node2D.new()
	debug_overlay.z_index = 10
	add_child(debug_overlay)
	debug_overlay.draw.connect(_draw_boxes)
	feedback=UfeCombatFeedback.new()
	add_child(feedback)
	cinematic=UfeSuperCinematic.new()
	add_child(cinematic)
	super_state=UfeSuperStateView.new()
	add_child(super_state)
	super_state.setup(self)
	capture_view.setup()

func bind_match(value: UfeMatchDirector, preserve_feedback: bool = false) -> void:
	if not is_same(simulation,value):
		projectile_history.clear()
		attachment_trail_records.clear()
		if feedback!=null and not preserve_feedback:feedback.reset_match()
	simulation=value
	for i in range(fighters.size()):
		var id:=simulation.fighters[i].definition.id
		if loaded_fighter_ids[i]==id:continue
		var data: Dictionary=UfeContentDatabase.read_json("res://content/fighters/%s/definition.json"%id)
		models[i]=load(data.presentation.model)
		view_configs[i]=data.presentation
		manifests[i]=UfeContentDatabase.read_json(data.presentation.manifest)
		loaded_fighter_ids[i]=id

func set_stage(id: String) -> void:
	selected_stage=UfeBattleStageCatalog.valid_id(id)
	if layered_stage!=null:
		layered_stage.set_stage(selected_stage)
		backdrop=layered_stage.sky

func update_view() -> void:
	if simulation == null: return
	# EX换定义后复用同一套正式加载路径；普通角色不会触发重读。
	if loaded_fighter_ids != simulation.fighters.map(func(f): return f.definition.id): bind_match(simulation)
	camera_x = (simulation.fighters[0].x + simulation.fighters[1].x)/2
	camera_y = 0
	for layer in stage_layers:
		layer.node.position.x = -posmod(int((camera_x-320)*float(layer.parallax)),int(layer.width))
	for i in range(2):
		var f := simulation.fighters[i]
		var sprite := fighters[i]
		var other := simulation.fighters[1-i]
		sprite.visible = not bool(f.frame().get("conceal",false))
		sprite.self_modulate.a = float(f.frame().get("opacity",1.0))
		# 登场暂停模拟，只有显式配置opacity的演出帧覆盖完整精灵透明度。
		if intro_tick>=0 and f.definition.state_frames.has("intro"):
			var intro_frames: Array=f.definition.state_frames["intro"]
			if not intro_frames.is_empty():
				var intro_frame: Dictionary=intro_frames[clampi(intro_tick,0,intro_frames.size()-1)]
				if intro_frame.has("opacity"):sprite.self_modulate.a=float(intro_frame["opacity"])
		# 抱持者整张图在前，两个操作方向使用同一规则，不拆肢体做遮挡。
		sprite.z_index = 3 if (other.state=="thrown" and int(other.combat.thrower)==i) or (other.state=="captured" and int(other.motion.get("capture_victim",{}).get("owner",-1))==i) else 2
		(sprite.material as ShaderMaterial).set_shader_parameter("red_timer",f.definition.id == "ultraman" and int(f.stats.hp)>0 and int(f.stats.hp)<=300 and simulation.tick%30<15)
		var animation := _animation(f, manifests[i])
		if not animation.is_empty():
			var path: String = animation.texture
			if not textures.has(path):
				if not walk_review_clip.is_empty() and path.is_absolute_path() and not path.begins_with("res://"):
					textures[path] = ImageTexture.create_from_image(Image.load_from_file(path))
				else: textures[path] = load(path)
			sprite.texture = textures[path]
			sprite.region_enabled = true
			var rect: Array = animation.rect
			sprite.region_rect = Rect2(rect[0],rect[1],rect[2],rect[3])
			sprite.scale = Vector2.ONE
			var anchor: Array = animation.anchor
			sprite.offset = Vector2(-int(anchor[0]),-int(anchor[1]))
			# 捕获小人的根在剪影中心；偏心裁片朝左时，锚点也须在格内镜像。
			if f.motion.has("capture_victim") and animation.key == "capture_shrinking":
				UfeEffectGeometry.apply_anchor(sprite,{"anchor":anchor},rect,f.facing)
		else:
			sprite.texture = models[i]
			sprite.region_enabled = false
			var native: bool = bool(view_configs[i].get("native",false))
			sprite.scale = Vector2.ONE if native else Vector2(0.5,0.5)
			sprite.offset = Vector2(-sprite.texture.get_width()/2,-int(view_configs[i].get("anchor_y",sprite.texture.get_height()-24)))
		sprite.flip_h = f.facing < 0
		sprite.position = Vector2(f.x-camera_x+320,GROUND-f.height)+capture_view.render_offset(self,i)
	# 抬高镜头时世界向下平移；各背景层沿用原有视差比例。
	backdrop.position.y = 0 # 最远背景沿用原来的零视差；不露出纹理上缘。
	for layer in stage_layers:
		layer.node.position.y = int(layer.base_y)+roundi(camera_y*float(layer.parallax))
	capture_view.sync_events(self)
	feedback.sync(simulation,camera_x,camera_y)
	cinematic.sync(simulation,camera_x,camera_y)
	_update_camera_framing()
	if layered_stage!=null:layered_stage.sync(camera_x,camera_y,cinematic.active,camera_zoom,position)
	backdrop.visible=true # 专用透明星云以最远星空打底，不能露出Viewport默认灰色。
	for layer in stage_layers:layer.node.visible=not cinematic.active
	while projectile_sprites.size()<simulation.projectiles.size():
		var effect := Sprite2D.new()
		var effect_material:=ShaderMaterial.new()
		effect_material.shader=preload("res://presentation/effect_palette.gdshader")
		effect.material=effect_material
		effect.z_index = 3
		add_child(effect)
		projectile_sprites.append(effect)
	for i in range(projectile_sprites.size()):
		var effect := projectile_sprites[i]
		effect.visible = not simulation.finished and i<simulation.projectiles.size()
		if not effect.visible: continue
		var p: Dictionary = simulation.projectiles[i]
		effect.modulate.a=float(p.get("end_alpha",1000))/1000.0
		if bool(p.get("beam",false)):
			effect.visible=false
			continue
		if not projectile_clips.has(p.effect):
			effect.visible = false
			continue
		var clip: Dictionary = UfeEffectGeometry.variant(projectile_clips[p.effect],int(p.get("level",1)))
		var path: String = clip.texture
		if not textures.has(path): textures[path] = load(path)
		effect.texture = textures[path]
		effect.region_enabled = true
		var rect: Array = clip.rects[(int(p.age)/int(clip.ticks))%clip.rects.size()]
		effect.region_rect = Rect2(rect[0],rect[1],rect[2],rect[3])
		effect.position = Vector2(int(p.x)-camera_x+320,GROUND-int(p.height)+camera_y)
		UfeEffectGeometry.apply_anchor(effect,clip,rect,int(p.facing))
		# 斜向原生像素特效由素材决定方向；未声明的既有特效沿用旧旋转。
		effect.rotation = 0.0 if str(clip.get("orientation",""))=="authored" else (PI/4 * (1 if int(p.facing)>0 else -1) if int(p.get("vy",0))<0 else 0.0)
		effect.scale=UfeEffectGeometry.scale_for(p)*UfeEffectGeometry.scale_for(clip)
		effect.z_index=1 if bool(projectile_clips[p.effect].get("behind_fighter",false)) else 3
		var tint: Array = p.get("color",[1,1,1,1])
		(effect.material as ShaderMaterial).set_shader_parameter("palette_tint",Color(float(tint[0]),float(tint[1]),float(tint[2]),float(tint[3])))
	_update_weapon_trails()
	_update_attached_effects()
	super_state.sync(self)
	debug_overlay.queue_redraw()

func attachments_for(i:int) -> Array:
	var f:=simulation.fighters[i]
	var attachments:Array=f.frame().get("attachments",[])
	# 演出与战斗保持原有的取帧时钟；只扩展同一帧中的挂件数量。
	var ceremony:="intro" if intro_tick>=0 else f.state if simulation.finished else ""
	if not ceremony.is_empty() and f.definition.state_frames.has(ceremony):
		var sequence:Array=f.definition.state_frames[ceremony]
		if not sequence.is_empty():
			var ceremony_frame:Dictionary=sequence[clampi(intro_tick if intro_tick>=0 else ending_tick,0,sequence.size()-1)]
			if ceremony_frame.has("attachments"):attachments=ceremony_frame.attachments
	var animation:=_animation(f,manifests[i])
	# 清单附件只补表现；用新数组合并，不能向模拟帧的原数组追加。
	var combined: Array=attachments.filter(func(a):return not a.has("sprite_range") or (int(f.frame().sprite)>=int(a.sprite_range[0]) and int(f.frame().sprite)<=int(a.sprite_range[1])))+animation.get("attachments",[])+capture_view.attachments_for(self,i)
	var other: UfeFighter=simulation.fighters[1-i]
	var holding: bool=other.state=="thrown" and int(other.combat.thrower)==i
	return UfeChargeEffectPolicy.filter(f,manifests[i],combined,holding)

func _update_attached_effects() -> void:
	for i in range(fighters.size()):
		var f := simulation.fighters[i]
		var attachments:=attachments_for(i)
		# 保留原来每人首槽的节点位置与绘制顺序，额外挂件按需扩池。
		while attached_slots[i].size()<attachments.size():
			var extra:=Sprite2D.new()
			var palette:=ShaderMaterial.new()
			palette.shader=preload("res://presentation/effect_palette.gdshader")
			extra.material=palette
			add_child(extra)
			attached_slots[i].append(extra)
			attached_effects.append(extra)
		for slot in range(attached_slots[i].size()):
			var effect:Sprite2D=attached_slots[i][slot]
			effect.visible=slot<attachments.size()
			if not effect.visible:continue
			var a:Dictionary=attachments[slot]
			if not projectile_clips.has(a.effect):
				effect.visible=false
				continue
			var clip:Dictionary=projectile_clips[a.effect]
			effect.scale=UfeEffectGeometry.scale_for(a)*UfeEffectGeometry.scale_for(clip)
			var path:String=clip.texture
			if not textures.has(path):textures[path]=load(path)
			effect.texture=textures[path]
			effect.region_enabled=true
			var r:Array=clip.rects[int(a.sprite)%clip.rects.size()]
			effect.region_rect=Rect2(r[0],r[1],r[2],r[3])
			UfeEffectGeometry.apply_anchor(effect,clip,r,int(a.get("facing",f.facing)))
			effect.z_index=int(a.get("z_index",1 if bool(a.get("behind_fighter",clip.get("behind_fighter",false))) else 3))
			var tint:Array=a.get("color",[1.0,1.0,1.0,1.0])
			(effect.material as ShaderMaterial).set_shader_parameter("palette_tint",Color(float(tint[0]),float(tint[1]),float(tint[2]),float(tint[3])))
			effect.position=Vector2(f.x+int(a.anchor[0])*f.facing-camera_x+320,GROUND-f.height-int(a.anchor[1])+camera_y)

func _update_weapon_trails() -> void:
	var entries: Array=[]
	var legacy_index:int=0
	projectile_history.sync(simulation)
	if not simulation.finished:
		for p in simulation.projectiles:
			# 成对残迹只播一次当前中点，不把双弧图复制到每刃历史点。
			var pair_key: String=str(p.get("pair_trail_effect",""))
			if projectile_clips.has(pair_key):
				for peer in simulation.projectiles:
					if int(peer.owner)!=int(p.owner) or str(peer.move)!=str(p.move) or str(peer.get("weapon_id",""))!=str(p.get("pair_trail_peer_id","")):continue
					if int(peer.life)<=0 or is_same(peer,p):continue
					var point: Array=[(int(p.x)+int(peer.x))/2,(int(p.height)+int(peer.height))/2]
					entries.append({"key":pair_key,"point":point,"age":int(p.age),"facing":int(p.facing),"color":p.get("color",[1,1,1,1]),"native_anchor":true})
					break
			var key:=str(p.get("trail_effect",""))
			if not projectile_clips.has(key):continue
			for point in p.get("trail_points",[]):
				entries.append({"key":key,"point":point,"age":int(p.age),"facing":int(p.facing),"color":p.get("color",[1,1,1,1]),"legacy_index":legacy_index})
				legacy_index+=1
			if not p.has("trail_points"):
				for point in projectile_history.points_for(p):entries.append({"key":key,"point":point,"age":int(p.age),"facing":int(p.facing),"color":p.get("color",[1,1,1,1]),"native_anchor":true})
		entries.append_array(_attachment_trail_entries())
	else:attachment_trail_records.clear()
	while weapon_trails.size()<entries.size():
		var sprite:=Sprite2D.new()
		var palette:=ShaderMaterial.new()
		palette.shader=preload("res://presentation/effect_palette.gdshader")
		sprite.material=palette
		sprite.z_index=2
		add_child(sprite)
		weapon_trails.append(sprite)
	for i in range(weapon_trails.size()):
		var sprite:=weapon_trails[i]
		sprite.visible=i<entries.size()
		if not sprite.visible:continue
		var e: Dictionary=entries[i]
		var clip: Dictionary=projectile_clips[e.key]
		sprite.z_index=1 if bool(clip.get("behind_fighter",false)) else 2
		var path: String=clip.texture
		if not textures.has(path):textures[path]=load(path)
		sprite.texture=textures[path]
		sprite.region_enabled=true
		var phase_index:int=int(e.get("legacy_index",i))
		var phase:int=(UfeEffectTimeline.phase(clip,int(e.age))+phase_index)%clip.rects.size() if bool(e.get("native_anchor",false)) else (int(e.age)/int(clip.ticks)+phase_index)%clip.rects.size()
		var rect: Array=clip.rects[phase]
		sprite.region_rect=Rect2(rect[0],rect[1],rect[2],rect[3])
		if bool(e.get("native_anchor",false)):
			UfeEffectGeometry.apply_anchor(sprite,clip,rect,int(e.facing))
		else:sprite.offset=Vector2.ZERO
		sprite.position=Vector2(int(e.point[0])-camera_x+320,GROUND-int(e.point[1])+camera_y)
		sprite.flip_h=int(e.facing)<0
		sprite.scale=UfeEffectGeometry.scale_for(clip)
		sprite.modulate.a=0.35+0.15*(phase_index%4)
		var tint: Array=e.color
		(sprite.material as ShaderMaterial).set_shader_parameter("palette_tint",Color(float(tint[0]),float(tint[1]),float(tint[2]),float(tint[3])))

func _attachment_trail_entries() -> Array:
	var active:Dictionary={}
	var entries:Array=[]
	for index in range(simulation.fighters.size()):
		var f:=simulation.fighters[index]
		var attachments:=attachments_for(index)
		for slot in range(attachments.size()):
			var a:Dictionary=attachments[slot]
			var trail:=str(a.get("trail_effect",""))
			if not projectile_clips.has(trail):continue
			var key:="%d/%d/%s/%s"%[index,slot,f.move_id,a.effect]
			active[key]=true
			if not attachment_trail_records.has(key):attachment_trail_records[key]={"points":[],"sample_tick":simulation.tick-2,"facing":f.facing}
			var row:Dictionary=attachment_trail_records[key]
			if int(row.facing)!=f.facing:row.points.clear();row.facing=f.facing
			if simulation.tick-int(row.sample_tick)>=2:
				row.points.push_front([f.x+f.facing*int(a.anchor[0]),f.height+int(a.anchor[1])])
				row.sample_tick=simulation.tick
				if row.points.size()>5:row.points.resize(5)
			for point in row.points.slice(1):entries.append({"key":trail,"point":point,"age":f.move_tick,"facing":f.facing,"color":a.get("color",[1,1,1,1]),"native_anchor":true})
	for key in attachment_trail_records.keys():
		if not active.has(key):attachment_trail_records.erase(key)
	return entries

func _sprite_bounds(sprite: Sprite2D) -> Rect2:
	var region := sprite.region_rect if sprite.region_enabled else Rect2(Vector2.ZERO,sprite.texture.get_size())
	var key := "%s:%s" % [sprite.texture.get_instance_id(),region]
	if not frame_bounds.has(key):
		var image := sprite.texture.get_image()
		if image.is_compressed(): image.decompress()
		frame_bounds[key] = image.get_region(Rect2i(region)).get_used_rect()
	var used: Rect2i = frame_bounds[key]
	if sprite.flip_h:used.position.x=int(region.size.x)-used.end.x
	if sprite.flip_v:used.position.y=int(region.size.y)-used.end.y
	return Rect2(sprite.position+(sprite.offset+Vector2(used.position))*sprite.scale,Vector2(used.size)*sprite.scale)

func _update_camera_framing() -> void:
	var bounds := _sprite_bounds(fighters[0])
	for i in range(1,fighters.size()):bounds=bounds.merge(_sprite_bounds(fighters[i]))
	var frame := UfeBattleFraming.fit(bounds,camera_zoom,feedback.shake)
	camera_zoom=float(frame.zoom)
	scale=Vector2.ONE*camera_zoom
	position=frame.origin
	framed_bounds=frame.bounds
	camera_lift=0.0

func _animation(f: UfeFighter, manifest: Dictionary) -> Dictionary:
	# 换定义前也必须播放EX自己的完整变身帧；开放前不会读取未完成素材。
	if f.state=="transform" and str(f.battle_form.get("mode",""))=="definition":
		var form_id: String=f.battle_form.target_definition.id
		if not form_manifests.has(form_id):
			form_manifests[form_id]=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%form_id)
		manifest=form_manifests[form_id]
	if manifest.is_empty(): return {}
	var key := f.animation_key()
	var tick := f.move_tick if not f.move_id.is_empty() else f.state_tick
	if f.move_id.is_empty():
		if f.state == "walk": key = "walk_forward" if f.resolver.previous_x*f.facing > 0 else "walk_back"
		if f.state == "dash":
			var start_ticks := _clip_ticks(manifest.get("clips",{}).get("dash_start",{}))
			var stop_ticks := _clip_ticks(manifest.get("clips",{}).get("dash_stop",{}))
			if tick < start_ticks: key = "dash_start"
			elif tick >= int(f.motion.duration)-stop_ticks:
				key = "dash_stop"
				tick -= int(f.motion.duration)-stop_ticks
			else: tick -= start_ticks
		if f.state == "takeoff" and f.motion.jump_kind == "chase": key = "chase_takeoff"
		if f.state == "air":
			key = "flip_forward" if f.motion.jump_kind == "diagonal" else "flip_back" if f.motion.jump_kind == "backward" else "chase_takeoff" if f.motion.jump_kind == "chase" else "vertical_jump"
			tick = clampi((16-f.vy-2)/8,0,3)*8 if key == "flip_back" else clampi((16-f.vy-2)/8,0,3)*3 if key == "flip_forward" else 16-f.vy
			if bool(manifest.get("clips",{}).get(key,{}).get("trajectory_driven",false)):
				tick = f.definition.jump_speed-f.vy
	var clips: Dictionary = manifest.get("clips", {})
	if intro_tick>=0:
		key="intro"
		tick=intro_tick
	elif f.state in ["victory","defeat","timeout"]:
		key=f.state
		tick=ending_tick
	var grounded_pose: Dictionary=f.motion.get("ko_grounded_pose",{}) if intro_tick<0 and f.state=="defeat" else {}
	if not grounded_pose.is_empty() and clips.has(str(grounded_pose.key)):
		key=str(grounded_pose.key)
		tick=0
	else:grounded_pose={}
	if not clips.has(key): return {}
	var clip: Dictionary = clips[key]
	var total := 0
	for duration in clip.ticks: total += int(duration)
	if bool(clip.get("loop",false)): tick %= maxi(1,total)
	else: tick = mini(tick,total-1)
	var index := 0
	while index < clip.ticks.size()-1 and tick >= int(clip.ticks[index]):
		tick -= int(clip.ticks[index])
		index += 1
	# 走路允许只重排显示时长；模拟中的受击框/回放数据保持原样。
	if intro_tick<0 and f.state not in ["victory","defeat","timeout"] and (not f.move_id.is_empty() or (f.definition.state_frames.has(key) and f.state!="walk") or (f.state=="dash" and f.definition.state_frames.has("dash")) or (f.state=="air" and key in ["vertical_jump","flip_back"])): index = clampi(int(f.frame().sprite)-int(clip.get("simulation_sprite_offset",0)),0,clip.rects.size()-1)
	if f.state=="air" and key=="chase_takeoff":index=clip.rects.size()-1
	if not grounded_pose.is_empty():index=clampi(int(grounded_pose.sprite)-int(clip.get("simulation_sprite_offset",0)),0,clip.rects.size()-1)
	var anchor: Array = clip.anchors[index] if clip.has("anchors") else [int(clip.cell)/2,int(clip.anchor_y)]
	var animation:Dictionary={"key":key,"texture": clip.texture, "index": index,"cell": clip.cell,"anchor_y": clip.anchor_y,"anchor":anchor,"rect":clip.rects[index]}
	if clip.has("attachments_by_frame"):
		var rows:Array=clip.attachments_by_frame
		animation.attachments=rows[index] if index<rows.size() else []
	return animation

func _clip_ticks(clip: Dictionary) -> int:
	var total := 0
	for duration in clip.get("ticks",[]): total += int(duration)
	return total

func _draw_boxes() -> void:
	if not show_boxes or simulation == null: return
	for p in simulation.projectiles:
		for b in UfeProjectileResolver.world_hitboxes(p):
			debug_overlay.draw_rect(Rect2(b.position.x-camera_x+320,GROUND-b.position.y-b.size.y+camera_y,b.size.x,b.size.y),Color("ff5c62"),false,1)
	for f in simulation.fighters:
		var data:=f.frame()
		var ceremony := "intro" if intro_tick>=0 else f.state if simulation.finished else ""
		if f.definition.state_frames.has(ceremony):
			var seq: Array=f.definition.state_frames[ceremony]
			data=seq[clampi(intro_tick if intro_tick>=0 else ending_tick,0,seq.size()-1)]
		if data.has("target") and data.target.get("mode","")=="hold" and simulation.fighters[1-simulation.fighters.find(f)].state=="thrown":
			var grip: Array=data.target.grip
			var at:=Vector2(f.x+f.facing*int(grip[0])-camera_x+320,GROUND-f.height-int(grip[1])+camera_y)
			debug_overlay.draw_circle(at,3,Color("ffd056"),false,1)
		if f.state=="thrown" and data.has("grab_points"):
			var grab: Array=data.grab_points.waist
			var at:=Vector2(f.x+f.facing*int(grab[0])-camera_x+320,GROUND-f.height-int(grab[1])+camera_y)
			debug_overlay.draw_line(at-Vector2(4,0),at+Vector2(4,0),Color("65f593"),1)
			debug_overlay.draw_line(at-Vector2(0,4),at+Vector2(0,4),Color("65f593"),1)
		for category in ["hurtboxes", "hitboxes"]:
			for box in data[category]:
				var world := UfeHitResolver.world_box(f,box)
				var rect := Rect2(world.position.x-camera_x+320,GROUND-world.position.y-world.size.y+camera_y,world.size.x,world.size.y)
				debug_overlay.draw_rect(rect,Color("50d9ff") if category == "hurtboxes" else Color("ff5c62"),false,1)
		if data.has("guard_box"):
			var world := UfeHitResolver.world_box(f,data.guard_box)
			debug_overlay.draw_rect(Rect2(world.position.x-camera_x+320,GROUND-world.position.y-world.size.y+camera_y,world.size.x,world.size.y),Color("ffd056"),false,1)
