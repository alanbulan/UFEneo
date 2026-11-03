extends "res://app/game_app.gd"
# 复用主场景，末帧显式保存，避免基础review提前一个观察帧保存。
func reset_round() -> void:
	selected_fighters=review_driver.call("matchup")
	super.reset_round()

func _physics_process(delta:float) -> void:
	# 到下一physics入口才停，让第719观察对应的view更新先绘出。
	if review and capture_tick>=review_driver.call("capture_length"):
		review_driver.save_file(review_trace)
		shutdown()
		return
	super._physics_process(delta)
