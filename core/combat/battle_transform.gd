class_name UfeBattleTransform
extends RefCounted
## 纯整数规则。开放表、定义和逐tick演出数据由装配层注入。
const ENERGY_COST := 3000

static func is_command(id: String) -> bool:
	return id == "battle_transform" or id.begins_with("battle_transform__")

static func can_transform(f: UfeFighter, move_id: String = "battle_transform") -> bool:
	return bool(f.battle_form.get("enabled", false)) and not f.transformed_this_round \
		and (f.battle_form.choices.has(move_id) if f.battle_form.has("choices") else move_id == "battle_transform") \
		and int(f.stats.energy) >= ENERGY_COST and int(f.stats.hp) > 0 \
		and int(f.stats.hp) * 2 <= f.base_definition.max_health

static func begin(f: UfeFighter, move_id: String = "battle_transform") -> void:
	if f.battle_form.has("choices"): f.battle_form = f.battle_form.choices[move_id]
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
	if form.has("choices"):
		var choices: Array = []
		var keys: Array = form.choices.keys(); keys.sort()
		for key in keys: choices.append([key, simulation_data(form.choices[key])])
		data.append(choices)
	return data
