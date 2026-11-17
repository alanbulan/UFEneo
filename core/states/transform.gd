extends UfeState
func step(f: UfeFighter, _input: UfeInputFrame, _command: Dictionary) -> void:
	UfeBattleTransform.advance(f)
