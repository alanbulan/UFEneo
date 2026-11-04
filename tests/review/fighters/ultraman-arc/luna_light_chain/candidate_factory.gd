extends RefCounted
## 三连只在正式main的内存候选定义中装配；不修改装甲开放状态。
static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema) == "ufeneo.luna.light-chain-main-candidate.v1")
	assert(bool(cfg.root_runtime_ready) and not bool(cfg.playable))
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "月亮候选来源变化")
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc__luna/definition.json")
	for flag in ["implemented", "playable", "select_visible"]: assert(not bool(flags[flag]))
	assert(cfg.definition.moves.size() == 3)
	for action in ["light1", "light2", "light3"]:
		assert(cfg.definition.moves.has(action) and cfg.presentation.manifest_data.clips.has(action))
	cfg["_candidate_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg

static func make_match(cfg: Dictionary, direction: int, kind: String) -> UfeMatchDirector:
	assert(direction in [-1, 1] and kind in ["hit", "block", "whiff"])
	var raw: Dictionary = cfg.definition
	var first := UfeFighterDefinition.new()
	first.id = str(raw.id)
	first.display_name = str(raw.display_name)
	first.max_health = int(raw.max_health)
	first.walk_speed = int(raw.walk_speed)
	first.jump_speed = int(raw.jump_speed)
	first.body_radius = int(raw.body_radius)
	first.moves = raw.moves.duplicate(true)
	for move in first.moves.values(): assert(UfeMoveData.validate(move))
	first.command_table = raw.command_table.duplicate(true)
	first.state_frames = raw.state_frames.duplicate(true)
	var second := UfeContentDatabase.fighter(str(cfg.opponent), false)
	var sim := UfeMatchDirector.new(first, second, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), {})
	var gap: int = 260 if kind == "whiff" else 70
	sim.fighters[0].x = 640 - direction * 50
	sim.fighters[1].x = sim.fighters[0].x + direction * gap
	sim.fighters[0].facing = direction
	sim.fighters[1].facing = -direction
	return sim

static func verify_original_inputs(cfg: Dictionary, tape: Dictionary) -> Dictionary:
	assert(str(tape.candidate_contract_sha256) == str(cfg._candidate_contract_sha256))
	var sim := make_match(cfg, int(tape.direction), str(tape.kind))
	assert(sim.content_fingerprint == str(tape.simulation_fingerprint))
	var errors: Array = []
	for tick in range(tape.original_pairs.size()):
		var pair: Array = tape.original_pairs[tick]
		sim.step([UfeInputFrame.unpack(pair[0]), UfeInputFrame.unpack(pair[1])])
		if sim.state_hash() != str(tape.state_hashes[tick]): errors.append({"tick": tick, "kind": "state_hash"})
	return {"errors": errors, "final_hash": sim.state_hash(), "tick_count": sim.tick}

static func verify_case(cfg: Dictionary, kind: String, depth: int, moves: Dictionary, contacts: Dictionary, counts: Dictionary, damage: int) -> Array:
	var errors: Array = []
	var expected_count: int = depth if kind == "hit" else 1
	if moves.size() != expected_count: errors.append({"kind": "unexpected_move_count", "moves": moves.keys()})
	for index in range(expected_count):
		if not moves.has("light%d" % (index+1)): errors.append({"kind": "missing_move", "stage": index+1})
	if kind == "hit":
		var expected_damage: int = 0
		for index in range(depth):
			var action: String = "light%d" % (index+1)
			expected_damage += int(cfg.definition.moves[action].damage)
			if str(contacts.get(action,"")) != "hit" or int(counts.get(action,0)) != 1:
				errors.append({"kind": "missing_or_repeated_stage_hit", "move": action})
		if contacts.size() != depth: errors.append({"kind": "unexpected_contact_count"})
		if damage != expected_damage: errors.append({"kind": "wrong_stage_damage", "expected": expected_damage, "actual": damage})
	elif kind == "block":
		if contacts.size() != 1 or str(contacts.get("light1","")) != "block" or int(counts.get("light1",0)) != 1:
			errors.append({"kind": "missing_or_repeated_real_block"})
		if damage != 0: errors.append({"kind": "unexpected_block_damage"})
	else:
		if not contacts.is_empty(): errors.append({"kind": "unexpected_whiff_contact"})
		if damage != 0: errors.append({"kind": "unexpected_whiff_damage"})
	return errors
