extends SceneTree
## 在正式主游戏上验证重复关闭和调用者退出码，不生成研究场景。
var output := ""
var test_case := "baseline-duplicate"
var app: Node

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--shutdown-out="): output = argument.trim_prefix("--shutdown-out=")
		if argument.begins_with("--shutdown-case="): test_case = argument.trim_prefix("--shutdown-case=")
	call_deferred("_run")

func _run() -> void:
	if output.is_empty():
		quit(2)
		return
	app = load("res://app/scenes/main.tscn").instantiate()
	root.add_child(app)
	current_scene = app
	for _frame in range(3): await process_frame
	var input_callback_targets_app := false
	for connection in Input.joy_connection_changed.get_connections():
		var callback: Callable = connection["callable"]
		if callback.get_object() == app: input_callback_targets_app = true
	InputMap.action_erase_events("p1_light")
	Input.joy_connection_changed.emit(-1, false)
	var input_reconfigured := not InputMap.action_get_events("p1_light").is_empty()
	var children_before := app.get_child_count()
	var expected_exit := 0
	if test_case == "baseline-duplicate":
		app.call("shutdown")
		app.call("shutdown")
	elif test_case == "normal":
		app.call("shutdown", 0)
	elif test_case == "failure":
		expected_exit = 7
		app.call("shutdown", expected_exit)
	elif test_case == "duplicate":
		expected_exit = 7
		app.call("shutdown", expected_exit)
		app.call("shutdown", 9)
	else:
		quit(2)
		return
	await process_frame
	# 首次关闭已释放子节点后再请求一次，仍须安全忽略，并保留首次代码。
	if test_case == "duplicate": app.call("shutdown", 3)
	var failures: Array[String] = []
	if not input_callback_targets_app: failures.append("手柄连接回调未绑定主游戏节点")
	if not input_reconfigured: failures.append("手柄连接变化后输入映射未重建")
	if children_before == 0: failures.append("主游戏未创建运行节点")
	if app.get_child_count() != 0: failures.append("关闭后仍有运行节点")
	if app.is_physics_processing(): failures.append("关闭后仍处理物理帧")
	var result := {"case": test_case, "children_before": children_before,
		"children_after": app.get_child_count(), "expected_exit": expected_exit,
		"physics_processing_after": app.is_physics_processing(), "failures": failures,
		"input_callback_targets_app": input_callback_targets_app, "input_reconfigured": input_reconfigured,
		"main_scene": "res://app/scenes/main.tscn", "native_exit_verified_by_runner": false}
	DirAccess.make_dir_recursive_absolute(output)
	var file := FileAccess.open(output.path_join("result.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(result, "\t"))
	print("MAIN_SHUTDOWN_LOGIC ", JSON.stringify(result))
	# 实际退出由GameApp发起；测试不再quit覆盖真实返回码。
