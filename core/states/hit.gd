extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if f.state_tick>=int(f.motion.duration): f.enter("air" if f.height>0 else "crouch" if input.y<0 else "idle")
