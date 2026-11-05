extends "res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd"
const HeavyFactory = preload("res://tests/review/fighters/ultraman-arc/luna_heavy/candidate_factory.gd")
var case_kind: String = "hit"
func _battle_match(_first: String, _second: String, _allow_pilot: bool = false) -> UfeMatchDirector:
	return HeavyFactory.make_match(candidate_contract, direction, case_kind)
func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if review_driver.trace.is_empty() or finishing: return
	var row: Dictionary = review_driver.trace[-1]
	var own: Dictionary = row.pair[0]
	if str(own.move_id).is_empty(): return
	var key: String = "%s-phase-%02d" % [str(own.move_id), int(own.animation.get("index", -1))]
	if not still_keys.has(key):
		still_keys[key] = true
		pending_stills += 1
		_save_still.call_deferred(int(row.movie_frame), key)

func _save_still(frame: int, key: String) -> void:
	if DisplayServer.get_name() == "headless":
		var skipped: Array = review_driver.get("stills")
		skipped.append({"movie_frame": frame, "key": key, "captured": false, "reason": "headless_no_graphical_evidence"})
		pending_stills -= 1
		return
	await RenderingServer.frame_post_draw
	var picture: Image = get_viewport().get_texture().get_image()
	var dimensions := Vector2i(picture.get_width(),picture.get_height())
	var window_dimensions: Vector2i = DisplayServer.window_get_size()
	var failures: Array = review_driver.get("failures")
	if dimensions not in [Vector2i(1280,720),Vector2i(1920,1080)] or dimensions != window_dimensions:
		failures.append({"kind":"unexpected_native_capture_size","image":[dimensions.x,dimensions.y],"window":[window_dimensions.x,window_dimensions.y]})
	var path: String = output_directory.path_join(key+".png")
	assert(not FileAccess.file_exists(path))
	assert(picture.save_png(path) == OK)
	var rows: Array = review_driver.get("stills")
	rows.append({"movie_frame":frame,"key":key,"path":path,"dimensions":[dimensions.x,dimensions.y],
		"window_dimensions":[window_dimensions.x,window_dimensions.y],"resized":false,"format":"PNG",
		"sha256":FileAccess.get_sha256(path)})
	pending_stills -= 1
