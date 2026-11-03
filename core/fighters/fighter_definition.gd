class_name UfeFighterDefinition
extends Resource
@export var id: String = ""
@export var display_name: String = ""
@export var max_health: int = 1000
@export var walk_speed: int = 2
@export var jump_speed: int = 16
@export var body_radius: int = 18
var moves: Dictionary = {}
var command_table: Array = []
var state_frames: Dictionary = {}

func simulation_data() -> Array:
	return [id, max_health, walk_speed, jump_speed, body_radius, command_table, moves, state_frames]
