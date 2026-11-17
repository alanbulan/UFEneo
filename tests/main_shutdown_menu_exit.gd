extends SceneTree
## 图形窗口运行正式主场景；通过真实按键导航到退出，不用测试quit覆盖返回码。
var app: Control
var output := ""
var tick := 0
var samples: Array = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--shutdown-out="): output = argument.trim_prefix("--shutdown-out=")
	assert(not output.is_empty(), "必须指定独立证据目录")
	DirAccess.make_dir_recursive_absolute(output)
	call_deferred("_boot")

func _boot() -> void:
	app = load("res://app/scenes/main.tscn").instantiate()
	root.add_child(app)
	current_scene = app

func _process(_delta: float) -> bool:
	if not is_instance_valid(app) or app.get("_shutting_down"): return false
	tick += 1
	# 与既有标题录制驱动一致，窗口可能未获默认焦点，先固定导航起点。
	if tick == 171: app.front.focus_buttons[0].grab_focus()
	if tick == 175: _sample.call_deferred("title")
	if tick in [181, 185, 189, 193, 197]: _key(KEY_S)
	if tick == 201: _sample.call_deferred("quit-focused")
	if tick == 205:
		var focused: Control = app.viewport.gui_get_focus_owner()
		var focus_text: String = focused.text if focused is Button else ""
		var failures: Array[String] = []
		if app.front.page != "title": failures.append("未停在主菜单")
		if focus_text != "退出": failures.append("按键导航未选中退出")
		var result := {"entry": "res://app/scenes/main.tscn", "page": app.front.page,
			"focus": focus_text, "input": "root.push_input(InputEventKey): S×5 → J",
			"samples": samples, "expected_exit": 0, "failures": failures,
			"native_exit_verified_by_runner": false}
		var file := FileAccess.open(output.path_join("menu-result.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(result, "\t"))
		print("MAIN_MENU_EXIT ", JSON.stringify(result))
		if failures.is_empty(): _key(KEY_J)
	return false

func _key(code: int) -> void:
	for pressed in [true, false]:
		var event := InputEventKey.new()
		event.keycode = code as Key
		event.physical_keycode = code as Key
		event.pressed = pressed
		root.push_input(event)

func _sample(label: String) -> void:
	await RenderingServer.frame_post_draw
	var path := output.path_join(label + ".png")
	root.get_texture().get_image().save_png(path)
	samples.append({"tick": tick, "path": path})
