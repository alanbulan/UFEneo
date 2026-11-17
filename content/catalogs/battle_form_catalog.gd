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
			"active":0, "recovery":timeline.frames.size(), "damage":0, "energy_cost":int(form.get("energy_cost", 3000)), "stamina_cost":0,
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
	# 先校验选择表，再加载运行资源。未开放/未实装候选不应触碰尚未完成的文件。
	var seen: Array = []
	var default_count := 0
	var active: Array = []
	var ids: Array = []
	for raw in source.choices:
		if not bool(raw.get("enabled", false)) or not bool(raw.get("implemented", true)): continue
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
	# 只有一个可切形态时没有切换可做：不接指令，避免把22+P变成必杀备用入口。
	if active.size() < 2: return {"definition":definition, "form":{}}
	var choices := {}
	var selected := {}
	for raw in active:
		var choice: Dictionary = raw.duplicate(true)
		var move_id := "battle_transform" if bool(choice.get("default", false)) else "battle_transform__" + str(choice.id)
		if choices.has(move_id): return _closed_choices(definition, source, "形态指令ID重复")
		var prepared := _assemble_single(definition, choice, move_id, choice.directions)
		choices[move_id] = prepared.form
		if bool(choice.get("default", false)): selected = prepared.form.duplicate(true)
	_copy_switch_data_to_targets(definition, choices)
	selected.choices = choices
	return {"definition":definition, "form":selected}

# 切过一次形态后f.definition已是目标定义；目标定义也要认识全部切换指令和时间轴，
# 否则第二次按E读不到battle_transform__*。只复制切换所需数据，不复制原形态招式。
static func _copy_switch_data_to_targets(definition: UfeFighterDefinition, choices: Dictionary) -> void:
	var switch_moves: Dictionary = {}
	var switch_commands: Array = []
	for entry in definition.command_table:
		if UfeBattleTransform.is_command(str(entry.move)):
			switch_commands.append(entry.duplicate(true))
	for move_id in definition.moves:
		if UfeBattleTransform.is_command(str(move_id)):
			switch_moves[str(move_id)] = definition.moves[move_id]
	for key in choices:
		var form: Dictionary = choices[key]
		var target: UfeFighterDefinition = form.get("target_definition")
		if target == null or target == definition: continue
		for move_id in switch_moves:
			if not target.moves.has(move_id): target.moves[move_id] = switch_moves[move_id]
		for entry in switch_commands:
			var exists := target.command_table.any(func(row): return str(row.move) == str(entry.move))
			if not exists: target.command_table.append(entry.duplicate(true))

static func _closed_choices(definition: UfeFighterDefinition, source: Dictionary, reason: String) -> Dictionary:
	return {"definition":definition, "form":{"id":source.id, "enabled":false, "configuration_error":reason}}

static func battle_playable(id: String) -> bool:
	return bool(registry().get(id, {}).get("enabled", false))

static func match_for(first: String = "ultraman", second: String = "zetton", allow_pilot: bool = false, enabled_overrides: Dictionary = {}, start_forms: Array = []) -> UfeMatchDirector:
	var a := prepare(first, allow_pilot, enabled_overrides)
	var b := prepare(second, allow_pilot, enabled_overrides)
	var forms: Dictionary = {}
	forms[first] = a.form
	forms[second] = b.form
	var starts: Dictionary = {}
	for i in range(2):
		var base := first if i == 0 else second
		var form_id := str(start_forms[i]) if i < start_forms.size() else ""
		if form_id.is_empty() or form_id == "default": continue
		# 只有配置了战斗切换表的角色才吃“出场形态”；外观类形态不参与开局定义。
		if registry().get(base, {}).is_empty(): continue
		if _open_choice(base, form_id, enabled_overrides).is_empty():
			push_warning("出场形态未开放或未实装，按基础形态开局：%s/%s" % [base, form_id])
			continue
		# 必须复用切换表里已装配的目标定义：它已带全部切换指令和时间轴。
		var start := _prepared_target(a.form if i == 0 else b.form, form_id)
		if start == null:
			push_warning("出场形态未装配，按基础形态开局：%s/%s" % [base, form_id])
			continue
		starts[i] = start
	return UfeMatchDirector.new(a.definition, b.definition, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), forms, starts)

# 出场形态必须来自该角色已开放且已实装的切换表，不能借选人界面塞任意角色。
static func _open_choice(base: String, form_id: String, enabled_overrides: Dictionary = {}) -> Dictionary:
	var source: Dictionary = registry().get(base, {})
	if source.is_empty() or not bool(enabled_overrides.get(base, source.get("enabled", false))): return {}
	for raw in source.get("choices", []):
		if str(raw.get("id", "")) != form_id: continue
		if bool(raw.get("enabled", false)) and bool(raw.get("implemented", true)): return raw
	return {}

static func _prepared_target(form: Dictionary, form_id: String) -> UfeFighterDefinition:
	for key in form.get("choices", {}):
		var choice: Dictionary = form.choices[key]
		if str(choice.get("id", "")) != form_id: continue
		return choice.get("target_definition")
	return null
