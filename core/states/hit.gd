extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, _command: Dictionary) -> void:
	if f.state_tick>=int(f.motion.duration):
		var resume: bool=f.height==0 and str(f.motion.get("hit_pose",""))=="hit_crouch" and input.y<0 and (input.held(UfeInputFrame.GUARD) or input.x*f.facing<0)
		f.enter("air" if f.height>0 else "crouch" if input.y<0 else "idle")
		# 保留原crouch中间tick与下tick命令上下文；不是提前进入防御状态。
		if resume and not f.definition.state_frames.get("crouch_guard",[]).is_empty():f.motion.hit_crouch_guard_resume=true
