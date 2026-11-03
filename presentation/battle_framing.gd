class_name UfeBattleFraming
extends RefCounted
## 只读画面取景；完整像素轮廓共用世界变换，不移动模拟人物。
const SAFE := Rect2(16,62,608,270)

static func fit(bounds: Rect2, previous_zoom: float, shake: Vector2 = Vector2.ZERO) -> Dictionary:
	var limit := minf(1.0,minf(SAFE.size.x/maxf(1.0,bounds.size.x),SAFE.size.y/maxf(1.0,bounds.size.y)))
	# 拉远立即保住新动作/击飞，靠近时缓慢回到正常比例。
	var zoom := minf(limit,lerpf(previous_zoom,limit,0.15))
	zoom = maxf(0.0001,zoom)
	var low := SAFE.position-bounds.position*zoom
	var high := SAFE.end-bounds.end*zoom
	var origin := Vector2(320-bounds.get_center().x*zoom,304*(1.0-zoom))+shake
	origin.x = clampf(origin.x,low.x,maxf(low.x,high.x))
	origin.y = clampf(origin.y,low.y,maxf(low.y,high.y))
	return {"zoom":zoom,"origin":origin,"bounds":Rect2(bounds.position*zoom+origin,bounds.size*zoom)}
