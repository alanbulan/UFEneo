class_name UfeImpactFeedbackPolicy
extends RefCounted
## 普通拳脚默认火花只按矩阵输入档分级；只读事件，不改伤害或命中停顿。
const LIGHT := ["light1", "light2", "light3", "crouch_light", "crouch_light2", "vertical_light", "diagonal_light", "chase_light1", "chase_light2", "dash_light", "dodge_counter", "wake_low"]
const HEAVY := ["heavy", "launcher", "spin_heavy", "sweep", "crouch_chain_sweep", "vertical_heavy", "diagonal_heavy", "dive", "chase_end", "dash_heavy", "back_counter", "wake_mid", "guard_counter", "bounce_follow_sweep"]
const CRUSH := ["crush", "tackle", "slide", "air_crush", "bounce_follow_crush"]

static func impact_id(event: Dictionary, fallback: String) -> String:
	if str(event.get("kind", "")) != "hit" or bool(event.get("projectile", false)):
		return fallback
	if fallback not in ["impact_light", "impact_heavy"]:
		return fallback
	var move := str(event.get("move", ""))
	if move in LIGHT: return "impact_feedback_light"
	if move in HEAVY: return "impact_feedback_heavy"
	if move in CRUSH: return "impact_feedback_crush"
	return fallback
