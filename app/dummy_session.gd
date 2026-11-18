class_name UfeDummySession
extends RefCounted
## 训练模式陪练行为录制与磁带采样辅助。

const TrainingTape = preload("res://input/training_tape.gd")


static func record_input(app: Object, frame: UfeInputFrame) -> void:
	if app.replay != null or not app.dummy_recording or not app.training or app.dummy != 4:
		return
	app.dummy_tape.append(frame.pack())
	app.dummy_facings.append(app.simulation.fighters[1].facing)


static func sample_input(app: Object) -> UfeInputFrame:
	match int(app.dummy):
		1:
			return UfeInputFrame.make(0, -1)
		2:
			return UfeInputFrame.make(0, 1 if app.simulation.tick % 45 == 0 else 0)
		3:
			return UfeInputFrame.make(0, 0, UfeInputFrame.GUARD)
		4:
			if app.dummy_recording:
				return UfeInputRouter.poll(1)
			if not app.dummy_tape.is_empty():
				var index: int = int(app.dummy_cursor) % app.dummy_tape.size()
				# 旧审片注入的磁带无朝向元数据时沿原始方向，不猜录制朝向。
				var facing: int = int(app.dummy_facings[index]) if index < app.dummy_facings.size() else 0
				var frame := TrainingTape.sample(app.dummy_tape[index], facing, app.simulation.fighters[1].facing, app.dummy_relative)
				app.dummy_cursor += 1
				return frame
	return UfeInputFrame.make()
