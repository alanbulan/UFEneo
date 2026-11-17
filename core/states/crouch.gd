extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	var defending: bool=input.y<0 and (input.held(UfeInputFrame.GUARD) or input.x*f.facing<0)
	# 松防仍下不会enter新状态，也必须解除本次恢复姿态。
	if not defending:f.motion.erase("hit_crouch_guard_resume")
	if defending: f.enter("crouch_guard")
	elif input.y >= 0: f.enter("crouch_rise",6)
	elif command.jump: locomotion(f, input, command)
