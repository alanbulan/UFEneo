class_name PixelVS
extends Control
signal sound_requested(id: String, owner: int)
## 位置由父容器分配；这里只对容器中的内容作0.36秒入场变换。
var age: float=0
var portraits: Array=[]
var symbol:=PixelArt.new("vs",Vector2(96,72))
var heights: Array=[144,166]
var intro_clips: Array=[{},{}]
var frame_atlases: Array=[[],[]]
func _init(ids: Array=["ultraman","zetton"]) -> void:
	size_flags_vertical=Control.SIZE_EXPAND_FILL
	size_flags_horizontal=Control.SIZE_EXPAND_FILL
	var column:=VBoxContainer.new();column.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(column)
	var center:=CenterContainer.new();column.add_child(center);center.add_child(symbol)
	var row:=HBoxContainer.new();row.size_flags_vertical=Control.SIZE_EXPAND_FILL
	row.add_theme_constant_override("separation",4)
	column.add_child(row)
	for i in range(2):
		var slot:=Control.new();slot.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(slot)
		var art:=PixelArt.new()
		var texture: Texture2D=UfeFighterDisplay.model(str(ids[i]))
		# 同一像素倍率显示两个完整定稿：透明画布大小不参与人物身高匹配。
		var atlas:=AtlasTexture.new();atlas.atlas=texture
		var image:=texture.get_image();var bounds:=image.get_used_rect()
		atlas.region=bounds;art.texture=atlas
		art.set_meta("native_height",bounds.size.y)
		art.set_meta("foot_anchor",Vector2(texture.get_width()/2.0-bounds.position.x,bounds.size.y))
		art.set_meta("side_extents",Vector2(texture.get_width()/2.0-bounds.position.x,bounds.end.x-texture.get_width()/2.0))
		art.face_player(i)
		heights[i]=bounds.size.y
		slot.add_child(art);art.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		portraits.append(art)
		# 有正式登场帧时在同一脚底锚点播放，仍保持两人的统一原生像素倍率。
		var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%ids[i])
		if manifest.get("clips",{}).has("intro"):
			intro_clips[i]=manifest.clips.intro
			var clip: Dictionary=intro_clips[i]
			var clip_texture: Texture2D=load(clip.texture)
			var atlas_image: Image=clip_texture.get_image()
			for source_rect in clip.rects:
				var cached_frame:=AtlasTexture.new();cached_frame.atlas=clip_texture
				cached_frame.region=Rect2(source_rect[0],source_rect[1],source_rect[2],source_rect[3])
				frame_atlases[i].append(cached_frame)
			var extents:=Vector2.ZERO
			for index in range(clip.rects.size()):
				var rect: Array=clip.rects[index]
				var used:=atlas_image.get_region(Rect2i(rect[0],rect[1],rect[2],rect[3])).get_used_rect()
				@warning_ignore("integer_division")
				var anchor: Array=clip.anchors[index] if clip.has("anchors") else clip.get("anchor",[int(rect[2])/2,int(clip.anchor_y)])
				extents.x=maxf(extents.x,int(anchor[0])-used.position.x)
				extents.y=maxf(extents.y,used.end.x-int(anchor[0]))
			art.set_meta("side_extents",extents)
		var native_sides: Vector2=art.get_meta("side_extents")
		slot.size_flags_stretch_ratio=maxf(1,native_sides.x+native_sides.y+4)
	# 长尾角色按实际占宽分配容器；VS放在上方，不遮住头角，也不占横向空间。
func _ready() -> void:
	var shared_entry_played:bool=false
	for owner_index in range(intro_clips.size()):
		var clip:Dictionary=intro_clips[owner_index]
		for event in clip.get("audio_events",[]):
			if event.get("kind","")!="sound":continue
			var id:String=str(event.id)
			# entry是共用页面入场音；本人角色声仍按双方各自触发。
			if id=="entry":
				if shared_entry_played:continue
				shared_entry_played=true
			sound_requested.emit(id,owner_index)
func _process(delta: float) -> void:
	age+=delta
	var progress:=clampf(age/0.36,0,1)
	var eased:=1-pow(1-progress,3)
	# 两图按同一倍率、脚底齐平；杰顿166px自然高于初代144px。
	var scale_factor:=maxf(1,floorf(minf((size.y-8)/float(maxi(heights[0],heights[1])),2)))
	for art in portraits:
		var extents: Vector2=art.get_meta("side_extents")
		scale_factor=minf(scale_factor,maxf(1,floorf((art.get_parent().size.x-8)/(extents.x+extents.y))))
		scale_factor=minf(scale_factor,maxf(1,floorf((art.get_parent().size.y-4)/float(maxi(heights[0],heights[1])))))
	for i in range(2):
		var art: PixelArt=portraits[i]
		if not intro_clips[i].is_empty():
			var clip: Dictionary=intro_clips[i];var total:=0
			for duration in clip.ticks:total+=int(duration)
			var tick:=mini(int(age*60),total-1);var index:=0
			for duration in clip.ticks:
				if tick<int(duration):break
				tick-=int(duration);index+=1
			index=mini(index,clip.rects.size()-1)
			art.texture=frame_atlases[i][index]
			var cell_width: int=int(clip.cell[0]) if clip.cell is Array else int(clip.cell)
			@warning_ignore("integer_division")
			var anchor: Array=clip.anchors[index] if clip.has("anchors") else clip.get("anchor",[cell_width/2,int(clip.anchor_y)])
			art.set_meta("foot_anchor",Vector2(int(anchor[0]),int(anchor[1])))
		var slot: Control=art.get_parent()
		var native: Vector2=art.texture.get_size()
		var display:=native*scale_factor
		var extents: Vector2=art.get_meta("side_extents")
		if art.flip_h:extents=Vector2(extents.y,extents.x)
		var root_x:=clampf(slot.size.x/2,extents.x*scale_factor+4,slot.size.x-extents.y*scale_factor-4)
		var base:=Vector2(root_x,slot.size.y)-art.displayed_foot_anchor()*scale_factor
		art.set_anchors_preset(Control.PRESET_TOP_LEFT)
		art.position=base+Vector2((-1 if i==0 else 1)*slot.size.x*(1-eased),0)
		art.size=display
		art.modulate.a=clampf(progress*3,0,1)
	symbol.pivot_offset=symbol.size/2
	var drop:=clampf((age-0.08)/0.24,0,1)
	symbol.scale=Vector2.ONE*lerpf(1.45,1.0,1-pow(1-drop,3))
	symbol.position.y=symbol.get_parent().size.y/2-symbol.size.y/2-36*(1-drop)
	symbol.modulate=Color(1.7,1.7,1.7,1) if age>=0.26 and age<0.31 else Color.WHITE
