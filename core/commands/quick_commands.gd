class_name UfeQuickCommands
extends RefCounted
## 原技能的额外输入别名；不复制招式、不开放缺失技能。
const DIRECTIONS := {"motion_236":[6,7],"motion_623":[3,9],"motion_214":[1,4],"motion_22":[2,8],"motion_41236":[5]}

static func extend(table: Array, moves: Dictionary = {}) -> Array:
	var result: Array = table.duplicate(true)
	var seen: Array = []
	for source in table:
		var id := str(source.move)
		if source.motion.is_empty() or not DIRECTIONS.has(id): continue
		var signature := JSON.stringify([id,source.states])
		if signature in seen: continue
		seen.append(signature)
		var entry: Dictionary = source.duplicate(true)
		entry.directions = DIRECTIONS[id].duplicate()
		entry.consume_jump = true
		entry.buttons = UfeInputFrame.SKILL
		entry.motion = []
		entry.quick_skill = true
		if moves.has(id):entry.min_energy=int(moves[id].get("energy_cost",0))
		entry.original_motion = source.motion.duplicate()
		entry.original_buttons = int(source.buttons)
		result.append(entry)
	return result

static func transform(source: Dictionary) -> Dictionary:
	var entry: Dictionary = source.duplicate(true)
	entry.buttons = UfeInputFrame.TRANSFORM
	entry.motion = []
	entry.quick_transform = true
	entry.consume_jump = true
	entry.priority = int(source.priority) + 1
	return entry
