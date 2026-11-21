class_name UfeCommandResolver
extends RefCounted
## 只解析当前方向与独立动作键；不再识别旧搓招序列或把上方向当跳跃。
const INPUT_BUFFER_TICKS := 8
const RULE_REVISION := 6
const HELD_JUMP_STATES := ["idle","walk","guard","crouch","crouch_start","crouch_rise","crouch_guard","turn","crouch_turn","charge","charge_start","charge_stop"]
const BUTTON_BITS := [1,2,4,8,16,32,64,128,256,512,1024]
var previous: int = 0
var age: int = 0
var press_ticks: Dictionary = {}
var tap_direction: int = 0
var tap_tick: int = -100
var previous_x: int = 0

func resolve(frame: UfeInputFrame, facing: int, state: String, table: Array, available_energy: int = -1, allow_transform: bool = false, fallback_state: String = "") -> Dictionary:
	age += 1
	var pressed := frame.buttons & ~previous
	var direction := 5 + frame.x * facing + frame.y * 3
	for bit in BUTTON_BITS:
		if pressed & bit:
			press_ticks[str(bit)] = age
	var dash := false
	if frame.x != 0 and frame.x != previous_x:
		dash = tap_direction == frame.x and age - tap_tick <= 12
		tap_direction = frame.x
		tap_tick = age
	previous_x = frame.x
	previous = frame.buttons
	var best := _select(frame, state, table, pressed, direction, available_energy, allow_transform)
	# 当前状态专属派生优先；只在未识别时缓存地面指令，执行仍遵守原取消窗。
	if best.is_empty() and not fallback_state.is_empty():
		best = _select(frame, fallback_state, table, pressed, direction, available_energy, allow_transform)
	# 硬直结束后仍可响应持续按住的跳跃键；组合用上方向永远不产生跳跃意图。
	var held_ground_jump: bool = state in HELD_JUMP_STATES and frame.held(UfeInputFrame.JUMP)
	return {"move": str(best.get("move", "")), "pressed": pressed, "direction": direction,
		"dash": dash, "jump": held_ground_jump or (pressed & UfeInputFrame.JUMP) != 0}

func _select(frame: UfeInputFrame, state: String, table: Array, pressed: int, direction: int, available_energy: int, allow_transform: bool) -> Dictionary:
	var best: Dictionary = {}
	for entry in table:
		if entry.has("min_energy") and available_energy < int(entry.min_energy): continue
		if bool(entry.get("transform", false)) and not allow_transform: continue
		# 形态/必杀独立键优先，不让同按的远程方向技抢走指令。
		if bool(entry.get("direction_skill", false)) and (frame.buttons & (UfeInputFrame.TRANSFORM | UfeInputFrame.SPECIAL)) != 0: continue
		if not (state in entry.states or "*" in entry.states): continue
		if not entry.directions.any(func(d): return int(d) == direction or int(d) == 0): continue
		var mask := int(entry.buttons)
		if (pressed & mask) == 0 or not frame.held(mask): continue
		var simultaneous := true
		for bit in BUTTON_BITS:
			if mask & bit and age - int(press_ticks.get(str(bit), -100)) > 3: simultaneous = false
		if not simultaneous: continue
		if best.is_empty() or int(entry.priority) > int(best.priority): best = entry
	return best

func snapshot() -> Array:
	return [previous, age, press_ticks, tap_direction, tap_tick, previous_x]
