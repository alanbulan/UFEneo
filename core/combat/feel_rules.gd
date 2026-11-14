class_name UfeFeelRules
extends RefCounted
## 全角色共用的手感分档。招式 JSON 仍是逐帧真源；这里只改模板复制出来的
## 硬直/推退/停顿，并给出普通技接必杀的取消路线。不按角色名分支。
const REVISION := 2
## 蓄力超重击：按住计时，松开按档出手。满 40 tick 自动出手。
## 满档击倒，不破防。O 键已是即时重压，再做成破防会和它重叠。
const POWER_HOLD_TIER2 := 20
const POWER_HOLD_AUTO := 40
const SCALE_START := 3
const SCALE_NUMERATOR := 90
const SCALE_FLOOR := 30

# 初速按本游戏尺度取：走路 2px/tick、轻击打距约 70px。
# 报告里的 6/10 滑完是 21/55px，会把轻击连段和防反带出判定，所以改成 4/5/6。
const _LIGHT := {
	"hitstop": 7, "block_adv": 1, "hit_adv": 5, "push": 4,
	"shake": 2, "shake_ticks": 6, "flash": 2, "weight": "light",
}
const _MEDIUM := {
	"hitstop": 9, "block_adv": 0, "hit_adv": 6, "push": 5,
	"shake": 4, "shake_ticks": 8, "flash": 2, "weight": "heavy",
}
const _HEAVY := {
	"hitstop": 12, "block_adv": -3, "hit_adv": 4, "push": 6,
	"shake": 6, "shake_ticks": 12, "flash": 3, "weight": "heavy",
}
const _SPECIAL := {
	"hitstop": 14, "block_adv": -4, "hit_adv": 2, "push": 6,
	"shake": 6, "shake_ticks": 12, "flash": 3, "weight": "heavy",
}
const _SUPER := {
	"hitstop": 16, "block_adv": -6, "hit_adv": 4, "push": 8,
	"shake": 6, "shake_ticks": 14, "flash": 3, "weight": "heavy",
}

const NORMAL_ROUTES := ["motion_236", "motion_623", "motion_214", "motion_22", "motion_41236", "special", "special2", "special3"]
const SPECIAL_ROUTES := ["special", "special2", "special3"]

static var _tiers: Dictionary = {}
static var _normals: Dictionary = {}

static func _ensure() -> void:
	if not _tiers.is_empty():
		return
	var groups := {
		"light1": _LIGHT, "light2": _LIGHT, "crouch_light": _LIGHT, "crouch_light2": _LIGHT,
		"dash_light": _LIGHT, "diagonal_light": _LIGHT, "vertical_light": _LIGHT, "chase_light1": _LIGHT,
		"light3": _MEDIUM, "sweep": _MEDIUM,
		"heavy": _HEAVY, "spin_heavy": _HEAVY, "launcher": _HEAVY, "dash_heavy": _HEAVY,
		"crush": _HEAVY, "slide": _HEAVY, "tackle": _HEAVY, "diagonal_heavy": _HEAVY,
		"vertical_heavy": _HEAVY, "dive": _HEAVY, "wake_mid": _HEAVY, "wake_low": _HEAVY,
		"back_counter": _HEAVY, "guard_counter": _HEAVY, "dodge_counter": _HEAVY,
		"air_crush": _HEAVY, "chase_end": _HEAVY, "chase_light2": _HEAVY,
		"motion_236": _SPECIAL, "motion_623": _SPECIAL, "motion_214": _SPECIAL,
		"motion_22": _SPECIAL, "motion_41236": _SPECIAL, "pulse": _SPECIAL, "low_pulse": _SPECIAL,
		"air_pulse": _SPECIAL, "ranged_forward": _SPECIAL, "special": _SPECIAL,
		"special2": _SPECIAL, "air_special": _SPECIAL,
		"special3": _SUPER,
	}
	_tiers = groups
	for id in ["light1", "light2", "light3", "heavy", "crouch_light", "crouch_light2", "sweep", "spin_heavy", "launcher", "dash_light", "dash_heavy", "crush", "slide", "tackle", "wake_low", "wake_mid", "diagonal_light", "vertical_light", "diagonal_heavy", "vertical_heavy"]:
		_normals[id] = true

static func tier(move_id: String) -> Dictionary:
	_ensure()
	return _tiers.get(move_id, {})

static func allows_route(move_id: String, target: String) -> bool:
	_ensure()
	if move_id.is_empty() or target.is_empty() or move_id == target:
		return false
	if _normals.has(move_id):
		return target in NORMAL_ROUTES
	if move_id.begins_with("motion_"):
		return target in SPECIAL_ROUTES
	return false

## 第 3 下起每下 ×0.9，整数百分比，下限 30。
static func scale_percent(hit_index: int) -> int:
	if hit_index < SCALE_START:
		return 100
	var percent := 100
	for _i in range(hit_index - (SCALE_START - 1)):
		percent = maxi(SCALE_FLOOR, percent * SCALE_NUMERATOR / 100)
	return percent

static func default_body_radius(template: String, target_height: int) -> int:
	if template == "biped_tail":
		var height := target_height if target_height > 0 else 190
		return clampi(int(round(float(height) * 0.26)), 46, 56)
	var height := target_height if target_height > 0 else 170
	return clampi(int(round(float(height) * 0.17)), 28, 40)

## 只改内存中的招式副本。模板值（受击 20 / 防御 12 / 推退 8）换成档位；
## 已经写过的推退距离换成初速，使滑动距离仍接近原作者写的像素。
static func apply_move(move: Dictionary) -> void:
	if bool(move.get("_feel_applied", false)):
		return
	move["_feel_applied"] = true
	var id := str(move.get("id", ""))
	var row := tier(id)
	if not row.is_empty():
		var feedback: Dictionary = move.get("feedback", {}).duplicate(true)
		feedback["hitstop"] = int(row.hitstop)
		feedback["blockstop"] = maxi(3, int(row.hitstop) - 2)
		feedback["shake"] = int(row.shake)
		feedback["shake_ticks"] = int(row.shake_ticks)
		feedback["flash"] = int(row.flash)
		feedback["impact_weight"] = str(row.weight)
		move["feedback"] = feedback
		var recovery := _recovery_after_first_hit(move)
		if recovery >= 0 and int(move.get("hitstun", -1)) == 20 and int(move.get("blockstun", -1)) == 12:
			move["blockstun"] = maxi(4, recovery + int(row.block_adv))
			move["hitstun"] = maxi(int(move.blockstun) + 2, recovery + int(row.hit_adv))
	if str(move.get("kind", "")) == "throw":
		return
	var push := int(move.get("pushback", 0))
	if push <= 0:
		return
	if not row.is_empty() and (push == 8 or push == int(row.push)):
		move["pushback"] = int(row.push)
	else:
		move["pushback"] = _speed_for_distance(push)

static func power_crush_tier(hold: int) -> int:
	if hold >= POWER_HOLD_AUTO:
		return 3
	if hold >= POWER_HOLD_TIER2:
		return 2
	return 1

static func power_crush_spec(tier: int) -> Dictionary:
	if tier >= 3:
		return {"damage_num": 18, "damage_den": 10, "hitstop": 16, "block_adv": -8, "hit_adv": 10, "push": 10, "knockdown": true, "shake": 8, "shake_ticks": 16, "flash": 4}
	if tier == 2:
		return {"damage_num": 14, "damage_den": 10, "hitstop": 14, "block_adv": -5, "hit_adv": 6, "push": 8, "knockdown": false, "shake": 6, "shake_ticks": 14, "flash": 3}
	return {"damage_num": 10, "damage_den": 10, "hitstop": 12, "block_adv": -3, "hit_adv": 4, "push": 6, "knockdown": false, "shake": 6, "shake_ticks": 12, "flash": 3}

## 没有专属剪辑的角色复用重击帧。数值按上面的档，不走模板 20/12 覆盖。
static func ensure_power_crush(moves: Dictionary) -> void:
	if moves.has("power_crush_1") or not moves.has("heavy"):
		return
	var heavy: Dictionary = moves["heavy"]
	for tier in [1, 2, 3]:
		var spec := power_crush_spec(tier)
		var move: Dictionary = heavy.duplicate(true)
		var id := "power_crush_%d" % tier
		move["id"] = id
		move["display_name"] = "蓄力超重击%d档" % tier
		move["kind"] = "strike"
		move["level"] = "mid"
		move["unblockable"] = false
		move["launch"] = false
		move["bounce"] = false
		move["knockdown"] = bool(spec.knockdown)
		move["energy_cost"] = 0
		move["stamina_cost"] = 0
		@warning_ignore("integer_division")
		move["damage"] = maxi(1, int(heavy.get("damage", 100)) * int(spec.damage_num) / int(spec.damage_den))
		move["pushback"] = int(spec.push)
		var recovery := _recovery_after_first_hit(move)
		if recovery >= 0:
			var blockstun := maxi(4, recovery + int(spec.block_adv))
			move["blockstun"] = blockstun
			move["hitstun"] = maxi(blockstun + 2, recovery + int(spec.hit_adv))
		var feedback: Dictionary = move.get("feedback", {}).duplicate(true)
		feedback["hitstop"] = int(spec.hitstop)
		feedback["blockstop"] = maxi(3, int(spec.hitstop) - 2)
		feedback["shake"] = int(spec.shake)
		feedback["shake_ticks"] = int(spec.shake_ticks)
		feedback["flash"] = int(spec.flash)
		feedback["impact_weight"] = "heavy"
		feedback["spark"] = "impact_heavy"
		move["feedback"] = feedback
		move["_feel_applied"] = true
		moves[id] = move

static func block_push(hit_push: int) -> int:
	if hit_push <= 0:
		return 0
	return maxi(hit_push, hit_push * 13 / 10)

static func _recovery_after_first_hit(move: Dictionary) -> int:
	var frames: Array = move.get("frames", [])
	for index in range(frames.size()):
		var boxes: Array = frames[index].get("hitboxes", [])
		if not boxes.is_empty():
			return frames.size() - index - 1
	return -1

## 最小初速，使 1+2+…+k 不小于原来的一次性推退距离。
static func _speed_for_distance(distance: int) -> int:
	var speed := 1
	while speed < 18 and speed * (speed + 1) / 2 < distance:
		speed += 1
	return speed
