extends "res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/main_game.gd"
const JumpFactory = preload("res://tests/review/fighters/ultraman-arc/luna_vertical_jump/candidate_factory.gd")
var capture_window_size:=Vector2i(1280,720)
func _battle_match(_first: String, _second: String, _allow_pilot: bool = false) -> UfeMatchDirector:
	return JumpFactory.make_match(candidate_contract, direction)
var capture_requests: Dictionary = {}
var capture_previous_process: bool = false
func _physics_process(delta: float) -> void:
	# 禁用旧共用入口的异步截图调度，改为本候选单tick停住后取图。
	for old_frame in [0,23,112,135]:still_keys["idle-%03d"%old_frame]=true
	super._physics_process(delta)
	# 审片只隐藏遮挡人物的训练说明板，正式HUD与记录仍保留。
	if training_overlay!=null:training_overlay.hide()
	if review_driver.trace.is_empty() or finishing:return
	var row: Dictionary=review_driver.trace[-1]
	row["training_overlay_visible"]=training_overlay.visible
	var own: Dictionary=row.pair[0]
	var key: String=""
	var n: int=int(row.input_relative_n)
	if int(row.jump_episode)==0 and n in [0,1,2,7,8,14,15,17,18,25,26,32,33,34,35,36,37]:
		key="vertical-n-%02d-%s-phase-%02d"%[n,str(own.animation.get("key","missing")),int(own.animation.get("index",-1))]
	elif int(row.movie_frame) in [0,100]:key="settled-idle-%03d"%int(row.movie_frame)
	if key.is_empty() or still_keys.has(key):return
	still_keys[key]=true
	capture_requests[key]={"tick":simulation.tick,"movie_frame":int(row.movie_frame),"sprite":int(own.frame_sprite),"state":str(own.state),"animation_key":str(own.animation.key),"state_hash":simulation.state_hash(),"render_rect":own.animation.rect.duplicate()}
	pending_stills+=1
	capture_previous_process=is_processing()
	set_process(false)
	set_physics_process(false)
	_save_still.call_deferred(int(row.movie_frame),key)

func _resume_after_capture() -> void:
	pending_stills-=1
	if pending_stills==0 and not finishing:
		set_process(capture_previous_process)
		set_physics_process(true)

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
	var fighter:=simulation.fighters[0]
	var actual_phase:=int(fighter.frame().sprite)
	var failures: Array=review_driver.get("failures")
	if simulation.tick!=int(expected.tick) or actual_phase!=int(expected.sprite) or fighter.state!=str(expected.state) or simulation.state_hash()!=str(expected.state_hash):
		failures.append({"kind":"capture_phase_changed_while_waiting","expected":expected,"actual_tick":simulation.tick,"actual_sprite":actual_phase})
		_resume_after_capture()
		return
	var sprite: Sprite2D=view.fighters[0]
	var r: Array=expected.render_rect
	var expected_rect:=Rect2(float(r[0]),float(r[1]),float(r[2]),float(r[3]))
	if not sprite.region_enabled or sprite.region_rect!=expected_rect:
		failures.append({"kind":"render_region_does_not_match_requested_phase","expected":r})
		_resume_after_capture()
		return
	# 候选同样核绘制前最终HUD安全区，不能仅用旧trace的屏幕边界冒充避让。
	var safe: Rect2=hud.battle_safe_rect()
	var final_bounds: Array=[]
	for node in view.fighters+view.framing_entities:
		var b: Rect2=view.get_global_transform()*view._sprite_bounds(node)
		final_bounds.append([b.position.x,b.position.y,b.size.x,b.size.y])
		if not safe.grow(0.1).encloses(b):failures.append({"kind":"final_alpha_outside_hud_safe_area","movie_frame":frame,"bounds":final_bounds[-1]})
	if not safe.is_equal_approx(view.framing_safe_rect):failures.append({"kind":"candidate_hud_provider_not_applied","movie_frame":frame})
	expected["final_render_bounds"]=final_bounds
	expected["final_safe_rect"]=[view.framing_safe_rect.position.x,view.framing_safe_rect.position.y,view.framing_safe_rect.size.x,view.framing_safe_rect.size.y]
	expected["hud_safe_rect"]=[safe.position.x,safe.position.y,safe.size.x,safe.size.y]
	expected["hud_visible"]=hud.visible
	expected["training_overlay_visible"]=training_overlay.visible
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
		"sha256":FileAccess.get_sha256(path),"request":expected,"captured_tick":simulation.tick,"captured_sprite":actual_phase,"simulation_frozen_during_capture":true})
	_resume_after_capture()
