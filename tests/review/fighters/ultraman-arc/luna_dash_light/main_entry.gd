extends SceneTree
const Factory = preload("res://tests/review/fighters/ultraman-arc/luna_dash_light/candidate_factory.gd")
const Driver = preload("res://tests/review/fighters/ultraman-arc/luna_dash_light/main_driver.gd")
func _initialize() -> void: call_deferred("open_main")
func open_main() -> void:
	var contract_path: String = ""
	var out: String = ""
	var direction: int = 1
	var kind: String = "hit"
	var tape: String = ""
	var requested_size:=Vector2i(1280,720)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="): contract_path = arg.trim_prefix("--contract=")
		elif arg.begins_with("--out="): out = arg.trim_prefix("--out=")
		elif arg == "--left": direction = -1
		elif arg.begins_with("--kind="): kind = arg.trim_prefix("--kind=")
		elif arg.begins_with("--tape="): tape = arg.trim_prefix("--tape=")
		elif arg.begins_with("--window-size="):
			var value:=arg.trim_prefix("--window-size=")
			assert(value in ["1280x720","1920x1080"],"仅接受原生720/1080窗口")
			requested_size=Vector2i(1920,1080) if value=="1920x1080" else Vector2i(1280,720)
		else: assert(false, "未知月亮候选参数")
	assert(kind in ["hit", "block", "whiff"] and not contract_path.is_empty())
	out = ProjectSettings.globalize_path(out).simplify_path()
	assert(out.begins_with(ProjectSettings.globalize_path("res://reports/luna-dash-light-resume/")))
	assert(not FileAccess.file_exists(out.path_join("main-trace.json")))
	assert(DirAccess.make_dir_recursive_absolute(out) == OK)
	var cfg: Dictionary = Factory.read_sealed(contract_path)
	var driver = Driver.new()
	driver.candidate_contract = cfg
	driver.direction = direction
	driver.kind = kind
	driver.output_directory = out
	if not tape.is_empty(): driver.input_tape = UfeContentDatabase.read_json(tape)
	var game = load("res://app/scenes/main.tscn").instantiate()
	game.set_script(load("res://tests/review/fighters/ultraman-arc/luna_dash_light/main_game.gd"))
	game.candidate_contract = cfg
	game.candidate_contract_path = contract_path
	game.direction = direction
	game.case_kind = kind
	game.capture_window_size=requested_size
	game.output_directory = out
	game.review_driver = driver
	game.review_trace = out.path_join("main-trace.json")
	game.review = true
	game.training = true
	game.local = true
	game.direct_battle = true
	game.selected_fighters = ["ultraman-arc__luna", str(cfg.opponent)]
	# _ready完成布局后再定窗口；整个等待阶段不采样输入、不推进模拟。
	game.process_mode=Node.PROCESS_MODE_DISABLED
	root.add_child(game)
	current_scene = game
	if not await stabilize_window(game,requested_size,out):
		quit(1)
		return
	game.process_mode=Node.PROCESS_MODE_INHERIT

func stabilize_window(game: Node, requested: Vector2i, out: String) -> bool:
	var record: Dictionary={"requested":[requested.x,requested.y],"headless":DisplayServer.get_name()=="headless","observations":[],"simulation_tick_before":game.simulation.tick}
	var success:=false
	if record.headless:
		record["status"]="headless_no_window_verification"
		success=true
	else:
		root.mode=Window.MODE_WINDOWED
		root.borderless=true
		root.wrap_controls=false
		root.min_size=Vector2i(1,1)
		root.position=Vector2i.ZERO
		root.size=requested
		DisplayServer.window_set_size(requested)
		var start:=Time.get_ticks_msec()
		var stable:=0
		while Time.get_ticks_msec()-start<5000:
			await process_frame
			var actual:=DisplayServer.window_get_size()
			var viewport_size:=root.get_visible_rect().size
			var matches:=actual==requested and Vector2i(viewport_size)==requested
			stable=stable+1 if matches else 0
			record.observations.append({"elapsed_ms":Time.get_ticks_msec()-start,"window":[actual.x,actual.y],"viewport":[viewport_size.x,viewport_size.y]})
			if stable>=8 and Time.get_ticks_msec()-start>=500:
				success=true
				break
		record["stable_frames"]=stable
		record["status"]="native_window_stable" if success else "native_window_size_not_reached"
	record["simulation_tick_after"]=game.simulation.tick
	record["trace_count_before_start"]=game.review_driver.trace.size()
	if game.simulation.tick!=0 or not game.review_driver.trace.is_empty():
		success=false;record["status"]="simulation_advanced_before_window_ready"
	var path:=out.path_join("window-setup.json")
	assert(not FileAccess.file_exists(path))
	var file:=FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify(record,"\t"));file.close()
	if not success:push_error("候选窗口未达到指定原生尺寸，已停止；实际记录见window-setup.json")
	return success
