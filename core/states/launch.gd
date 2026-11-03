extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if input.held(UfeInputFrame.GUARD) and f.vy < 0 and f.state_tick > 12:
		f.combat.invulnerable = 12
		f.enter("air_tech", 12)
