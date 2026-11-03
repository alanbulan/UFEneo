extends SceneTree
## 仅逻辑夹具。默认站位，全部移动/跳跃/出投/拆投经真实step；不写fighter状态、坐标或高度。
var errors: Array[String] = []
var out := "res://reports/review/2026-11-02/gomora-super3-throw-target-step-v1"
var baseline_path := ""
var baseline_mode := false

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func write_json(path: String, value: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		check(false, "write " + path)
		return
	file.store_string(JSON.stringify(value, "", true) + "\n")

func fixture(owner: int, explicit: Variant = null) -> UfeMatchDirector:
	var actor := UfeContentDatabase.fighter("gomora", true)
	var victim := UfeContentDatabase.fighter("ultraman", true)
	if explicit != null:
		var move: Dictionary = actor.moves.throw_forward.duplicate(true)
		move.id = "fixture_target_throw"
		move.throw_target_air = explicit
		actor.moves[str(move.id)] = move
		actor.command_table = [{"move":str(move.id), "states":["idle", "walk"], "directions":[0],
			"buttons":UfeInputFrame.THROW, "motion":[], "priority":10000}]
	return UfeMatchDirector.new(actor if owner == 0 else victim, victim if owner == 0 else actor,
		load("res://content/rules/neo.tres"), UfeContentDatabase.states())

func row(sim: UfeMatchDirector, pair: Array) -> Array:
	return [sim.tick, pair.map(func(i): return i.pack()), sim.state_hash(), sim.events.duplicate(true),
		sim.fighters[0].snapshot().duplicate(true), sim.fighters[1].snapshot().duplicate(true)]

func run_case(owner: int, airborne: bool, explicit: Variant = null, tech_delay: int = 0) -> Dictionary:
	var sim := fixture(owner, explicit)
	var recorder := UfeReplayRecorder.new()
	var rows: Array = []
	var stage := -1
	var captured := false
	var capture_age := 0
	var techs := 0
	var slams := 0
	var hits := 0
	var started := false
	var capture_origin_height := -1
	var max_air_height := 0
	for tick in range(240):
		var a := sim.fighters[owner]
		var b := sim.fighters[1-owner]
		var pair: Array = [UfeInputFrame.make(), UfeInputFrame.make()]
		if stage < 0:
			if absi(a.x-b.x) <= 52: stage = 0
			else:
				pair[0] = UfeInputFrame.make(1)
				pair[1] = UfeInputFrame.make(-1)
		if stage >= 0:
			if airborne and stage == 3:
				pair[1-owner] = UfeInputFrame.make(0, 1)
				if explicit == null: pair[owner] = UfeInputFrame.make(0, 1)
			if stage == 8: pair[owner] = UfeInputFrame.make(0, 0, UfeInputFrame.THROW)
			stage += 1
		if captured and tech_delay > 0:
			capture_age += 1
			if capture_age == tech_delay: pair[1-owner] = UfeInputFrame.make(0, 0, UfeInputFrame.THROW)
		sim.step(pair)
		recorder.append(pair, sim)
		rows.append(row(sim, pair))
		if not a.move_id.is_empty(): started = true
		max_air_height = maxi(max_air_height, b.height)
		if b.state == "thrown" and not captured:
			captured = true
			capture_origin_height = int(b.motion.get("throw_origin_height", -1))
		for event in sim.events:
			if str(event.kind) == "throw_tech": techs += 1
			if str(event.kind) == "throw_slam": slams += 1
			if str(event.kind) == "hit": hits += 1
	check(stage >= 0, "default position really walked into range")
	check(started, "input really started throw " + str([owner,airborne,explicit]))
	if airborne: check(max_air_height > 0, "victim really jumped")
	return {"fingerprint":sim.content_fingerprint, "rows":rows, "captured":captured,
		"capture_origin_height":capture_origin_height, "techs":techs, "slams":slams, "hits":hits,
		"victim_hp":sim.fighters[1-owner].stats.hp, "recorder":recorder}

func strip_recorder(result: Dictionary) -> Dictionary:
	var value := result.duplicate()
	value.erase("recorder")
	return value

func replay_same_steps(result: Dictionary, owner: int, label: String) -> void:
	var recorder: UfeReplayRecorder = result.recorder
	var path := out + "/" + label + "-after-replay.json"
	check(recorder.save_file(path) == OK, "save replay " + label)
	var playback := fixture(owner)
	var loaded := UfeReplayRecorder.load_file(path, playback.content_fingerprint)
	check(loaded != null, "current fingerprint accepts replay " + label)
	if loaded == null: return
	for i in range(loaded.frames.size()):
		var pair := [UfeInputFrame.unpack(loaded.frames[i][0]), UfeInputFrame.unpack(loaded.frames[i][1])]
		playback.step(pair)
		check(playback.state_hash() == str(result.rows[i][2]), "replay step " + label + "/" + str(i))
	check(playback.state_hash() == loaded.final_hash, "replay final " + label)

func validation() -> void:
	var original: Dictionary = UfeContentDatabase.fighter("gomora", true).moves.throw_forward
	check(UfeMoveData.validate(original), "legacy missing field validates")
	for value in [true, false]:
		var move := original.duplicate(true)
		move.throw_target_air = value
		check(UfeMoveData.validate(move), "boolean throw target validates " + str(value))
	for value in [null, 0, 1, 1.0, "true", [], {}]:
		var move := original.duplicate(true)
		move.throw_target_air = value
		check(not UfeMoveData.validate(move), "invalid throw target type rejected " + str(value))
	var nonthrow := original.duplicate(true)
	nonthrow.kind = "melee"
	nonthrow.throw_target_air = true
	check(not UfeMoveData.validate(nonthrow), "nonthrow target field rejected")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg == "--baseline": baseline_mode = true
		if arg.begins_with("--throw-target-out="): out = arg.trim_prefix("--throw-target-out=")
		if arg.begins_with("--throw-target-baseline="): baseline_path = arg.trim_prefix("--throw-target-baseline=")
	DirAccess.make_dir_recursive_absolute(out)
	if baseline_path.is_empty(): baseline_path = out + "/legacy-before.json"
	var before: Variant = {}
	if baseline_mode:
		check(not FileAccess.file_exists(baseline_path), "never overwrite baseline")
		if not errors.is_empty(): quit(1); return
	else:
		before = JSON.parse_string(FileAccess.get_file_as_string(baseline_path))
		check(before is Dictionary and before.size() == 4, "four real-step legacy baselines required")
		if not errors.is_empty(): quit(1); return
	var evidence := {}
	for owner in [0, 1]:
		for airborne in [false, true]:
			var key := "legacy_%d_%s" % [owner, "air" if airborne else "ground"]
			var result := run_case(owner, airborne)
			check(result.captured and result.slams == 1 and result.hits == 1, "legacy actual capture and one impact " + key)
			check((int(result.capture_origin_height) > 0) == airborne, "legacy target actual height " + key)
			var stripped := strip_recorder(result)
			evidence[key] = stripped
			if baseline_mode:
				check(result.recorder.save_file(out + "/" + key + "-before-replay.json") == OK, "save old replay")
			else:
				var old: Dictionary = before[key]
				check(str(old.fingerprint) != str(result.fingerprint), "explicit rule fingerprint changes " + key)
				check(old.rows == JSON.parse_string(JSON.stringify(result.rows)), "legacy every input/state/event unchanged " + key)
				var old_replay := UfeReplayRecorder.load_file(baseline_path.get_base_dir() + "/" + key + "-before-replay.json", str(result.fingerprint))
				check(old_replay == null and not UfeReplayRecorder.last_error.is_empty(), "old fingerprint replay rejected " + key)
				replay_same_steps(result, owner, key)
	if baseline_mode:
		write_json(baseline_path, evidence)
	else:
		validation()
		for target_air in [false, true]:
			for actual_air in [false, true]:
				var key := "explicit_%s_target_%s" % [target_air, actual_air]
				var result := run_case(0, actual_air, target_air)
				var should_capture: bool = target_air == actual_air
				check(bool(result.captured) == should_capture, "generic target gate " + key)
				check(int(result.slams) == (1 if should_capture else 0), "generic unique impact or real miss " + key)
				if should_capture: check((int(result.capture_origin_height) > 0) == actual_air, "generic actual capture origin " + key)
				evidence[key] = strip_recorder(result)
		for delay in [1, 2, 3, 4]:
			var result := run_case(0, true, true, delay)
			check(result.captured, "tech test actual capture " + str(delay))
			check(int(result.techs) == (1 if delay <= 3 else 0), "real-tick tech boundary " + str(delay))
			check(int(result.slams) == (0 if delay <= 3 else 1), "tech prevents landing damage " + str(delay))
			evidence["tech_" + str(delay)] = strip_recorder(result)
	write_json(out + ("/baseline-result.json" if baseline_mode else "/after-result.json"),
		{"errors":errors, "cases":evidence, "baseline":baseline_path, "baseline_mode":baseline_mode,
		"only_input_steps":true, "gameplay_visual_acceptance":false, "gomora_super3_installed":false})
	print("THROW_TARGET_STEP ", JSON.stringify({"errors":errors, "baseline_mode":baseline_mode}))
	quit(0 if errors.is_empty() else 1)
