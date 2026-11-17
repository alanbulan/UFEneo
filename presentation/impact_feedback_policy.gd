class_name UfeImpactFeedbackPolicy
extends RefCounted
## 普通拳脚默认火花只按矩阵输入档分级；只读事件，不改伤害或命中停顿。
## 档位与 core/combat/feel_rules.gd 一致：light3、扫腿是「中」档，不是轻档。
const LIGHT := ["light1", "light2", "crouch_light", "crouch_light2", "vertical_light", "diagonal_light", "chase_light1", "chase_light2", "dash_light", "dodge_counter", "wake_low"]
const MEDIUM := ["light3", "sweep"]
const HEAVY := ["heavy", "launcher", "spin_heavy", "crouch_chain_sweep", "vertical_heavy", "diagonal_heavy", "dive", "chase_end", "dash_heavy", "back_counter", "wake_mid", "guard_counter", "bounce_follow_sweep"]
const CRUSH := ["crush", "tackle", "slide", "air_crush", "bounce_follow_crush"]

## 档名共用；共享名册没有中档图，中档按重档火花播放。
const SHARED := {"light": "impact_feedback_light", "medium": "impact_feedback_heavy", "heavy": "impact_feedback_heavy", "crush": "impact_feedback_crush"}

## 返回本招属于哪个普通拳脚档；专属火花、飞行道具、防御一律返回空串。
static func tier(event: Dictionary, fallback: String) -> String:
	if str(event.get("kind", "")) != "hit" or bool(event.get("projectile", false)):
		return ""
	if fallback not in ["impact_light", "impact_heavy"]:
		return ""
	var move := str(event.get("move", ""))
	if move in LIGHT: return "light"
	if move in MEDIUM: return "medium"
	if move in HEAVY: return "heavy"
	if move in CRUSH: return "crush"
	return ""

static func impact_id(event: Dictionary, fallback: String) -> String:
	var row := tier(event, fallback)
	return str(SHARED.get(row, fallback)) if not row.is_empty() else fallback
