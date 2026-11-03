extends SceneTree
## 根持唯一Godot锁时显式执行；必须提供已审17源的冻结合同。
const Factory = preload("res://tools/rebuild/ultraman-arc/luna-jump-resume-20261102-v1/candidate_factory.gd")
const Driver = preload("res://tools/rebuild/ultraman-arc/luna-jump-resume-20261102-v1/main_driver.gd")

func _initialize() -> void:call_deferred("open_formal_main")

func open_formal_main() -> void:
	var contract_path: String=""
	var output_directory: String=""
	var direction: int=1
	var tape_path: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--luna-s2-contract="):contract_path=arg.trim_prefix("--luna-s2-contract=")
		elif arg.begins_with("--luna-s2-out="):output_directory=arg.trim_prefix("--luna-s2-out=")
		elif arg=="--luna-s2-direction=right":direction=1
		elif arg=="--luna-s2-direction=left":direction=-1
		elif arg.begins_with("--luna-s2-original-tape="):tape_path=arg.trim_prefix("--luna-s2-original-tape=")
		else:assert(false,"基础跳跃入口拒绝额外参数："+arg)
	assert(not contract_path.is_empty() and not output_directory.is_empty())
	var cfg: Dictionary=Factory.read_sealed(contract_path)
	output_directory=ProjectSettings.globalize_path(output_directory).simplify_path()
	var allowed: String=ProjectSettings.globalize_path("res://reports/review/2026-11-02/").simplify_path().trim_suffix("/")+"/luna-jump-resume-"
	assert(output_directory.to_lower().begins_with(allowed.to_lower()))
	assert(not FileAccess.file_exists(output_directory.path_join("main-trace.json")))
	assert(DirAccess.make_dir_recursive_absolute(output_directory)==OK)
	var driver=Driver.new()
	driver.candidate_contract=cfg;driver.direction=direction;driver.output_directory=output_directory
	if not tape_path.is_empty():driver.input_tape=UfeContentDatabase.read_json(tape_path)
	var game=load("res://app/scenes/main.tscn").instantiate()
	game.set_script(load("res://tools/rebuild/ultraman-arc/luna-jump-resume-20261102-v1/main_game.gd"))
	game.candidate_contract=cfg;game.candidate_contract_path=contract_path;game.direction=direction;game.output_directory=output_directory
	game.review_driver=driver;game.review_trace=output_directory.path_join("main-trace.json")
	game.review=true;game.training=true;game.local=true;game.direct_battle=true
	game.selected_fighters=["ultraman-arc__luna",str(cfg.opponent)]
	root.add_child(game);current_scene=game
