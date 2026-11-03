extends SceneTree

func _initialize() -> void:
	call_deferred("open_main")

func open_main() -> void:
	var game = load("res://app/scenes/main.tscn").instantiate()
	game.set_script(load("res://tests/review/app/ko_finish_review_game.gd"))
	game.review_driver = load("res://tests/review/app/ko_finish_review_driver.gd").new()
	game.review = true
	game.direct_battle = true
	game.local = true
	game.selected_fighters = game.review_driver.matchup()
	root.add_child(game)
	current_scene = game
