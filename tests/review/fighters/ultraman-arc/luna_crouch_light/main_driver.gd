extends UfeReviewDriver
## 只送持续下方向+LIGHT一次 InputFrame；观察器从不修改模拟和位置。
const Factory = preload("res://tests/review/fighters/ultraman-arc/luna_crouch_light/candidate_factory.gd")
var candidate_contract: Dictionary = {}
var direction: int = 1
var kind: String = "hit"
var input_tape: Dictionary = {}
var output_directory: String = ""
var failures: Array = []
var stills: Array = []
var saved: bool = false

func _init() -> void:
	profile = "luna_crouch_light"
	last_section = 0
func length_frames() -> int: return 180
func section(_frame: int) -> int: return 0
func boxes(_frame: int) -> bool: return false
func label(_frame: int) -> String: return "月亮蹲左拳候选 · " + kind
func prepare_match(sim: UfeMatchDirector) -> void:
	assert(sim.tick == 0 and sim.fighters[0].definition.id == "ultraman-arc__luna")
	if not input_tape.is_empty():
		assert(Factory.verify_input_shape(input_tape).is_empty())
		assert(str(input_tape.simulation_fingerprint) == sim.content_fingerprint)
		assert(str(input_tape.candidate_contract_sha256) == str(candidate_contract._candidate_contract_sha256))
		assert(int(input_tape.direction) == direction and str(input_tape.kind) == kind)

func sample(frame: int, _sim: UfeMatchDirector) -> UfeInputFrame:
	if not input_tape.is_empty(): return UfeInputFrame.unpack(input_tape.original_pairs[frame][0])
	return UfeInputFrame.make(0, -1, UfeInputFrame.LIGHT if frame == 20 else 0)

func second_sample(frame: int) -> UfeInputFrame:
	if not input_tape.is_empty(): return UfeInputFrame.unpack(input_tape.original_pairs[frame][1])
	return UfeInputFrame.make(0, -1 if kind == "block" else 0, UfeInputFrame.GUARD if kind in ["block", "stand_guard"] else 0)

func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	var pair: Array = []
	for index in range(2):
		var f := sim.fighters[index]
		var animation: Dictionary = view._animation(f, view.manifests[index])
		var bounds: Rect2 = view.get_global_transform() * view._sprite_bounds(view.fighters[index])
		pair.append({"id": f.definition.id, "state": f.state, "state_tick": f.state_tick, "move_id": f.move_id, "move_tick": f.move_tick,
			"x": f.x, "height": f.height, "vy": f.vy, "facing": f.facing, "hp": f.stats.hp, "stamina": f.stats.stamina, "animation": animation,
			"frame_sprite": int(f.frame().sprite), "full_alpha_viewport_bounds": [bounds.position.x,bounds.position.y,bounds.size.x,bounds.size.y]})
		if bounds.position.x < 0 or bounds.position.y < 0 or bounds.end.x > 640 or bounds.end.y > 360:
			failures.append({"frame": frame, "kind": "full_body_outside_viewport", "player": index})
	if pair[0].animation.is_empty() or int(pair[0].animation.get("index", -1)) != int(pair[0].frame_sprite):
		failures.append({"frame": frame, "kind": "simulation_presentation_phase_mismatch"})
	var state_hash: String = sim.state_hash()
	if not input_tape.is_empty() and state_hash != str(input_tape.state_hashes[frame]):
		failures.append({"frame": frame, "kind": "independent_replay_hash"})
	trace.append({"movie_frame": frame, "tick": sim.tick, "state_hash": state_hash, "original_inputs": last_inputs.duplicate(true),
		"pair": pair, "events": sim.events.duplicate(true), "projectiles": sim.projectiles.duplicate(true), "simulation_fingerprint": sim.content_fingerprint})

func _write_new(path: String, value: Dictionary) -> void:
	assert(not FileAccess.file_exists(path))
	var file := FileAccess.open(path, FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(value, "\t"))

func save_file(path: String) -> void:
	if saved or trace.size() < length_frames(): return
	saved = true
	var pairs: Array = []
	var hashes: Array = []
	var moves: Dictionary = {}
	var contacts: Dictionary = {}
	var contact_counts: Dictionary = {}
	for row in trace:
		pairs.append(row.original_inputs)
		hashes.append(row.state_hash)
		var action: String = str(row.pair[0].move_id)
		if not action.is_empty(): moves[action] = true
		for event in row.events:
			if str(event.get("kind","")) in ["hit","block"] and int(event.get("player",-1)) == 0:
				contacts[str(event.move)] = str(event.kind)
				contact_counts[str(event.move)] = int(contact_counts.get(str(event.move),0))+1
	var damage: int = int(trace[0].pair[1].hp)-int(trace[-1].pair[1].hp)
	failures.append_array(Factory.verify_case(candidate_contract,kind,moves,contacts,contact_counts,damage))
	failures.append_array(Factory.verify_phases(trace))
	failures.append_array(Factory.verify_grounded_receiver(trace,kind))
	var tape: Dictionary = {"format": "ufeneo_luna_crouch_light_tape_v1", "candidate_contract_sha256": candidate_contract._candidate_contract_sha256,
		"simulation_fingerprint": trace[0].simulation_fingerprint, "direction": direction, "kind": kind,
		"original_pairs": pairs, "state_hashes": hashes, "events": trace.map(func(row): return row.events), "projectiles": trace.map(func(row): return row.projectiles)}
	var replay: Dictionary = Factory.verify_original_inputs(candidate_contract, tape)
	if not replay.errors.is_empty(): failures.append({"kind": "fresh_sim_replay", "errors": replay.errors})
	_write_new(output_directory.path_join("actual-input-tape.json"), tape)
	_write_new(output_directory.path_join("auxiliary-fresh-sim-replay.json"), replay)
	_write_new(path, {"trace": trace, "failures": failures, "stills": stills, "direction": direction, "kind": kind,
		"animation_ticks": candidate_contract.animation_ticks, "graphical_review": false, "headless": DisplayServer.get_name() == "headless",
		"input_source": "持续下方向+LIGHT一次的InputFrame，非真人硬件；独立回放不再次采样自适应输入", "installed": false, "playable": false})
