extends SceneTree
var errors: Array = []
var cases: Array = []
var OUT := "res://reports/review/2026-10-31/transform-mechanism-current/"

func check(ok: bool, name: String) -> void:
	if not ok: errors.append(name); printerr("FAIL " + name)

func neutral() -> UfeInputFrame: return UfeInputFrame.make()
func advance(sim: UfeMatchDirector, count: int) -> void:
	for i in range(count): sim.step([neutral(), neutral()])
func setup(id: String = "ultraman-taro", overrides: Dictionary = {}) -> UfeMatchDirector:
	var sim := UfeBattleFormCatalog.match_for(id, "ultraman", true, overrides)
	sim.fighters[0].stats.hp = 500
	sim.fighters[0].stats.energy = 3000
	return sim
func transform_input(sim: UfeMatchDirector) -> void:
	for input in [UfeInputFrame.make(0,-1), neutral(), UfeInputFrame.make(0,-1,UfeInputFrame.SPECIAL)]:
		sim.step([input, neutral()])
func _initialize() -> void: call_deferred("run")

func test_conditions_and_fallback() -> void:
	for missing in ["energy", "health", "once", "form"]:
		var sim := setup("ultraseven" if missing == "form" else "ultraman-taro")
		var f := sim.fighters[0]
		if missing == "energy": f.stats.energy = 2000
		if missing == "health": f.stats.hp = 501
		if missing == "once": f.transformed_this_round = true
		transform_input(sim)
		check(f.state != "transform", "test_conditions_" + missing)
		check(f.move_id == ("special2" if missing == "energy" else "special3"), "test_fallback_" + missing)
	var sim := setup()
	transform_input(sim)
	check(sim.fighters[0].state == "transform" and sim.fighters[0].stats.energy == 0, "test_half_health_and_cost")
	check(sim.fighters[0].transformed_this_round, "test_once_consumed_at_start")
	var held := setup()
	for i in range(8): held.step([UfeInputFrame.make(0,-1,UfeInputFrame.SPECIAL if i==7 else 0), neutral()])
	check(held.fighters[0].state != "transform", "test_held_down_is_not_double_down")
	var matrix := setup()
	for input in [UfeInputFrame.make(0,-1), neutral(), UfeInputFrame.make(0,-1,UfeInputFrame.CRUSH)]: matrix.step([input,neutral()])
	check(matrix.fighters[0].move_id == "motion_22", "test_existing_22_crush_unchanged")
	cases.append("test_conditions_and_fallback")

func test_invulnerable_and_control() -> void:
	var sim := setup()
	transform_input(sim)
	var f := sim.fighters[0]
	var other := sim.fighters[1]
	var remaining := sim.remaining
	for tick in range(60):
		check(f.state == "transform" and UfeHitResolver.invulnerable(f), "test_full_transform_invulnerability")
		for move in ["heavy", "throw_forward"]:
			other.move_id = move
			other.move_tick = int(other.definition.moves[move].startup)
			other.combat.connected = false
			check(not UfeHitResolver.can_hit(other, f), "test_hit_and_throw_miss_" + move)
		other.clear_move()
		var old_x := other.x
		sim.step([UfeInputFrame.make(1,1,UfeInputFrame.LIGHT|UfeInputFrame.DODGE), UfeInputFrame.make(1)])
		check(other.x > old_x, "test_opponent_keeps_moving")
		check(int(f.stats.hp) == 500 and f.height == 0, "test_cannot_interrupt_transform")
		if tick == 46: check(f.form_id.is_empty(), "test_palette_before_tick48")
		if tick == 47: check(f.form_id == "super-taro", "test_palette_at_tick48")
	check(sim.remaining == remaining, "test_transform_pauses_clock_only")
	check(f.state == "idle" and f.form_id == "super-taro", "test_control_returns_after_performance")
	sim.step([neutral(), neutral()])
	sim.step([UfeInputFrame.make(0,0,UfeInputFrame.LIGHT), neutral()])
	check(f.move_id == "light1", "test_super_state_can_attack")
	# 实体光弹穿过演出中的受击框，不能结算或被消除。
	var shot := setup()
	transform_input(shot)
	var projectile: Dictionary = shot.fighters[1].definition.moves.pulse.projectile.duplicate(true)
	shot.fighters[1].x = shot.fighters[0].x + 90
	UfeProjectileResolver.spawn(shot, 1, projectile, "pulse")
	advance(shot, 18)
	check(int(shot.fighters[0].stats.hp) == 500, "test_projectile_misses_transform")
	cases.append("test_invulnerable_and_control")

func test_super_beam_and_round_reset() -> void:
	for hit in [true, false]:
		var sim := setup()
		transform_input(sim)
		advance(sim, 60)
		var f := sim.fighters[0]
		f.stats.energy = 3000
		if not hit: f.x = 100; sim.fighters[1].x = 1200
		sim.step([UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL), neutral()])
		check(f.move_id == "super_special3", "test_level3_replaced_" + str(hit))
		var contact := false
		for i in range(115):
			sim.step([neutral(), neutral()])
			contact = contact or sim.events.any(func(e): return e.kind == "hit" and e.get("move","") == "super_special3")
		check(contact == hit, "test_cosmo_hit_or_whiff_" + str(hit))
		check(f.form_id.is_empty() and f.transformed_this_round, "test_cosmo_always_reverts_" + str(hit))
		f.stats.energy = 3000
		transform_input(sim)
		check(f.state != "transform" and f.move_id == "special3", "test_no_second_transform_after_cosmo")
	var sim := setup()
	transform_input(sim); advance(sim,60)
	sim.remaining = 1
	advance(sim,1)
	check(sim.finished and sim.fighters[0].form_id == "super-taro", "test_round_end_retains_palette")
	var next := UfeBattleFormCatalog.match_for("ultraman-taro", "ultraman")
	check(not next.fighters[0].transformed_this_round and next.fighters[0].form_id.is_empty(), "test_next_round_clears_usage")
	check(next.fighters[0].stats.hp == 1000 and next.fighters[0].stats.energy == 0, "test_next_round_normal_stats")
	cases.append("test_super_beam_and_round_reset")

func test_ex_definition_switch() -> void:
	for base in ["gomora", "red_king"]:
		# 名册现已正式开放EX；关闭规则夹具必须显式关闭，不能依赖历史默认值。
		var disabled := {}; disabled[base] = false
		var closed := setup(base, disabled)
		check(not UfeBattleTransform.can_transform(closed.fighters[0]), "test_ex_disabled_" + base)
		transform_input(closed)
		check(closed.fighters[0].move_id == "special3" and closed.fighters[0].definition.id == base, "test_ex_disabled_fallback_" + base)
		var enabled := {}; enabled[base] = true
		var sim := setup(base, enabled)
		var f := sim.fighters[0]
		f.stats.hp = 420; f.x = 880; f.facing = -1
		f.combat.round_score = 37
		transform_input(sim); advance(sim,72)
		var target: UfeFighterDefinition = f.battle_form.target_definition
		check(f.definition == target and f.definition.id == "ex_" + base, "test_ex_definition_swap_" + base)
		check(f.definition.moves == target.moves and f.definition.command_table == target.command_table and f.definition.state_frames == target.state_frames, "test_ex_move_command_hurtbox_swap_" + base)
		check(f.state == "form_entry" and UfeHitResolver.invulnerable(f), "test_ex_own_entry_" + base)
		check(f.stats.hp == 420 and f.stats.energy == 0 and f.x == 880 and f.facing == -1 and f.combat.round_score == 37, "test_ex_values_retained_" + base)
		advance(sim,36)
		check(f.state == "idle", "test_ex_entry_returns_control_" + base)
		check(sim.content_fingerprint != closed.content_fingerprint, "test_ex_flag_changes_replay_fingerprint_" + base)
		sim.remaining = 1; advance(sim,1)
		check(f.definition == target and f.definition.id == "ex_" + base and f.form_id == "ex_" + base and f.combat.round_score == 37, "test_ex_round_retains_definition_" + base)
		var next := setup(base, enabled)
		check(not next.fighters[0].transformed_this_round and next.fighters[0].definition.id == base, "test_ex_next_round_reset_" + base)
		# 普通形态已经发出的弹体在换定义后仍沿用发射时的数据。
		var pending := setup(base, enabled)
		var actor := pending.fighters[0]
		var shot: Dictionary = {}
		for frame in actor.definition.moves.pulse.frames:
			if not frame.get("shots",[]).is_empty(): shot=frame.shots[0].duplicate(true); break
		check(not shot.is_empty(), "test_ex_projectile_fixture_authored_" + base)
		shot.speed=0; shot.life=180
		UfeProjectileResolver.spawn(pending,0,shot,"pulse")
		pending.projectiles[0].x=1200
		transform_input(pending); advance(pending,72)
		pending.projectiles[0].x=pending.fighters[1].x
		pending.projectiles[0].height=75
		advance(pending,1)
		check(pending.fighters[1].stats.hp<1000, "test_ex_pending_projectile_keeps_source_move_" + base)
	cases.append("test_ex_definition_switch")

func test_cpu_seed() -> void:
	var a := setup(); var b := setup()
	var ai_a := UfeComputerController.new(20261026, "normal", 0)
	var ai_b := UfeComputerController.new(20261026, "normal", 0)
	for tick in range(600):
		var aa := ai_a.sample(a); var bb := ai_b.sample(b)
		check(aa.pack() == bb.pack(), "test_cpu_seed_inputs_identical")
		a.step([aa,neutral()]); b.step([bb,neutral()])
		check(a.state_hash() == b.state_hash(), "test_cpu_seed_simulation_identical")
	check(a.fighters[0].transformed_this_round and int(ai_a.actions.get("transform",0)) == 1, "test_cpu_transforms_once")
	cases.append("test_cpu_seed")

func test_replay_format6() -> void:
	var sim := UfeBattleFormCatalog.match_for("ultraman-taro", "ultraman")
	var twin := UfeBattleFormCatalog.match_for("ultraman-taro", "ultraman")
	var record := UfeReplayRecorder.new()
	var motion_age := -1
	var hit_count := 0
	var transform_tick := -1
	var cosmo_tick := -1
	for tick in range(1700):
		var input := neutral(); var other := neutral()
		var f := sim.fighters[0]
		if not f.transformed_this_round:
			if motion_age < 0 and UfeBattleTransform.can_transform(f) and f.state in UfeBattleFormCatalog.GROUND_STATES: motion_age = 0
			if motion_age >= 0 and motion_age < 3:
				input = UfeInputFrame.make(0,-1 if motion_age != 1 else 0,UfeInputFrame.SPECIAL if motion_age == 2 else 0)
				motion_age += 1
			else: input = UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
			if int(f.stats.hp) > 500 and tick % 85 == 30: other = UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
		elif f.state != "transform":
			input = UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL if int(f.stats.energy)>=3000 else UfeInputFrame.CHARGE)
		var pair := [input,other]
		sim.step(pair); twin.step(pair); record.append(pair,sim)
		if sim.fighters[0].transformed_this_round and transform_tick<0: transform_tick=tick
		if sim.fighters[0].move_id=="super_special3" and cosmo_tick<0: cosmo_tick=tick
		check(sim.state_hash() == twin.state_hash(), "test_transform_tick_determinism")
		if sim.events.any(func(e):return e.kind == "hit" and e.get("move","") == "super_special3"): hit_count += 1
	check(sim.fighters[0].transformed_this_round and hit_count > 0, "test_replay_natural_start_reaches_transform_and_cosmo")
	print("自然开局回放诊断 ", {"transform_tick":transform_tick,"cosmo_tick":cosmo_tick,"hp":sim.fighters[0].stats.hp,"energy":sim.fighters[0].stats.energy,"state":sim.fighters[0].state,"motion_age":motion_age,"hit_count":hit_count})
	check(record.save_file("user://transform-format6.json") == OK, "test_format6_save")
	var loaded := UfeReplayRecorder.load_file("user://transform-format6.json", sim.content_fingerprint)
	check(loaded != null and UfeReplayRecorder.FORMAT == 6, "test_format6_load")
	var replay := UfeBattleFormCatalog.match_for("ultraman-taro", "ultraman")
	if loaded != null:
		for pair in loaded.frames: replay.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
		check(replay.state_hash() == loaded.final_hash, "test_format6_replay_final_hash")
	var file := FileAccess.open("user://transform-format5-old.json", FileAccess.WRITE)
	file.store_string('{"format":5}'); file.close()
	check(UfeReplayRecorder.load_file("user://transform-format5-old.json", sim.content_fingerprint) == null and "格式6" in UfeReplayRecorder.last_error, "test_format5_explicit_rejection")
	cases.append("test_replay_format6")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--regression-out="):OUT=arg.trim_prefix("--regression-out=").trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	test_conditions_and_fallback()
	test_invulnerable_and_control()
	test_super_beam_and_round_reset()
	test_ex_definition_switch()
	test_cpu_seed()
	test_replay_format6()
	FileAccess.open(OUT + "logic.json", FileAccess.WRITE).store_string(JSON.stringify({"passed":errors.is_empty(), "cases":cases,"errors":errors},"\t"))
	print("TRANSFORM_MECHANISM " + ("PASS" if errors.is_empty() else str(errors.slice(0,8))))
	quit(0 if errors.is_empty() else 1)
