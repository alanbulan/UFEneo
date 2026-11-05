extends RefCounted
## 仅在5张月亮本人整源经过根审并冻结后使用；不开放角色，不补假相。
const SharedFactory = preload("res://tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1/candidate_factory.gd")
const CLOCKS := {"backstep":[3,3,4,3,3]}
const STATE_KEYS := {"backstep":"backstep"}

static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.schema) == "ufeneo.luna.backstep-main-candidate.v1" and bool(cfg.root_runtime_ready))
	assert(str(cfg.fighter) == "ultraman-arc__luna" and str(cfg.opponent) == "zetton")
	for flag in ["playable","implemented","select_visible","transform_enabled"]:assert(not bool(cfg[flag]))
	for resource in cfg.bound_resources:assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "后撤候选冻结源变化")
	var raw: Dictionary = cfg.definition
	assert(raw.moves.is_empty() and raw.command_table.is_empty() and int(raw.jump_speed) == 16)
	assert(raw.state_frames.size() == 4 and cfg.presentation.manifest_data.clips.size() == 4)
	for action in CLOCKS:
		var ticks: Array = CLOCKS[action]
		var clip: Dictionary = cfg.presentation.manifest_data.clips[action]
		assert(clip.ticks.size() == ticks.size() and clip.rects.size() == ticks.size())
		assert(str(clip.source_fighter) == "ultraman-arc__luna" and not bool(clip.loop))
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
	var flags: Dictionary = UfeContentDatabase.read_json("res://content/fighters/ultraman-arc__luna/definition.json")
	for flag in ["implemented", "playable", "select_visible"]: assert(not bool(flags[flag]))
	for clip in cfg.presentation.manifest_data.clips.values():
		assert(FileAccess.get_sha256(str(clip.texture)) == str(clip.atlas_sha256))
	cfg["_candidate_contract_sha256"] = FileAccess.get_sha256(path)
	return cfg

static func make_match(cfg: Dictionary, direction: int) -> UfeMatchDirector:
	return SharedFactory.make_match(cfg,direction)

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
