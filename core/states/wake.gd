extends UfeState
func step(f: UfeFighter, input: UfeInputFrame, command: Dictionary) -> void:
	# 起身按后或防御键就是防御。翻滚要按闪避键加方向；闪避优先于“按后即防”。
	if input.held(UfeInputFrame.DODGE) and input.x != 0:
		f.motion.direction = input.x
		f.combat.invulnerable = 20
		f.enter("roll_forward" if input.x * f.facing > 0 else "roll_back", 20)
		return
	if input.held(UfeInputFrame.GUARD) or input.x * f.facing < 0:
		f.enter("guard")
		return
	super.step(f, input, command)
