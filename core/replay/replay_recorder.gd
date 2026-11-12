class_name UfeReplayRecorder
extends RefCounted
const FORMAT := 6
var fingerprint: String = ""
var fighter_ids: Array = []
# 出场形态（选人界面选定）；基础ID仍在fighter_ids，旧回放缺省为default。
var forms: Array = []
var frames: Array = []
var final_hash: String = ""
var match_seed: int=20261022
var ai_difficulty: String="normal"
static var last_error: String = ""

func append(inputs: Array, simulation: UfeMatchDirector) -> void:
	if frames.is_empty():
		fingerprint = simulation.content_fingerprint
		fighter_ids = [simulation.fighters[0].base_definition.id, simulation.fighters[1].base_definition.id]
		forms = [str(simulation.fighters[0].form_id) if not simulation.fighters[0].form_id.is_empty() else "default",
			str(simulation.fighters[1].form_id) if not simulation.fighters[1].form_id.is_empty() else "default"]
	frames.append([inputs[0].pack(), inputs[1].pack()])
	final_hash = simulation.state_hash()

func save_file(path: String) -> Error:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null: return FileAccess.get_open_error()
	file.store_string(JSON.stringify({"format": FORMAT, "tick_rate": 60, "rules": "neo", "fighters": fighter_ids,
		"forms": forms, "content": fingerprint, "frames": frames, "final_hash": final_hash,"match_seed":match_seed,"ai_difficulty":ai_difficulty}))
	return OK

# 原严格接口保留；结构解析不能替代内容兼容性校验。
static func load_file(path: String, expected: String) -> UfeReplayRecorder:
	var replay:=read_candidate(path)
	if replay==null or not replay.matches_content(expected):return null
	return replay

func matches_content(expected: String) -> bool:
	if fingerprint!=expected:
		last_error="规则或招式数据已改变，无法播放该回放"
		return false
	return true

static func _reject(reason: String) -> UfeReplayRecorder:
	last_error=reason
	return null

static func _integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==int(value)

# 仅返回待校验候选；调用者必须按合法人物装配当前规则，并调用matches_content后才播放。
static func read_candidate(path: String) -> UfeReplayRecorder:
	last_error=""
	if not FileAccess.file_exists(path):return _reject("暂无回放")
	var file:=FileAccess.open(path,FileAccess.READ)
	if file==null:return _reject("无法读取回放文件")
	var parser:=JSON.new()
	if parser.parse(file.get_as_text())!=OK:return _reject("回放文件损坏：JSON格式错误")
	var data=parser.data
	if not data is Dictionary:return _reject("回放文件损坏：根数据不是对象")
	if data.get("format")!=FORMAT:
		return _reject("旧回放不兼容：快捷出招与体力规则已更新，当前仅支持格式6，请重新录制")
	if data.get("tick_rate")!=60 or data.get("rules")!="neo":
		return _reject("规则或招式数据已改变，无法播放该回放")
	if not data.get("content") is String or data.content.is_empty():return _reject("回放文件损坏：缺少内容指纹")
	if not data.get("fighters") is Array or data.fighters.size()!=2:return _reject("回放角色数据无效：需要两名角色")
	var identifier:=RegEx.new()
	identifier.compile("^[a-z0-9][a-z0-9_-]*$")
	for id in data.fighters:
		if not id is String or id.length()>128 or identifier.search(id)==null:return _reject("回放角色数据无效：角色ID不合法")
	# 旧格式6回放没有forms字段：按双方基础形态复原。
	var forms_data=data.get("forms",["default","default"])
	if not forms_data is Array or forms_data.size()!=2:return _reject("回放形态数据无效：需要双方出场形态")
	for form_id in forms_data:
		if not form_id is String or form_id.length()>128:return _reject("回放形态数据无效：形态ID不合法")
		if not form_id.is_empty() and identifier.search(form_id)==null:return _reject("回放形态数据无效：形态ID不合法")
	if not data.get("frames") is Array or data.frames.is_empty() or data.frames.size()>36000:return _reject("回放输入数据无效：帧数错误")
	for pair in data.frames:
		if not pair is Array or pair.size()!=2:return _reject("回放输入数据无效：需要双方输入")
		for frame in pair:
			if not frame is Array or frame.size()!=3:return _reject("回放输入数据无效：输入帧结构错误")
			for number in frame:
				if not _integer(number):return _reject("回放输入数据无效：输入必须为整数")
			if absi(int(frame[0]))>1 or absi(int(frame[1]))>1 or int(frame[2])<0 or int(frame[2])>UfeInputFrame.ALL_BUTTONS:return _reject("回放输入数据无效：方向或按键越界")
	if not _integer(data.get("match_seed",20261022)) or not data.get("ai_difficulty","normal") is String or not data.get("final_hash","") is String:
		return _reject("回放元数据无效：种子、难度或最终状态格式错误")
	var replay:=UfeReplayRecorder.new()
	replay.fingerprint=data.content
	replay.fighter_ids=data.fighters
	replay.forms=forms_data.duplicate()
	replay.frames=data.frames
	replay.final_hash=data.get("final_hash","")
	replay.match_seed=int(data.get("match_seed",20261022))
	replay.ai_difficulty=data.get("ai_difficulty","normal")
	return replay
