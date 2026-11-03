class_name UfeReplayRecorder
extends RefCounted
const FORMAT := 6
var fingerprint: String = ""
var fighter_ids: Array = []
var frames: Array = []
var final_hash: String = ""
var match_seed: int=20261022
var ai_difficulty: String="normal"
static var last_error: String = ""

func append(inputs: Array, simulation: UfeMatchDirector) -> void:
	if frames.is_empty():
		fingerprint = simulation.content_fingerprint
		fighter_ids = [simulation.fighters[0].base_definition.id, simulation.fighters[1].base_definition.id]
	frames.append([inputs[0].pack(), inputs[1].pack()])
	final_hash = simulation.state_hash()

func save_file(path: String) -> Error:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null: return FileAccess.get_open_error()
	file.store_string(JSON.stringify({"format": FORMAT, "tick_rate": 60, "rules": "neo", "fighters": fighter_ids,
		"content": fingerprint, "frames": frames, "final_hash": final_hash,"match_seed":match_seed,"ai_difficulty":ai_difficulty}))
	return OK

static func load_file(path: String, expected: String) -> UfeReplayRecorder:
	last_error = ""
	if not FileAccess.file_exists(path):
		last_error = "暂无回放"
		return null
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Dictionary or data.get("format") != FORMAT:
		last_error = "旧回放不兼容：快捷出招与体力规则已更新，当前仅支持格式6，请重新录制"
		return null
	if data.get("content") != expected or data.get("tick_rate") != 60 or data.get("rules") != "neo":
		last_error = "规则或招式数据已改变，无法播放该回放"
		return null
	if not data.get("fighters") is Array or data.fighters.size() != 2:
		return null
	if not data.get("frames") is Array or data.frames.is_empty() or data.frames.size() > 36000:
		return null
	for pair in data.frames:
		if not pair is Array or pair.size() != 2: return null
		for frame in pair:
			if not frame is Array or frame.size() != 3: return null
			for number in frame:
				if not (number is int or number is float) or number != int(number): return null
			if absi(int(frame[0])) > 1 or absi(int(frame[1])) > 1 or int(frame[2]) < 0 or int(frame[2]) > UfeInputFrame.ALL_BUTTONS: return null
	var replay := UfeReplayRecorder.new()
	replay.fingerprint = expected
	replay.fighter_ids = data.fighters
	replay.frames = data.frames
	replay.final_hash = str(data.get("final_hash", ""))
	replay.match_seed=int(data.get("match_seed",20261022))
	replay.ai_difficulty=str(data.get("ai_difficulty","normal"))
	return replay
