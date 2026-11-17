extends UfeReviewDriver
const Factory=preload("res://tests/review/app/hud_framing/factory.gd")
var contract: Dictionary={}
var direction: int=1
var output_directory: String=""
var input_tape: Dictionary={}
var failures: Array=[]
var stills: Array=[]
var saved: bool=false
func _init() -> void:
	profile="hud_framing"
	last_section=0
func length_frames() -> int:return int(contract.length_frames)
func section(_frame: int) -> int:return 0
func boxes(_frame: int) -> bool:return false
func label(_frame: int) -> String:return "镜头/HUD完整轮廓回归"
func prepare_match(sim: UfeMatchDirector) -> void:
	assert(sim.tick==0)
	if not input_tape.is_empty():assert(input_tape.contract_sha256==contract.contract_sha256 and int(input_tape.direction)==direction)
func wanted(frame: int,index: int) -> UfeInputFrame:
	var pair: Array=contract.inputs[frame]
	var raw: Array=pair[index].duplicate()
	raw[0]=int(raw[0])*direction
	return UfeInputFrame.unpack(raw)
func sample(frame: int,_sim: UfeMatchDirector) -> UfeInputFrame:
	return wanted(frame,0) if input_tape.is_empty() else UfeInputFrame.unpack(input_tape.original_pairs[frame][0])
func second_sample(frame: int) -> UfeInputFrame:
	return wanted(frame,1) if input_tape.is_empty() else UfeInputFrame.unpack(input_tape.original_pairs[frame][1])
static func rect_array(r: Rect2) -> Array:return [r.position.x,r.position.y,r.size.x,r.size.y]
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair: Array=[]
	for i in range(2):
		var f:=sim.fighters[i]
		var bounds: Rect2=view.get_global_transform()*view._sprite_bounds(view.fighters[i])
		var animation: Dictionary=view._animation(f,view.manifests[i])
		pair.append({"id":f.definition.id,"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"height":f.height,"x":f.x,"facing":f.facing,"hp":f.stats.hp,"energy":f.stats.energy,"frame_sprite":int(f.frame().sprite),"animation":animation,"full_alpha_viewport_bounds":rect_array(bounds)})
		if not view.framing_safe_rect.grow(0.1).encloses(bounds):failures.append({"frame":frame,"player":i,"kind":"body_outside_hud_safe_area","bounds":rect_array(bounds),"safe":rect_array(view.framing_safe_rect)})
	var entities: Array=[]
	for node in view.framing_entities:
		var bounds: Rect2=view.get_global_transform()*view._sprite_bounds(node)
		entities.append({"texture":node.texture.resource_path,"region":rect_array(node.region_rect),"bounds":rect_array(bounds)})
		if not view.framing_safe_rect.grow(0.1).encloses(bounds):failures.append({"frame":frame,"kind":"weapon_outside_hud_safe_area"})
	if not input_tape.is_empty() and sim.state_hash()!=str(input_tape.state_hashes[frame]):failures.append({"frame":frame,"kind":"independent_replay_hash_mismatch"})
	trace.append({"movie_frame":frame,"tick":sim.tick,"state_hash":sim.state_hash(),"pair":pair,"entities":entities,"safe_rect":rect_array(view.framing_safe_rect),"camera_zoom":view.camera_zoom,"original_inputs":last_inputs.duplicate(true),"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)})
func write_new(path: String,value: Dictionary) -> void:
	assert(not FileAccess.file_exists(path))
	var file:=FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify(value,"\t"))
func save_file(path: String) -> void:
	if saved or trace.size()<length_frames():return
	saved=true
	var replay:=Factory.make_match(contract,direction)
	var tape: Dictionary={"contract_sha256":contract.contract_sha256,"direction":direction,"original_pairs":[],"state_hashes":[]}
	for row in trace:
		tape.original_pairs.append(row.original_inputs)
		tape.state_hashes.append(row.state_hash)
		replay.step([UfeInputFrame.unpack(row.original_inputs[0]),UfeInputFrame.unpack(row.original_inputs[1])])
		if replay.state_hash()!=row.state_hash:failures.append({"tick":row.tick,"kind":"fresh_sim_hash_mismatch"})
	write_new(output_directory.path_join("actual-input-tape.json"),tape)
	write_new(path,{"contract_sha256":contract.contract_sha256,"direction":direction,"trace":trace,"stills":stills,"failures":failures,"writes_user_settings":false,"writes_last_replay":false})
