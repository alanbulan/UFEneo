extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, _command: Dictionary) -> void:
	if not input.held(UfeInputFrame.CHARGE): f.enter("charge_stop",9)
