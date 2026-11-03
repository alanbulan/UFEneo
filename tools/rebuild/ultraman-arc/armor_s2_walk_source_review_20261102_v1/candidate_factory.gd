extends RefCounted
## 仅供根将来正式main训练入口调用；不注册人物、不写用户文件、不换已建sim定义。
const ID := "ultraman-arc__luna"

static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary = UfeContentDatabase.read_json(path)
	assert(str(cfg.get("schema", "")) == "ufeneo.arc-luna.s2.main_candidate.v1")
	assert(bool(cfg.get("root_runtime_ready", false)), "根尚未冻结此候选的本人资源/临时定义")
	assert(str(cfg.get("fighter", "")) == ID)
	assert(not bool(cfg.get("playable", true)) and not bool(cfg.get("transform_enabled", true)))
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path)) == str(resource.sha256), "候选资源指纹变化")
	var raw: Dictionary = cfg.definition
	assert(str(raw.id) == ID and raw.moves.is_empty() and raw.command_table.is_empty())
	var frames: Dictionary = raw.state_frames
	assert(frames.keys().size() == 3)
	for key in ["idle", "turn", "walk_forward"]:
		assert(frames.has(key) and not frames[key].is_empty(), "缺本人S2状态帧")
		assert(cfg.presentation.manifest_data.clips.has(key), "缺本人S2表现帧")
		var clip: Dictionary = cfg.presentation.manifest_data.clips[key]
		assert(clip.source_fighter == ID, "不得用本体或其它人物帧装配月亮")
		for frame in frames[key]:
			assert(frame.hitboxes.is_empty() and frame.events.is_empty())
	assert(frames.walk_forward.size() == 32)
	for tick in range(32):
		assert(int(frames.walk_forward[tick].sprite) == (tick >> 2))
	assert(cfg.presentation.manifest_data.clips.walk_forward.ticks.size() == 8)
	for duration in cfg.presentation.manifest_data.clips.walk_forward.ticks:
		assert(int(duration) == 4)
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
	# 月亮定义和本人状态表在第一次UfeMatchDirector构造之前即已完整建立。
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
	# 独立回放入口只读原双方InputFrame，不采样输入驱动，也不存last_replay。
	assert(str(tape.candidate_contract_sha256) == str(cfg._candidate_contract_sha256))
	var sim := make_match(cfg, int(tape.direction))
	assert(sim.content_fingerprint == str(tape.simulation_fingerprint))
	assert(tape.original_pairs.size() == tape.state_hashes.size())
	var errors: Array = []
	for tick in range(tape.original_pairs.size()):
		var pair: Array = tape.original_pairs[tick]
		sim.step([UfeInputFrame.unpack(pair[0]), UfeInputFrame.unpack(pair[1])])
		if sim.state_hash() != str(tape.state_hashes[tick]):
			errors.append({"tick":sim.tick, "expected":tape.state_hashes[tick], "actual":sim.state_hash()})
	return {"errors":errors, "final_hash":sim.state_hash(), "simulation_fingerprint":sim.content_fingerprint,
		"tick_count":sim.tick, "writes_user_settings":false, "writes_last_replay":false}
