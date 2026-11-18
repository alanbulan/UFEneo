class_name UfeStateRules
extends RefCounted
## 战斗状态分组常量、谓词与舞台边界常量（单一事实来源）。

const STAGE_LEFT := 28
const STAGE_RIGHT := 1252
const TRANSFORM_GROUND_STATES := [
	"idle", "walk", "crouch", "crouch_start", "crouch_rise",
	"guard", "crouch_guard", "charge", "charge_start", "charge_stop",
	"turn", "crouch_turn",
]
const CROUCH_STATES := ["crouch", "crouch_start", "crouch_guard", "crouch_blockstun", "crouch_turn"]
const AIRBORNE_STATES := ["air", "takeoff", "air_attack", "launch", "bounce", "air_tech"]
const GUARD_STATES := ["guard", "crouch_guard", "blockstun", "crouch_blockstun"]
const GUARDABLE_STATES := [
	"idle", "walk", "crouch", "crouch_start", "crouch_rise",
	"guard", "crouch_guard", "blockstun", "crouch_blockstun",
	"turn", "crouch_turn", "land", "wake",
]


static func clamp_stage_x(x: int) -> int:
	return clampi(x, STAGE_LEFT, STAGE_RIGHT)


static func stage_pair_shift(first_x: int, second_x: int) -> int:
	var left := mini(first_x, second_x)
	var right := maxi(first_x, second_x)
	if left < STAGE_LEFT:
		return STAGE_LEFT - left
	if right > STAGE_RIGHT:
		return STAGE_RIGHT - right
	return 0


static func is_airborne_state(state: String) -> bool:
	return state in AIRBORNE_STATES


static func is_crouch_state(state: String) -> bool:
	return state in CROUCH_STATES


static func is_guard_state(state: String) -> bool:
	return state in GUARD_STATES


static func is_guardable_state(state: String) -> bool:
	return state in GUARDABLE_STATES
