extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if command.jump: locomotion(f,input,command)
	elif input.y<0: f.enter("crouch_start",6)
	elif f.state_tick>=6: f.enter("idle")
