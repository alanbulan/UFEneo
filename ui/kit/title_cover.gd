extends Control
## 主菜单专用封面：GPT 新绘整幅群像与独立像素标题。
## 只移动完整美术层；不修改人物像素、战斗资源或可玩状态。
var age: float=0.0
var ensemble: PixelArt
var logo_layers: Array=[]
var logo_slices: Array=[]
var glints: Array=[]
var nebula: PixelArt

func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	clip_contents=true
	ensemble=PixelArt.new()
	ensemble.texture=preload("res://assets/ui/title-cover/ensemble.png")
	add_child(ensemble)
	# GPT 生成的星云层从标题后方掠过；不用程序粒子或绘制线条。
	nebula=PixelArt.new("stars_near")
	add_child(nebula)
	nebula.modulate=Color(0.65,0.8,1.0,0.22)
	for i in range(3):
		var logo:=PixelArt.new("logo")
		add_child(logo);logo_layers.append(logo)
		if i<2:logo.modulate=Color(0.36,0.67,1.0,0.0)
	# 标题本身的像素横片错时冲入，完成后还原完整纹理。
	# 这是UI标题美术的入场，不切割或重组任何人物。
	var title_source: Texture2D=PixelPanel.NEO_THEME.get_icon("logo","NeoKit")
	for bounds in [Vector2i(0,20),Vector2i(20,21),Vector2i(41,20),Vector2i(61,21)]:
		var atlas:=AtlasTexture.new();atlas.atlas=title_source
		atlas.region=Rect2(0,bounds.x,195,bounds.y)
		var piece:=PixelArt.new();piece.texture=atlas
		piece.stretch_mode=TextureRect.STRETCH_SCALE
		add_child(piece);logo_slices.append({"art":piece,"bounds":bounds})
	# 高光来自同一张已生成星云中的亮星，完整纹理小块复用。
	var stars: Texture2D=PixelPanel.NEO_THEME.get_icon("stars_near","NeoKit")
	for i in range(3):
		var atlas:=AtlasTexture.new();atlas.atlas=stars
		atlas.region=Rect2(506,77,31,31)
		var glint:=PixelArt.new();glint.texture=atlas
		add_child(glint);glints.append(glint)

func _process(delta: float) -> void:
	if not is_visible_in_tree():return
	age+=delta
	var unit:=size/Vector2(640,326)
	# 等比fit完整透明安全边，不裁头角或脚端。
	var native:=ensemble.texture.get_size()
	var fit:=minf(1.0,minf(size.x/native.x,size.y/native.y))
	ensemble.size=native*fit
	ensemble.position=Vector2(size.x-ensemble.size.x,0).round()
	var reveal:=clampf((age-0.85)/1.15,0.0,1.0)
	ensemble.modulate.a=1.0-pow(1.0-reveal,3.0)
	# 整幅场景只做一原生像素的慢速视差，安全透明边保全。
	ensemble.position+=Vector2(roundf(sin(age*0.30)),roundf(sin(age*0.23)))
	nebula.size=Vector2(240,100)*unit
	var sweep:=fmod(maxf(0.0,age-1.2),7.5)
	var sweep_progress:=clampf(sweep/1.8,0.0,1.0)
	nebula.position=(Vector2(-18+sweep_progress*38,-4)*unit).round()
	nebula.modulate.a=0.10+sin(sweep_progress*PI)*0.28
	var settled:=clampf((age-0.25)/0.85,0.0,1.0)
	var ease:=1.0-pow(1.0-settled,4.0)
	# 中央大标题先成形，再收至安全角；群像同步显现。
	var dock:=clampf((age-1.15)/0.80,0.0,1.0)
	var dock_ease:=1.0-pow(1.0-dock,4.0)
	for i in range(logo_layers.size()):
		var logo: PixelArt=logo_layers[i]
		logo.size=Vector2(390,164).lerp(Vector2(195,82),dock_ease).round()
		var center: Vector2=(size-logo.size)/2.0-Vector2(0,18)
		logo.position=(center.lerp(Vector2(-4,-7)*unit,dock_ease)-Vector2(0,18*(1.0-ease))).round()
		logo.pivot_offset=logo.size/2.0
		if i==2:
			logo.scale=Vector2.ONE
			logo.modulate.a=clampf((age-0.95)/0.20,0.0,1.0)
		else:
			logo.scale=Vector2.ONE*(1.0+(1.0-ease)*(0.12+0.08*i))
			logo.position.x+=(-1 if i==0 else 1)*roundf((1.0-ease)*22.0)
			logo.modulate.a=(1.0-ease)*settled*0.48+(0.06+sin(age*0.9)*0.025 if i==0 and age>1.15 else 0.0)
	var title_rect: PixelArt=logo_layers[2]
	var pixel_scale:=minf(title_rect.size.x/195.0,title_rect.size.y/82.0)
	var origin:=title_rect.position+(title_rect.size-Vector2(195,82)*pixel_scale)/2.0
	for i in range(logo_slices.size()):
		var piece: PixelArt=logo_slices[i].art
		var bounds: Vector2i=logo_slices[i].bounds
		var phase:=clampf((age-0.12-i*0.10)/0.65,0.0,1.0)
		var eased:=1.0-pow(1.0-phase,4.0)
		piece.visible=age<1.15
		piece.size=Vector2(195,bounds.y)*pixel_scale
		piece.position=(origin+Vector2((1.0-eased)*(38 if i%2==0 else -38),bounds.x*pixel_scale)).round()
		piece.modulate.a=phase*(1.0-clampf((age-0.95)/0.20,0.0,1.0))
	# 低频两秒掠光，间隔约六秒；不持续闪白或污染选项。
	var cycle:=fmod(maxf(0.0,age-1.2),7.5)
	for i in range(glints.size()):
		var star: PixelArt=glints[i]
		var phase:=clampf((cycle-i*0.18)/1.8,0.0,1.0)
		star.size=Vector2(17,17)*unit
		star.position=(origin+Vector2((12+phase*168)*pixel_scale,(28-i*7)*pixel_scale)).round()
		star.modulate.a=sin(phase*PI)*0.7 if age>1.2 else 0.0
