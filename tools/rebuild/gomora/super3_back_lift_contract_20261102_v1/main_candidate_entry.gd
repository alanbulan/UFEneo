extends SceneTree
func _initialize() -> void:call_deferred("open_main")
func open_main() -> void:
	var game=load("res://app/scenes/main.tscn").instantiate()
	game.set_script(load("res://tools/rebuild/gomora/super3_back_lift_contract_20261102_v1/main_candidate_game.gd"))
	game.review_driver=load("res://tools/rebuild/gomora/super3_back_lift_contract_20261102_v1/main_candidate_driver.gd").new()
	game.review=true;game.training=false;game.direct_battle=true;game.local=true;game.selected_fighters=game.review_driver.matchup()
	root.add_child(game);current_scene=game
