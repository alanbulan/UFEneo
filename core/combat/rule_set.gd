class_name UfeRuleSet
extends Resource
@export var id: String = "neo"
@export var display_name: String = "新纪元格斗"
@export var stun_threshold: int = 300
## 眩晕结束后的免疫窗口，防止同一套连续命中无限刷新眩晕。
@export var stun_immunity: int = 90
@export var round_ticks: int = 5400
@export var description: String = ""

func simulation_data() -> Array:
	return [id, stun_threshold, stun_immunity, round_ticks, UfeStaminaRules.simulation_data(), UfeCommandResolver.INPUT_BUFFER_TICKS, UfeCommandResolver.RULE_REVISION, UfeMeleeHitGroups.RULE_REVISION]
