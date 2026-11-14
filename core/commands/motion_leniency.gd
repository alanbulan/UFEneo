class_name UfeMotionLeniency
extends RefCounted
## 搓招宽容。精确序列仍有效；另外接受常见漏斜向。
## 单步间隔最多 8 tick，从最新输入回溯整段不超过 16 tick。
const STEP_WINDOW := 8
const SPAN := 16

static func matches(history: Array, seq: Array) -> bool:
	if seq.is_empty():
		return true
	if _match(history, seq):
		return true
	for alt in _alternatives(seq):
		if _match(history, alt):
			return true
	return false

static func _same(seq: Array, expected: Array) -> bool:
	if seq.size() != expected.size():
		return false
	for index in range(seq.size()):
		if int(seq[index]) != int(expected[index]):
			return false
	return true

static func _alternatives(seq: Array) -> Array:
	# 招式表从 JSON 读入，方向号是浮点；不能用数组直接相等。
	if _same(seq, [2, 3, 6]):
		return [[2, 6]]
	if _same(seq, [2, 1, 4]):
		return [[2, 4]]
	if _same(seq, [6, 2, 3]):
		return [[6, 3, 2, 3], [3, 2, 3]]
	if _same(seq, [4, 1, 2, 3, 6]):
		return [[4, 1, 2, 6], [4, 2, 6]]
	return []

static func _match(history: Array, seq: Array) -> bool:
	var need := seq.duplicate()
	need.reverse()
	var hi := 0
	var oldest := 0
	for req in need:
		var found := false
		var steps := 0
		while hi < history.size() and steps <= STEP_WINDOW:
			if int(history[hi]) == int(req):
				found = true
				oldest = hi
				hi += 1
				break
			hi += 1
			steps += 1
		if not found:
			return false
	return oldest < SPAN
