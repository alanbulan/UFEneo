extends UfeReviewDriver
## 输入真实按下保持松开downInputFrame；正式main推进，观察器不写任何sim字段。
const Factory = preload("res://tests/review/fighters/ultraman-arc/galaxion_crouch/candidate_factory.gd")
const CROUCH_STARTS := [24,102]
var candidate_contract: Dictionary = {}
var direction: int = 1
var input_tape: Dictionary = {}
var output_directory: String = ""
var failures: Array = []
var stills: Array = []
var saved: bool = false

func _init() -> void:
	profile = "arc_galaxion_s2_crouch_whole_candidate"
	last_section = 0

func length_frames() -> int:return 240
func section(_frame: int) -> int:return 0
func boxes(_frame: int) -> bool:return false
func label(_frame: int) -> String:return "银河装甲 · 入蹲 / 保持 / 起身 / 再次触发" + (" · 原输入回放" if not input_tape.is_empty() else "")

func prepare_match(sim: UfeMatchDirector) -> void:
	assert(sim.tick == 0 and sim.fighters[0].definition.id == "ultraman-arc__galaxion")
	assert(sim.fighters[0].base_definition == sim.fighters[0].definition)
	if not input_tape.is_empty():
		assert(str(input_tape.format) == "ufeneo_galaxion_crouch_candidate_tape_v1")
		assert(str(input_tape.candidate_contract_sha256) == str(candidate_contract._candidate_contract_sha256))
		assert(str(input_tape.source_fingerprint) == str(candidate_contract.source_fingerprint))
		assert(str(input_tape.simulation_fingerprint) == sim.content_fingerprint)
		assert(int(input_tape.direction) == direction and input_tape.original_pairs.size() == length_frames())

func requested_input(frame: int) -> UfeInputFrame:
	return UfeInputFrame.make(0,-1) if (frame>=24 and frame<78) or (frame>=102 and frame<156) else UfeInputFrame.make()

func sample(frame: int, _sim: UfeMatchDirector) -> UfeInputFrame:
	return UfeInputFrame.unpack(input_tape.original_pairs[frame][0]) if not input_tape.is_empty() else requested_input(frame)

func second_sample(frame: int) -> UfeInputFrame:
	return UfeInputFrame.unpack(input_tape.original_pairs[frame][1]) if not input_tape.is_empty() else UfeInputFrame.make()

func expected_phase(ticks: Array, n: int) -> int:
	var cursor: int = 0
	for phase in range(ticks.size()):
		cursor += int(ticks[phase])
		if n < cursor:return phase
	return ticks.size()-1

func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	var episode: int = -1
	var n: int = -1
	for index in range(2):
		if frame >= int(CROUCH_STARTS[index]) and frame <= int(CROUCH_STARTS[index])+60:
			episode=index;n=frame-int(CROUCH_STARTS[index]);break
	var pair: Array = []
	for index in range(2):
		var fighter := sim.fighters[index]
		var animation: Dictionary = view._animation(fighter,view.manifests[index])
		var bounds: Rect2 = view.get_global_transform() * view._sprite_bounds(view.fighters[index])
		pair.append({"id":fighter.definition.id,"state":fighter.state,"state_tick":fighter.state_tick,"x":fighter.x,"height":fighter.height,
			"vx":fighter.vx,"vy":fighter.vy,"facing":fighter.facing,"jump_kind":str(fighter.motion.jump_kind),"animation":animation,
			"frame_sprite":int(fighter.frame().sprite),"stamina":int(fighter.stats.stamina),"hp":int(fighter.stats.hp),
			"full_alpha_viewport_bounds":[bounds.position.x,bounds.position.y,bounds.size.x,bounds.size.y]})
		if bounds.position.x < 0 or bounds.position.y < 0 or bounds.end.x > 640 or bounds.end.y > 360:failures.append({"frame":frame,"kind":"full_body_outside_viewport","player":index})
	var actual: Dictionary = pair[0]
	if actual.animation.is_empty():failures.append({"frame":frame,"kind":"missing_galaxion_clip"})
	if episode >= 0:
		var expected_state: String = "crouch_start" if n<6 else "crouch" if n<54 else "crouch_rise" if n<60 else "idle"
		var expected_tick: int = n if n<6 else n-6 if n<54 else n-54 if n<60 else 0
		var base_x: int = int(trace[int(CROUCH_STARTS[episode])-1].pair[0].x)
		if actual.state != expected_state or int(actual.state_tick) != expected_tick:failures.append({"frame":frame,"kind":"state_clock_mismatch","n":n})
		if int(actual.height)!=0 or int(actual.x)!=base_x:failures.append({"frame":frame,"kind":"stationary_crouch_mismatch","n":n})
		var duration: int = 24 if expected_state=="crouch" else 60 if expected_state=="idle" else 6
		var expected: int = expected_phase(Factory.CLOCKS[expected_state],expected_tick%duration)
		if str(actual.animation.get("key",""))!=expected_state or int(actual.animation.get("index",-1))!=expected or int(actual.frame_sprite)!=expected:failures.append({"frame":frame,"kind":"phase_mismatch","n":n})
	for index in range(2):
		var expected_input: Array = requested_input(frame).pack() if index == 0 else UfeInputFrame.make().pack()
		if last_inputs[index] != expected_input:failures.append({"frame":frame,"kind":"unexpected_original_input","player":index})
	var state_hash: String = sim.state_hash()
	if not input_tape.is_empty():
		if state_hash != str(input_tape.state_hashes[frame]):failures.append({"frame":frame,"kind":"independent_original_input_hash_mismatch"})
		for key in ["events","projectiles"]:
			if JSON.stringify(JSON.parse_string(JSON.stringify(sim.get(key))),"",true) != JSON.stringify(input_tape[key][frame],"",true):failures.append({"frame":frame,"kind":"independent_"+key+"_mismatch"})
	trace.append({"movie_frame":frame,"tick":sim.tick,"state_hash":state_hash,"crouch_episode":episode,"input_relative_n":n,
		"simulation_fingerprint":sim.content_fingerprint,"original_inputs":last_inputs.duplicate(true),"pair":pair,
		"camera_x":view.camera_x,"camera_zoom":view.camera_zoom,"view_position":[view.position.x,view.position.y],
		"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)})

func _write_new(path: String, value: Dictionary) -> void:
	assert(not FileAccess.file_exists(path))
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(value,"\t"))

func save_file(path: String) -> void:
	if saved or trace.size() < length_frames():return
	saved=true
	var pairs: Array=[]
	var hashes: Array=[]
	var event_tape: Array=[]
	var projectile_tape: Array=[]
	for row in trace:
		pairs.append(row.original_inputs);hashes.append(row.state_hash);event_tape.append(row.events);projectile_tape.append(row.projectiles)
	var tape: Dictionary={"format":"ufeneo_galaxion_crouch_candidate_tape_v1","candidate_contract_sha256":candidate_contract._candidate_contract_sha256,
		"source_fingerprint":candidate_contract.source_fingerprint,"simulation_fingerprint":trace[0].simulation_fingerprint,"direction":direction,
		"initial_positions":candidate_contract.initial_positions["right" if direction > 0 else "left"],"original_pairs":pairs,"state_hashes":hashes,"events":event_tape,"projectiles":projectile_tape}
	var auxiliary: Dictionary=Factory.verify_original_inputs(candidate_contract,tape)
	if not auxiliary.errors.is_empty():failures.append({"kind":"fresh_sim_original_input_replay","errors":auxiliary.errors})
	_write_new(output_directory.path_join("actual-input-tape.json"),tape)
	_write_new(output_directory.path_join("auxiliary-fresh-sim-replay.json"),auxiliary)
	_write_new(path,{"mode":"independent_visible_replay" if not input_tape.is_empty() else "actual_main_inputframe_recording",
		"input_source":"正式main训练按下保持松开down输入对应InputFrame；非真人硬件，建sim之后无位置/状态覆写。",
		"candidate_contract_sha256":candidate_contract._candidate_contract_sha256,"source_fingerprint":candidate_contract.source_fingerprint,
		"direction":direction,"trace":trace,"failures":failures,"stills":stills,"writes_user_settings":false,"writes_last_replay":false,
		"playable":false,"transform_enabled":false,"crouch_art_accepted":false})
