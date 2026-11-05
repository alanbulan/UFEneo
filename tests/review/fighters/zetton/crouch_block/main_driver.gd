extends UfeReviewDriver
## 单次正式攻击+受方蹲U；松蹲只在观察到真实block后改变下一tick输入。
const Factory=preload("res://tests/review/fighters/zetton/crouch_block/candidate_factory.gd")
var candidate_contract: Dictionary={}
var direction: int=1
var kind: String="low"
var input_tape: Dictionary={}
var output_directory: String=""
var failures: Array=[]
var stills: Array=[]
var saved: bool=false
var saw_stun: bool=false
var saw_contact: bool=false
func _init() -> void:
	profile="zetton_crouch_block"
	last_section=0
func length_frames() -> int:return Factory.LENGTH
func section(_frame: int) -> int:return 0
func boxes(_frame: int) -> bool:return false
func label(_frame: int) -> String:return "杰顿低蹲防御硬直候选 · "+kind
func prepare_match(sim: UfeMatchDirector) -> void:
	assert(sim.tick==0 and sim.fighters[0].definition.id=="ultraman" and sim.fighters[1].definition.id=="zetton")
	if not input_tape.is_empty():
		assert(Factory.verify_input_shape(input_tape).is_empty())
		assert(str(input_tape.simulation_fingerprint)==sim.content_fingerprint)
		assert(str(input_tape.candidate_contract_sha256)==str(candidate_contract._candidate_contract_sha256))
		assert(int(input_tape.direction)==direction and str(input_tape.kind)==kind)
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	if not input_tape.is_empty():return UfeInputFrame.unpack(input_tape.original_pairs[frame][0])
	if sim.fighters[1].state==Factory.ACTION:saw_stun=true
	return Factory.attacker_input(frame,kind,direction)
func second_sample(frame: int) -> UfeInputFrame:
	if not input_tape.is_empty():return UfeInputFrame.unpack(input_tape.original_pairs[frame][1])
	return UfeInputFrame.make(0,0 if kind=="release_down" and saw_stun else -1,UfeInputFrame.GUARD)
static func rect_array(r: Rect2) -> Array:return [r.position.x,r.position.y,r.size.x,r.size.y]
static func texture_source(view: UfeSideView,body: Sprite2D) -> String:
	for path in view.textures:
		if is_same(view.textures[path],body.texture):return str(path)
	return str(body.texture.resource_path) if body.texture!=null else ""
static func fighter_record(f: UfeFighter,animation: Dictionary) -> Dictionary:
	return {"id":f.definition.id,"state":f.state,"state_tick":f.state_tick,"duration":int(f.motion.duration),"move_id":f.move_id,"move_tick":f.move_tick,
		"x":f.x,"height":f.height,"vy":f.vy,"facing":f.facing,"hp":f.stats.hp,"stamina":f.stats.stamina,"animation":animation,"frame_sprite":int(f.frame().sprite)}
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair: Array=[]
	for i in range(2):
		var f:=sim.fighters[i]
		var body: Sprite2D=view.fighters[i]
		var animation: Dictionary=view._animation(f,view.manifests[i])
		var bounds: Rect2=view.get_global_transform()*view._sprite_bounds(body)
		var record: Dictionary=fighter_record(f,animation)
		record["full_alpha_viewport_bounds"]=rect_array(bounds)
		record["render_texture"]=texture_source(view,body)
		record["render_texture_resource_path"]=body.texture.resource_path
		record["render_region"]=rect_array(body.region_rect)
		record["render_region_enabled"]=body.region_enabled
		pair.append(record)
		if animation.is_empty() or int(animation.get("index",-1))!=int(f.frame().sprite) or record.render_texture!=str(animation.get("texture","")) or record.render_region!=animation.get("rect",[]) or not body.region_enabled:
			failures.append({"frame":frame,"player":i,"kind":"simulation_actual_texture_region_mismatch"})
		if bounds.position.x<0 or bounds.position.y<0 or bounds.end.x>640 or bounds.end.y>360:failures.append({"frame":frame,"player":i,"kind":"full_body_outside_viewport"})
	for event in sim.events:
		if str(event.get("kind","")) in ["hit","block"]:saw_contact=true
	if not input_tape.is_empty() and sim.state_hash()!=str(input_tape.state_hashes[frame]):failures.append({"frame":frame,"kind":"independent_replay_hash"})
	trace.append({"movie_frame":frame,"tick":sim.tick,"state_hash":sim.state_hash(),"original_inputs":last_inputs.duplicate(true),"pair":pair,
		"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"hitstop":sim.hitstop,"simulation_fingerprint":sim.content_fingerprint})
func _write_new(path: String,value: Dictionary) -> void:
	assert(not FileAccess.file_exists(path))
	var file:=FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify(value,"\t"));file.close()
func save_file(path: String) -> void:
	if saved or trace.size()<length_frames():return
	saved=true
	failures.append_array(Factory.verify_trace(candidate_contract,kind,trace))
	var tape: Dictionary={"format":"ufeneo_zetton_crouch_block_tape_v1","candidate_contract_sha256":candidate_contract._candidate_contract_sha256,
		"simulation_fingerprint":trace[0].simulation_fingerprint,"direction":direction,"kind":kind,
		"original_pairs":trace.map(func(row):return row.original_inputs),"state_hashes":trace.map(func(row):return row.state_hash),
		"events":trace.map(func(row):return row.events),"projectiles":trace.map(func(row):return row.projectiles)}
	var replay: Dictionary=Factory.verify_original_inputs(candidate_contract,tape)
	if not replay.errors.is_empty():failures.append({"kind":"fresh_sim_replay","errors":replay.errors})
	_write_new(output_directory.path_join("actual-input-tape.json"),tape)
	_write_new(output_directory.path_join("auxiliary-fresh-sim-replay.json"),replay)
	_write_new(path,{"trace":trace,"failures":failures,"stills":stills,"direction":direction,"kind":kind,"animation_ticks":[4,6],
		"graphical_review":false,"real_speed_art_accepted":false,"headless":DisplayServer.get_name()=="headless","installed":false,
		"input_source":"单次正式招式InputFrame，非真人键盘；松蹲仅首次block后，独立回放只读原输入带",
		"duration_note":"4/6为10行源映射；逐tick记录实际duration/state_tick/hitstop，不以静帧或脸灯位移声称实速通过"})
