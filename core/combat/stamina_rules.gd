class_name UfeStaminaRules
extends RefCounted
## 体力是短时攻防韧性；不足时不禁止攻击或能量技。
const MAXIMUM := 1000
const RECOVERY_DELAY := 18
const MOVE_REGEN := 12
const REST_REGEN := 10
const CHARGE_REGEN := 3
const DODGE_COST := 120
const TIRED_DODGE_INVULNERABLE := 4
const GUARD_BREAK_RECOVERY := 350
const RULE_REVISION := 2

static func simulation_data() -> Array:
	return [MAXIMUM,RECOVERY_DELAY,MOVE_REGEN,REST_REGEN,CHARGE_REGEN,DODGE_COST,TIRED_DODGE_INVULNERABLE,GUARD_BREAK_RECOVERY,RULE_REVISION]

static func finish_guard_break(f: UfeFighter) -> void:
	f.stats.stamina = maxi(GUARD_BREAK_RECOVERY, int(f.stats.stamina))
	f.combat.stamina_delay = RECOVERY_DELAY

static func spend(f: UfeFighter, amount: int) -> int:
	var paid := mini(int(f.stats.stamina), maxi(0, amount))
	f.stats.stamina = maxi(0, int(f.stats.stamina) - maxi(0, amount))
	if amount > 0: f.combat.stamina_delay = RECOVERY_DELAY
	return paid

static func rate(f: UfeFighter) -> int:
	if not f.move_id.is_empty(): return 0
	if f.state == "walk": return MOVE_REGEN
	if f.state in ["idle","crouch","crouch_start","crouch_rise","turn","crouch_turn"]: return REST_REGEN
	if f.state == "charge": return CHARGE_REGEN
	return 0

static func advance(f: UfeFighter, previous_state: String, explicit_regen: int = -1) -> void:
	if previous_state == "guardbreak" and f.state != "guardbreak":
		finish_guard_break(f)
	var recovery := rate(f)
	if recovery == 0 or previous_state in ["attack","air_attack","guard","crouch_guard","blockstun","crouch_blockstun","hit","launch","bounce","down","guardbreak","dodge","dash","backstep","stun"]:
		f.combat.stamina_delay = RECOVERY_DELAY
		return
	if int(f.combat.get("stamina_delay",0)) > 0:
		f.combat.stamina_delay = int(f.combat.stamina_delay) - 1
		return
	# 旧显式抑制只能进一步限制恢复，不能绕过状态和等待时间。
	if explicit_regen >= 0: recovery = mini(recovery, explicit_regen)
	f.stats.stamina = mini(MAXIMUM, int(f.stats.stamina) + recovery)
