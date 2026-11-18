class_name UfeAppHarness
extends RefCounted
## 主场景运行期挂载基类；app 层只依赖该抽象接口，不引用 tests/。


func parse_args(_app: Control, _args: PackedStringArray) -> void:
	pass


func override_matchup(_app: Control) -> Array:
	return []


func wants_intro(_app: Control) -> bool:
	return false


func after_start_match(_app: Control) -> void:
	pass


func after_ready(_app: Control) -> void:
	pass


func on_begin_match_from_front(_app: Control) -> void:
	pass


func before_physics(_app: Control, _tick: int) -> void:
	pass


func on_front_visible(_app: Control, _tick: int) -> void:
	pass


func before_simulation_step(_app: Control, _tick: int) -> void:
	pass


func should_restart_match_on_section(_app: Control) -> bool:
	return false


func override_inputs(_app: Control, _tick: int, first: UfeInputFrame, second: UfeInputFrame) -> Array:
	return [first, second]


func after_step(_app: Control, _tick: int) -> void:
	pass
