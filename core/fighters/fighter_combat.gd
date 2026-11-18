class_name UfeFighterCombat
extends RefCounted
## 参战角色的强类型战斗交互与输入缓冲状态。

var buffer: String = ""
var buffer_ticks: int = 0
var buffer_next: String = ""
var buffer_next_ticks: int = 0
var connected: bool = false
var confirmed: bool = false
var blocked: bool = false
var combo: int = 0
var combo_ticks: int = 0
var bounced: bool = false
var invulnerable: int = 0
var thrower: int = -1
var throw_age: int = 0
var throw_damage_done: bool = false
var power: int = 1
var absorbed: int = 0
var stamina_delay: int = 0
var round_score: int = 0
var hit_groups: Dictionary = {}


func has_hit_groups() -> bool:
	return not hit_groups.is_empty()


func clear_hit_groups() -> void:
	hit_groups = {}


func has_hit_group(group: Variant) -> bool:
	return hit_groups.has(str(group))


func get_hit_group(group: Variant, default_value: Variant = "") -> Variant:
	return hit_groups.get(str(group), default_value)


func set_hit_group(group: Variant, value: Variant) -> void:
	hit_groups[str(group)] = value


func duplicate_state() -> UfeFighterCombat:
	var copy := UfeFighterCombat.new()
	copy.buffer = buffer
	copy.buffer_ticks = buffer_ticks
	copy.buffer_next = buffer_next
	copy.buffer_next_ticks = buffer_next_ticks
	copy.connected = connected
	copy.confirmed = confirmed
	copy.blocked = blocked
	copy.combo = combo
	copy.combo_ticks = combo_ticks
	copy.bounced = bounced
	copy.invulnerable = invulnerable
	copy.thrower = thrower
	copy.throw_age = throw_age
	copy.throw_damage_done = throw_damage_done
	copy.power = power
	copy.absorbed = absorbed
	copy.stamina_delay = stamina_delay
	copy.round_score = round_score
	copy.hit_groups = hit_groups.duplicate(true)
	return copy


static func from_dict(d: Dictionary) -> UfeFighterCombat:
	var result := UfeFighterCombat.new()
	result.buffer = str(d.get("buffer", ""))
	result.buffer_ticks = int(d.get("buffer_ticks", 0))
	result.buffer_next = str(d.get("buffer_next", ""))
	result.buffer_next_ticks = int(d.get("buffer_next_ticks", 0))
	result.connected = bool(d.get("connected", false))
	result.confirmed = bool(d.get("confirmed", false))
	result.blocked = bool(d.get("blocked", false))
	result.combo = int(d.get("combo", 0))
	result.combo_ticks = int(d.get("combo_ticks", 0))
	result.bounced = bool(d.get("bounced", false))
	result.invulnerable = int(d.get("invulnerable", 0))
	result.thrower = int(d.get("thrower", -1))
	result.throw_age = int(d.get("throw_age", 0))
	result.throw_damage_done = bool(d.get("throw_damage_done", false))
	result.power = int(d.get("power", 1))
	result.absorbed = int(d.get("absorbed", 0))
	result.stamina_delay = int(d.get("stamina_delay", 0))
	result.round_score = int(d.get("round_score", 0))
	var groups_raw: Variant = d.get("hit_groups", {})
	result.hit_groups = (groups_raw as Dictionary).duplicate(true) if groups_raw is Dictionary else {}
	return result


func to_dict() -> Dictionary:
	var result: Dictionary = {
		"buffer": buffer,
		"buffer_ticks": buffer_ticks,
		"buffer_next": buffer_next,
		"buffer_next_ticks": buffer_next_ticks,
		"connected": connected,
		"confirmed": confirmed,
		"blocked": blocked,
		"combo": combo,
		"combo_ticks": combo_ticks,
		"bounced": bounced,
		"invulnerable": invulnerable,
		"thrower": thrower,
		"throw_age": throw_age,
		"throw_damage_done": throw_damage_done,
		"power": power,
		"absorbed": absorbed,
		"stamina_delay": stamina_delay,
		"round_score": round_score,
	}
	if not hit_groups.is_empty():
		result["hit_groups"] = hit_groups.duplicate(true)
	return result
