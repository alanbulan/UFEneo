extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, _command: Dictionary) -> void:
	if not input.held(UfeInputFrame.CHARGE): f.enter("charge_stop",9)
	elif f.state_tick>=9: f.enter("charge")
