class_name UfeFighterStats
extends RefCounted
## 参战角色的强类型数值状态（生命、能量、体力、眩晕与减速）。

var hp: int = 1000
var energy: int = 0
var stamina: int = 1000
var stun: int = 0
var stun_immune: int = 0
var chill_ticks: int = 0
var chill_percent: int = 100


func duplicate_state() -> UfeFighterStats:
	var copy := UfeFighterStats.new()
	copy.hp = hp
	copy.energy = energy
	copy.stamina = stamina
	copy.stun = stun
	copy.stun_immune = stun_immune
	copy.chill_ticks = chill_ticks
	copy.chill_percent = chill_percent
	return copy


static func from_dict(d: Dictionary) -> UfeFighterStats:
	var result := UfeFighterStats.new()
	result.hp = int(d.get("hp", 1000))
	result.energy = int(d.get("energy", 0))
	result.stamina = int(d.get("stamina", 1000))
	result.stun = int(d.get("stun", 0))
	result.stun_immune = int(d.get("stun_immune", 0))
	result.chill_ticks = int(d.get("chill_ticks", 0))
	result.chill_percent = int(d.get("chill_percent", 100))
	return result


func to_dict() -> Dictionary:
	return {
		"hp": hp,
		"energy": energy,
		"stamina": stamina,
		"stun": stun,
		"stun_immune": stun_immune,
		"chill_ticks": chill_ticks,
		"chill_percent": chill_percent,
	}
