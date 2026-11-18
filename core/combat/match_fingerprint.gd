class_name UfeMatchFingerprint
extends RefCounted
## 对局内容指纹构造与确定性状态散列序列化。

const MOVE_START_RULE_REVISION := 2
const CHASE_INTERRUPT_RULE_REVISION := 1
const CROUCH_GUARD_RESUME_RULE_REVISION := 1
const HIT_CROUCH_GUARD_RESUME_RULE_REVISION := 1


static func compute(first: UfeFighterDefinition, second: UfeFighterDefinition, rule: UfeRuleSet, form_rules: Array, start_data: Array) -> String:
	var fingerprint_data: Array = [
		6, 60, rule.simulation_data(), first.simulation_data(), second.simulation_data(), form_rules,
		["round_end_identity", 1],
		["move_start_conditions", MOVE_START_RULE_REVISION],
		["hit_pushback_bounds", UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],
		["throw_target_air", UfeHitResolver.THROW_TARGET_RULE_REVISION],
		["chase_interrupt", CHASE_INTERRUPT_RULE_REVISION],
		["projectile_contact_direction", UfeHitResolver.PROJECTILE_DIRECTION_RULE_REVISION],
		["projectile_move_isolation", UfeHitResolver.PROJECTILE_MOVE_ISOLATION_RULE_REVISION],
		["projectile_beam_reflection", UfeProjectileResolver.BEAM_REFLECTION_RULE_REVISION],
	]
	if start_data.any(func(row: Array): return not str(row[0]).is_empty()):
		fingerprint_data.append(["start_forms", start_data])
	# 恢复姿态影响state_tick和实际受击框；旧格式6仍可解析，但旧内容指纹不可重放。
	fingerprint_data.append(["crouch_guard_resume_hold", CROUCH_GUARD_RESUME_RULE_REVISION])
	fingerprint_data.append(["hit_crouch_guard_resume_pose", HIT_CROUCH_GUARD_RESUME_RULE_REVISION])
	fingerprint_data.append(["feel_rules", UfeFeelRules.REVISION])
	if UfeThrowResolver.RootOffsets.used_in(fingerprint_data):
		fingerprint_data.append(["throw_root_overrides", UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION])
	if UfeThrowResolver.CurrentCapture.used_in(fingerprint_data):
		fingerprint_data.append(["throw_current_capture", UfeThrowResolver.CurrentCapture.REVISION])
	return JSON.stringify(fingerprint_data, "", true).sha256_text()


static func state_hash(tick: int, remaining: int, hitstop: int, finished: bool, winner: int, projectiles: Array, fighters: Array[UfeFighter]) -> String:
	return JSON.stringify(
		[tick, remaining, hitstop, finished, winner, projectiles, fighters[0].snapshot(), fighters[1].snapshot()],
		"",
		true
	).sha256_text()
