extends SceneTree
## 仅验证确定性模拟；测试用EX定义不代表装甲美术已经完成。
const OUT := "res://reports/review/2026-10-27/armor-transform-routing/"
var errors: Array = []
var routing_evidence: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func legacy_snapshots() -> Dictionary:
	var results := {}
	for base in ["ultraman-taro", "gomora", "red_king"]:
		for facing in [-1, 1]:
			for enabled in [false, true]:
				var flags := {}; flags[base] = enabled
				var sim := UfeBattleFormCatalog.match_for(base, "ultraman", true, flags)
				var f := sim.fighters[0]
				f.stats.hp = 420; f.stats.energy = 3000
				f.x = 880 if facing < 0 else 470
				sim.fighters[1].x = 470 if facing < 0 else 880
				f.facing = facing; sim.fighters[1].facing = -facing
				var hashes: Array = []
				var events: Array = []
				for tick in range(360):
					var input := UfeInputFrame.make()
					if tick in [0, 2]: input = UfeInputFrame.make(0, -1, UfeInputFrame.SPECIAL if tick == 2 else 0)
					if tick == 130: input = UfeInputFrame.make(0, 0, UfeInputFrame.LIGHT)
					if tick == 175: f.stats.energy = 3000
					if tick == 176: input = UfeInputFrame.make(0, 0, UfeInputFrame.SPECIAL)
					if tick == 330: sim.remaining = 1
					sim.step([input, UfeInputFrame.make()])
					hashes.append(sim.state_hash())
					events.append(sim.events.duplicate(true))
				results["%s/%s/%s" % [base, facing, enabled]] = {"hashes":hashes, "events":events, "fingerprint":sim.content_fingerprint}
	return results

func choice_source() -> Dictionary:
	var choices: Array = []
	for row in [["neutral",[2,5],"ex_red_king"], ["forward",[3,6],"ex_gomora"], ["backward",[1,4],"ex_red_king"], ["up",[7,8,9],"ex_gomora"]]:
		var choice: Dictionary = UfeBattleFormCatalog.registry()["gomora" if row[2] == "ex_gomora" else "red_king"].duplicate(true)
		choice.id = "fixture-" + str(row[0]); choice.enabled = true
		choice.directions = row[1]; choice.default = row[0] == "neutral"
		choice.display_name = str(row[0]) + "测试变身"
		choices.append(choice)
	return {"id":"fixture-armors", "enabled":true, "choices":choices}

func fixture(facing: int = 1, source: Dictionary = {}) -> UfeMatchDirector:
	var definition := UfeContentDatabase.fighter("ultraman", true)
	var a := UfeBattleFormCatalog.assemble(definition, choice_source() if source.is_empty() else source)
	var sim := UfeMatchDirector.new(a.definition, UfeContentDatabase.fighter("ultraseven", true), load("res://content/rules/neo.tres"), UfeContentDatabase.states(), {"ultraman":a.form})
	var f := sim.fighters[0]
	f.stats.hp = 500; f.stats.energy = 3000
	f.x = 880 if facing < 0 else 470
	sim.fighters[1].x = 470 if facing < 0 else 880
	f.facing = facing; sim.fighters[1].facing = -facing
	return sim

func input_for(direction: int, facing: int, buttons: int = 0) -> UfeInputFrame:
	return UfeInputFrame.make(([0,-1,0,1,-1,0,1,-1,0,1][direction]) * facing, [0,-1,-1,-1,0,0,0,1,1,1][direction], buttons)

func drive(sim: UfeMatchDirector, direction: int) -> void:
	var facing := sim.fighters[0].facing
	for input in [input_for(2,facing), input_for(5,facing), input_for(2,facing), input_for(direction,facing,UfeInputFrame.SPECIAL)]:
		sim.step([input, UfeInputFrame.make()])

func advance(sim: UfeMatchDirector, ticks: int) -> void:
	for tick in range(ticks): sim.step([UfeInputFrame.make(), UfeInputFrame.make()])

func test_routing_and_lifecycle() -> void:
	for facing in [-1,1]:
		for direction in range(1,10):
			var sim := fixture(facing)
			var f := sim.fighters[0]
			var selector := "neutral" if direction in [2,5] else "forward" if direction in [3,6] else "backward" if direction in [1,4] else "up"
			drive(sim,direction)
			check(f.state == "transform" and f.height == 0 and int(f.stats.energy) == 0, "route_start_%s_%s" % [facing,direction])
			check(str(f.battle_form.id) == "fixture-" + selector, "relative_selector_%s_%s" % [facing,direction])
			var selected_move := f.move_id
			var target: UfeFighterDefinition = f.battle_form.target_definition
			var transform_ticks: int = f.definition.moves[selected_move].frames.size()
			var entry_ticks: int = f.battle_form.entry_frames.size()
			var x := f.x; var hp := int(f.stats.hp)
			var clock := sim.remaining
			for tick in range(transform_ticks):
				check(UfeHitResolver.invulnerable(f), "invulnerable_transform_%s_%s_%s" % [facing,direction,tick])
				sim.step([input_for(8,facing,UfeInputFrame.LIGHT),UfeInputFrame.make()])
				if tick < transform_ticks-1: check(f.move_id == selected_move, "selection_locked_%s_%s_%s" % [facing,direction,tick])
			check(f.definition == target and f.form_id == "fixture-" + selector, "definition_and_id_swapped_%s_%s" % [facing,direction])
			check(f.state == "form_entry" and f.height == 0, "entry_no_accidental_jump_%s_%s" % [facing,direction])
			advance(sim,entry_ticks)
			check(f.state == "idle" and f.x == x and int(f.stats.hp) == hp and f.facing == facing, "retained_values_and_control_%s_%s" % [facing,direction])
			check(sim.remaining == clock, "transform_and_entry_pause_clock_%s_%s" % [facing,direction])
			f.stats.energy = 3000
			drive(sim,2)
			check(f.state != "transform" and f.transformed_this_round and not UfeBattleTransform.can_transform(f), "no_second_armor_%s_%s" % [facing,direction])
			# 第二次22+P回退到三级必杀，其演出也暂停计时；先自然收招再验局末。
			advance(sim,160)
			sim.remaining = 1; advance(sim,1)
			check(sim.finished and f.definition == target and f.form_id == "fixture-" + selector, "round_end_retains_selected_form_%s_%s" % [facing,direction])
			routing_evidence.append({"facing":facing,"direction":direction,"selector":selector,"move":selected_move,"target":target.id,"transform_ticks":transform_ticks,"entry_ticks":entry_ticks})
	check(not fixture().fighters[0].transformed_this_round, "new_round_clears_usage")

func free_source() -> Dictionary:
	var choices: Array = []
	for row in [["neutral",[2,5],"ex_red_king"], ["forward",[3,6],"ex_gomora"], ["backward",[1,4],"ex_red_king"]]:
		var choice: Dictionary = UfeBattleFormCatalog.registry()["gomora" if row[2] == "ex_gomora" else "red_king"].duplicate(true)
		choice.id = "free-" + str(row[0]); choice.enabled = true
		choice.directions = row[1]; choice.default = row[0] == "neutral"
		choice.display_name = str(row[0]) + "免费切换"
		choice.free_switch = true; choice.energy_cost = 0
		choices.append(choice)
	return {"id":"fixture-free-forms", "enabled":true, "choices":choices}

# E独立切已开放形态：不耗气、每局不限次数，但切到当前形态不重播。
func test_free_switch_choices() -> void:
	var sim := fixture(1, free_source())
	var f := sim.fighters[0]
	f.stats.energy = 0
	check(UfeBattleTransform.can_transform(f, ""), "free_switch_any_choice_available")
	drive(sim,6)
	check(f.state == "transform" and int(f.stats.energy) == 0, "free_switch_no_energy_cost")
	check(not f.transformed_this_round, "free_switch_not_once_per_round")
	var ticks: int = f.definition.moves[f.move_id].frames.size() + f.battle_form.entry_frames.size()
	advance(sim,ticks)
	check(f.state == "idle" and f.definition.id == "ex_gomora", "free_switch_first_target")
	check(UfeBattleTransform.can_transform(f, ""), "free_switch_repeat_available")
	drive(sim,2)
	check(f.state == "transform" and int(f.stats.energy) == 0, "free_switch_repeat_no_cost")
	ticks = f.definition.moves[f.move_id].frames.size() + f.battle_form.entry_frames.size()
	advance(sim,ticks)
	check(f.definition.id == "ex_red_king", "free_switch_second_target")
	drive(sim,2)
	check(f.state != "transform" and f.definition.id == "ex_red_king", "free_switch_same_form_not_replayed")

# 选人界面出场形态：开局definition直接是形态定义，基础ID留在base_definition供回放复原。
func test_start_definition() -> void:
	var a := UfeBattleFormCatalog.assemble(UfeContentDatabase.fighter("ultraman", true), free_source())
	var base := UfeContentDatabase.fighter("ultraseven", true)
	var free_choice: Dictionary = a.form.choices["battle_transform__free-forward"]
	var target: UfeFighterDefinition = free_choice.target_definition
	var sim := UfeMatchDirector.new(a.definition, base, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), {"ultraman":a.form}, {0:target})
	var f := sim.fighters[0]
	check(f.definition == target and f.base_definition.id == "ultraman", "start_form_definition_without_base_swap")
	check(f.form_id == "ex_gomora", "start_form_id_kept")
	var plain := UfeMatchDirector.new(a.definition, base, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), {"ultraman":a.form})
	check(plain.content_fingerprint != sim.content_fingerprint, "start_form_changes_fingerprint")
	# 回放必须记住出场形态，重放才能装回同一开局定义。
	var recorder := UfeReplayRecorder.new()
	recorder.append([UfeInputFrame.make(), UfeInputFrame.make()], UfeMatchDirector.new(a.definition, base, load("res://content/rules/neo.tres"), UfeContentDatabase.states(), {"ultraman":a.form}, {0:target}))
	check(recorder.forms == ["ex_gomora", "default"], "start_form_recorded_in_replay")
	check(f.battle_form_choices.size() == 3, "start_form_keeps_all_choices")
	f.stats.energy = 0
	drive(sim,2)
	check(f.state == "transform", "start_form_can_switch_to_default")
	var ticks: int = f.definition.moves[f.move_id].frames.size() + f.battle_form.entry_frames.size()
	advance(sim,ticks)
	check(f.definition.id == "ex_red_king" and int(f.stats.energy) == 0, "start_form_switch_target_and_cost")

func test_buffer_fallback_and_jump() -> void:
	var buffered := fixture()
	buffered.hitstop = 7
	drive(buffered,8)
	check(buffered.fighters[0].combat.buffer == "battle_transform__fixture-up", "buffer_keeps_target_id")
	for tick in range(5): buffered.step([input_for(6,1),UfeInputFrame.make()])
	check(buffered.fighters[0].state == "transform" and buffered.fighters[0].battle_form.id == "fixture-up", "buffer_uses_input_time_selector")
	for missing in ["energy","health","once"]:
		var sim := fixture(); var f := sim.fighters[0]
		if missing == "energy": f.stats.energy = 2000
		if missing == "health": f.stats.hp = 501
		if missing == "once": f.transformed_this_round = true
		drive(sim,8)
		check(f.state != "transform" and f.definition.id == "ultraman", "condition_fallback_"+missing)
		check(f.move_id == ("special2" if missing == "energy" else "special3") and f.height == 0, "ordinary_super_fallback_"+missing)
	for direction in [7,8,9]:
		var jump := fixture()
		jump.step([input_for(direction,1,UfeInputFrame.SPECIAL),UfeInputFrame.make()])
		check(jump.fighters[0].state != "transform", "plain_up_special_does_not_transform_%s" % direction)
		var simple := fixture()
		simple.step([input_for(direction,1),UfeInputFrame.make()])
		check(simple.fighters[0].state == "takeoff", "ordinary_jump_kept_%s" % direction)
	var expired := fixture()
	for d in [2,5,2]: expired.step([input_for(d,1),UfeInputFrame.make()])
	advance(expired,20)
	expired.step([input_for(8,1),UfeInputFrame.make()])
	check(expired.fighters[0].state == "takeoff", "expired_double_down_does_not_swallow_jump")
	var crush := fixture()
	for input in [input_for(2,1),input_for(5,1),input_for(2,1,UfeInputFrame.CRUSH)]: crush.step([input,UfeInputFrame.make()])
	check(crush.fighters[0].move_id == "motion_22", "existing_double_down_crush_kept")

func test_configuration_and_fingerprint() -> void:
	for defect in ["directions","default","duplicate","disabled"]:
		var source := choice_source()
		if defect == "directions": source.choices[1].directions = [2]
		if defect == "default": source.choices[0].default = false
		if defect == "duplicate": source.choices[1].id = source.choices[0].id
		if defect == "disabled":
			source.enabled = false
			for choice in source.choices: choice.transform = "res://must-not-read-missing-armor.json"
		var sim := fixture(1,source)
		check(not UfeBattleTransform.can_transform(sim.fighters[0]), "invalid_or_closed_form_"+defect)
		check(not sim.fighters[0].definition.moves.has("battle_transform"), "invalid_table_has_no_partial_moves_"+defect)
	var original := fixture()
	var changed := choice_source()
	changed.choices[3].target = "ex_red_king"
	var modified := fixture(1,changed)
	check(original.content_fingerprint != modified.content_fingerprint, "nondefault_target_changes_replay_fingerprint")
	var pending := fixture()
	var f := pending.fighters[0]
	var projectile: Dictionary = f.definition.moves.pulse.projectile.duplicate(true)
	projectile.speed = 0; projectile.life = 180
	UfeProjectileResolver.spawn(pending,0,projectile,"pulse")
	check(pending.projectiles[0].has("source_move"), "base_projectile_keeps_definition_before_multi_transform")
	var damage := int(pending.projectiles[0].source_move.damage)
	drive(pending,6); advance(pending,72)
	check(f.definition.id == "ex_gomora" and int(pending.projectiles[0].source_move.damage) == damage, "projectile_source_survives_multi_definition_change")

func test_replay(run_out: String) -> void:
	for facing in [-1,1]:
		for direction in [5,6,4,8]:
			var sim := fixture(facing)
			var twin := fixture(facing)
			var recorder := UfeReplayRecorder.new()
			for tick in range(160):
				var input := input_for(2,facing) if tick in [0,2] else input_for(5,facing)
				if tick == 3: input = input_for(direction,facing,UfeInputFrame.SPECIAL)
				if tick == 125: input = input_for(5,facing,UfeInputFrame.LIGHT)
				var pair := [input,UfeInputFrame.make()]
				sim.step(pair); twin.step(pair); recorder.append(pair,sim)
				check(sim.state_hash() == twin.state_hash(), "multi_tick_determinism_%s_%s_%s" % [facing,direction,tick])
			var path := run_out + "replay-%s-%s.json" % [facing,direction]
			check(recorder.save_file(path) == OK, "save_multi_replay_%s_%s" % [facing,direction])
			var loaded := UfeReplayRecorder.load_file(path,sim.content_fingerprint)
			check(loaded != null, "load_multi_replay_%s_%s" % [facing,direction])
			var replay := fixture(facing)
			if loaded != null:
				for pair in loaded.frames: replay.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
				check(replay.state_hash() == loaded.final_hash, "multi_replay_final_hash_%s_%s" % [facing,direction])
			var changed := choice_source(); changed.choices[3].target = "ex_red_king"
			check(UfeReplayRecorder.load_file(path,fixture(facing,changed).content_fingerprint) == null, "changed_target_rejects_replay_%s_%s" % [facing,direction])

func run() -> void:
	var baseline := "--baseline" in OS.get_cmdline_user_args()
	var label := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--label="): label = arg.trim_prefix("--label=")
	var run_out := OUT + label + "/" if not label.is_empty() else "user://armor-transform-routing/"
	DirAccess.make_dir_recursive_absolute(OUT)
	DirAccess.make_dir_recursive_absolute(run_out)
	var data := legacy_snapshots()
	FileAccess.open(run_out + "legacy-snapshot.json", FileAccess.WRITE).store_string(JSON.stringify(data))
	if baseline:
		check(not FileAccess.file_exists(OUT + "legacy-baseline.json"), "baseline_must_not_overwrite")
		if errors.is_empty(): FileAccess.open(OUT + "legacy-baseline.json", FileAccess.WRITE).store_string(JSON.stringify(data))
	else:
		if FileAccess.file_exists(OUT + "legacy-baseline.json"):
			var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OUT + "legacy-baseline.json"))
			# JSON读取的数值均为float；两边同样解码，避免事件整数的序列化假差异。
			check(original == JSON.parse_string(JSON.stringify(data)), "legacy_all_ticks_events_and_fingerprints_unchanged")
		test_routing_and_lifecycle()
		test_free_switch_choices()
		test_start_definition()
		test_buffer_fallback_and_jump()
		test_configuration_and_fingerprint()
		test_replay(run_out)
	FileAccess.open(run_out + "logic-result.json", FileAccess.WRITE).store_string(JSON.stringify({"passed":errors.is_empty(), "errors":errors,"routing":routing_evidence,"legacy_baseline_available":FileAccess.file_exists(OUT+"legacy-baseline.json")}, "\t"))
	print("ARMOR_TRANSFORM_ROUTING " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
