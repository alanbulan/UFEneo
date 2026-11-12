class_name UfeBattleTransform
extends RefCounted
## 纯整数规则。开放表、定义和逐tick演出数据由装配层注入。
const ENERGY_COST := 3000

static func is_command(id: String) -> bool:
	return id == "battle_transform" or id.begins_with("battle_transform__")

static func _choices(f: UfeFighter) -> Dictionary:
	if not f.battle_form_choices.is_empty(): return f.battle_form_choices
	# 关闭/非法配置的原表仍带Array型choices，不能当选择表。
	var choices = f.battle_form.get("choices", {})
	return choices if choices is Dictionary else {}

# 传入空 move_id 表示“任选一个已开放形态”；单形态角色沿用原 battle_transform 判定。
static func can_transform(f: UfeFighter, move_id: String = "battle_transform") -> bool:
	var root := _choices(f)
	if move_id.is_empty():
		if root.is_empty(): return _can_transform(f, root, "battle_transform")
		var keys: Array = root.keys(); keys.sort()
		for key in keys:
			if _can_transform(f, root, str(key)): return true
		return false
	return _can_transform(f, root, move_id)

static func _can_transform(f: UfeFighter, root: Dictionary, move_id: String) -> bool:
	if not bool(f.battle_form.get("enabled", false)) or int(f.stats.hp) <= 0: return false
	if root.is_empty():
		return move_id == "battle_transform" and not f.transformed_this_round \
			and int(f.stats.energy) >= ENERGY_COST \
			and int(f.stats.hp) * 2 <= f.base_definition.max_health
	if not root.has(move_id): return false
	var target: Dictionary = root[move_id]
	if bool(target.get("free_switch", false)):
		# E 独立切已开放形态：不耗气、每局不限次数，但切到当前形态不重播。
		var target_definition: UfeFighterDefinition = target.get("target_definition")
		return target_definition == null or target_definition.id != f.definition.id
	return not f.transformed_this_round \
		and int(f.stats.energy) >= ENERGY_COST \
		and int(f.stats.hp) * 2 <= f.base_definition.max_health

static func begin(f: UfeFighter, move_id: String = "battle_transform") -> void:
	var root := _choices(f)
	if root.has(move_id): f.battle_form = root[move_id]
	if not bool(f.battle_form.get("free_switch", false)):
		f.stats.energy = int(f.stats.energy) - ENERGY_COST
		f.transformed_this_round = true
	f.clear_move()
	f.combat.buffer = ""
	f.combat.buffer_ticks = 0
	f.motion.jump_buffer = 0
	f.motion.chase_window = 0
	f.vx = 0
	f.vy = 0
	# 独立ID进入既有buffer和快照，演出中改方向不会改变所选形态。
	f.move_id = move_id
	f.enter("transform")

static func advance(f: UfeFighter) -> void:
	f.combat.buffer = ""
	f.combat.buffer_ticks = 0
	f.motion.jump_buffer = 0
	if f.state == "form_entry":
		if f.state_tick >= f.battle_form.get("entry_frames", []).size(): f.enter("idle")
		return
	f.move_tick = f.state_tick
	if str(f.battle_form.mode) == "palette" and f.state_tick >= int(f.battle_form.palette_switch_tick):
		f.form_id = str(f.battle_form.id)
	if f.state_tick < f.definition.moves[f.move_id].frames.size(): return
	f.clear_move()
	f.form_id = str(f.battle_form.id)
	if str(f.battle_form.mode) == "definition":
		# 同一Fighter对象保留体力、扣费后能量、位置、朝向、连段和本局计分。
		f.definition = f.battle_form.target_definition
		f.enter("form_entry" if not f.battle_form.get("entry_frames", []).is_empty() else "idle")
	else:
		f.enter("idle")

static func after_move_tick(f: UfeFighter) -> void:
	if f.move_id == "super_special3" and f.move_tick >= int(f.battle_form.get("revert_tick", 88)):
		f.form_id = ""

static func round_end(_f: UfeFighter) -> void:
	# 2026-11-01用户裁定：当前具体形态贯穿KO/胜负结算，新局由reset重新构造。
	pass

static func simulation_data(form: Dictionary) -> Array:
	if form.is_empty(): return []
	if not bool(form.get("enabled", false)): return [form.id, false]
	var target: UfeFighterDefinition = form.get("target_definition")
	var data := [form.id, true, form.mode, ENERGY_COST, 1, 2, 1,
		form.get("palette_switch_tick", 0), form.get("revert_tick", 0), form.get("entry_frames", []),
		target.simulation_data() if target != null else []]
	# 仅显式声明的免费切换形态扩充指纹；旧单形态数组保持原样。
	if form.has("free_switch"):
		data.append(bool(form.free_switch))
	if form.has("choices"):
		var choices: Array = []
		var keys: Array = form.choices.keys(); keys.sort()
		for key in keys: choices.append([key, simulation_data(form.choices[key])])
		data.append(choices)
	return data
