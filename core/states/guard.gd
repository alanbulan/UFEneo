extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if command.jump: locomotion(f,input,command)
	elif input.y<0: f.enter("crouch_guard")
	elif not input.held(UfeInputFrame.GUARD) and input.x*f.facing>=0: locomotion(f,input,command)
