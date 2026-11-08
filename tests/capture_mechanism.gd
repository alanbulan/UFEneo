extends SceneTree
## 纯模拟专项；人物/FX/声音与主游戏画面验收另行完成。
var OUT := "user://capture-mechanism/"
var errors: Array = []
var cases: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func save(name: String, value: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	FileAccess.open(OUT + name, FileAccess.WRITE).store_string(JSON.stringify(value, "", true) + "\n")

func row(sim: UfeMatchDirector, inputs: Array) -> Dictionary:
	return {"inputs":inputs.map(func(i): return i.pack()), "hash":sim.state_hash(),
		"fighters":[sim.fighters[0].snapshot().duplicate(true),sim.fighters[1].snapshot().duplicate(true)],
		"projectiles":sim.projectiles.duplicate(true), "events":sim.events.duplicate(true),
		"tick":sim.tick,"remaining":sim.remaining,"hitstop":sim.hitstop,"finished":sim.finished,"winner":sim.winner}

func frame(sprite: int = 0) -> Dictionary:
	return {"sprite":sprite,"dx":0,"dy":0,"hitboxes":[],"hurtboxes":[[-18,0,36,128]],"cancel":[],"events":[]}

func move_data(id: String, damage: int = 115) -> Dictionary:
	return {"id":id,"kind":"projectile","damage":damage,"hitstun":12,"blockstun":12,"pushback":0,"stun":0,
		"stamina_cost":0,"energy_cost":0,"level":"mid","unblockable":false,"chip_damage":0,
		"launch":false,"bounce":false,"knockdown":false,"frames":[]}

func command(id: String, buttons: int, motion: Array = []) -> Dictionary:
	return {"states":["idle","walk","crouch","turn","charge","guard"],"directions":[0],"buttons":buttons,"motion":motion,"priority":800,"move":id}

func repeat_index(index: int, count: int) -> Array:
	var result: Array = []
	for i in range(count): result.append(index)
	return result

func capture_move() -> Dictionary:
	var move := move_data("motion_41236")
	move.stamina_cost = 40; move.energy_cost = 500
	for tick in range(72): move.frames.append(frame(tick))
	move.frames[8].shots = [{"capture":true,"spawn":[28,70],"box":[-8,-30,16,60],"speed":16,"life":30}]
	move.capture = {"flight_tick":9,"flight_max_ticks":30,"success_tick":10,"success_end_tick":62,"miss_recovery_tick":62,
		"hand_anchor":[35,85],"lift_height":60,"release_distance":80,"release_ground_tick":2,
		"stages":[
			{"id":"enclose","ticks":8,"victim_animation":"fixture_enclosed","victim_frames":[0,0,1,1,2,2,3,3]},
			{"id":"shrink","ticks":12,"victim_animation":"fixture_shrinking","victim_frames":[0,0,1,1,2,2,3,3,4,4,5,5]},
			{"id":"return","ticks":12,"victim_animation":"fixture_shrinking","victim_frames":repeat_index(5,12)},
			{"id":"held","ticks":8,"victim_animation":"fixture_shrinking","victim_frames":repeat_index(5,8)},
			{"id":"release","ticks":6,"victim_animation":"fixture_restore","victim_frames":[
				{"animation":"fixture_shrinking","frame":5},{"animation":"fixture_shrinking","frame":5},0,1,2,3]}]}
	return move

func fixture(config: Dictionary) -> UfeMatchDirector:
	var first := UfeContentDatabase.fighter("ultraman-teo",true)
	var second := UfeContentDatabase.fighter(str(config.opponent),true)
	first.moves.motion_41236 = capture_move()
	first.command_table = UfeContentDatabase.merge_commands(first.command_table,[command("motion_41236",UfeInputFrame.THROW,[4,1,2,3,6])])
	for name in ["fixture_enclosed","fixture_shrinking","fixture_restore"]:
		var count := 6 if name == "fixture_shrinking" else 4
		second.state_frames[name] = []
		for index in range(count): second.state_frames[name].append(frame(index))
	if str(config.kind) == "missing_pose": second.state_frames.erase("fixture_restore")
	if str(config.kind) in ["interrupted","death"]:
		var counter := move_data("counter_fixture",20)
		for tick in range(10): counter.frames.append(frame())
		counter.frames[0].shots = [{"spawn":[25,70],"box":[-6,-6,12,12],"speed":4,"life":90}]
		second.moves.counter_fixture = counter
		second.command_table = UfeContentDatabase.merge_commands(second.command_table,[command("counter_fixture",UfeInputFrame.RANGED)])
	if str(config.kind) in ["reflect","absorb"]:
		for posture in second.state_frames.guard:
			posture.projectile_guard = str(config.kind); posture.guard_box = [-50,0,100,150]
	var sim := UfeMatchDirector.new(first,second,load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	var facing := int(config.facing)
	var actor := sim.fighters[0]; var target := sim.fighters[1]
	actor.x = 730 if facing < 0 else 470
	var gap := 155
	if str(config.kind) == "miss": gap = 650
	if str(config.kind) == "wall": actor.x = 180 if facing < 0 else 1100
	target.x = actor.x+facing*gap
	actor.facing = facing; target.facing = -facing; actor.stats.energy = 500
	if str(config.kind) == "insufficient_energy": actor.stats.energy = 499
	if str(config.kind) == "insufficient_stamina": actor.stats.stamina = 0
	if str(config.kind) == "death": actor.stats.hp = 10
	if str(config.kind) == "round_end": sim.remaining = 40
	return sim

func sample(config: Dictionary, age: int, sim: UfeMatchDirector) -> Array:
	var first := UfeInputFrame.make(); var second := UfeInputFrame.make()
	var facing := int(config.facing)
	var start := 0 if str(config.kind) == "insufficient_stamina" else 10
	var elapsed := age-start
	if elapsed == 0: first = UfeInputFrame.make(-facing,0)
	if elapsed == 1: first = UfeInputFrame.make(-facing,-1)
	if elapsed == 2: first = UfeInputFrame.make(0,-1)
	if elapsed == 3: first = UfeInputFrame.make(facing,-1)
	if elapsed == 4: first = UfeInputFrame.make(facing,0,UfeInputFrame.THROW)
	match str(config.kind):
		"guard","reflect","absorb": second = UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
		"crouch_guard": second = UfeInputFrame.make(0,-1,UfeInputFrame.GUARD)
		"airborne":
			if age == 20: second = UfeInputFrame.make(0,1)
		"interrupted","death":
			if age == 0: second = UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
		"victim_mash":
			if sim.fighters[1].state == "captured": second = UfeInputFrame.make(-facing,1,UfeInputFrame.THROW|UfeInputFrame.LIGHT|UfeInputFrame.HEAVY)
	return [first,second]

func mutate(config: Dictionary, sim: UfeMatchDirector) -> void:
	# 专门的损坏注入与输入实战分列；不会冒称这些字段由按键制造。
	if not sim.fighters[0].motion.has("capture"): return
	var phase := str(sim.fighters[0].motion.capture.phase)
	if str(config.kind) == "move_changed" and phase == "shrink":
		sim.fighters[0].clear_move(); sim.fighters[0].enter("idle")
	if str(config.kind) == "invalid_relation" and phase == "held": sim.fighters[0].motion.capture.victim = 99

func run_case(config: Dictionary, saved_inputs: Array = []) -> Dictionary:
	var sim := fixture(config)
	var rows: Array = []
	var protection: Array = []
	var attacker := UfeFighter.new(UfeContentDatabase.fighter("ultraman"),0)
	attacker.move_id = "throw_forward"
	for age in range(150):
		mutate(config,sim)
		var inputs: Array = sample(config,age,sim) if saved_inputs.is_empty() else saved_inputs[age].map(func(p): return UfeInputFrame.unpack(p))
		sim.step(inputs); rows.append(row(sim,inputs))
		if sim.fighters[1].state == "captured":
			attacker.x = sim.fighters[1].x-10
			protection.append(not UfeHitResolver.can_hit(attacker,sim.fighters[1]) and not UfeCaptureResolver.eligible(sim.fighters[1],capture_move().capture))
	return {"config":config,"fingerprint":sim.content_fingerprint,"rows":rows,"protection":protection}

func events_of(record: Dictionary, kind: String) -> Array:
	var result: Array = []
	for sample_row in record.rows:
		for event in sample_row.events:
			if str(event.kind) == kind: result.append({"tick":sample_row.tick,"event":event})
	return result

func check_case(record: Dictionary) -> void:
	var config: Dictionary = record.config
	var label := str(config)
	var success := str(config.kind) in ["success","wall","victim_mash","insufficient_stamina"]
	var starts := events_of(record,"capture_start"); var begins := events_of(record,"capture_begin")
	var impacts := events_of(record,"capture_impact"); var failures := events_of(record,"capture_fail")
	var last: Dictionary = record.rows.back()
	if str(config.kind) in ["insufficient_energy","missing_pose"]:
		check(starts.is_empty() and begins.is_empty() and impacts.is_empty(),label+"资源不足或受方缺相前置拒绝")
		check(int(last.fighters[0][10].energy) == (499 if str(config.kind)=="insufficient_energy" else 500),label+"前置拒绝无扣能")
	else:
		check(starts.size() == 1,label+"只启动及付费一次")
		if not starts.is_empty():
			check(int(starts[0].event.stamina_cost) == 40 and int(starts[0].event.energy_cost) == 500,label+"实际费用")
		var expected_energy := 40 if str(config.kind) in ["interrupted","death"] else 0
		check(int(last.fighters[0][10].energy) == expected_energy,label+"捕获无额外奖励，普通弹体受击奖励保持")
		if str(config.kind) == "insufficient_stamina":
			check(record.rows[4].fighters[0][12].has("capture") and int(record.rows[4].fighters[0][10].energy) == 0,label+"现行体力规则允许空体启动并扣能")
			check(not starts.is_empty() and int(starts[0].tick) == 5,label+"现行体力规则不延迟原输入")
	check(not last.fighters[0][12].has("capture") and not last.fighters[1][12].has("capture_victim"),label+"最终双方关系清理")
	check(last.projectiles.all(func(p): return not bool(p.get("capture",false))),label+"最终无捕获弹体")
	check(str(last.fighters[0][6]) != "capturing" and str(last.fighters[1][6]) != "captured",label+"没有永久不可行动状态")
	if success:
		check(begins.size() == 1 and impacts.size() == 1,label+"实际接触后一次结算")
		check(int(last.fighters[1][10].hp) == 885,label+"只结算115伤")
		var durations := {"enclose":0,"shrink":0,"return":0,"held":0,"release":0}
		for sample_row in record.rows:
			var relation: Dictionary = sample_row.fighters[0][12].get("capture",{})
			var phase := str(relation.get("phase",""))
			if durations.has(phase): durations[phase] = int(durations[phase])+1
			if phase in ["enclose","shrink","return","held"]: check(int(sample_row.fighters[1][10].hp) == 1000,label+"held末之前不扣血")
			if phase == "release":
				var victim: Dictionary = sample_row.fighters[1][12].capture_victim
				var age := int(relation.phase_age)
				check(str(victim.animation) == ("fixture_shrinking" if age < 2 else "fixture_restore"),label+"释放两clip切换")
				if age >= 2: check(int(sample_row.fighters[1][2]) == 0,label+"恢复帧在安全地面")
		check(durations == {"enclose":8,"shrink":12,"return":12,"held":8,"release":6},label+"五阶段时长")
		check(record.protection.all(func(p): return p),label+"捕获期间免普通投技及再捕获")
		check(int(last.fighters[0][1]) >= 28 and int(last.fighters[0][1]) <= 1252 and int(last.fighters[1][1]) >= 28 and int(last.fighters[1][1]) <= 1252,label+"墙边合法落点")
		check(absi(int(last.fighters[0][1])-int(last.fighters[1][1])) >= 80,label+"安全释放不重叠")
	elif str(config.kind) in ["guard","crouch_guard","miss","airborne","reflect","absorb"]:
		check(begins.is_empty() and impacts.is_empty() and not failures.is_empty(),label+"失败不进入持球成功路径")
		check(int(last.fighters[1][10].hp) == 1000,label+"失败无伤害或削血")
		if str(config.kind) in ["guard","crouch_guard"]: check(events_of(record,"block").size() == 1,label+"原站蹲防御命中")
		if str(config.kind) == "reflect": check(events_of(record,"projectile_reflect").size() == 1,label+"反射盾安全截断")
		if str(config.kind) == "absorb": check(events_of(record,"projectile_absorb").size() == 1,label+"吸收盾安全截断")
	elif str(config.kind) in ["interrupted","death","round_end","move_changed","invalid_relation"]:
		check(begins.size() == 1 and impacts.is_empty(),label+"中断发生在成功接触后、结算前")
		check(not events_of(record,"capture_abort").is_empty(),label+"异常安全释放")
		if str(config.kind) in ["interrupted","death"]: check(not events_of(record,"hit").is_empty(),label+"真实对方弹体打断")
		if str(config.kind) in ["death","round_end"]: check(bool(last.finished),label+"真实回合终局")

func schema_checks() -> void:
	var move := capture_move()
	check(UfeMoveData.validate(move),"完整捕获schema合法")
	for key in ["flight_tick","success_tick","success_end_tick","miss_recovery_tick","flight_max_ticks","release_ground_tick"]:
		var clock_invalid := move.duplicate(true); clock_invalid.capture[key] = 2.5
		check(not UfeMoveData.validate(clock_invalid),"拒绝非整数时钟/"+key)
	var invalid := move.duplicate(true); invalid.capture.flight_max_ticks = 31
	check(not UfeMoveData.validate(invalid),"捕获飞行不能超过30tick")
	invalid = move.duplicate(true); invalid.capture.stages[4].victim_frames[0] = {"animation":"","frame":0}
	check(not UfeMoveData.validate(invalid),"拒绝无本人clip的释放映射")
	invalid = move.duplicate(true); invalid.frames[9].shots = invalid.frames[8].shots.duplicate(true)
	check(not UfeMoveData.validate(invalid),"等待段不能重复发射")
	invalid = move.duplicate(true); invalid.erase("capture")
	check(not UfeMoveData.validate(invalid),"捕获弹体不能悄悄退成普通伤害")

func new_cases() -> void:
	schema_checks()
	for opponent in ["zetton","ultraseven"]:
		for facing in [-1,1]:
			for kind in ["success","guard","crouch_guard","miss","airborne"]:
				var record := run_case({"opponent":opponent,"facing":facing,"kind":kind})
				check_case(record); cases.append(record)
	for kind in ["wall","victim_mash","insufficient_energy","insufficient_stamina","interrupted","death","round_end","missing_pose","reflect","absorb","move_changed","invalid_relation"]:
		for facing in ([-1,1] if kind == "wall" else [1]):
			var record := run_case({"opponent":"zetton","facing":facing,"kind":kind})
			check_case(record); cases.append(record)
	var fresh := fixture({"opponent":"zetton","facing":1,"kind":"success"})
	check(fresh.projectiles.is_empty() and fresh.fighters.all(func(f): return not f.motion.has("capture") and not f.motion.has("capture_victim")),"重开构造不共享旧关系或弹体")
	# 单独的判定注入：实际输入先捕获，再核被捕获姿势即便残留盾字段也不能反弹新弹体。
	var config := {"opponent":"zetton","facing":1,"kind":"success"}
	var protected := fixture(config)
	for age in range(60):
		protected.step(sample(config,age,protected))
		if protected.fighters[1].state == "captured": break
	check(protected.fighters[1].state == "captured","免疫单测由真实输入先完成捕获")
	var pose := protected.fighters[1].frame()
	pose.projectile_guard = "reflect"; pose.guard_box = [-30,0,60,128]
	var offset := (protected.fighters[1].x-protected.fighters[0].x)*protected.fighters[0].facing
	UfeProjectileResolver.spawn(protected,0,{"spawn":[offset,70],"box":[-4,-4,8,8],"speed":0,"life":10},"motion_41236")
	var contacts: Array = []; var events_before := protected.events.duplicate(true)
	UfeProjectileResolver.advance(protected,contacts)
	check(contacts.is_empty() and protected.events == events_before,"捕获期间无普通弹体伤害、投射盾反射或再次交互")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	for argument in args:
		if argument.begins_with("--test-out="):OUT=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
	if "--replay" in args:
		var source: Array = JSON.parse_string(FileAccess.get_file_as_string(OUT+"capture-cases.json"))
		for record in source:
			var inputs: Array = record.rows.map(func(r): return r.inputs)
			var replay := run_case(record.config,inputs)
			check(record == JSON.parse_string(JSON.stringify(replay)),"独立进程真实InputFrame/全快照/事件回放/"+str(record.config))
		save("replay-result.json",{"errors":errors,"all_fields_compared":true,"cases":source.size()})
	else:
		new_cases(); save("capture-cases.json",cases)
		save("logic-result.json",{"errors":errors,"cases":cases.size(),"scope":"current capture schema and behavior; independent replay is a separate invocation"})
	print("CAPTURE_CORE " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
