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

static func fit(bounds: Rect2, _previous_zoom: float, shake: Vector2 = Vector2.ZERO, safe: Rect2 = SAFE, _recover_zoom: bool = true) -> Dictionary:
	var limit := minf(safe.size.x/maxf(1.0,bounds.size.x),safe.size.y/maxf(1.0,bounds.size.y))
	# 平时锁在 1，像素不随跳跃做非整数缩放。只有轮廓大到需要一半或更小时才改用 1/2、1/3。
	var zoom := 1.0
	if limit <= 0.5:
		var denom := 2
		while denom < 8 and (1.0 / float(denom)) > limit + 0.00001:
			denom += 1
		zoom = 1.0 / float(denom)
	var low := safe.position-bounds.position*zoom
	var high := safe.end-bounds.end*zoom
	var origin := Vector2(320-bounds.get_center().x*zoom,304*(1.0-zoom))
	origin.x = clampf(origin.x,low.x,maxf(low.x,high.x))
	origin.y = clampf(origin.y,low.y,maxf(low.y,high.y))
	origin += shake
	return {"zoom":zoom,"origin":origin,"bounds":Rect2(bounds.position*zoom+origin,bounds.size*zoom)}
