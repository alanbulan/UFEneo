extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if input.y<0 and (input.held(UfeInputFrame.GUARD) or input.x*f.facing<0): f.enter("crouch_guard")
	elif input.y >= 0: f.enter("crouch_rise",6)
	elif command.jump: locomotion(f, input, command)
