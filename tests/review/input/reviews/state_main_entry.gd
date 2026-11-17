extends SceneTree
# 用现有主场景和已验证的末帧保存适配，不创建预览场景。
func _initialize() -> void:call_deferred("open_main")

func open_main() -> void:
	var driver_path:String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--state-review-driver="):driver_path=arg.trim_prefix("--state-review-driver=")
	if not driver_path.begins_with("res://content/fighters/") or not driver_path.ends_with("_review_driver.gd"):
		quit(2);return
	var game=load("res://app/scenes/main.tscn").instantiate()
	game.set_script(load("res://tests/review/fighters/ultraman-arc/codex_charge_review_game.gd"))
	game.review_driver=load(driver_path).new()
	game.review=true;game.training=true;game.direct_battle=true
	game.selected_fighters=game.review_driver.matchup()
	root.add_child(game);current_scene=game
