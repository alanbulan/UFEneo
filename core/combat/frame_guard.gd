class_name UfeFrameGuard
extends RefCounted
## 可选逐帧实体屏；没有这些字段的招式保持既有判定和事件。
static func melee_point(a: UfeFighter, b: UfeFighter, move: Dictionary) -> Variant:
	var frame:=b.frame()
	if str(frame.get("melee_guard",""))!="block":return null
	if str(move.get("kind","")) in ["throw","projectile"] or bool(move.get("unblockable",false)):return null
	if b.state in ["down","thrown","defeat","timeout"] or UfeHitResolver.invulnerable(b):return null
	if (a.x-b.x)*b.facing<0:return null
	var guard: Array=frame.get("guard_box",[])
	if guard.size()!=4:return null
	for box in a.frame().hitboxes:
		var area:=UfeHitResolver.world_box(a,box).intersection(UfeHitResolver.world_box(b,guard))
		if area.has_area():return area.get_center()
	return null

static func block_melee(a: UfeFighter,b: UfeFighter,move: Dictionary) -> void:
	a.combat.connected=true
	UfeStaminaRules.spend(b, UfeStaminaRules.block_cost(int(move.damage)))
	if int(b.stats.stamina)==0:
		b.clear_move()
		b.enter("guardbreak",35)

static func decorate(event: Dictionary, frame: Dictionary, point: Vector2i, facing: int) -> Dictionary:
	# 仅新屏的显式显示字段加入事件，不改变旧屏字典。
	if frame.has("guard_effect") or frame.has("guard_sound"):
		event.x=point.x;event.height=point.y;event.effect_facing=facing
		if frame.has("guard_effect"):event.guard_effect=frame.guard_effect
		if frame.has("guard_sound"):event.guard_sound=frame.guard_sound
	return event
