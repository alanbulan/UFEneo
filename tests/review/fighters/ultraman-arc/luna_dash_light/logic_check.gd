extends SceneTree
## 正式模拟+真实InputFrame的6个候选用例；不称画面验收。
const Factory = preload("res://tests/review/fighters/ultraman-arc/luna_dash_light/candidate_factory.gd")
const Driver = preload("res://tests/review/fighters/ultraman-arc/luna_dash_light/main_driver.gd")
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var path: String = ""
	var out: String = ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="): path = arg.trim_prefix("--contract=")
		elif arg.begins_with("--out="): out = arg.trim_prefix("--out=")
		else: assert(false, "未知候选检查参数")
	assert(not path.is_empty() and not out.is_empty())
	out = ProjectSettings.globalize_path(out).simplify_path()
	assert(out.begins_with(ProjectSettings.globalize_path("res://reports/luna-dash-light-resume/")))
	assert(not FileAccess.file_exists(out))
	var cfg: Dictionary = Factory.read_sealed(path)
	var errors: Array = []
	var results: Array = []
	var all_phases: Dictionary = {}
	var presentation_probe := UfeSideView.new()
	presentation_probe.intro_tick = -1
	for direction in [1, -1]:
		for kind in ["hit", "block", "whiff"]:
			var sim := Factory.make_match(cfg, direction, kind)
			var driver = Driver.new()
			driver.candidate_contract = cfg
			driver.direction = direction
			driver.kind = kind
			var start_hp: int = sim.fighters[1].stats.hp
			var pairs: Array = []
			var hashes: Array = []
			var moves: Dictionary = {}
			var phase_trace: Array = []
			var contacts: Dictionary = {}
			var contact_counts: Dictionary = {}
			for tick in range(driver.length_frames()):
				var first: UfeInputFrame = driver.sample(tick, sim)
				var second: UfeInputFrame = driver.second_sample(tick)
				pairs.append([first.pack(), second.pack()])
				sim.step([first, second])
				hashes.append(sim.state_hash())
				for event in sim.events:
					if str(event.get("kind", "")) in ["hit", "block"] and int(event.get("player", -1)) == 0:
						contacts[str(event.move)] = str(event.kind)
						contact_counts[str(event.move)] = int(contact_counts.get(str(event.move),0))+1
				var f := sim.fighters[0]
				var pair_trace: Array = []
				for fighter in sim.fighters:
					pair_trace.append({"move_id": fighter.move_id, "state": fighter.state, "frame_sprite": int(fighter.frame().sprite), "x": fighter.x, "height": fighter.height})
				phase_trace.append({"pair": pair_trace})
				var animation: Dictionary = presentation_probe._animation(f, cfg.presentation.manifest_data)
				if animation.is_empty() or not Factory.animation_matches(animation, int(f.frame().sprite), cfg):
					errors.append({"kind": "simulation_presentation_phase_mismatch", "tick": tick, "move": f.move_id})
				if not f.move_id.is_empty():
					moves[f.move_id] = true
					all_phases[f.move_id+":"+str(int(f.frame().sprite))] = true
			var damage: int = start_hp - int(sim.fighters[1].stats.hp)
			var tape: Dictionary = {"candidate_contract_sha256": cfg._candidate_contract_sha256,
				"simulation_fingerprint": sim.content_fingerprint, "direction": direction, "kind": kind,
				"original_pairs": pairs, "state_hashes": hashes}
			var replay: Dictionary = Factory.verify_original_inputs(cfg, tape)
			var record: Dictionary = {"direction": direction, "kind": kind, "damage": damage,
				"forward_displacement": (sim.fighters[0].x-int(phase_trace[0].pair[0].x))*direction,
				"target_pushback": (sim.fighters[1].x-int(phase_trace[0].pair[1].x))*direction,
				"moves": moves.keys(), "contacts": contacts, "contact_counts": contact_counts, "initial_gap": Factory.WHIFF_GAP if kind == "whiff" else Factory.HIT_GAP, "replay_errors": replay.errors, "final_hash": sim.state_hash()}
			results.append(record)
			if not replay.errors.is_empty(): errors.append({"kind": "replay_mismatch", "case": record})
			var case_errors: Array = Factory.verify_case(cfg,kind,moves,contacts,contact_counts,damage)
			case_errors.append_array(Factory.verify_phases(phase_trace))
			case_errors.append_array(Factory.verify_motion(phase_trace, direction, kind))
			for error in case_errors: errors.append({"error":error,"case":record})
	for action in ["dash_light"]:
		for phase in range(5):
			if not all_phases.has(action+":"+str(phase)): errors.append({"kind": "unreached_phase", "action": action, "phase": phase})
	presentation_probe.free()
	var file := FileAccess.open(out, FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify({"cases": results, "errors": errors, "phases": all_phases.keys(), "graphical_review": false,
		"installed": false, "playable": false, "original_inputs_replayed": true, "simulation_presentation_phase_checked": true, "double_forward_then_light_input_checked": true, "real_displacement_and_pushback_checked": true,
		"candidate_contract_sha256": cfg._candidate_contract_sha256}, "\t"))
	file.close()
	print("月亮冲刺轻拳逻辑用例：", results.size(), "，错误：", errors.size())
	quit(0 if errors.is_empty() else 1)
