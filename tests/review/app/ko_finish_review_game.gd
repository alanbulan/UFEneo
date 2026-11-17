extends "res://app/game_app.gd"
var stills_dir: String = ""
var still_keys: Dictionary = {}
var audio_cursor: int = 0
var pause_done: bool = false
var pause_until: int = -1
var replay_started: bool = false
var replay_pause_tested: bool = false
var restart_started: bool = false
var restarted_at: int = -1
var lifecycle: Array = []

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--ko-stills="): stills_dir = arg.trim_prefix("--ko-stills=")
	if not stills_dir.is_empty(): DirAccess.make_dir_recursive_absolute(stills_dir)
	super._ready()

func _battle_match(first: String, second: String, _allow_pilot: bool = false) -> UfeMatchDirector:
	return UfeBattleFormCatalog.match_for(first,second,true)

func start_match() -> void:
	training = false
	super.start_match()
	intro = 75

func reset_round() -> void:
	training = false
	super.reset_round()
	intro = 75

func _physics_process(delta: float) -> void:
	if not is_instance_valid(view): return
	if capture_tick >= 19000:
		push_error("KO专项未自然完成，保留失败trace")
		_finish_review()
		return
	var kind: String = str(review_driver.kind)
	if ko_finish.active and not pause_done and ko_finish.real_age >= 18:
		_action("pause")
		pause_done = true
		pause_until = capture_tick + 12
		lifecycle.append({"kind":"pause_during_slowmo","frame":capture_tick,"real_age":ko_finish.real_age})
	elif pause_until == capture_tick:
		_action("pause")
		lifecycle.append({"kind":"resume_slowmo","frame":capture_tick,"real_age":ko_finish.real_age})
	if kind == "full_replay" and replay == null and not replay_started and ending_tick >= 100:
		review_driver.release_keys()
		var event := InputEventKey.new()
		event.keycode = KEY_F4;event.physical_keycode = KEY_F4;event.pressed = true
		_input(event)
		replay_started = true
		lifecycle.append({"kind":"actual_f4_input","frame":capture_tick,"loaded":replay != null})
	if replay != null and paused and not replay_pause_tested:
		var event := InputEventKey.new()
		event.keycode = KEY_ENTER;event.physical_keycode = KEY_ENTER;event.pressed = true
		_input(event)
		replay_pause_tested = true
		lifecycle.append({"kind":"enter_after_replay","frame":capture_tick,"overlay_visible":hud.menu.visible,"message":message})
		review_driver.save_file(review_trace)
		_finish_review()
		return
	if kind != "full_replay" and not restart_started and simulation.finished and ending_tick >= 100:
		_action("restart")
		restart_started = true
		restarted_at = capture_tick
		lifecycle.append({"kind":"restart","frame":capture_tick,"ko_active":ko_finish.active,"scene_cleared":ko_finish.scene == null,"tick":simulation.tick})
	if restart_started and capture_tick >= restarted_at + 90:
		_action("home")
		lifecycle.append({"kind":"home","frame":capture_tick,"front_visible":front.visible,"ko_active":ko_finish.active,"scene_cleared":ko_finish.scene == null})
		_finish_review()
		return
	var previous_tick: int = simulation.tick
	var previous_cursor: int = replay_cursor
	super._physics_process(delta)
	if review_driver.trace.is_empty(): return
	var row: Dictionary = review_driver.trace[-1]
	if replay != null:
		row.simulation_stepped = replay_cursor > previous_cursor
		row.inputs = replay.frames[replay_cursor-1].duplicate(true) if replay_cursor > previous_cursor else [[0,0,0],[0,0,0]]
	else:
		row.simulation_stepped = simulation.tick > previous_tick
	row.paused = paused
	row.ko = {"active":ko_finish.active,"real_age":ko_finish.real_age,"slow_age":ko_finish.slow_age,"effect_steps":ko_finish.effect_steps}
	row.phase = "restarted" if restart_started else "f4" if replay != null else "original"
	row.audio_played = audio.played.slice(audio_cursor).duplicate(true)
	audio_cursor = audio.played.size()
	row.hud = {"word":hud.word_key,"result_visible":hud.result_panel.visible,"top_bar_visible":hud.top_bar.visible}
	row.replay_cursor = replay_cursor
	row.replay_frames = replay.frames.size() if replay != null else 0
	var key: String = ""
	if simulation.finished and (ko_finish.real_age in [0,6,12,24,42,57,60] or ending_tick == 8):
		key = row.phase + ("-result" if ending_tick == 8 else "-ko-%02d" % ko_finish.real_age)
	if not key.is_empty() and not still_keys.has(key):
		still_keys[key] = true
		_save_still.call_deferred(key,capture_tick-1)

func _save_still(key: String, frame: int) -> void:
	if stills_dir.is_empty(): return
	await RenderingServer.frame_post_draw
	var picture := get_viewport().get_texture().get_image()
	if picture.get_width() > 768: picture.resize(768,roundi(picture.get_height()*768.0/picture.get_width()),Image.INTERPOLATE_LANCZOS)
	var path: String = stills_dir.path_join(key + ".jpg")
	if FileAccess.file_exists(path):
		push_error("拒绝覆盖KO审图")
		return
	if picture.save_jpg(path,0.8) != OK or FileAccess.get_file_as_bytes(path).size() > 150000:
		push_error("KO审图存储/大小不合格")
	review_driver.stills.append({"frame":frame,"key":key,"path":path,"sha256":FileAccess.get_sha256(path)})

func _finish_review() -> void:
	review_driver.release_keys()
	review_driver.save_file(review_trace)
	var output := FileAccess.open(review_trace.get_base_dir().path_join("lifecycle.json"),FileAccess.WRITE)
	output.store_string(JSON.stringify({"events":lifecycle,"case":review_driver.kind,"generated_videos":0}))
	output.close()
	shutdown()
