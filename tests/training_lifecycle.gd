extends SceneTree
## 经真实主游戏动作与physics入口验证；必须使用隔离XDG运行，F4会写user://last_replay.json。
class TestApp extends "res://app/game_app.gd":
	var reject_match: bool=false
	func _ready() -> void:pass
	func _battle_match(first: String, second: String, allow_pilot: bool=false) -> UfeMatchDirector:
		if reject_match:return null
		return super._battle_match(first,second,allow_pilot)

var errors: Array=[]
var checks: int=0
var app: TestApp
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1
	if not ok:errors.append(label);printerr(label)
func seed_tape() -> void:
	app.dummy_tape=[[1,0,0],[0,-1,UfeInputFrame.LIGHT],[-1,0,0]]
	app.dummy_facings=[1,1,-1]
	app.dummy_relative=true
	app.dummy=4
	app.dummy_cursor=2
func enter_replay(complete: bool) -> void:
	app.selected_fighters=["zetton","ultraman"]
	app.training=true
	app.reset_round()
	app.intro=0
	for tick in range(4):
		var pair: Array=[UfeInputFrame.make(),UfeInputFrame.make()]
		app.simulation.step(pair);app.recorder.append(pair,app.simulation)
	app.dummy_recording=true
	app._action("replay")
	check(not app.dummy_recording,"F4进入完整回放停止陪练录制")
	check(app.replay!=null,"真实F4入口载入回放")
	if complete:
		for tick in range(5):app._physics_process(1.0/60.0)
		check(app.paused and app.replay_cursor==4,"F4输入耗尽实际自动暂停")
	# 旧选人菜单和正在播放的回放可以来自不同组合，不能使用旧selected_fighters重建。
	app.selected_fighters=["ultraman","zetton"]
	seed_tape()
func test_transition(complete: bool,recording: bool) -> void:
	enter_replay(complete)
	var saved: Array=app.dummy_tape.duplicate(true)
	var facings: Array=app.dummy_facings.duplicate()
	if complete:app._action("pause")
	app._action("settings")
	app._action("dummy_record" if recording else "dummy_playback")
	var label:="%s/%s"%[complete,recording]
	check(app.replay==null and app.training and not app.paused,"回放切真实训练/"+label)
	check(app.selected_fighters==["zetton","ultraman"],"采用回放人物而非旧选人/"+label)
	check(app.simulation.fighters[0].base_definition.id=="zetton" and app.simulation.fighters[1].base_definition.id=="ultraman","新训练局人物匹配/"+label)
	check(app.simulation.tick==0 and app.recorder.frames.is_empty(),"重建初始状态与完整局录制/"+label)
	check(app.dummy_relative and app.dummy==4 and app.dummy_cursor==0,"保留方向和循环模式但归零游标/"+label)
	check(app.dummy_recording==recording,"录制状态正确/"+label)
	check(app.dummy_tape.is_empty() if recording else app.dummy_tape==saved,"仅显式新录制清磁带/"+label)
	if not recording:check(app.dummy_facings==facings,"播放保留逐帧朝向/"+label)
	check(app.intro==75,"保留正式75tick开场/"+label)
	for tick in range(75):app._physics_process(1.0/60.0)
	check(app.simulation.tick==0 and app.recorder.frames.is_empty() and app.intro==0,"开场不采样不录入/"+label)
	Input.action_press("p2_right")
	app._physics_process(1.0/60.0)
	Input.action_release("p2_right")
	check(app.simulation.tick==1 and app.recorder.frames.size()==1,"新训练实际推进并录完整局/"+label)
	if recording:check(app.dummy_tape==[[1,0,0]],"真实2P设备输入进入新磁带/"+label)
	else:check(app.dummy_cursor==1 and app.recorder.frames[0][1]==[-1,0,0],"首帧从磁带起点按朝向播放/"+label)
func run() -> void:
	UfeInputRouter.configure()
	app=TestApp.new();root.add_child(app);app.set_physics_process(false);app.start_match()
	for complete in [false,true]:
		for recording in [false,true]:test_transition(complete,recording)
	# 转换失败必须保留正在播放的局、选人、磁带和模式。
	enter_replay(true)
	var old_sim:=app.simulation;var old_replay:=app.replay
	var saved: Array=app.dummy_tape.duplicate(true)
	var facings: Array=app.dummy_facings.duplicate()
	app.reject_match=true
	app._action("dummy_record")
	check(app.simulation==old_sim and app.replay==old_replay and app.paused,"构建失败不提交新局")
	check(app.dummy_tape==saved and app.dummy_facings==facings and app.dummy_cursor==2,"构建失败不损磁带与游标")
	check(app.selected_fighters==["ultraman","zetton"] and not app.dummy_recording,"构建失败不改选人与录制模式")
	app.reject_match=false
	# 防御性检查：完整回放中的录制调用不得污染磁带。
	app.dummy_recording=true
	app._record_dummy_input(UfeInputFrame.make(0,0,UfeInputFrame.HEAVY))
	check(app.dummy_tape==saved,"完整回放禁止边播边录")
	app._action("dummy_playback")
	app.dummy_cursor=2;app.dummy_recording=true
	app._action("restart")
	check(app.dummy_cursor==0 and not app.dummy_recording and app.dummy_tape==saved,"再战停止跨局录制并从头播放，保留磁带")
	check(app.dummy_relative and app.dummy==4,"再战保留方向及陪练模式")
	# 正常局结束后同样不能在finished模拟上继续采样。
	app.simulation.finished=true
	app._action("dummy_record")
	check(not app.simulation.finished and app.simulation.tick==0 and app.dummy_recording,"终局录制创建新训练局")
	app._show_page("title")
	check(not app.dummy_recording,"离开对局结束录制边界")
	print("TRAINING_LIFECYCLE ",JSON.stringify({"checks":checks,"errors":errors}))
	await app.shutdown(0 if errors.is_empty() else 1)
	app.free()
	# AudioServer 在独立线程按真实时间回收 playback；headless 帧循环极快，
	# 只等帧不够，退出前必须让出真实时间，否则报 AudioStream 泄漏。
	OS.delay_msec(120)
