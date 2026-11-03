extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if input.held(UfeInputFrame.GUARD) and f.vy < 0 and f.state_tick > 8:
		f.enter("air_tech", 6)
