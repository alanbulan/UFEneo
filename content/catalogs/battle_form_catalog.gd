class_name UfeBattleFormCatalog
extends RefCounted
## 对局装配门面；文件读取留在content，core只接收整数规则和定义。
const PATH := "res://content/catalogs/battle_forms.json"
const GROUND_STATES := ["idle","walk","crouch","crouch_start","crouch_rise","guard","crouch_guard","charge","charge_start","charge_stop","turn","crouch_turn"]

static func registry() -> Dictionary:
	return UfeContentDatabase.read_json(PATH).forms

static func command(display_name: String, move_id: String = "battle_transform", directions: Array = [0]) -> Dictionary:
	var entry := {"move":move_id, "display_name":display_name, "states":GROUND_STATES,
		"directions":directions, "buttons":UfeInputFrame.SPECIAL, "motion":[2,5,2], "priority":1000}
	# 上方向仅在本次22+P确实选中装甲时消费，不影响普通跳跃。
	if directions.any(func(d): return int(d) >= 7): entry.consume_jump = true
	return entry

static func prepare(id: String, allow_pilot: bool, enabled_overrides: Dictionary = {}) -> Dictionary:
	var source: Dictionary = registry().get(id, {})
	var definition := UfeContentDatabase.fighter(id, allow_pilot or battle_playable(id))
	if source.is_empty(): return {"definition":definition, "form":{}}
	var form: Dictionary = source.duplicate(true)
	form.enabled = bool(enabled_overrides.get(id, form.enabled))
	return assemble(definition, form)

static func assemble(definition: UfeFighterDefinition, form: Dictionary) -> Dictionary:
	if not form.enabled: return {"definition":definition, "form":form}
	if form.has("choices"): return _assemble_choices(definition, form)
	return _assemble_single(definition, form, "battle_transform", [0])

static func _assemble_single(definition: UfeFighterDefinition, form: Dictionary, move_id: String, directions: Array) -> Dictionary:
	var timeline: Dictionary = UfeContentDatabase.read_json(str(form.transform))
	var move: Dictionary = timeline.duplicate(true)
	if str(form.mode) == "definition":
		form.target_definition = UfeContentDatabase.fighter(str(form.target), true)
		form.entry_frames = timeline.get("entry_frames", [])
		move.merge({"id":move_id, "display_name":str(form.get("display_name", "EX变身")), "kind":"transformation", "startup":0,
			"active":0, "recovery":timeline.frames.size(), "damage":0, "energy_cost":3000, "stamina_cost":0,
			"level":"mid", "unblockable":false, "launch":false, "bounce":false, "knockdown":false}, true)
	else:
		var super_move: Dictionary = UfeContentDatabase.read_json(str(form.super_move))
		definition.moves[str(super_move.id)] = super_move
	definition.moves[move_id] = move
	var original := command(str(move.display_name), move_id, directions)
	definition.command_table.append(original)
	definition.command_table.append(UfeQuickCommands.transform(original))
	return {"definition":definition, "form":form}

static func _assemble_choices(definition: UfeFighterDefinition, source: Dictionary) -> Dictionary:
	# 先校验选择表，再加载运行资源。未开放候选不应触碰尚未完成的文件。
	var seen: Array = []
	var default_count := 0
	var active: Array = []
	var ids: Array = []
	for raw in source.choices:
		if not bool(raw.get("enabled", false)): continue
		if str(raw.get("id", "")).is_empty() or str(raw.id) in ids:
			return _closed_choices(definition, source, "形态ID为空或重复")
		ids.append(str(raw.id))
		var directions: Array = raw.get("directions", [])
		if directions.is_empty(): return _closed_choices(definition, source, "形态缺少方向")
		for d in directions:
			if int(d) < 1 or int(d) > 9 or int(d) in seen:
				return _closed_choices(definition, source, "形态方向重叠或非法")
			seen.append(int(d))
		if bool(raw.get("default", false)):
			default_count += 1
			if not (2 in directions and 5 in directions): return _closed_choices(definition, source, "默认形态须接下和中立")
		active.append(raw)
	if default_count != 1: return _closed_choices(definition, source, "须开放且仅开放一个默认形态")
	var choices := {}
	var selected := {}
	for raw in active:
		var choice: Dictionary = raw.duplicate(true)
		var move_id := "battle_transform" if bool(choice.get("default", false)) else "battle_transform__" + str(choice.id)
		if choices.has(move_id): return _closed_choices(definition, source, "形态指令ID重复")
		var prepared := _assemble_single(definition, choice, move_id, choice.directions)
		choices[move_id] = prepared.form
		if bool(choice.get("default", false)): selected = prepared.form.duplicate(true)
	selected.choices = choices
	return {"definition":definition, "form":selected}

static func _closed_choices(definition: UfeFighterDefinition, source: Dictionary, reason: String) -> Dictionary:
	return {"definition":definition, "form":{"id":source.id, "enabled":false, "configuration_error":reason}}

static func battle_playable(id: String) -> bool:
	return bool(registry().get(id, {}).get("enabled", false))

static func match_for(first: String = "ultraman", second: String = "zetton", allow_pilot: bool = false, enabled_overrides: Dictionary = {}) -> UfeMatchDirector:
	var a := prepare(first, allow_pilot, enabled_overrides)
	var b := prepare(second, allow_pilot, enabled_overrides)
	var forms: Dictionary = {}
	forms[first] = a.form
	forms[second] = b.form
	return UfeMatchDirector.new(a.definition, b.definition, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), forms)
