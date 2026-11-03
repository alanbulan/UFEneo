extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if f.state_tick>=int(f.motion.duration):
		f.enter("guard" if input.held(UfeInputFrame.GUARD) or input.x*f.facing<0 else "idle")
