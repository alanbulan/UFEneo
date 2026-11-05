extends "res://app/game_app.gd"
## 实例化正式main，只换首局工厂与内存clips，截图是原生720/1080PNG。
const Factory=preload("res://tools/rebuild/gomora/back_lift_resume/runtime/factory.gd")
var candidate_contract: Dictionary={}
var candidate_contract_path: String=""
var stills_dir: String=""
var window_size:=Vector2i(1280,720)
var keys_seen: Dictionary={}
var pending_stills: int=0
var finishing: bool=false
func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--back-lift-stills="):stills_dir=arg.trim_prefix("--back-lift-stills=")
		elif arg.begins_with("--back-lift-size="):
			var parts:=arg.trim_prefix("--back-lift-size=").split("x")
			window_size=Vector2i(int(parts[0]),int(parts[1]))
	assert(window_size in [Vector2i(1280,720),Vector2i(1920,1080)])
	assert(not stills_dir.is_empty());DirAccess.make_dir_recursive_absolute(stills_dir)
	super._ready()
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(window_size)
func _battle_match(_first: String,_second: String,_allow_pilot: bool=false) -> UfeMatchDirector:
	return Factory.make_match(candidate_contract,review_driver.owner,review_driver.kind)
func start_match() -> void:
	training=false;super.start_match();intro=75
	view.walk_review_clip=candidate_contract_path
	for i in range(2):
		var identity: String=simulation.fighters[i].definition.id
		if candidate_contract.clips.has(identity):
			view.manifests[i]=view.manifests[i].duplicate(true)
			view.manifests[i].clips.merge(candidate_contract.clips[identity].duplicate(true),true)
	view.update_view()
func reset_round() -> void:assert(false,"候选固定单局，不进入正式再战")
func _input(_event: InputEvent) -> void:pass
func _action(_name: String) -> void:pass
func _front_action(_name: String) -> void:pass
func _physics_process(delta: float) -> void:
	if capture_tick>=review_driver.capture_length():
		if not finishing:
			finishing=true;set_physics_process(false);_finish.call_deferred()
		return
	super._physics_process(delta)
	if review_driver.trace.is_empty():return
	var row: Dictionary=review_driver.trace[-1]
	row.actual_window_size=[DisplayServer.window_get_size().x,DisplayServer.window_get_size().y]
	var owner: int=review_driver.owner
	var labels: Array=[]
	if row.pair[owner].move=="special3":
		labels.append("body-%02d"%int(row.pair[owner].animation.get("index",-1)))
		if row.pair[1-owner].state=="thrown":labels.append("receiver-"+str(row.pair[1-owner].animation.get("key",""))+"-%02d"%int(row.pair[1-owner].animation.get("index",-1)))
	for event in row.events:
		if event.kind in ["hit","throw_slam","throw_tech","throw_whiff"]:labels.append(str(event.kind))
	for label in labels:
		if not keys_seen.has(label):
			keys_seen[label]=true;pending_stills+=1;_save_still.call_deferred(str(label),int(row.movie_frame))
func _save_still(label: String,requested_frame: int) -> void:
	await RenderingServer.frame_post_draw
	var picture: Image=get_viewport().get_texture().get_image()
	var actual:=Vector2i(picture.get_width(),picture.get_height())
	if actual!=window_size or DisplayServer.window_get_size()!=window_size:
		review_driver.failures.append({"kind":"wrong_native_capture_size","actual":[actual.x,actual.y]})
	var path: String=stills_dir.path_join(label+".png")
	assert(not FileAccess.file_exists(path));assert(picture.save_png(path)==OK)
	var state: Dictionary=review_driver.snapshot(simulation)
	for i in range(2):state.pair[i].animation=view._animation(simulation.fighters[i],view.manifests[i])
	review_driver.stills.append({"key":label,"requested_frame":requested_frame,"actual_frame":capture_tick-1,"path":path,
		"sha256":FileAccess.get_sha256(path),"dimensions":[actual.x,actual.y],"resized":false,"actual":state})
	pending_stills-=1
func _finish() -> void:
	while pending_stills>0:await get_tree().process_frame
	review_driver.save_file(review_trace)
	review_driver.release_keys()
	shutdown(0 if review_driver.failures.is_empty() else 1)
