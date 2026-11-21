class_name UfeBattleFraming
extends RefCounted
## 只读画面取景；完整像素轮廓共用世界变换，不移动模拟人物。
## 无HUD的独立表现测试保留默认区；正式主游戏必须传入HUD实测可用区。
const SAFE := Rect2(16,62,608,270)

## 经现用附件图集核实的手持实体；只用于attached_slots，不追逐离手投射物。
## 剑/长枪等烘在人物整帧内的武器已由人物Alpha包含，刀光/光束不在此表。
const HELD_ENTITY_EFFECTS := ["red_king_super1_held","red_king_super2_held","red_king_super3_held","red_king_rock_small","red_king_rock_large"]

static func is_held_entity(attachment: Dictionary, clip: Dictionary) -> bool:
	return str(attachment.get("effect","")) in HELD_ENTITY_EFFECTS or bool(attachment.get("framing_entity",clip.get("framing_entity",false)))

static func fit(bounds: Rect2, _previous_zoom: float, shake: Vector2 = Vector2.ZERO, safe: Rect2 = SAFE, _recover_zoom: bool = true, zoom_safe: Rect2 = Rect2()) -> Dictionary:
	# 常驻HUD决定缩放预算；训练信息等临时覆盖层只通过safe平移避让。
	var zoom_area := zoom_safe if zoom_safe.has_area() else safe
	var limit := minf(zoom_area.size.x/maxf(1.0,bounds.size.x),zoom_area.size.y/maxf(1.0,bounds.size.y))
	# 平时锁在1；极端轮廓只用1/2或1/3，不因覆盖层挤压一路缩到1/8。
	var zoom := 1.0
	if limit <= 0.5:
		zoom = 0.5 if limit >= 0.5 - 0.00001 else 1.0 / 3.0
	var low := safe.position-bounds.position*zoom
	var high := safe.end-bounds.end*zoom
	var origin := Vector2(320-bounds.get_center().x*zoom,304*(1.0-zoom))
	origin.x = clampf(origin.x,low.x,maxf(low.x,high.x))
	origin.y = clampf(origin.y,low.y,maxf(low.y,high.y))
	origin += shake
	return {"zoom":zoom,"origin":origin,"bounds":Rect2(bounds.position*zoom+origin,bounds.size*zoom)}
