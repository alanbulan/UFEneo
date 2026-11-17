extends "res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd"
## 继承已实跑正式main装配/退出/小JPEG，只覆盖首次工厂和跳跃选相截图。
const JumpFactory = preload("res://tools/rebuild/ultraman-arc/luna-jump-resume-20261102-v1/candidate_factory.gd")

func _battle_match(_first: String, _second: String, _allow_pilot: bool = false) -> UfeMatchDirector:
	return JumpFactory.make_match(candidate_contract,direction)

func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if review_driver.trace.is_empty() or finishing:return
	var row: Dictionary=review_driver.trace[-1]
	var episode: int=int(row.jump_episode)
	if episode < 0:return
	var f: Dictionary=row.pair[0]
	var key: String="jump-%d-%s-phase-%02d" % [episode,str(f.animation.get("key","missing")),int(f.animation.get("index",-1))]
	if int(row.input_relative_n) in [16,17,32,33,36,37]:key="jump-%d-n-%02d" % [episode,int(row.input_relative_n)]
	if not still_keys.has(key):
		still_keys[key]=true;pending_stills+=1
		_save_still.call_deferred(int(row.movie_frame),key)
