extends SceneTree
const Factory=preload("res://tools/rebuild/gomora/back_lift_resume/runtime/factory.gd")
func _initialize() -> void:call_deferred("open_main")
func open_main() -> void:
	assert("--diagnostic-fx-hidden" in OS.get_cmdline_user_args(), "诊断入口必须显式启用")
	var contract_path: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="):contract_path=arg.trim_prefix("--contract=")
	assert(not contract_path.is_empty())
	var cfg: Dictionary=Factory.read_sealed(contract_path)
	var game=load("res://app/scenes/main.tscn").instantiate()
	game.set_script(load("res://tools/rebuild/gomora/back_lift_resume/runtime/ground_diagnostic_game.gd"))
	game.candidate_contract=cfg;game.candidate_contract_path=contract_path
	game.review_driver=load("res://tools/rebuild/gomora/back_lift_resume/runtime/driver.gd").new()
	game.review_driver.candidate_contract=cfg
	game.review=true;game.training=false;game.direct_battle=true;game.local=true;game.selected_fighters=game.review_driver.matchup()
	root.add_child(game);current_scene=game
