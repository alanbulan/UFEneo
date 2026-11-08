extends SceneTree
## 仪器回归：测试提供action样本和白名单事件；不声称原生键盘验收。
const Audit=preload("res://app/training_input_audit.gd")
class TestApp extends "res://app/game_app.gd":
	func _ready() -> void:pass
var errors: Array=[]
var checks: int=0
var first: TestApp
var second: TestApp
var out: String="user://training-input-audit-test"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--audit-test-out="):out=arg.trim_prefix("--audit-test-out=")
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1
	if not ok:errors.append(label);printerr(label)
func mode(app) -> Array:
	return [app.training,app.local,app.dummy,app.dummy_recording,app.replay!=null,app.paused,app.intro,app.dummy_cursor,app.dummy_tape,app.dummy_facings]
func advance(count: int) -> void:
	for tick in range(count):
		first._physics_process(1.0/60.0);second._physics_process(1.0/60.0)
		check(first.simulation.state_hash()==second.simulation.state_hash(),"有无观察器同输入state_hash相同")
		check(mode(first)==mode(second) and first.recorder.frames==second.recorder.frames,"观察器不改模式磁带或实际输入")
func action(name: String) -> void:
	first._action(name);second._action(name)
func key(code: Key,echo: bool=false) -> void:
	var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true;event.echo=echo
	first._input(event);second._input(event)
func read_lines(path: String) -> Array:
	var result: Array=[]
	for line in FileAccess.get_file_as_string(path).split("\n",false):
		var parser:=JSON.new()
		check(parser.parse(line)==OK,"日志逐行合法JSON")
		if parser.data is Dictionary:result.append(parser.data)
	return result
func run() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	# 重复运行必须从干净目录开始：Audit 拒绝已存在的日志路径，
	# 残留旧文件会让观察器变成 null 并让后续 close() 崩溃。
	for name in DirAccess.get_files_at(out):
		DirAccess.remove_absolute(out.path_join(name))
	check(Audit.from_arguments(PackedStringArray())==null,"无显式开关不创建观察器")
	check(DirAccess.get_files_at(out).is_empty(),"默认没有文件写入")
	UfeInputRouter.configure_values({})
	# 默认键位一主键只绑一个动作：以前 2P 跳跃和上方向同按 KEY_UP。
	for owner in range(2):
		var used: Dictionary={}
		for name in UfeInputRouter.ACTIONS:
			var code := int(UfeInputRouter.default_key_binding(owner,name).keycode)
			if code>0:
				check(not used.has(code),"默认键位不重复 %dP %s" % [owner+1,name])
				used[code]=true
	first=TestApp.new();root.add_child(first);first.set_physics_process(false);first.start_match()
	second=TestApp.new();root.add_child(second);second.set_physics_process(false);second.start_match()
	check(first.training_input_audit==null and second.training_input_audit==null,"主游戏默认诊断关闭")
	var path:=out.path_join("observer.jsonl")
	second.training_input_audit=Audit.from_arguments(PackedStringArray(["--training-input-audit="+path]))
	check(second.training_input_audit!=null,"仅显式参数打开日志")
	action("local");advance(75)
	Input.action_press("p2_right");advance(12);Input.action_release("p2_right")
	Input.action_press("p2_down");advance(8);Input.action_release("p2_down")
	Input.action_press("p1_right");advance(5);Input.action_release("p1_right")
	# 原生样式事件只验证日志字段/过滤，不用它伪装物理设备送达。
	key(KEY_D);key(KEY_A)
	action("dummy_record")
	Input.action_press("p2_down");advance(10);Input.action_release("p2_down")
	key(KEY_ENTER,true);advance(2)
	check(second.dummy_recording,"echo事件不改变原游戏行为")
	key(KEY_ENTER);advance(3)
	check(not second.dummy_recording and second.paused,"真实主游戏Enter规则由主游戏自身执行")
	action("pause");advance(65)
	key(KEY_R);advance(77)
	second.training_input_audit.close();second.training_input_audit.close()
	var rows:=read_lines(path)
	var saw_raw:=false;var saw_live:=false;var saw_paused:=false;var saw_intro:=false;var saw_enter:=false;var saw_echo:=false
	var previous: int=-1
	for row in rows:
		check(int(row.sequence)>previous,"诊断序号严格递增")
		previous=int(row.sequence)
		if row.kind=="key_event":
			check(int(row.keycode) in [KEY_D,KEY_RIGHT,KEY_DOWN,KEY_ENTER,KEY_R,KEY_F4],"只记录允许的按键")
			check(not row.has("unicode") and not row.has("text"),"不记录字符或任意文本")
			if int(row.keycode)==KEY_ENTER:saw_enter=true;saw_echo=saw_echo or bool(row.echo)
		if row.kind=="physics":
			if UfeInputFrame.unpack(row.before.poll2).pack()==[1,0,0]:saw_raw=true
			if row.sampled and UfeInputFrame.unpack(row.second).pack()==[1,0,0] and row.source=="live":saw_live=true
			if row.before.paused and not row.sampled and not row.advanced:saw_paused=true
			if int(row.before.intro)>0 and not row.sampled and not row.advanced:saw_intro=true
	check(saw_raw and saw_live,"被动记录实际router样本及真正送模拟second")
	check(saw_paused and saw_intro,"暂停及开场明确没有推进或采样")
	check(saw_enter and saw_echo,"白名单按下与echo字段完整")
	check(rows[-1].kind=="closed","正常关闭flush并写结束记录")
	var existing:=FileAccess.get_file_as_string(path)
	var no_overwrite:=Audit.new(path)
	check(no_overwrite.file==null and FileAccess.get_file_as_string(path)==existing,"已有诊断文件不被截断")
	var limited:=Audit.new(out.path_join("bounded.jsonl"),3)
	for tick in range(6):limited.begin_frame(second);limited.end_frame(second)
	limited.close()
	var bounded:=read_lines(out.path_join("bounded.jsonl"))
	check(bounded.size()<=3 and bounded[-1].kind=="limit","到达上限明确截断且文件有界")
	var result:={"checks":checks,"errors":errors,"rows":rows.size(),"physics_samples":second.training_input_audit.physics_sample,"scope":"instrumentation with action samples and constructed InputEventKey; not native hardware input acceptance"}
	FileAccess.open(out.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print("TRAINING_INPUT_AUDIT ",JSON.stringify(result))
	await first.shutdown(0,false)
	first.free()
	await second.shutdown(0 if errors.is_empty() else 1)
	# AudioServer 在独立线程上按真实时间回收已停止的 playback。headless 下
	# 帧循环极快，只等 process_frame 不够，必须让出真实时间，否则退出时会报
	# AudioStream/Playback 泄漏。
	OS.delay_msec(120)
