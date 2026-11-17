extends RefCounted
## 训练输入适配，不改原始录制帧；完整对局回放继续记录实际送入模拟的输入。
static func sample(packed: Array, recorded_facing: int, current_facing: int, relative: bool) -> UfeInputFrame:
	var frame:=UfeInputFrame.unpack(packed)
	if relative and recorded_facing in [-1,1] and current_facing in [-1,1]:
		frame.x*=recorded_facing*current_facing
	return frame
