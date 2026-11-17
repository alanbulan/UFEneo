extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if command.jump: locomotion(f,input,command)
	elif input.y>=0: f.enter("guard" if input.held(UfeInputFrame.GUARD) else "crouch_rise",6)
	elif not input.held(UfeInputFrame.GUARD) and input.x*f.facing>=0: f.enter("crouch")
