extends SceneTree
## 减速（chill）规则的整数与确定性检查：只改移动位移，不改招式/受击时序。
var errors: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func fixture() -> UfeMatchDirector:
	var sim := UfeContentDatabase.match_for()
	sim.fighters[0].x = 500; sim.fighters[0].facing = 1
	sim.fighters[1].x = 600; sim.fighters[1].facing = -1
	return sim

func chill_move(sim: UfeMatchDirector, ticks: int = 120, percent: int = 50) -> Dictionary:
	var move: Dictionary = sim.fighters[0].definition.moves.pulse.duplicate(true)
	move.stamina_cost = 0; move.energy_cost = 0
	move.chill = {"ticks": ticks, "speed_percent": percent}
	return move

func test_hit_applies_chill() -> void:
	var sim := fixture()
	var a := sim.fighters[0]
	var b := sim.fighters[1]
	var move := chill_move(sim)
	check(UfeHitResolver.apply(a, b, move, false, sim.rules) == "hit", "命中结算")
	check(int(b.stats.chill_ticks) == 120, "命中写入减速时长")
	check(int(b.stats.chill_percent) == 50, "命中写入减速档位")

func test_block_does_not_chill() -> void:
	var sim := fixture()
	var b := sim.fighters[1]
	var move := chill_move(sim)
	check(UfeHitResolver.apply(sim.fighters[0], b, move, true, sim.rules) == "block", "防御结算")
	check(int(b.stats.chill_ticks) == 0, "防御命中不减速")

func test_stronger_and_longer_wins() -> void:
	var sim := fixture()
	var b := sim.fighters[1]
	UfeHitResolver.apply(sim.fighters[0], b, chill_move(sim, 120, 50), false, sim.rules)
	UfeHitResolver.apply(sim.fighters[0], b, chill_move(sim, 60, 70), false, sim.rules)
	check(int(b.stats.chill_ticks) == 120, "较短减速不缩短剩余时长")
	check(int(b.stats.chill_percent) == 50, "较弱减速不覆盖更强档位")
	UfeHitResolver.apply(sim.fighters[0], b, chill_move(sim, 180, 40), false, sim.rules)
	check(int(b.stats.chill_ticks) == 180, "较长减速延长剩余时长")
	check(int(b.stats.chill_percent) == 40, "更强减速覆盖档位")

func idle_target(b: UfeFighter) -> void:
	b.state = "idle"; b.state_tick = 0; b.move_id = ""
	b.motion.duration = 0; b.height = 0; b.vy = 0

func test_walk_and_dash_speed() -> void:
	var base := fixture()
	var plain := base.fighters[1]
	idle_target(plain)
	var plain_start := plain.x
	base.step([UfeInputFrame.make(), UfeInputFrame.make(1, 0)])
	var plain_delta := plain.x - plain_start
	check(plain_delta == plain.definition.walk_speed, "未减速按原走速")

	var sim := fixture()
	var b := sim.fighters[1]
	idle_target(b)
	b.stats.chill_ticks = 120; b.stats.chill_percent = 50
	var start := b.x
	sim.step([UfeInputFrame.make(), UfeInputFrame.make(1, 0)])
	check(b.x - start == 1, "50% 减速走速减半")
	check(int(b.stats.chill_ticks) == 119, "每 tick 递减减速时长")

	# 减速期间冲刺同样按档位缩放；动作时序不变。
	var dash := fixture()
	var d := dash.fighters[1]
	idle_target(d)
	d.stats.chill_ticks = 120; d.stats.chill_percent = 50
	d.enter("dash", 22); d.motion.direction = 1
	var dash_start := d.x
	dash.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(d.x - dash_start == 3, "50% 减速冲刺减半")
	check(d.state == "dash", "减速不改变动作状态")

func test_expiry_restores_speed() -> void:
	var sim := fixture()
	var b := sim.fighters[1]
	idle_target(b)
	b.stats.chill_ticks = 2; b.stats.chill_percent = 50
	sim.step([UfeInputFrame.make(), UfeInputFrame.make(1, 0)])
	sim.step([UfeInputFrame.make(), UfeInputFrame.make(1, 0)])
	check(int(b.stats.chill_ticks) == 0, "减速时长归零")
	idle_target(b)
	var start := b.x
	sim.step([UfeInputFrame.make(), UfeInputFrame.make(1, 0)])
	check(b.x - start == b.definition.walk_speed, "减速到期恢复原走速")

func test_validation() -> void:
	var move: Dictionary = UfeContentDatabase.fighter("ultraman").moves.pulse.duplicate(true)
	for chill in [{"ticks": 120, "speed_percent": 50}, {"ticks": 1, "speed_percent": 99}]:
		var copy := move.duplicate(true); copy.chill = chill
		check(UfeMoveData.validate(copy), "合法减速/%s" % chill)
	for chill in [{"ticks": 120}, {"speed_percent": 50}, {"ticks": 0, "speed_percent": 50},
			{"ticks": 120, "speed_percent": 0}, {"ticks": 120, "speed_percent": 100},
			{"ticks": 120.5, "speed_percent": 50}, {"ticks": "120", "speed_percent": 50},
			{"ticks": 120, "speed_percent": 50, "freeze": true}, true]:
		var copy := move.duplicate(true); copy.chill = chill
		check(not UfeMoveData.validate(copy), "非法减速被拒/%s" % chill)
	# 佐菲超级冻霜是当前唯一使用该字段的招式，必须通过校验。
	check(UfeMoveData.validate(UfeContentDatabase.fighter("zoffy").moves.special2), "佐菲 special2 减速字段合法")

func run() -> void:
	test_hit_applies_chill(); test_block_does_not_chill(); test_stronger_and_longer_wins()
	test_walk_and_dash_speed(); test_expiry_restores_speed(); test_validation()
	print("CHILL_EFFECT " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
