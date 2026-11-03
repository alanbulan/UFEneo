extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, _command: Dictionary) -> void:
	if f.state_tick>=int(f.motion.duration):
		f.enter("crouch_guard" if input.y<0 and (input.held(UfeInputFrame.GUARD) or input.x*f.facing<0) else "crouch" if input.y<0 else "idle")
