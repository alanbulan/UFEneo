extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	locomotion(f, input, command)
