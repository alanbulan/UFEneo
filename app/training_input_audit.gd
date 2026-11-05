extends RefCounted
## 显式启用的主游戏只读仪器；不改变Input、模式、模拟或回放。
const KEYS: Dictionary={KEY_D:"D",KEY_RIGHT:"Right",KEY_DOWN:"Down",KEY_ENTER:"Enter",KEY_R:"R",KEY_F4:"F4"}
const MAX_ROWS: int=20000
const MAX_BYTES: int=16*1024*1024
var file: FileAccess
var sequence: int=0
var physics_sample: int=0
var rows: int=0
var bytes_written: int=0
var row_limit: int=MAX_ROWS
var capped: bool=false
var pending: Dictionary={}
var last_signature: String=""
var skipped: int=0
var last_skipped: Dictionary={}

static func from_arguments(arguments: PackedStringArray):
	for argument in arguments:
		if argument.begins_with("--training-input-audit="):
			var audit:=new(argument.trim_prefix("--training-input-audit="))
			if audit.file!=null:return audit
			push_warning("训练输入诊断未启用：日志路径为空、已存在或不可写")
	return null

func _init(path: String,limit: int=MAX_ROWS) -> void:
	row_limit=clampi(limit,2,MAX_ROWS)
	if path.is_empty() or FileAccess.file_exists(path):return
	file=FileAccess.open(path,FileAccess.WRITE)
	if file==null:return
	_write({"kind":"header","sequence":0,"schema":1,"keys":["D","Right","Down","Enter","R","F4"],"max_rows":row_limit,"max_bytes":MAX_BYTES,"note":"Godot事件来源不等于已验证物理硬件；每physics前后被动采样，相同状态最多60采样心跳；不记录unicode/文本。"})

func record_event(event: InputEvent) -> void:
	if file==null or capped or not event is InputEventKey:return
	if not KEYS.has(event.keycode) and not KEYS.has(event.physical_keycode):return
	if not last_skipped.is_empty():
		last_skipped.skipped_same_samples=skipped
		_write(last_skipped);last_skipped={};skipped=0
	sequence+=1
	_write({"kind":"key_event","sequence":sequence,"physics_sample":physics_sample,"keycode":int(event.keycode),"physical_keycode":int(event.physical_keycode),"pressed":event.pressed,"echo":event.echo,"shift":event.shift_pressed,"ctrl":event.ctrl_pressed,"alt":event.alt_pressed,"meta":event.meta_pressed})

func _snapshot(app) -> Dictionary:
	var keys: Dictionary={}
	for code in KEYS:
		keys[KEYS[code]]={"physical":Input.is_physical_key_pressed(code),"logical":Input.is_key_pressed(code)}
	var actions: Dictionary={}
	for action in ["p1_right","p2_right","p2_down"]:actions[action]=Input.is_action_pressed(action)
	return {"tick":app.simulation.tick if app.simulation!=null else -1,"training":app.training,"local":app.local,"dummy":app.dummy,"dummy_recording":app.dummy_recording,"replay":app.replay!=null,"replay_cursor":app.replay_cursor,"paused":app.paused,"intro":app.intro,"finished":app.simulation.finished if app.simulation!=null else false,"front_visible":is_instance_valid(app.front) and app.front.visible,"tape_length":app.dummy_tape.size(),"tape_cursor":app.dummy_cursor,"keys":keys,"actions":actions,"poll2":UfeInputRouter.poll(1).pack()}

func begin_frame(app) -> void:
	if file==null or capped:return
	sequence+=1;physics_sample+=1
	pending={"kind":"physics","sequence":sequence,"physics_sample":physics_sample,"before":_snapshot(app),"sampled":false,"second":null,"source":"not_stepped"}

func sampled(second: UfeInputFrame,source: String) -> void:
	if pending.is_empty():return
	pending.sampled=true;pending.second=second.pack();pending.source=source

func end_frame(app) -> void:
	if pending.is_empty():return
	pending.after=_snapshot(app)
	pending.advanced=pending.after.tick!=pending.before.tick
	var signature_data:=pending.duplicate(true)
	signature_data.erase("sequence");signature_data.erase("physics_sample")
	for phase in ["before","after"]:signature_data[phase].erase("tick")
	var signature:=JSON.stringify(signature_data)
	if signature!=last_signature or physics_sample%60==0:
		pending.skipped_same_samples=skipped
		_write(pending);last_signature=signature;skipped=0;last_skipped={}
	else:
		skipped+=1;last_skipped=pending
	pending={}

func _write(row: Dictionary) -> void:
	if file==null or capped:return
	var line:=JSON.stringify(row)+"\n"
	if rows>=row_limit-1 or bytes_written+line.to_utf8_buffer().size()>MAX_BYTES-512:
		line=JSON.stringify({"kind":"limit","sequence":sequence,"physics_sample":physics_sample,"reason":"row_or_byte_limit","rows_before_limit":rows})+"\n"
		capped=true
	file.store_string(line);rows+=1;bytes_written+=line.to_utf8_buffer().size()
	# 有界心跳刷盘；正常关闭必刷。事件与状态不写入core/state_hash。
	if rows%60==0 or capped:file.flush()

func close() -> void:
	if file==null:return
	if not last_skipped.is_empty():
		last_skipped.skipped_same_samples=skipped
		_write(last_skipped);last_skipped={}
	sequence+=1
	_write({"kind":"closed","sequence":sequence,"physics_sample":physics_sample,"capped":capped})
	file.flush();file=null;pending={}
