extends SceneTree
## 体力规则回归：基础拳脚免费；远程/必杀/闪避/格挡付费且不足不启动；
## 格挡按伤害四分之一扣体力；眩晕结束后有免疫，不能连续刷新。
const FREE_IDS := ["light1","light2","light3","crouch_light","crouch_light2",
	"throw_forward","throw_back","air_throw","dash_throw",
	"chase_light1","chase_light2","chase_end","wake_low","wake_mid"]
const GATED_IDS := ["pulse","low_pulse","air_pulse","ranged_forward","special","special2","special3","motion_236","motion_623","motion_214"]
var failed: Array[String] = []
func check(ok: bool, label: String) -> void:
	if not ok:
		failed.append(label)
		printerr("FAIL: "+label)

func denied(sim: UfeMatchDirector, reason: String) -> int:
	return sim.events.filter(func(e):return str(e.kind)=="move_denied" and str(e.get("reason",""))==reason).size()

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var definition := UfeContentDatabase.fighter("ultraman")
	for id in FREE_IDS:
		check(definition.moves.has(id) and int(definition.moves[id].stamina_cost)==0,"基础行动零体力消耗 "+id)
	for id in GATED_IDS:
		check(definition.moves.has(id) and int(definition.moves[id].stamina_cost)>0,"发力招保留体力代价 "+id)
	# 体力正好够时启动并扣费；差一点时明确拒绝且不启动。
	var sim := UfeContentDatabase.match_for("ultraman","zetton")
	var p1 := sim.fighters[0]
	p1.stats.stamina = 29
	sim.step([UfeInputFrame.make(0,0,UfeInputFrame.RANGED),UfeInputFrame.make()])
	check(p1.move_id.is_empty() and denied(sim,"stamina")==1,"体力不足远程不启动")
	sim.step([UfeInputFrame.make(),UfeInputFrame.make()])
	p1.stats.stamina = 30
	sim.step([UfeInputFrame.make(0,0,UfeInputFrame.RANGED),UfeInputFrame.make()])
	check(p1.move_id=="pulse" and int(p1.stats.stamina)==0,"体力恰好够时正常启动并扣费")
	# 0 体力仍可出普通拳脚，不会失去基本行动。
	sim = UfeContentDatabase.match_for("ultraman","zetton")
	p1 = sim.fighters[0]
	p1.stats.stamina = 0
	sim.step([UfeInputFrame.make(0,0,UfeInputFrame.LIGHT),UfeInputFrame.make()])
	check(p1.move_id=="light1","0体力仍能出轻击")
	# 格挡按伤害四分之一扣体力，不再按全额伤害扣。
	sim = UfeContentDatabase.match_for("ultraman","zetton")
	var attacker := sim.fighters[0]
	var blocker := sim.fighters[1]
	blocker.state = "guard"
	blocker.stats.stamina = 1000
	var light: Dictionary = attacker.definition.moves.light1
	UfeHitResolver.apply(attacker,blocker,light,true,sim.rules)
	check(int(blocker.stats.stamina)==1000-UfeStaminaRules.block_cost(int(light.damage)),"格挡体力按伤害四分之一")
	# 眩晕免疫：免疫期内不再累积，免疫结束后恢复累积。
	sim = UfeContentDatabase.match_for("ultraman","zetton")
	attacker = sim.fighters[0]
	blocker = sim.fighters[1]
	blocker.stats.stun = sim.rules.stun_threshold-1
	UfeHitResolver.apply(attacker,blocker,light,false,sim.rules)
	check(blocker.state=="stun" and int(blocker.stats.stun_immune)>0,"达到阈值进入眩晕并开始免疫")
	blocker.state = "idle"
	blocker.stats.stun = sim.rules.stun_threshold-1
	UfeHitResolver.apply(attacker,blocker,light,false,sim.rules)
	check(blocker.state!="stun" and int(blocker.stats.stun)==sim.rules.stun_threshold-1,"免疫期内不再累积眩晕")
	blocker.stats.stun_immune = 0
	UfeHitResolver.apply(attacker,blocker,light,false,sim.rules)
	check(blocker.state=="stun","免疫结束后重新可被眩晕")
	# 连续远程：体力见底后会出现明确拒绝，且眩晕不会无限刷新。
	sim = UfeContentDatabase.match_for("ultraman","zetton")
	p1 = sim.fighters[0]
	var p2 := sim.fighters[1]
	var shots := 0
	var last_move := ""
	var stunned := 0
	var stun_entries := 0
	var stamina_denials := 0
	var last_state := p2.state
	for tick in range(1800):
		var press := tick % 27 == 0
		var before := int(p1.stats.stamina)
		p2.stats.hp = 1000 # 只观察体力与眩晕，不让对局提前结束。
		sim.step([UfeInputFrame.make(0,0,UfeInputFrame.RANGED) if press else UfeInputFrame.make(),UfeInputFrame.make()])
		stamina_denials += denied(sim,"stamina")
		if p1.move_id=="pulse" and last_move!="pulse":
			shots += 1
			check(before>=int(p1.definition.moves.pulse.stamina_cost),"每次远程启动都真实付得起体力")
		last_move=p1.move_id
		if p2.state=="stun": stunned += 1
		if p2.state=="stun" and last_state!="stun":
			stun_entries += 1
			check(int(p2.stats.stun_immune)>0,"眩晕开始时免疫窗口已生效")
		last_state=p2.state
	check(stamina_denials>0,"持续连打后体力不足会被明确拒绝")
	check(shots>0 and shots<60,"连续远程次数受体力预算约束")
	check(stun_entries<=4 and stunned<400,"眩晕不会无限刷新")
	# 守方持续后防：每次格挡只付伤害四分之一，攻方先耗尽体力，守方不先破防。
	sim = UfeContentDatabase.match_for("ultraman","zetton")
	p1 = sim.fighters[0]
	p2 = sim.fighters[1]
	var p2_min := 1000
	var guard_breaks := 0
	var p2_last := p2.state
	var guard_denials := 0
	for tick in range(1800):
		var press := tick % 27 == 0
		sim.step([UfeInputFrame.make(0,0,UfeInputFrame.RANGED) if press else UfeInputFrame.make(),UfeInputFrame.make(1,0,0)])
		guard_denials += denied(sim,"stamina")
		p2_min = mini(p2_min,int(p2.stats.stamina))
		if p2.state=="guardbreak" and p2_last!="guardbreak": guard_breaks += 1
		p2_last=p2.state
	check(int(p2.stats.stamina)>0 and guard_breaks==0,"持续后防不会被单发远程先打破防")
	check(int(p1.stats.stamina)<int(p2.stats.stamina) and guard_denials>0,"守方在体力战中不先耗尽")
	print("shots=%d denials=%d stunned=%d entries=%d final_stamina=%d | guard: p1=%d p2_min=%d breaks=%d" % [shots,stamina_denials,stunned,stun_entries,int(p1.stats.stamina),int(p1.stats.stamina),p2_min,guard_breaks])
	print("STAMINA_ECONOMY "+("PASS" if failed.is_empty() else "FAIL: "+str(failed)))
	quit(0 if failed.is_empty() else 1)
