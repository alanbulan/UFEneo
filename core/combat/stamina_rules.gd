class_name UfeStaminaRules
extends RefCounted
## 体力是发力与防守的预算：普通拳脚、投技和受身不收费，远程、必杀、
## 闪避和格挡收费；体力不足时这些招式不启动，但角色不会失去基本行动。
const MAXIMUM := 1000
const RECOVERY_DELAY := 30
const WALK_REGEN := 8
const REST_REGEN := 8
const CHARGE_REGEN := 4
const DODGE_COST := 120
const TIRED_DODGE_INVULNERABLE := 4
const GUARD_BREAK_RECOVERY := 350
const RULE_REVISION := 3

static func simulation_data() -> Array:
	return [MAXIMUM,RECOVERY_DELAY,WALK_REGEN,REST_REGEN,CHARGE_REGEN,DODGE_COST,TIRED_DODGE_INVULNERABLE,GUARD_BREAK_RECOVERY,RULE_REVISION]

static func block_cost(damage: int) -> int:
	@warning_ignore("integer_division") # 体力按伤害的四分之一整数扣除。
	return maxi(10, damage / 4)

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
	if f.state == "walk": return WALK_REGEN
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
