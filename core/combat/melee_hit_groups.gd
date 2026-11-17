class_name UfeMeleeHitGroups
extends RefCounted
const RULE_REVISION := 2
## 显式分段的实体攻击：同一段接触一次，各段独立；飞行物沿用自己的接触寿命。
const INTEGER_FIELDS := ["damage", "chip_damage", "stun", "hitstun", "blockstun", "pushback"]
const BOOLEAN_FIELDS := ["knockdown", "launch", "bounce", "unblockable"]

static func integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value == int(value)

static func validate(move: Dictionary) -> bool:
	if not move.has("hit_groups"):
		for frame in move.frames:
			if frame.has("hit_group") or frame.has("requires_hit_group"): return false
		return true
	if str(move.get("kind", "")) != "strike" or move.has("capture"): return false
	var groups: Variant = move.hit_groups
	if not groups is Dictionary or groups.is_empty(): return false
	var used: Dictionary = {}
	var required_by_group: Dictionary = {}
	var first_tick: Dictionary = {}
	var last_tick: Dictionary = {}
	for key in groups:
		if not key is String or not key.is_valid_int() or str(int(key)) != key or int(key) <= 0: return false
		var overrides: Variant = groups[key]
		if not overrides is Dictionary or overrides.is_empty(): return false
		for field in overrides:
			var value: Variant = overrides[field]
			if field in INTEGER_FIELDS:
				if not integer(value) or (field != "pushback" and int(value) < 0): return false
			elif field in BOOLEAN_FIELDS:
				if not value is bool: return false
			elif field == "level":
				if value not in ["mid", "low", "overhead"]: return false
			else: return false
	for tick in range(move.frames.size()):
		var frame: Dictionary = move.frames[tick]
		if frame.hitboxes.is_empty():
			if frame.has("hit_group") or frame.has("requires_hit_group"): return false
			continue
		var group: Variant = frame.get("hit_group", null)
		if not integer(group) or int(group) <= 0 or not groups.has(str(int(group))): return false
		var key: String = str(int(group))
		var required: Variant = frame.get("requires_hit_group", 0)
		if frame.has("requires_hit_group") and (not integer(required) or int(required)<=0 or int(required)>=int(group) or not groups.has(str(int(required)))): return false
		if required_by_group.has(key) and int(required_by_group[key])!=int(required): return false
		required_by_group[key] = int(required)
		if not first_tick.has(key): first_tick[key] = tick
		last_tick[key] = tick
		used[key] = true
	if used.size()!=groups.size(): return false
	for key in required_by_group:
		var required: int = int(required_by_group[key])
		if required>0 and int(last_tick[str(required)])>=int(first_tick[key]): return false
	return true

static func spent(f: UfeFighter) -> bool:
	var group := int(f.frame().get("hit_group", 0))
	if group <= 0: return bool(f.combat.connected)
	var required: int = int(f.frame().get("requires_hit_group", 0))
	# 仅明确记录的实际hit放行；旧bool去重记录、block和尝试均不算。
	var prior: Variant = f.combat.get("hit_groups", {}).get(str(required), "")
	if required>0 and not (prior is String and prior=="hit"): return true
	return f.combat.get("hit_groups", {}).has(str(group))

static func contact_move(f: UfeFighter, move: Dictionary) -> Dictionary:
	var result := move.duplicate(true)
	var group := str(int(f.frame().get("hit_group", 0)))
	for key in move.get("hit_groups", {}).get(group, {}):
		result[key] = move.hit_groups[group][key]
	return result

static func record(f: UfeFighter, group: int, move_id: String, result: String = "") -> void:
	# 同tick互相打断的接触仍照旧结算，但不能给已清除/已换招的攻击者留下旧段记录。
	if group <= 0 or f.move_id != move_id: return
	if not f.combat.has("hit_groups"): f.combat.hit_groups = {}
	var dependent: bool = f.definition.moves[move_id].frames.any(func(frame): return frame.has("requires_hit_group"))
	# 未启用依赖的旧招仍逐位写旧bool值；新招保存明确实际结果进入快照。
	if dependent:
		f.combat.hit_groups[str(group)] = result
	else:
		f.combat.hit_groups[str(group)] = true
