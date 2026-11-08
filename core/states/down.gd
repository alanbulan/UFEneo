extends UfeState
func step(f: UfeFighter, _input: UfeInputFrame, _command: Dictionary) -> void:
	if f.state_tick >= int(f.motion.duration): f.enter("wake", 20)
