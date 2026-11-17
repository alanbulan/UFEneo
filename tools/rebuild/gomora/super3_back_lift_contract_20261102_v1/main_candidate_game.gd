extends "res://app/game_app.gd"
var stills_dir: String=""
var keys_seen: Dictionary={}
var window_size: Vector2i=Vector2i(1280,720)
func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--back-lift-stills="):stills_dir=arg.trim_prefix("--back-lift-stills=")
		if arg.begins_with("--back-lift-size="):
			var dimensions: PackedStringArray=arg.trim_prefix("--back-lift-size=").split("x")
			window_size=Vector2i(int(dimensions[0]),int(dimensions[1]))
	assert(not stills_dir.is_empty());DirAccess.make_dir_recursive_absolute(stills_dir)
	super._ready()
	# 正式_ready会应用用户全屏偏好；仅本次harness窗口覆盖，不持久化偏好。
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(window_size)
	Engine.physics_ticks_per_second=60
func _battle_match(first: String,second: String,_allow_pilot: bool=false) -> UfeMatchDirector:return super._battle_match(first,second,false)
func start_match() -> void:
	training=false;selected_fighters=review_driver.matchup();super.start_match();intro=75
func reset_round() -> void:
	training=false;selected_fighters=review_driver.matchup();super.reset_round();intro=75
func _physics_process(delta: float) -> void:
	assert(DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_WINDOWED and DisplayServer.window_get_size()==window_size)
	assert(Engine.physics_ticks_per_second==60)
	if review and capture_tick>=review_driver.capture_length():
		review_driver.save_file(review_trace);shutdown();return
	super._physics_process(delta)
	if not review or not is_instance_valid(view) or review_driver.trace.is_empty():return
	var row: Dictionary=review_driver.trace[-1]
	row.actual_window_size=[DisplayServer.window_get_size().x,DisplayServer.window_get_size().y]
	row.actual_window_mode=DisplayServer.window_get_mode();row.physics_ticks_per_second=Engine.physics_ticks_per_second
	var owner: int=int(row.owner)
	hud.debug_visible=true;hud.debug_label.text=review_driver.label(int(row.movie_frame));hud.debug_label.show();training_overlay.hide()
	var labels: Array=[]
	if row.pair[owner].move=="special3":
		labels.append("body-phase-%02d"%int(row.pair[owner].animation.get("index",-1)))
		if row.pair[1-owner].state=="thrown":labels.append("receiver-"+str(row.pair[1-owner].animation.get("key",""))+"-%02d"%int(row.pair[1-owner].animation.get("index",-1)))
	for event in row.events:
		if event.kind in ["hit","throw_slam","throw_tech","throw_whiff"]:labels.append(str(event.kind))
	for label in labels:
		if not keys_seen.has(label):keys_seen[label]=true;save_still.call_deferred(str(label),int(row.movie_frame))
func save_still(label: String,requested_frame: int) -> void:
	var path: String=stills_dir.path_join(label+".jpg");assert(not FileAccess.file_exists(path))
	await RenderingServer.frame_post_draw
	if not is_instance_valid(view):return
	var actual: Dictionary=review_driver.snapshot(simulation)
	for i in range(2):actual.pair[i].animation=view._animation(simulation.fighters[i],view.manifests[i]).duplicate(true)
	var picture: Image=view.get_viewport().get_texture().get_image();assert(picture.get_width()==640 and picture.get_height()==360)
	assert(picture.save_jpg(path,0.8)==OK);assert(FileAccess.get_file_as_bytes(path).size()<=150000)
	review_driver.stills.append({"key":label,"requested_frame":requested_frame,"actual_frame":capture_tick-1,"path":path,"sha256":FileAccess.get_sha256(path),"actual":actual})
