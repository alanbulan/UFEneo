extends SceneTree
## 独立进程只解包主游戏保存的InputFrame，不加载驱动、不生成新输入。
func _initialize() -> void: call_deferred("run")
func canonical(value: Variant) -> String: return JSON.stringify(JSON.parse_string(JSON.stringify(value)),"",true)

func run() -> void:
	var path: String = ""
	var output: String = ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--ko-trace="): path = arg.trim_prefix("--ko-trace=")
		if arg.begins_with("--ko-output="): output = arg.trim_prefix("--ko-output=")
	if path.is_empty() or output.is_empty() or FileAccess.file_exists(output):
		push_error("KO独立回放路径无效或结果已存在")
		quit(2)
		return
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	var start: Dictionary = data.initial
	var sim: UfeMatchDirector
	var errors: Array = []
	var previous: String = ""
	var observations: int = 0
	for row in data.trace:
		var phase: String = str(row.phase)
		if sim == null or phase != previous:
			sim = UfeBattleFormCatalog.match_for(str(start.ids[0]),str(start.ids[1]),true)
			if phase != "f4":
				for i in range(2):
					sim.fighters[i].x = int(start.positions[i]);sim.fighters[i].facing = int(start.facings[i]);sim.fighters[i].stats.hp = int(start.hp[i])
			previous = phase
			if sim.content_fingerprint != str(start.content_fingerprint): errors.append("正式内容指纹不符")
		if bool(row.simulation_stepped) or phase == "f4" and int(row.tick) > sim.tick:
			sim.step([UfeInputFrame.unpack(row.inputs[0]),UfeInputFrame.unpack(row.inputs[1])])
		if sim.state_hash() != str(row.state_hash) or canonical(sim.events) != canonical(row.events):
			errors.append(str(row.frame)+"原输入状态/事件差异")
			break
		observations += 1
	var file := FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify({"errors":errors,"observations":observations,"trace_sha256":FileAccess.get_sha256(path),"generated_videos":0}))
	file.close()
	for error in errors: push_error(str(error))
	quit(0 if errors.is_empty() else 1)
