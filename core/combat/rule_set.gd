class_name UfeRuleSet
extends Resource
@export var id: String = "neo"
@export var display_name: String = "新纪元格斗"
@export var stun_threshold: int = 300
@export var round_ticks: int = 5400
@export var description: String = ""

func simulation_data() -> Array:
	return [id, stun_threshold, round_ticks, UfeStaminaRules.simulation_data(), UfeCommandResolver.INPUT_BUFFER_TICKS, UfeCommandResolver.RULE_REVISION, UfeMeleeHitGroups.RULE_REVISION]
