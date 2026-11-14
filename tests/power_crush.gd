extends SceneTree
## 站立 O：点按不延迟，按住蓄力分档，满档强化破防，回放确定。
var errors: Array = []

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr("FAIL " + label)

func crush_input(held: bool) -> UfeInputFrame:
	return UfeInputFrame.make(0, 0, UfeInputFrame.CRUSH if held else 0)

func fresh() -> UfeMatchDirector:
	var sim := UfeContentDatabase.match_for("ultraseven", "ultraseven")
	sim.fighters[0].x = 400
	sim.fighters[1].x = 470
	sim.fighters[0].facing = 1
	sim.fighters[1].facing = -1
	return sim

func hold_crush(sim: UfeMatchDirector, ticks: int) -> void:
	for _i in ticks:
		sim.step([crush_input(true), UfeInputFrame.make()])

func test_loaded_numbers() -> void:
	var sim := fresh()
	var moves: Dictionary = sim.fighters[0].definition.moves
	var original: Dictionary = moves.crush
	check(bool(original.unblockable) and not bool(original.knockdown), "原超重击仍是破防，不是击倒")
	check(moves.has("crush_charge_2") and moves.has("crush_charge_3") and not moves.has("power_crush_1"), "只从原超重击派生二档和三档")
	check(int(moves.crush_charge_2.damage) == int(original.damage) * 14 / 10, "二档伤害为原招的 140%")
	check(int(moves.crush_charge_3.damage) == int(original.damage) * 18 / 10, "三档伤害为原招的 180%")
	check(int(moves.crush_charge_2.feedback.hitstop) == int(original.feedback.hitstop) + 2, "二档停顿升一档")
	check(int(moves.crush_charge_2.pushback) == int(original.pushback) + 2, "二档推退升一档")
	check(int(moves.crush_charge_3.feedback.hitstop) == int(original.feedback.hitstop) + 4, "三档停顿再升一档")
	check(int(moves.crush_charge_3.pushback) == int(original.pushback) + 4, "三档推退再升一档")
	check(bool(moves.crush_charge_3.unblockable) and not bool(moves.crush_charge_3.knockdown), "满档保持破防，不改成击倒")
	check(int(moves.crush_charge_3.enhanced_guard_break) == UfeFeelRules.CRUSH_BREAK_TICKS, "满档破防硬直加长")
	check(int(moves.crush_charge_2.energy_cost) == 0 and int(moves.crush_charge_3.energy_cost) == 0, "不消耗能量槽")
	check(UfeContentDatabase.fighter("ultraman").moves.has("crush_charge_3"), "其他角色的站立超重击也能蓄力")
	check(UfeInputFrame.ALL_BUTTONS == 2047 and not ("power_crush" in UfeInputRouter.ACTIONS), "没有新增按键")

func test_tap_is_immediate() -> void:
	var tapped := fresh()
	tapped.step([crush_input(true), UfeInputFrame.make()])
	var heavy := fresh()
	heavy.step([UfeInputFrame.make(0, 0, UfeInputFrame.HEAVY), UfeInputFrame.make()])
	check(tapped.fighters[0].move_id == "crush" and tapped.fighters[0].move_tick == heavy.fighters[0].move_tick, "点按与重击同一 tick 出招")
	tapped.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(tapped.fighters[0].move_id == "crush" and tapped.fighters[0].state != "crush_charge", "松开后原超重击继续，不进入蓄力")
	var three := fresh()
	hold_crush(three, 3)
	three.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(three.fighters[0].move_id == "crush" and three.fighters[0].state != "crush_charge", "按住 3 tick 后松开仍是原招")

func test_tiers() -> void:
	var entered := fresh()
	hold_crush(entered, 4)
	check(entered.fighters[0].state == "crush_charge" and int(entered.fighters[0].motion.crush_hold) == 4, "按住满 4 tick 进入蓄力")
	var tier1 := fresh()
	hold_crush(tier1, 4)
	hold_crush(tier1, 15)
	var before := int(tier1.fighters[0].stats.stamina)
	tier1.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(tier1.fighters[0].move_id == "crush", "累计 19 tick 松开仍出原超重击")
	check(int(tier1.fighters[0].stats.stamina) == before - int(tier1.fighters[0].definition.moves.crush.stamina_cost), "出手只扣一次原招体力")
	var tier2 := fresh()
	hold_crush(tier2, 4 + 16)
	tier2.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(tier2.fighters[0].move_id == "crush_charge_2", "累计 20 tick 松开是 2 档")
	var tier39 := fresh()
	hold_crush(tier39, 4 + 35)
	tier39.step([UfeInputFrame.make(), UfeInputFrame.make()])
	check(tier39.fighters[0].move_id == "crush_charge_2", "累计 39 tick 松开仍是 2 档")
	var auto := fresh()
	var energy := int(auto.fighters[0].stats.energy)
	hold_crush(auto, 4 + 36)
	check(auto.fighters[0].move_id == "crush_charge_3", "累计 40 tick 自动出 3 档")
	check(int(auto.fighters[0].stats.energy) == energy, "出手不改变能量槽")

func test_other_buttons_and_cancel() -> void:
	var slide := fresh()
	slide.step([UfeInputFrame.make(0, -1, UfeInputFrame.CRUSH), UfeInputFrame.make()])
	check(slide.fighters[0].move_id == "slide" and slide.fighters[0].state != "crush_charge", "下段 O 仍是滑铲")
	var air := fresh()
	air.fighters[0].state = "air"
	air.fighters[0].height = 40
	air.fighters[0].motion.jump_kind = "vertical"
	air.step([crush_input(true), UfeInputFrame.make()])
	check(air.fighters[0].move_id == "air_crush" and air.fighters[0].state != "crush_charge", "空中 O 仍是下砸")
	var guard := fresh()
	hold_crush(guard, 6)
	guard.step([UfeInputFrame.make(0, 0, UfeInputFrame.GUARD), UfeInputFrame.make()])
	check(guard.fighters[0].state == "guard" and guard.fighters[0].move_id.is_empty(), "防御取消蓄力")
	var dodge := fresh()
	hold_crush(dodge, 6)
	dodge.step([UfeInputFrame.make(0, 0, UfeInputFrame.DODGE), UfeInputFrame.make()])
	check(dodge.fighters[0].state == "dodge" and dodge.fighters[0].move_id.is_empty(), "闪避取消蓄力")
	var charge := fresh()
	charge.step([UfeInputFrame.make(0, 0, UfeInputFrame.CHARGE), UfeInputFrame.make()])
	check(charge.fighters[0].state == "charge_start", "Q 蓄能不进入超重击蓄力")
	var hit := fresh()
	hold_crush(hit, 6)
	hit.fighters[0].x = 400
	hit.fighters[1].x = 470
	hit.step([crush_input(true), UfeInputFrame.make(0, 0, UfeInputFrame.LIGHT)])
	var interrupted := false
	for _i in 16:
		if hit.fighters[0].state == "hit":
			interrupted = true
			break
		hit.step([crush_input(true), UfeInputFrame.make()])
	check(interrupted and hit.fighters[0].move_id.is_empty(), "被打中断蓄力且不出招")

func test_guard_break_and_overlay() -> void:
	var sim := fresh()
	var charged: Dictionary = sim.fighters[0].definition.moves.crush_charge_3
	var original: Dictionary = sim.fighters[0].definition.moves.crush
	check(UfeHitResolver.apply(sim.fighters[0], sim.fighters[1], charged, true, sim.rules) == "hit", "满档打在防御上仍然命中")
	check(sim.fighters[1].state == "guardbreak" and int(sim.fighters[1].motion.duration) == UfeFeelRules.CRUSH_BREAK_TICKS, "满档把防御打成更长的破防")
	var open := fresh()
	check(UfeHitResolver.apply(open.fighters[0], open.fighters[1], open.fighters[0].definition.moves.crush_charge_3, false, open.rules) == "hit", "满档打空防是命中")
	check(open.fighters[1].state == "hit", "没有防御时不满档击倒")
	var plain := fresh()
	check(UfeHitResolver.apply(plain.fighters[0], plain.fighters[1], original, true, plain.rules) == "hit", "点按超重击仍然打穿防御")
	check(plain.fighters[1].state == "hit", "点按不进入加长破防")
	var shown := fresh()
	hold_crush(shown, 8)
	var overlay := UfeTrainingOverlay.new()
	root.add_child(overlay)
	overlay.update_match(shown)
	check(str(overlay.info[0].text).contains("超重击") and str(overlay.info[0].text).contains("1档"), "训练模式显示当前档位")

func snapshot_run() -> Array:
	var sim := fresh()
	var rows: Array = []
	hold_crush(sim, 4 + 16)
	sim.step([UfeInputFrame.make(), UfeInputFrame.make()])
	for _i in 4:
		sim.step([UfeInputFrame.make(), UfeInputFrame.make()])
		rows.append(JSON.stringify(sim.fighters[0].snapshot()))
	rows.append(sim.content_fingerprint)
	return rows

func test_replay() -> void:
	var first := snapshot_run()
	var second := snapshot_run()
	check(first == second, "同一输入两次快照与指纹一致")
	check(str(first[-1]).length() == 64, "内容指纹稳定")

func run() -> void:
	test_loaded_numbers()
	test_tap_is_immediate()
	test_tiers()
	test_other_buttons_and_cancel()
	test_guard_break_and_overlay()
	test_replay()
	print("POWER_CRUSH " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
