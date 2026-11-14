extends SceneTree
## 蓄力超重击：档位边界、满档自动出手、被打中断、回放确定性。
var errors: Array = []

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func hold_input(held: bool) -> UfeInputFrame:
	return UfeInputFrame.make(0, 0, UfeInputFrame.POWER_CRUSH if held else 0)

func fresh() -> UfeMatchDirector:
	var sim := UfeContentDatabase.match_for("ultraseven", "ultraseven")
	sim.fighters[0].x = 400
	sim.fighters[1].x = 480
	sim.fighters[0].facing = 1
	sim.fighters[1].facing = -1
	return sim

func charge_for(sim: UfeMatchDirector, ticks: int, release: bool) -> void:
	sim.step([hold_input(true), UfeInputFrame.make()])
	for _i in ticks:
		sim.step([hold_input(true), UfeInputFrame.make()])
	if release:
		sim.step([hold_input(false), UfeInputFrame.make()])

func test_loaded_numbers() -> void:
	var sim := fresh()
	var moves: Dictionary = sim.fighters[0].definition.moves
	var light: Dictionary = moves.light1
	var heavy: Dictionary = moves.heavy
	check(int(light.hitstun) == 22 and int(light.blockstun) == 18 and int(light.pushback) == 4, "轻击档位硬直与推退")
	check(int(light.feedback.hitstop) == 7, "轻击命中停顿")
	check(int(heavy.hitstun) == 22 and int(heavy.blockstun) == 15 and int(heavy.pushback) == 6, "重击档位硬直与推退")
	check(int(heavy.feedback.hitstop) == 12, "重击命中停顿")
	check(moves.has("power_crush_1") and moves.has("power_crush_2") and moves.has("power_crush_3"), "三档招式已注入")
	check(int(moves.power_crush_1.damage) == int(heavy.damage), "一档伤害等于重击")
	check(int(moves.power_crush_2.damage) == int(heavy.damage) * 14 / 10, "二档伤害为重击的 140%")
	check(int(moves.power_crush_3.damage) == int(heavy.damage) * 18 / 10, "三档伤害为重击的 180%")
	check(bool(moves.power_crush_3.knockdown) and not bool(moves.power_crush_3.unblockable), "满档击倒且不破防")
	check(int(moves.power_crush_1.energy_cost) == 0 and int(moves.power_crush_3.energy_cost) == 0, "不消耗能量槽")
	var other := UfeContentDatabase.fighter("ultraman")
	check(other.moves.has("power_crush_3"), "其他角色也能用蓄力超重击")

func test_tiers() -> void:
	var first := fresh()
	charge_for(first, 19, true)
	check(first.fighters[0].move_id == "power_crush_1", "按住 19 tick 松开是 1 档")
	var second := fresh()
	charge_for(second, 20, true)
	check(second.fighters[0].move_id == "power_crush_2", "按住 20 tick 松开是 2 档")
	var third := fresh()
	charge_for(third, 39, true)
	check(third.fighters[0].move_id == "power_crush_2", "按住 39 tick 松开仍是 2 档")
	var auto := fresh()
	var energy := int(auto.fighters[0].stats.energy)
	charge_for(auto, 40, false)
	check(auto.fighters[0].move_id == "power_crush_3", "按住到 40 tick 自动出 3 档")
	check(int(auto.fighters[0].stats.energy) == energy, "出手不改变能量槽")

func test_cancel_and_hit() -> void:
	var guard := fresh()
	charge_for(guard, 5, false)
	check(guard.fighters[0].state == "power_charge", "蓄力中停留在 power_charge")
	guard.step([UfeInputFrame.make(0, 0, UfeInputFrame.GUARD), UfeInputFrame.make()])
	check(guard.fighters[0].state == "guard" and guard.fighters[0].move_id.is_empty(), "防御取消蓄力")
	var dodge := fresh()
	charge_for(dodge, 5, false)
	dodge.step([UfeInputFrame.make(0, 0, UfeInputFrame.DODGE), UfeInputFrame.make()])
	check(dodge.fighters[0].state == "dodge" and dodge.fighters[0].move_id.is_empty(), "闪避取消蓄力")
	var charge := fresh()
	charge.step([UfeInputFrame.make(0, 0, UfeInputFrame.CHARGE), UfeInputFrame.make()])
	check(charge.fighters[0].state == "charge_start", "Q 蓄能不进入蓄力超重击")
	var hit := fresh()
	charge_for(hit, 6, false)
	hit.step([hold_input(true), UfeInputFrame.make(0, 0, UfeInputFrame.LIGHT)])
	var interrupted := false
	for _i in 16:
		if hit.fighters[0].state == "hit":
			interrupted = true
			break
		hit.step([hold_input(true), UfeInputFrame.make()])
	check(interrupted and hit.fighters[0].move_id.is_empty(), "被打中断蓄力且不出招")

func test_knockdown_and_overlay() -> void:
	var sim := fresh()
	var move: Dictionary = sim.fighters[0].definition.moves.power_crush_3
	check(UfeHitResolver.apply(sim.fighters[0], sim.fighters[1], move, false, sim.rules) == "hit", "满档命中结算")
	check(sim.fighters[1].state == "down", "满档命中击倒")
	var blocked := fresh()
	var blocked_move: Dictionary = blocked.fighters[0].definition.moves.power_crush_3
	check(UfeHitResolver.apply(blocked.fighters[0], blocked.fighters[1], blocked_move, true, blocked.rules) == "block", "满档仍可被防")
	check(blocked.fighters[1].state == "blockstun", "被防进入防御硬直而不是击倒")
	var shown := fresh()
	charge_for(shown, 8, false)
	var overlay := UfeTrainingOverlay.new()
	root.add_child(overlay)
	overlay.update_match(shown)
	check(str(overlay.info[0].text).contains("蓄力超重击") and str(overlay.info[0].text).contains("1档"), "训练模式显示当前档位")

func snapshot_run() -> Array:
	var sim := fresh()
	var rows: Array = []
	sim.step([hold_input(true), UfeInputFrame.make()])
	for _i in 20:
		sim.step([hold_input(true), UfeInputFrame.make()])
	sim.step([hold_input(false), UfeInputFrame.make()])
	for _i in 4:
		sim.step([UfeInputFrame.make(), UfeInputFrame.make()])
		rows.append(JSON.stringify(sim.fighters[0].snapshot()))
	rows.append(sim.content_fingerprint)
	return rows

func test_replay() -> void:
	var first := snapshot_run()
	var second := snapshot_run()
	check(first == second, "同一输入两次快照与指纹一致")
	check(str(first[-1]) == str(second[-1]) and str(first[-1]).length() == 64, "内容指纹稳定")

func run() -> void:
	test_loaded_numbers()
	test_tiers()
	test_cancel_and_hit()
	test_knockdown_and_overlay()
	test_replay()
	print("POWER_CRUSH " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
