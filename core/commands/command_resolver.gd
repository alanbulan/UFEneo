class_name UfeCommandResolver
extends RefCounted
const Motion = preload("res://third_party/shoto/motion_parser.gd")
const INPUT_BUFFER_TICKS := 10
const RULE_REVISION := 3
const HELD_JUMP_STATES := ["idle","walk","guard","crouch","crouch_start","crouch_rise","crouch_guard","turn","crouch_turn","charge","charge_start","charge_stop"]
const BUTTON_BITS := [1,2,4,8,16,32,64,128,256,512,1024,2048]
var previous: int = 0
var age: int = 0
var history: Array = []
var press_ticks: Dictionary = {}
var tap_direction: int = 0
var tap_tick: int = -100
var previous_x: int = 0

func resolve(frame: UfeInputFrame, facing: int, state: String, table: Array, available_energy: int = -1, allow_quick_transform: bool = false, fallback_state: String = "") -> Dictionary:
	age += 1
	var pressed := frame.buttons & ~previous
	var direction := Motion.to_numpad(frame.x * facing, frame.y)
	for bit in BUTTON_BITS:
		if pressed & bit:
			press_ticks[str(bit)] = age
	history.push_front(direction)
	if history.size() > 36:
		history.pop_back()
	var dash := false
	if frame.x != 0 and frame.x != previous_x:
		dash = tap_direction == frame.x and age - tap_tick <= 12
		tap_direction = frame.x
		tap_tick = age
	previous_x = frame.x
	previous = frame.buttons
	var best := _select(frame, state, table, pressed, direction, available_energy, allow_quick_transform)
	# 当前状态专属派生优先；只在未识别时缓存地面指令，执行仍遵守原取消窗。
	if best.is_empty() and not fallback_state.is_empty():
		best = _select(frame, fallback_state, table, pressed, direction, available_energy, allow_quick_transform)
	# 上方向/跳跃键在合法地面状态保持时继续请求，防止在较长防御硬直中
	# 首次7tick跳缓存先耗尽，真正可行动后却永远不跳。技能确实选中时仍消费上跳。
	var held_ground_jump: bool=state in HELD_JUMP_STATES and (frame.y>0 or frame.held(UfeInputFrame.JUMP))
	var result := {"move": str(best.get("move", "")), "pressed": pressed, "direction": direction,
		"dash": dash, "jump": held_ground_jump or (frame.y > 0 and (history.size() < 2 or int(history[1]) < 7)) or (pressed & UfeInputFrame.JUMP) != 0}
	if bool(best.get("consume_jump", false)) and direction >= 7:
		result.jump = false
		result.consume_jump = true
	return result

func _select(frame: UfeInputFrame, state: String, table: Array, pressed: int, direction: int, available_energy: int, allow_quick_transform: bool) -> Dictionary:
	var best: Dictionary = {}
	for entry in table:
		if entry.has("min_energy") and available_energy < int(entry.min_energy): continue
		if bool(entry.get("quick_transform",false)) and not allow_quick_transform: continue
		# 独立形态键没有条件时不误放技能；原P和正常上跳保持。
		if bool(entry.get("quick_skill",false)) and (frame.held(UfeInputFrame.TRANSFORM) or frame.held(UfeInputFrame.SPECIAL) or frame.held(UfeInputFrame.LIGHT | UfeInputFrame.HEAVY)): continue
		if not (state in entry.states or "*" in entry.states): continue
		if not entry.directions.any(func(d): return int(d) == direction or int(d) == 0): continue
		var mask := int(entry.buttons)
		if (pressed & mask) == 0 or not frame.held(mask): continue
		var simultaneous := true
		for bit in BUTTON_BITS:
			if bit == UfeInputFrame.SKILL and bool(entry.get("quick_transform",false)): continue
			if mask & bit and age - int(press_ticks.get(str(bit), -100)) > 3: simultaneous = false
		if not simultaneous or not Motion.matches(history, entry.motion, 5): continue
		if best.is_empty() or int(entry.priority) > int(best.priority): best = entry
	return best

func snapshot() -> Array:
	return [previous, age, history, press_ticks, tap_direction, tap_tick, previous_x]
