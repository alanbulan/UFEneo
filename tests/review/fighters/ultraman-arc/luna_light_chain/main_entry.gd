extends SceneTree
const Factory = preload("res://tests/review/fighters/ultraman-arc/luna_light_chain/candidate_factory.gd")
const Driver = preload("res://tests/review/fighters/ultraman-arc/luna_light_chain/main_driver.gd")
func _initialize() -> void: call_deferred("open_main")
func open_main() -> void:
	var contract_path: String = ""
	var out: String = ""
	var direction: int = 1
	var kind: String = "hit"
	var depth: int = 3
	var tape: String = ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="): contract_path = arg.trim_prefix("--contract=")
		elif arg.begins_with("--out="): out = arg.trim_prefix("--out=")
		elif arg == "--left": direction = -1
		elif arg.begins_with("--kind="): kind = arg.trim_prefix("--kind=")
		elif arg.begins_with("--depth="): depth = int(arg.trim_prefix("--depth="))
		elif arg.begins_with("--tape="): tape = arg.trim_prefix("--tape=")
		else: assert(false, "未知月亮候选参数")
	assert(depth in [1,2,3] and not contract_path.is_empty())
	out = ProjectSettings.globalize_path(out).simplify_path()
	assert(out.begins_with(ProjectSettings.globalize_path("res://reports/luna-light-chain-resume/")))
	assert(not FileAccess.file_exists(out.path_join("main-trace.json")))
	assert(DirAccess.make_dir_recursive_absolute(out) == OK)
	var cfg: Dictionary = Factory.read_sealed(contract_path)
	var driver = Driver.new()
	driver.candidate_contract = cfg
	driver.direction = direction
	driver.kind = kind
	driver.depth = depth
	driver.output_directory = out
	if not tape.is_empty(): driver.input_tape = UfeContentDatabase.read_json(tape)
	var game = load("res://app/scenes/main.tscn").instantiate()
	game.set_script(load("res://tests/review/fighters/ultraman-arc/luna_light_chain/main_game.gd"))
	game.candidate_contract = cfg
	game.candidate_contract_path = contract_path
	game.direction = direction
	game.case_kind = kind
	game.output_directory = out
	game.review_driver = driver
	game.review_trace = out.path_join("main-trace.json")
	game.review = true
	game.training = true
	game.local = true
	game.direct_battle = true
	game.selected_fighters = ["ultraman-arc__luna", str(cfg.opponent)]
	root.add_child(game)
	current_scene = game
