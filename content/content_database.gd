class_name UfeContentDatabase
extends RefCounted
static func read_json(path: String):
	return JSON.parse_string(FileAccess.get_file_as_string(path))

# 父模板在前，子模板只保存差异；旧humanoid没有template.json时行为不变。
static func template_chain(id: String) -> Array[String]:
	var result: Array[String] = []
	var current := id
	while not current.is_empty():
		assert(not result.has(current), "体型模板不能循环继承")
		result.push_front(current)
		var path := "res://content/templates/%s/template.json" % current
		current = str(read_json(path).get("extends", "")) if FileAccess.file_exists(path) else ""
	return result

static func merge_commands(base: Array, overrides: Array) -> Array:
	var moves: Array = []
	for entry in overrides:
		if not moves.has(entry.move): moves.append(entry.move)
	var result := base.filter(func(e): return e.move not in moves)
	result.append_array(overrides)
	return result

static func template_commands(id: String) -> Array:
	var result: Array = []
	for name in template_chain(id):
		result = merge_commands(result, read_json("res://content/templates/%s/command_table.json" % name))
	return result

static func template_moves(id: String) -> Dictionary:
	var result := {}
	for name in template_chain(id):
		var base := "res://content/templates/%s/" % name
		for move_id in read_json(base + "move_manifest.json"):
			result[move_id] = base + "moves/%s.json" % move_id
	return result

static func fighter(id: String, allow_pilot: bool=false) -> UfeFighterDefinition:
	var data: Dictionary = read_json("res://content/fighters/%s/definition.json" % id)
	assert(data.get("playable", true) or (allow_pilot and data.get("pilot_playable",false)), "准备中的角色没有正式资源，不可进入对局")
	var result := UfeFighterDefinition.new()
	result.id = id
	result.display_name = data.display_name
	result.max_health = int(data.max_health)
	result.walk_speed = int(data.walk_speed)
	result.jump_speed = int(data.get("jump_speed",16))
	var presented: Dictionary = data.get("presentation", {})
	result.body_radius = int(data.get("body_radius", UfeFeelRules.default_body_radius(str(data.get("template", "humanoid")), int(presented.get("target_height", 0)))))
	var posture_path := "res://content/fighters/%s/state_frames.json" % id
	if FileAccess.file_exists(posture_path): result.state_frames = read_json(posture_path)
	result.command_table = template_commands(data.template)
	var overrides: Array = read_json("res://content/fighters/%s/command_table.json" % id)
	result.command_table = merge_commands(result.command_table, overrides)
	result.command_table=result.command_table.filter(func(e):return str(e.move) not in data.get("unsupported_moves",[]))
	var inherited_moves := template_moves(data.template)
	var local_manifest := "res://content/fighters/%s/move_manifest.json" % id
	if FileAccess.file_exists(local_manifest):
		for move_id in read_json(local_manifest):
			inherited_moves[move_id] = "res://content/fighters/%s/moves/%s.json" % [id, move_id]
	for move_id in inherited_moves:
		var path := "res://content/fighters/%s/moves/%s.json" % [id, move_id]
		if data.get("production_status","")=="pilot_partial" and str(move_id) in data.get("unsupported_moves",[]):continue
		# 模板清单可列角色专属招式（taunt/special2/special3），模板自身不一定带文件；
		# 角色未提供本地文件时跳过并告警，不能让整个角色加载失败。
		var source := path if FileAccess.file_exists(path) else str(inherited_moves[move_id])
		if not FileAccess.file_exists(source):
			push_warning("缺少招式文件，已跳过：%s/%s" % [id, move_id])
			continue
		result.moves[move_id] = read_json(source)
		UfeFeelRules.apply_move(result.moves[move_id])
	result.command_table = UfeQuickCommands.extend(result.command_table,result.moves)
	return result

static func states() -> Dictionary:
	var result := {}
	var paths: Dictionary = read_json("res://content/states.json")
	for id in paths:
		result[id] = load(paths[id]).new()
	return result

static func match_for(first: String = "ultraman", second: String = "zetton", allow_pilot: bool=false) -> UfeMatchDirector:
	return UfeMatchDirector.new(fighter(first,allow_pilot), fighter(second,allow_pilot), load("res://content/rules/neo.tres"), states())
