extends SceneTree
var failures: Array[String] = []
func check(ok: bool, label: String) -> void:
	if not ok: failures.append(label)
func _initialize() -> void:
	# 旧两人按原加载算法核对，模板继承不能改变既有招式或回放指纹。
	for id in ["ultraman", "zetton"]:
		var actual := UfeContentDatabase.fighter(id)
		var data: Dictionary = UfeContentDatabase.read_json("res://content/fighters/%s/definition.json" % id)
		var commands: Array = UfeContentDatabase.read_json("res://content/templates/humanoid/command_table.json")
		for entry in UfeContentDatabase.read_json("res://content/fighters/%s/command_table.json" % id):
			commands = commands.filter(func(e): return str(e.move) != str(entry.move))
			commands.append(entry)
		commands=commands.filter(func(e): return str(e.move) not in data.get("unsupported_moves", []))
		var original_commands: Array=actual.command_table.filter(func(entry):return not bool(entry.get("quick_skill",false)) and not bool(entry.get("quick_transform",false)))
		check(original_commands==commands, id+"原输入映射精确保留；快捷仅作新增别名")
		for move in UfeContentDatabase.read_json("res://content/templates/humanoid/move_manifest.json"):
			var path := "res://content/fighters/%s/moves/%s.json" % [id, move]
			var old=UfeContentDatabase.read_json(path if FileAccess.file_exists(path) else "res://content/templates/humanoid/moves/%s.json" % move)
			check(actual.moves[move]==old, id+"招式数据保留"+str(move))
	check(UfeContentDatabase.template_chain("biped_tail")==["humanoid","biped_tail"], "体型继承顺序")
	var moves := UfeContentDatabase.template_moves("biped_tail")
	check(moves.size()==UfeContentDatabase.template_moves("humanoid").size(), "父动作完整继承")
	for id in ["spin_heavy","sweep","tackle"]:
		check(str(moves[id]).contains("/biped_tail/"), "尾动作覆盖"+id)
	check(str(moves["light1"]).contains("/humanoid/"), "通用动作无复制")
	var commands := UfeContentDatabase.template_commands("biped_tail")
	var sweep_count := 0
	for entry in commands:
		if entry.move=="sweep":
			sweep_count+=1
			check(entry.display_name=="扫尾", "所有下段派生覆盖扫尾")
	check(sweep_count==3, "覆盖时保留蹲姿/连打/落地三种输入")
	print("STAGE4_TEMPLATE "+("PASS" if failures.is_empty() else str(failures)))
	quit(0 if failures.is_empty() else 1)
