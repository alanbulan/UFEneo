extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	if f.state_tick<=6:f.x+=int(f.motion.get("tech_direction",-f.facing))*3
	super.step(f, input, command)
