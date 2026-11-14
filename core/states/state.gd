class_name UfeState
extends RefCounted
func step(f: UfeFighter, _input: UfeInputFrame, _command: Dictionary) -> void:
	if int(f.motion.duration) > 0 and f.state_tick >= int(f.motion.duration):
		f.enter("air" if f.height > 0 else "idle")

## 受方减速（chill）只作用于移动位移，不改变出招、受击与硬直时序。
@warning_ignore("integer_division") # 整数取整，结果为整数像素。
static func move_speed(f: UfeFighter, base: int) -> int:
	if int(f.stats.get("chill_ticks", 0)) <= 0:return base
	var percent := clampi(int(f.stats.get("chill_percent", 100)), 1, 100)
	return maxi(1, (base * percent + 50) / 100)

func locomotion(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if command.jump:
		f.vy = f.definition.jump_speed
		f.vx = input.x * 4
		f.motion.jump_kind = "vertical" if input.x == 0 else "backward" if input.x*f.facing<0 else "diagonal"
		f.enter("takeoff", 2)
	elif int(command.pressed) & UfeInputFrame.DODGE:
		var paid := UfeStaminaRules.spend(f, UfeStaminaRules.DODGE_COST)
		f.motion.dodge_tired = paid < UfeStaminaRules.DODGE_COST
		f.enter("dodge", 18)
		f.combat.invulnerable = UfeStaminaRules.TIRED_DODGE_INVULNERABLE if bool(f.motion.dodge_tired) else 12
	elif input.y < 0:
		f.enter("crouch_guard" if input.held(UfeInputFrame.GUARD) or input.x*f.facing<0 else "crouch_start",6)
	elif input.held(UfeInputFrame.GUARD):
		f.enter("guard")
	elif input.held(UfeInputFrame.CHARGE):
		f.enter("charge_start",9)
	elif input.held(UfeInputFrame.POWER_CRUSH) and f.definition.moves.has("power_crush_1"):
		f.motion.power_crush_hold = 0
		f.motion.power_crush_tier = 1
		f.enter("power_charge")
	elif command.dash:
		f.motion.direction = input.x
		f.enter("dash" if input.x * f.facing > 0 else "backstep", 22 if input.x * f.facing > 0 else 16)
	elif input.x != 0:
		f.x += input.x * move_speed(f, f.definition.walk_speed)
		if f.state != "walk": f.enter("walk")
	else:
		if f.state != "idle": f.enter("idle")
