extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, _command: Dictionary) -> void:
	if f.state_tick>=int(f.motion.duration): f.enter("crouch" if input.y<0 else "crouch_rise",6)
