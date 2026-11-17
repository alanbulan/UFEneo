extends SceneTree
## 空中限定在真正启动时重验；只验模拟、输入缓存、扣费和回放，不代替画面验收。
const OUT := "res://reports/review/2026-11-01/ex-gomora-air-only-buffer-fix-v1/"
var errors: Array = []
var evidence: Dictionary = {}
var run_out: String = ""

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func write_json(path: String, data: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		check(false, "write_" + path)
		return
	file.store_string(JSON.stringify(data, "\t", true) + "\n")

func fixture(facing: int = 1, definition: UfeFighterDefinition = null) -> UfeMatchDirector:
	var first := UfeContentDatabase.fighter("ex_gomora", true) if definition == null else definition
	var sim := UfeMatchDirector.new(first, UfeContentDatabase.fighter("ultraman", true), load("res://content/rules/neo.tres"), UfeContentDatabase.states())
	sim.fighters[0].x = 1100 if facing < 0 else 180
	sim.fighters[1].x = 180 if facing < 0 else 1100
	sim.fighters[0].facing = facing
	sim.fighters[1].facing = -facing
	sim.fighters[0].stats.energy = 777
	return sim

func row(sim: UfeMatchDirector) -> Dictionary:
	var f := sim.fighters[0]
	return {"tick":sim.tick, "height":f.height, "vy":f.vy, "state":f.state, "move":f.move_id, "move_tick":f.move_tick,
		"energy":f.stats.energy, "stamina":f.stats.stamina, "buffer":f.combat.buffer, "buffer_ticks":f.combat.buffer_ticks,
		"projectiles":sim.projectiles.duplicate(true), "events":sim.events.duplicate(true), "hash":sim.state_hash()}

func test_landing_buffer() -> void:
	for facing in [-1, 1]:
		for stop in [0, 2]:
			var sim := fixture(facing)
			var f := sim.fighters[0]
			f.enter("air"); f.height = 1; f.vy = -1
			sim.hitstop = stop
			check(sim.command_state(f) == "vertical_air", "landing_resolver_starts_air_%s_%s" % [facing,stop])
			var trace: Array = []
			var idle_buffer_seen := false
			for tick in range(20):
				var input := UfeInputFrame.make(0, 0, UfeInputFrame.RANGED if tick == 0 else 0)
				sim.step([input, UfeInputFrame.make()])
				trace.append(row(sim))
				if tick == 0:
					check(f.combat.buffer == "air_pulse", "landing_I_really_resolved_and_buffered_%s_%s" % [facing,stop])
					check(f.height == (1 if stop > 0 else 0), "landing_physics_after_resolver_%s_%s" % [facing,stop])
				if f.state == "idle" and str(f.combat.buffer) == "air_pulse": idle_buffer_seen = true
				check(f.move_id.is_empty(), "landing_never_starts_air_move_%s_%s_%s" % [facing,stop,tick])
				check(int(f.stats.energy) == 777 and int(f.stats.stamina) == 1000, "landing_no_cost_%s_%s_%s" % [facing,stop,tick])
				check(sim.projectiles.is_empty() and sim.events.is_empty(), "landing_no_projectile_or_sound_%s_%s_%s" % [facing,stop,tick])
			check(idle_buffer_seen, "landing_survives_until_idle_before_denial_%s_%s" % [facing,stop])
			check(str(f.combat.buffer).is_empty() and int(f.combat.buffer_ticks) == 0, "landing_buffer_expires_normally_%s_%s" % [facing,stop])
			evidence["landing/%s/%s" % [facing,stop]] = trace

func jump_input(tick: int) -> UfeInputFrame:
	if tick == 0: return UfeInputFrame.make(0, 1)
	if tick == 2: return UfeInputFrame.make(0, 0, UfeInputFrame.RANGED)
	return UfeInputFrame.make()

func test_natural_air_start() -> void:
	for facing in [-1, 1]:
		var sim := fixture(facing)
		var f := sim.fighters[0]
		var seen_projectile := false
		var cast_sounds := 0
		var trace: Array = []
		for tick in range(30):
			sim.step([jump_input(tick), UfeInputFrame.make()])
			trace.append(row(sim))
			if tick == 2:
				check(f.height > 0 and f.state == "air_attack" and f.move_id == "air_pulse", "natural_W_then_I_starts_air_%s" % facing)
				check(int(f.stats.energy) == 777 and int(f.stats.stamina) == 965, "natural_I_pays_35_stamina_no_energy_%s" % facing)
			for projectile in sim.projectiles:
				if str(projectile.get("move", "")) == "air_pulse": seen_projectile = true
			for event in sim.events:
				if str(event.get("kind", "")) == "sound" and str(event.get("id", "")) == "ex_gomora_projectile_cast": cast_sounds += 1
		check(seen_projectile and cast_sounds == 1, "natural_I_emits_one_cast_and_real_projectile_%s" % facing)
		evidence["natural-air/%s" % facing] = trace

func test_start_boundary_and_generic_id() -> void:
	var results: Array = []
	for facing in [-1, 1]:
		for height in [0, 1]:
			var definition := UfeContentDatabase.fighter("ex_gomora", true)
			var move: Dictionary = definition.moves.air_pulse.duplicate(true)
			move.id = "fixture_air_locked"; move.energy_cost = 111; move.stamina_cost = 17
			definition.moves[move.id] = move
			var sim := fixture(facing, definition)
			var f := sim.fighters[0]
			f.height = height; f.stats.stamina = 543
			f.move_id = "light1"; f.move_tick = 2; f.enter("attack")
			f.combat.buffer = str(move.id); f.combat.buffer_ticks = 10
			var before := sim.state_hash()
			sim._start(f, str(move.id))
			if height == 0:
				check(sim.state_hash() == before and sim.events.is_empty(), "generic_ground_denial_preserves_entire_state_and_cost_%s" % facing)
			else:
				check(f.move_id == str(move.id) and f.state == "air_attack", "generic_height_one_starts_%s" % facing)
				check(int(f.stats.energy) == 666 and int(f.stats.stamina) == 526, "generic_air_cost_paid_once_%s" % facing)
			results.append({"facing":facing, "start_height":height, "before_hash":before, "after":row(sim)})
		var actual := fixture(facing)
		var before_actual := actual.state_hash()
		actual._start(actual.fighters[0], "air_pulse")
		check(actual.state_hash() == before_actual, "actual_air_pulse_direct_ground_denied_%s" % facing)
	evidence.generic_start_boundary = results

func test_legacy_ground_buffer() -> void:
	for facing in [-1, 1]:
		var missing := UfeContentDatabase.fighter("ex_gomora", true)
		var explicit_false := UfeContentDatabase.fighter("ex_gomora", true)
		missing.moves.light1.erase("air_only")
		explicit_false.moves.light1.air_only = false
		var first := fixture(facing, missing)
		var second := fixture(facing, explicit_false)
		first.fighters[0].enter("hit", 4); second.fighters[0].enter("hit", 4)
		var started := false
		var trace: Array = []
		for tick in range(24):
			var input := UfeInputFrame.make(0, 0, UfeInputFrame.LIGHT if tick == 0 else 0)
			first.step([input, UfeInputFrame.make()]); second.step([input, UfeInputFrame.make()])
			if tick == 0:
				check(first.fighters[0].move_id.is_empty() and first.fighters[0].combat.buffer == "light1", "legacy_ground_input_really_buffered_%s" % facing)
			if first.fighters[0].move_id == "light1": started = true
			check(first.state_hash() == second.state_hash() and first.events == second.events, "missing_equals_false_all_ticks_and_events_%s_%s" % [facing,tick])
			trace.append(row(first))
		check(started, "legacy_ground_cache_starts_after_hitstun_%s" % facing)
		evidence["legacy-ground/%s" % facing] = trace

func test_validation() -> void:
	var original: Dictionary = UfeContentDatabase.fighter("ex_gomora", true).moves.air_pulse
	check(UfeMoveData.validate(original), "actual_air_only_move_valid")
	for value in [true, false]:
		var move := original.duplicate(true); move.air_only = value
		check(UfeMoveData.validate(move), "boolean_air_only_valid_%s" % value)
	var missing := original.duplicate(true); missing.erase("air_only")
	check(UfeMoveData.validate(missing), "missing_air_only_keeps_legacy_valid")
	var unrestricted := original.duplicate(true); unrestricted.air_only = false; unrestricted.erase("air_allowed")
	check(UfeMoveData.validate(unrestricted), "false_air_only_needs_no_air_allowed")
	for value in [null, 0, 1, 1.0, "true", [], {}]:
		var move := original.duplicate(true); move.air_only = value
		check(not UfeMoveData.validate(move), "nonboolean_air_only_rejected_%s" % str(value))
	for value in [null, false, 0, 1, 1.0, "true", [], {}]:
		var move := original.duplicate(true); move.air_allowed = value
		check(not UfeMoveData.validate(move), "air_only_requires_explicit_true_air_allowed_%s" % str(value))
	var no_air := original.duplicate(true); no_air.erase("air_allowed")
	check(not UfeMoveData.validate(no_air), "air_only_missing_air_allowed_rejected")

func old_fingerprint(sim: UfeMatchDirector) -> String:
	var forms: Array = []
	for f in sim.fighters: forms.append(UfeBattleTransform.simulation_data(f.battle_form))
	return JSON.stringify([6, 60, sim.rules.simulation_data(), sim.fighters[0].definition.simulation_data(), sim.fighters[1].definition.simulation_data(), forms, ["round_end_identity", 1]], "", true).sha256_text()

func test_fingerprint_and_replay() -> void:
	for facing in [-1, 1]:
		var sim := fixture(facing)
		var twin := fixture(facing)
		var recorder := UfeReplayRecorder.new()
		var legacy := old_fingerprint(sim)
		check(sim.content_fingerprint != legacy, "start_rule_revision_changes_fingerprint_independently_of_data_%s" % facing)
		for tick in range(90):
			var pair := [jump_input(tick), UfeInputFrame.make()]
			sim.step(pair); twin.step(pair); recorder.append(pair, sim)
			check(sim.state_hash() == twin.state_hash() and sim.events == twin.events, "twin_tick_hash_and_events_%s_%s" % [facing,tick])
		var path := run_out + "replay-%s.json" % facing
		check(recorder.save_file(path) == OK, "save_current_rule_replay_%s" % facing)
		var loaded := UfeReplayRecorder.load_file(path, sim.content_fingerprint)
		check(loaded != null, "load_current_rule_replay_%s" % facing)
		var replay := fixture(facing)
		if loaded != null:
			for pair in loaded.frames: replay.step([UfeInputFrame.unpack(pair[0]), UfeInputFrame.unpack(pair[1])])
			check(replay.state_hash() == loaded.final_hash, "replay_final_hash_%s" % facing)
		var old_path := run_out + "old-rule-replay-%s.json" % facing
		recorder.fingerprint = legacy
		check(recorder.save_file(old_path) == OK, "save_old_rule_fixture_%s" % facing)
		check(UfeReplayRecorder.load_file(old_path, sim.content_fingerprint) == null, "old_rule_replay_rejected_%s" % facing)
		check(UfeReplayRecorder.last_error == "规则或招式数据已改变，无法播放该回放", "old_rule_rejection_reason_%s" % facing)
		evidence["replay/%s" % facing] = {"current_fingerprint":sim.content_fingerprint, "old_formula_same_data":legacy, "final_hash":sim.state_hash(), "ticks":90}

func run() -> void:
	var label := "logic-run-v1"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--label="): label = arg.trim_prefix("--label=").validate_filename()
	run_out = OUT + label + "/"
	DirAccess.make_dir_recursive_absolute(run_out)
	test_validation()
	test_start_boundary_and_generic_id()
	test_landing_buffer()
	test_natural_air_start()
	test_legacy_ground_buffer()
	test_fingerprint_and_replay()
	write_json(run_out + "logic-result.json", {"passed":errors.is_empty(), "errors":errors, "engine_pending":false,
		"move_start_rule_revision":UfeMatchDirector.MOVE_START_RULE_REVISION, "evidence":evidence})
	print("AIR_ONLY_START " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
