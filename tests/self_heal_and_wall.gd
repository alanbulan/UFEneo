extends SceneTree
## 自身回复与光壁拦截的整数规则；不涉画面与听感。
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

func heal_move(sim: UfeMatchDirector) -> Dictionary:
	var f := sim.fighters[0]
	f.definition.moves = f.definition.moves.duplicate(true)
	var move: Dictionary = f.definition.moves.pulse.duplicate(true)
	move.stamina_cost = 0; move.energy_cost = 0
	move.self_heal = {"frame": 1, "amount": 120, "cleanse": true}
	f.definition.moves.heal_test = move
	return move

func test_self_heal() -> void:
	var sim := fixture()
	heal_move(sim)
	var f := sim.fighters[0]
	f.stats.hp = 900; f.stats.stun = 30
	sim._start(f, "heal_test")
	sim.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(f.stats.hp == 900, "声明帧之前不回血")
	check(int(f.stats.stun) > 0, "声明帧之前不清眩晕")
	sim.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(f.stats.hp == 1000, "回血按上限截断")
	check(f.stats.stun == 0, "回复帧清眩晕")
	var healed: Array = sim.events.filter(func(e): return str(e.get("kind", "")) == "self_heal")
	check(healed.size() == 1 and int(healed[0].amount) == 100, "回血事件只结算实际回复量")
	var before := int(f.stats.hp)
	sim.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(f.stats.hp == before, "同一招只结算一次")

func test_no_hit() -> void:
	var sim := fixture()
	var b := sim.fighters[1]
	var contacts: Array = []
	UfeProjectileResolver.spawn(sim, 0, {"spawn":[100,82],"box":[-12,-10,24,20],"speed":0,"life":6,"no_hit":true}, "special_rings")
	UfeProjectileResolver.advance(sim, contacts)
	check(contacts.is_empty(), "纯表现弹体不形成接触")
	check(b.stats.hp == 1000, "纯表现弹体不扣血")

func test_wall() -> void:
	var sim := fixture()
	var b := sim.fighters[1]
	var wall := {"spawn":[40,82],"box":[0,-65,88,130],"speed":0,"life":12,"wall":true}
	UfeProjectileResolver.spawn(sim, 0, wall, "motion_22")
	check(sim.projectiles[0].wall == true, "光壁标记进入弹体")
	var contacts: Array = []
	UfeProjectileResolver.advance(sim, contacts)
	check(contacts.is_empty(), "光壁不击中人物")
	check(b.stats.hp == 1000, "光壁不扣血")
	# 对手一发静止弹已与光壁相交：同 tick 被消去，光壁本身保留。
	UfeProjectileResolver.spawn(sim, 1, {"spawn":[10,82],"box":[-12,-10,24,20],"speed":0,"life":9}, "pulse")
	UfeProjectileResolver.advance(sim, contacts)
	var enemy_left := sim.projectiles.filter(func(p): return int(p.owner) == 1)
	check(enemy_left.is_empty(), "对方弹体被光壁消去")
	var wall_left := sim.projectiles.filter(func(p): return bool(p.get("wall", false)))
	check(wall_left.size() == 1, "光壁拦截后保留")
	check(not sim.events.filter(func(e): return str(e.get("kind", "")) == "wall_intercept").is_empty(), "记录光壁拦截事件")
	check(contacts.is_empty() and b.stats.hp == 1000, "拦截不产生人物伤害")

func test_validation() -> void:
	var move: Dictionary = UfeContentDatabase.fighter("ultraman").moves.pulse.duplicate(true)
	for value in [true, false]:
		var copy := move.duplicate(true); copy.frames[0].shots = [{"no_hit":value,"wall":value}]
		check(UfeMoveData.validate(copy), "no_hit/wall 布尔值合法/%s" % value)
	for value in [0, 1, "true", null]:
		var copy := move.duplicate(true); copy.frames[0].shots = [{"no_hit":value}]
		check(not UfeMoveData.validate(copy), "no_hit 非布尔被拒/%s" % value)
		copy = move.duplicate(true); copy.frames[0].shots = [{"wall":value}]
		check(not UfeMoveData.validate(copy), "wall 非布尔被拒/%s" % value)
	for heal in [{"frame":0,"amount":120}, {"frame":1,"amount":0,"cleanse":true}]:
		var copy := move.duplicate(true); copy.self_heal = heal
		check(UfeMoveData.validate(copy), "合法自身回复/%s" % heal)
	for heal in [{"amount":120}, {"frame":-1,"amount":120}, {"frame":0,"amount":1.5},
			{"frame":0,"amount":120,"cleanse":1}, {"frame":99,"amount":120},
			{"frame":0,"amount":120,"heal_over_ticks":180}, "120"]:
		var copy := move.duplicate(true); copy.self_heal = heal
		check(not UfeMoveData.validate(copy), "非法自身回复被拒/%s" % heal)

func run() -> void:
	test_self_heal(); test_no_hit(); test_wall(); test_validation()
	print("SELF_HEAL_AND_WALL " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
