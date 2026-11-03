extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	f.x += int(f.motion.direction) * 6
	super.step(f, input, command)
