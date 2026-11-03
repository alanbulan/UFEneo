class_name UfeEffectGeometry
extends RefCounted
## 运行时只读比例。非1比例必须是显式声明的整数像素倍数。
static func valid(data: Dictionary) -> bool:
	var value: Variant=data.get("display_scale",[data.get("visual_scale",1),data.get("visual_scale",1)])
	if not value is Array or value.size()!=2:return false
	var unit:=true
	for v in value:
		if not (v is int or v is float) or not is_finite(float(v)) or float(v)<1 or float(v)!=floorf(float(v)):return false
		if float(v)!=1.0:unit=false
		if data.has("visual_scale") and float(v)!=float(data.visual_scale):return false
	return unit or bool(data.get("pixel_integer_scale",false))

static func scale_for(data: Dictionary) -> Vector2:
	assert(valid(data),"特效缩放违规：仅允许1或数据显式标注的整数像素倍数")
	var value: Array=data.get("display_scale",[data.get("visual_scale",1),data.get("visual_scale",1)])
	return Vector2(float(value[0]),float(value[1]))

static func variant(clip: Dictionary,level: int) -> Dictionary:
	return clip.get("variants",{}).get(str(level),clip)

## 持续束只读取每束的模拟世界坐标；不从人物或首束推导第二束的位置。
static func beam_position(projectile: Dictionary, offset: int, camera_x: int, camera_y: int) -> Vector2:
	return Vector2(int(projectile.x)+int(projectile.facing)*offset-camera_x+320,304-int(projectile.height)+camera_y)

## flip_h在裁片矩形内翻转；偏心图集的矩形也必须围绕发射锚点镜像。
## offset仍是原生像素，由Sprite2D.scale统一放大，不能再乘一次display_scale。
static func apply_anchor(sprite: Sprite2D,clip: Dictionary,rect: Array,facing: int) -> void:
	var pivot: Array=clip.get("anchor",[float(rect[2])/2.0,float(rect[3])/2.0])
	var half:=Vector2(float(rect[2])/2.0,float(rect[3])/2.0) if sprite.centered else Vector2.ZERO
	var left:float=-float(pivot[0]) if facing>=0 else float(pivot[0])-float(rect[2])
	sprite.offset=half+Vector2(left,-float(pivot[1]))
	sprite.flip_h=facing<0
