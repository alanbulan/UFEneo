extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, _command: Dictionary) -> void:
	if f.state_tick>=int(f.motion.duration):
		if input.y<0 and (input.held(UfeInputFrame.GUARD) or input.x*f.facing<0):
			f.enter("crouch_guard")
			# 已低蹲受挡只恢复本人保持，不重播站入蹲的入架；模拟框与显示共用此帧。
			var poses: Array=f.definition.state_frames.get("crouch_guard",[])
			if not poses.is_empty():f.state_tick=poses.size()-1
		else:
			f.enter("crouch" if input.y<0 else "idle")
