extends "res://tools/rebuild/gomora/back_lift_resume/runtime/game.gd"
## 仅候选诊断：模拟与正式视图仍正常更新；绘制前隐藏独立FX，不改双方精灵和层序。
var diagnostic_headless_check: bool=false
var hidden_nodes: Array=[]
var diagnostic_tick_keys: Dictionary={}
func _ready() -> void:
	assert("--diagnostic-fx-hidden" in OS.get_cmdline_user_args())
	diagnostic_headless_check="--diagnostic-headless-check" in OS.get_cmdline_user_args()
	super._ready()
	RenderingServer.frame_pre_draw.connect(_hide_fx)
func _restore_fx() -> void:
	for item in hidden_nodes:
		if is_instance_valid(item.node):item.node.visible=item.visible
	hidden_nodes.clear()
func _hide_node(node: Sprite2D) -> void:
	if not is_instance_valid(node) or node.texture==null:return
	assert(node not in view.fighters)
	if hidden_nodes.any(func(item):return item.node==node):return
	hidden_nodes.append({"node":node,"visible":node.visible})
	node.visible=false
func _hide_fx() -> void:
	if view==null:return
	for slots in view.attached_slots:
		for node in slots:_hide_node(node)
	for node in view.weapon_trails:_hide_node(node)
	for particle in view.feedback.particles:_hide_node(particle.node)
	# 白闪不是独立节点；仅覆盖渲染材质参数，不改feedback计数或模拟。
	for fighter in view.fighters:
		(fighter.material as ShaderMaterial).set_shader_parameter("hit_flash",false)
func _physics_process(delta: float) -> void:
	# 在正式update_view及相机取景前恢复原可见性，保持正常呈现计算。
	_restore_fx()
	super._physics_process(delta)
	_hide_fx()
	if review_driver.trace.is_empty():return
	var row: Dictionary=review_driver.trace[-1]
	row.diagnostic_fx_hidden=true
	row.diagnostic_white_flash_hidden=true
	row.diagnostic_hidden_nodes=hidden_nodes.map(func(item):return {"texture":item.node.texture.resource_path,"was_visible":item.visible,"visible":item.node.visible})
	var a: Dictionary=row.pair[review_driver.owner]
	var raw: int=int(a.move_tick)
	if a.move=="special3" and raw>=20 and raw<=32 and not diagnostic_tick_keys.has(raw):
		diagnostic_tick_keys[raw]=true
		pending_stills+=1
		_save_still.call_deferred("diagnostic-raw-%02d"%raw,int(row.movie_frame))
func _save_still(label: String,requested_frame: int) -> void:
	if not diagnostic_headless_check:await RenderingServer.frame_post_draw
	var state: Dictionary=review_driver.snapshot(simulation)
	for i in range(2):state.pair[i].animation=view._animation(simulation.fighters[i],view.manifests[i])
	var item: Dictionary={"key":label,"requested_frame":requested_frame,"actual_frame":capture_tick-1,
		"diagnostic_fx_hidden":true,"diagnostic_white_flash_hidden":true,"headless_no_image":diagnostic_headless_check,"actual":state}
	if not diagnostic_headless_check:
		var picture: Image=get_viewport().get_texture().get_image()
		var actual:=Vector2i(picture.get_width(),picture.get_height())
		if actual!=window_size or DisplayServer.window_get_size()!=window_size:
			review_driver.failures.append({"kind":"wrong_native_capture_size","actual":[actual.x,actual.y]})
		var path: String=stills_dir.path_join(label+".png")
		assert(not FileAccess.file_exists(path));assert(picture.save_png(path)==OK)
		item.merge({"path":path,"sha256":FileAccess.get_sha256(path),"dimensions":[actual.x,actual.y],"resized":false})
	if label.begins_with("diagnostic-raw-"):
		var requested_raw:=int(label.trim_prefix("diagnostic-raw-"))
		if int(state.pair[review_driver.owner].move_tick)!=requested_raw or capture_tick-1!=requested_frame:
			review_driver.failures.append({"kind":"diagnostic_capture_frame_mismatch","requested_raw":requested_raw,"actual_raw":state.pair[review_driver.owner].move_tick})
	review_driver.stills.append(item)
	pending_stills-=1
func _finish() -> void:
	while pending_stills>0:await get_tree().process_frame
	review_driver.save_file(review_trace)
	var saved: Dictionary=UfeContentDatabase.read_json(review_trace)
	saved.diagnostic_fx_hidden=true
	saved.diagnostic_white_flash_hidden=true
	saved.diagnostic_headless_check=diagnostic_headless_check
	saved.diagnostic_scope="只隐藏独立附着/拖尾/命中粒子FX；仅渲染前覆盖白闪shader参数，双方精灵/层序/动画/模拟/计时正常；不能替代正常FX验收。"
	var file:=FileAccess.open(review_trace,FileAccess.WRITE);assert(file!=null)
	file.store_string(JSON.stringify(saved));file.close()
	review_driver.release_keys()
	shutdown(0 if review_driver.failures.is_empty() else 1)
