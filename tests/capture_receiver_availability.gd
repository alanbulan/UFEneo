extends SceneTree
## 当前真实名册的输入/费用回归；不向角色塞占位受方帧。
const IDS := ["black_king","eleking","ex_gomora","ex_red_king","gomora","neronga","red_king",
	"ultraman","ultraman-ace","ultraman-arc","ultraman-blazar","ultraman-jack","ultraman-leo",
	"ultraman-omega","ultraman-taro","ultraman-teo","ultraseven","zetton"]
const SUPPORTED := ["ultraseven","zetton","ultraman-omega"]
var output: String = ""
var input_source: String = ""
var expect_fixed: bool = false
var errors: Array = []
var records: Array = []
var definitions: Dictionary = {}
var registry: Dictionary = {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		if arg.begins_with("--replay-source="): input_source = arg.trim_prefix("--replay-source=")
		if arg == "--expect-fixed": expect_fixed = true
	call_deferred("run")

func check(value: bool, reason: String) -> void:
	if not value: errors.append(reason)

func build(config: Dictionary) -> UfeMatchDirector:
	var first: String = "ultraman-teo" if int(config.owner) == 0 else str(config.target)
	var second: String = str(config.target) if int(config.owner) == 0 else "ultraman-teo"
	for id in [first,second]:
		if not definitions.has(id): definitions[id] = UfeBattleFormCatalog.prepare(id,false)
	if registry.is_empty(): registry = UfeContentDatabase.states()
	var forms := {first:definitions[first].form,second:definitions[second].form}
	return UfeMatchDirector.new(definitions[first].definition,definitions[second].definition,
		load("res://content/rules/neo.tres"),registry,forms)

func snapshot(sim: UfeMatchDirector) -> Dictionary:
	return {"tick":sim.tick,"remaining":sim.remaining,"hitstop":sim.hitstop,"finished":sim.finished,
		"winner":sim.winner,"hash":sim.state_hash(),"fighters":sim.fighters.map(func(f):return f.snapshot().duplicate(true)),
		"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)}

func play(config: Dictionary, saved: Array = []) -> Dictionary:
	var sim := build(config)
	var owner := int(config.owner)
	var own: UfeFighter = sim.fighters[owner]
	var charge_done := false
	var cast_age := -1
	var paid := 0
	var stamina_paid := 0
	var starts := 0
	var impacts := 0
	var denied := 0
	var failures: Array = []
	var rows: Array = []
	for age in range(240):
		var pair := [UfeInputFrame.make(),UfeInputFrame.make()]
		if saved.is_empty():
			if not charge_done and int(own.stats.energy) < 500:
				pair[owner] = UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
			else:
				charge_done = true
				if cast_age < 0 and own.state == "idle": cast_age = age
				if cast_age >= 0:
					var elapsed := age-cast_age
					if str(config.input) == "H" and elapsed == 0:
						pair[owner] = UfeInputFrame.make(0,0,UfeInputFrame.SKILL)
					elif str(config.input) == "41236L":
						match elapsed:
							0: pair[owner] = UfeInputFrame.make(-own.facing,0)
							1: pair[owner] = UfeInputFrame.make(-own.facing,-1)
							2: pair[owner] = UfeInputFrame.make(0,-1)
							3: pair[owner] = UfeInputFrame.make(own.facing,-1)
							4: pair[owner] = UfeInputFrame.make(own.facing,0,UfeInputFrame.THROW)
		else:
			pair = saved[age].inputs.map(func(p):return UfeInputFrame.unpack(p))
		var before_stamina := int(own.stats.stamina)
		var before_energy := int(own.stats.energy)
		sim.step(pair)
		paid += maxi(0,before_energy-int(own.stats.energy))
		stamina_paid += maxi(0,before_stamina-int(own.stats.stamina))
		for event in sim.events:
			if str(event.kind) == "capture_start": starts += 1
			if str(event.kind) == "capture_impact": impacts += 1
			if str(event.kind) == "capture_fail": failures.append(str(event.reason))
			if str(event.kind) == "move_denied" and str(event.reason) == "capture_receiver": denied += 1
		rows.append({"inputs":pair.map(func(p):return p.pack()),"state":snapshot(sim)})
	var supported := str(config.target) in SUPPORTED
	var label := str(config)
	check(starts == (0 if expect_fixed and not supported else 1),label+"启动次数")
	check(paid == (0 if expect_fixed and not supported else 500),label+"真实费用")
	check(stamina_paid == (0 if expect_fixed and not supported else 40),label+"真实体力费用")
	check(denied == (1 if expect_fixed and not supported else 0),label+"不支持受方一次前置拒绝")
	check(impacts == (1 if supported else 0),label+"真实捕获结算")
	if supported:
		check(failures.is_empty() and int(sim.fighters[1-owner].stats.hp) == 885,label+"原支持对手保持115伤")
	elif expect_fixed:
		check(failures.is_empty() and int(own.stats.energy) == 500,label+"缺相不再先施放后超时")
	else:
		check(failures == ["projectile_expired"],label+"修前缺相实际弹体过期路径")
	if not saved.is_empty(): check(JSON.parse_string(JSON.stringify(rows)) == saved,label+"独立原InputFrame完整快照/事件重放")
	return {"config":config,"rows":rows,"fingerprint":sim.content_fingerprint,"starts":starts,"energy_paid":paid,
		"stamina_paid":stamina_paid,"impacts":impacts,"denials":denied,"failures":failures,"final_energy":int(own.stats.energy)}

func run() -> void:
	if output.is_empty() or FileAccess.file_exists(output):
		printerr("须指定全新--output，禁止覆盖旧证据")
		quit(2)
		return
	if input_source.is_empty():
		for target in IDS:
			for owner in [0,1]: records.append(play({"target":target,"owner":owner,"input":"H"}))
		for target in ["ultraman-omega","zetton"]:
			for owner in [0,1]: records.append(play({"target":target,"owner":owner,"input":"41236L"}))
	else:
		var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(input_source))
		for record in original.records:
			var replayed := play(record.config,record.rows)
			check(replayed.fingerprint == str(record.fingerprint),"独立回放指纹")
			records.append({"config":record.config,"fingerprint":replayed.fingerprint,"full_snapshot_rows_checked":replayed.rows.size()})
	var file := FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify({"expect_fixed":expect_fixed,"errors":errors,"records":records,
		"all_current_loaded_definitions":IDS,"includes_direct_ex_and_teo_mirror":true,
		"input_source":input_source,"simulation_fixture_writes":0,"visual_art_approved":false,"generated_videos":0},"",true))
	file.close()
	print("CAPTURE_RECEIVER_AVAILABILITY "+("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
