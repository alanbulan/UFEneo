extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	var tech_dir := f.motion.tech_direction if f.motion.tech_direction != 0 else -f.facing
	if f.state_tick <= 6: f.x += tech_dir * 3
	super.step(f, input, command)
