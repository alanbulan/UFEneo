extends RefCounted
## 仅在银河本人完整源经过根审并冻结后使用；不开放角色，不补假相。
const ID := "ultraman-arc__galaxion"
const CLOCKS := {"idle":[10,10,10,10,10,10],"crouch_start":[3,3],"crouch":[12,12],"crouch_rise":[3,3]}
const STATE_KEYS := {"idle":"idle","crouch_start":"crouch_start","crouch":"crouch","crouch_rise":"crouch_rise"}

static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema) == "ufeneo.galaxion.crouch-main-candidate.v1" and bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter) == "ultraman-arc__galaxion" and str(cfg.opponent) == "zetton")
	for flag in ["playable","implemented","select_visible","transform_enabled"]:assert(not bool(cfg[flag]))
	for resource in cfg.bound_resources:assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "蹲起候选冻结源变化")
	var raw: Dictionary = cfg.definition
	assert(raw.moves.is_empty() and raw.command_table.is_empty() and int(raw.jump_speed) == 16)
	assert(raw.state_frames.size() == 4 and cfg.presentation.manifest_data.clips.size() == 4)
	for action in CLOCKS:
		var ticks: Array = CLOCKS[action]
		var clip: Dictionary = cfg.presentation.manifest_data.clips[action]
		assert(clip.ticks.size() == ticks.size() and clip.rects.size() == ticks.size())
		assert(str(clip.source_fighter) == "ultraman-arc__galaxion" and bool(clip.loop) == (action in ["idle","crouch"]))
		assert(int(clip.cell) == 320 and int(clip.get("simulation_sprite_offset",0)) == 0)
		var phases: Array = []
		for phase in range(ticks.size()):
			assert(float(clip.ticks[phase]) == float(ticks[phase]))
			assert(int(clip.anchors[phase][0]) == 160 and int(clip.anchors[phase][1]) == 280)
			for _tick in range(int(ticks[phase])):phases.append(phase)
		var frames: Array = raw.state_frames[STATE_KEYS[action]]
		assert(frames.size() == phases.size())
		for tick in range(frames.size()):assert(int(frames[tick].sprite) == int(phases[tick]))
	for state in raw.state_frames:
		for frame in raw.state_frames[state]:
			assert(frame.hitboxes.is_empty() and frame.events.is_empty() and frame.cancel.is_empty())
			assert(int(frame.dx) == 0 and int(frame.dy) == 0 and not bool(frame.get("invulnerable",false)))
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc__galaxion/definition.json")
	for flag in ["implemented", "playable", "select_visible"]: assert(not bool(flags[flag]))
	for clip in cfg.presentation.manifest_data.clips.values():
		assert(FileAccess.get_sha256(str(clip.texture)) == str(clip.atlas_sha256))
	cfg["_candidate_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg

static func temporary_definition(cfg: Dictionary) -> UfeFighterDefinition:
	var raw: Dictionary = cfg.definition
	var result := UfeFighterDefinition.new()
	result.id = ID
	result.display_name = str(raw.display_name)
	result.max_health = int(raw.max_health)
	result.walk_speed = int(raw.walk_speed)
	result.jump_speed = int(raw.jump_speed)
	result.body_radius = int(raw.body_radius)
	result.moves = {}
	result.command_table = []
	result.state_frames = raw.state_frames.duplicate(true)
	return result

static func make_match(cfg: Dictionary, direction: int) -> UfeMatchDirector:
	assert(direction in [-1,1])
	assert(bool(cfg.get("root_runtime_ready", false)))
	# 银河定义和本人状态表在第一次UfeMatchDirector构造之前即已完整建立。
	var first := temporary_definition(cfg)
	var second := UfeContentDatabase.fighter(str(cfg.opponent), false)
	var sim := UfeMatchDirector.new(first, second, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), {})
	var setup: Dictionary = cfg.initial_positions["right" if direction > 0 else "left"]
	assert(sim.tick == 0)
	sim.fighters[0].x = int(setup.p1_x)
	sim.fighters[1].x = int(setup.p2_x)
	sim.fighters[0].facing = direction
	sim.fighters[1].facing = -direction
	return sim


static func verify_original_inputs(cfg: Dictionary, tape: Dictionary) -> Dictionary:
	assert(str(tape.candidate_contract_sha256) == str(cfg._candidate_contract_sha256))
	var sim := make_match(cfg,int(tape.direction))
	assert(sim.content_fingerprint == str(tape.simulation_fingerprint))
	assert(tape.original_pairs.size() == tape.state_hashes.size())
	var errors: Array = []
	for tick in range(tape.original_pairs.size()):
		var pair: Array = tape.original_pairs[tick]
		sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
		if sim.state_hash() != str(tape.state_hashes[tick]):errors.append({"tick":sim.tick,"kind":"hash_mismatch"})
		for key in ["events","projectiles"]:
			if JSON.stringify(JSON.parse_string(JSON.stringify(sim.get(key))),"",true) != JSON.stringify(tape[key][tick],"",true):errors.append({"tick":sim.tick,"kind":key+"_mismatch"})
	return {"errors":errors,"final_hash":sim.state_hash(),"simulation_fingerprint":sim.content_fingerprint,"tick_count":sim.tick,"no_user_writes":true}
