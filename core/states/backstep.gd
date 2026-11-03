extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	f.x += int(f.motion.direction) * 5
	super.step(f, input, command)
