extends "res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd"
const SweepFactory = preload("res://tests/review/fighters/ultraman-arc/luna_sweep/candidate_factory.gd")
var case_kind: String = "hit"
var capture_window_size:=Vector2i(1280,720)
func _battle_match(_first: String, _second: String, _allow_pilot: bool = false) -> UfeMatchDirector:
	return SweepFactory.make_match(candidate_contract, direction, case_kind)
var capture_requests: Dictionary = {}
func _physics_process(delta: float) -> void:
	# 禁用旧共用入口的异步截图调度，改为本候选单tick停住后取图。
	for old_frame in [0,23,112,135]:still_keys["idle-%03d"%old_frame]=true
	super._physics_process(delta)
	# 审片只隐藏遮挡人物的训练说明板，正式HUD与记录仍保留。
	if training_overlay!=null:training_overlay.hide()
	if review_driver.trace.is_empty() or finishing:return
	var row: Dictionary=review_driver.trace[-1]
	row["training_overlay_visible"]=training_overlay.visible
	var requests: Array = []
	var own: Dictionary=row.pair[0]
	var key: String=""
	if not str(own.move_id).is_empty():
		key="%s-phase-%02d"%[str(own.move_id),int(own.animation.get("index",-1))]
	elif str(own.state) in ["crouch_start", "crouch", "crouch_rise"]:
		key="%s-phase-%02d"%[str(own.state),int(own.frame_sprite)]
	elif int(row.movie_frame) in [0,112]:key="settled-idle-%03d"%int(row.movie_frame)
	if not key.is_empty() and not still_keys.has(key): requests.append({"key":key,"player":0})
	var target: Dictionary=row.pair[1]
	if str(target.state) in ["down", "wake"]:
		var target_key: String="target-%s-phase-%02d"%[str(target.state),int(target.frame_sprite)]
		if not still_keys.has(target_key): requests.append({"key":target_key,"player":1})
	if requests.is_empty():return
	set_physics_process(false)
	# 同一tick若双方同时出现新相，独立请求共享真实画面，全部完成再推进。
	for item in requests:
		var observed: Dictionary=row.pair[int(item.player)]
		still_keys[item.key]=true
		capture_requests[item.key]={"tick":simulation.tick,"movie_frame":int(row.movie_frame),"player":int(item.player),
			"sprite":int(observed.frame_sprite),"state":str(observed.state),"move_id":str(observed.move_id),
			"state_hash":simulation.state_hash(),"render_rect":observed.animation.rect.duplicate()}
		pending_stills+=1
	for item in requests:_save_still.call_deferred(int(row.movie_frame),str(item.key))

func _resume_after_capture() -> void:
	pending_stills-=1
	if pending_stills==0 and not finishing:set_physics_process(true)

func _save_still(frame: int, key: String) -> void:
	if DisplayServer.get_name() == "headless":
		var skipped: Array = review_driver.get("stills")
		var request: Dictionary=capture_requests[key]
		if simulation.tick!=int(request.tick) or simulation.state_hash()!=str(request.state_hash):
			review_driver.failures.append({"kind":"headless_capture_gate_advanced_simulation","request":request,"observed_tick":simulation.tick})
		skipped.append({"movie_frame": frame, "key": key, "captured": false, "reason": "headless_no_graphical_evidence","request":request,"observed_tick":simulation.tick})
		_resume_after_capture()
		return
	await RenderingServer.frame_post_draw
	var expected: Dictionary=capture_requests[key]
	var player: int=int(expected.player)
	var fighter:=simulation.fighters[player]
	var actual_phase:=int(fighter.frame().sprite)
	var failures: Array=review_driver.get("failures")
	if simulation.tick!=int(expected.tick) or actual_phase!=int(expected.sprite) or fighter.move_id!=str(expected.move_id) or fighter.state!=str(expected.state) or simulation.state_hash()!=str(expected.state_hash):
		failures.append({"kind":"capture_phase_changed_while_waiting","expected":expected,"actual_tick":simulation.tick,"actual_sprite":actual_phase})
		_resume_after_capture()
		return
	var sprite: Sprite2D=view.fighters[player]
	var r: Array=expected.render_rect
	var expected_rect:=Rect2(float(r[0]),float(r[1]),float(r[2]),float(r[3]))
	if not sprite.region_enabled or sprite.region_rect!=expected_rect:
		failures.append({"kind":"render_region_does_not_match_requested_phase","expected":r})
		_resume_after_capture()
		return
	var picture: Image = get_viewport().get_texture().get_image()
	var dimensions := Vector2i(picture.get_width(),picture.get_height())
	var window_dimensions: Vector2i = DisplayServer.window_get_size()
	if dimensions!=capture_window_size or dimensions != window_dimensions:
		failures.append({"kind":"unexpected_native_capture_size","image":[dimensions.x,dimensions.y],"window":[window_dimensions.x,window_dimensions.y]})
	var path: String = output_directory.path_join(key+".png")
	assert(not FileAccess.file_exists(path))
	assert(picture.save_png(path) == OK)
	var rows: Array = review_driver.get("stills")
	rows.append({"movie_frame":frame,"key":key,"path":path,"dimensions":[dimensions.x,dimensions.y],
		"window_dimensions":[window_dimensions.x,window_dimensions.y],"resized":false,"format":"PNG",
		"sha256":FileAccess.get_sha256(path),"request":expected,"captured_tick":simulation.tick,"captured_sprite":actual_phase,"captured_player":player,"captured_state":fighter.state,"simulation_frozen_during_capture":true})
	_resume_after_capture()
