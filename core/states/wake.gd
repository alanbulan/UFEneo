extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if input.x != 0:
		f.motion.direction = input.x
		f.combat.invulnerable = 20
		f.enter("roll_forward" if input.x*f.facing > 0 else "roll_back", 20)
	else: super.step(f, input, command)
