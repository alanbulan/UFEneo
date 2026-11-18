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
