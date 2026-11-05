extends SceneTree
## 正式主游戏F4键事件保存、0输入换人、暂停菜单按钮信号播放；隔离XDG必需。
class TestApp extends "res://app/game_app.gd":
	var changed_rule: bool=false
	func _ready() -> void:pass
	func _battle_match(first: String,second: String,allow_pilot: bool=false) -> UfeMatchDirector:
		var original:=super._battle_match(first,second,allow_pilot)
		if not changed_rule:return original
		var rule:=original.rules.duplicate(true) as UfeRuleSet
		rule.round_ticks-=60
		var forms: Dictionary={}
		for fighter in original.fighters:forms[fighter.base_definition.id]=fighter.battle_form
		return UfeMatchDirector.new(original.fighters[0].base_definition,original.fighters[1].base_definition,rule,original.states,forms)

var app: TestApp
var errors: Array=[]
var rows: Array=[]
var checks: int=0
var output: String="user://replay-match-loading"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--replay-test-out="):output=arg.trim_prefix("--replay-test-out=")
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1
	if not ok:errors.append(label);printerr(label)
func write_text(path: String,value: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(value)
func key(code: Key) -> void:
	var event:=InputEventKey.new();event.keycode=code;event.pressed=true;app._input(event)
func menu_click(panel: Control,label: String) -> void:
	for child in panel.get_child(0).get_children():
		if child is Button and child.text==label:child.pressed.emit();return
	check(false,"缺正式按钮/"+label)
func new_round(ids: Array) -> void:
	app._action("select")
	# 只配置已选中的人物，调用与正式选人/场景确认相同的新局入口。
	app.front.selections=ids.duplicate();app.front.mode="training"
	app._front_action("begin_match")
	check(app.simulation.tick==0 and app.recorder.frames.is_empty() and app.intro==75,"正式新局保持0输入和75tick开场")
func canonical_frames(frames: Array) -> Array:
	var result: Array=[]
	for pair in frames:result.append([UfeInputFrame.unpack(pair[0]).pack(),UfeInputFrame.unpack(pair[1]).pack()])
	return result
func source(ids: Array,name: String,rule_changed: bool=false) -> String:
	app.changed_rule=rule_changed
	new_round(ids)
	app.dummy=0
	for tick in range(75):app._physics_process(1.0/60.0)
	for tick in range(24):
		if tick==0:Input.action_press("p1_right")
		if tick==8:Input.action_release("p1_right")
		if tick==10:Input.action_press("p1_light")
		if tick==11:Input.action_release("p1_light")
		app._physics_process(1.0/60.0)
	var original: Array=app.recorder.frames.duplicate(true)
	check(original.size()==24,"通过正式physics真实采样24帧/"+name)
	key(KEY_F4)
	check(app.replay!=null and canonical_frames(app.replay.frames)==original,"F4实际保存并载回原输入/"+name)
	var raw:=FileAccess.get_file_as_string("user://last_replay.json")
	write_text(output.path_join(name+"-original.json"),raw)
	app.changed_rule=false
	return raw
func attempt(raw: String,current_ids: Array,label: String,should_load: bool,reason: String="") -> void:
	new_round(current_ids)
	write_text("user://last_replay.json",raw)
	key(KEY_ESCAPE)
	check(app.paused and app.hud.menu.visible,"开场0输入时真实Esc暂停/"+label)
	menu_click(app.hud.menu,"训练设置")
	check(app.hud.settings.visible,"正式训练设置菜单/"+label)
	app.dummy_tape=[[1,0,0],[0,-1,1]];app.dummy_facings=[1,-1]
	app.dummy_relative=true;app.dummy_cursor=1;app.dummy_recording=true
	var old_sim:=app.simulation;var old_hash:=old_sim.state_hash()
	var old_recorder:=app.recorder
	var old_selected: Array=app.selected_fighters.duplicate()
	var old_tape: Array=app.dummy_tape.duplicate(true)
	var old_facings: Array=app.dummy_facings.duplicate()
	var old_file_hash:=FileAccess.get_file_as_string("user://last_replay.json").sha256_text()
	menu_click(app.hud.settings,"播放回放 F4")
	var loaded: bool=app.replay!=null
	var row: Dictionary={"case":label,"expected_load":should_load,"loaded":loaded,"message":app.message,"current_ids":current_ids,"current_hash_before":old_hash,"current_fingerprint":old_sim.content_fingerprint,"input_file_sha256":old_file_hash}
	check(loaded==should_load,"播放许可符合预期/"+label)
	check(FileAccess.get_file_as_string("user://last_replay.json").sha256_text()==old_file_hash,"0输入不会覆盖原回放文件/"+label)
	check(app.dummy_tape==old_tape and app.dummy_facings==old_facings and app.dummy_relative,"载入不污染陪练磁带/"+label)
	if should_load and loaded:
		var data: Dictionary=JSON.parse_string(raw)
		check(app.simulation.fighters[0].base_definition.id==data.fighters[0] and app.simulation.fighters[1].base_definition.id==data.fighters[1],"恢复录制人物及顺序/"+label)
		check(canonical_frames(app.replay.frames)==canonical_frames(data.frames),"不改录制原输入/"+label)
		for tick in range(data.frames.size()+1):app._physics_process(1.0/60.0)
		check(app.simulation.state_hash()==data.final_hash and app.paused,"完整正式回放最终hash一致/"+label)
		row["final_hash"]=app.simulation.state_hash()
		key(KEY_R)
		check(app.replay==null and app.selected_fighters==data.fighters,"真实R再战沿用回放人物/"+label)
		check(app.simulation.fighters[0].base_definition.id==data.fighters[0] and app.simulation.fighters[1].base_definition.id==data.fighters[1],"再战画面双方不回旧选人/"+label)
		check(app.simulation.tick==0 and app.intro==75 and app.recorder.frames.is_empty(),"再战为正式新局/"+label)
		row["restart_ids"]=app.selected_fighters.duplicate()
	elif not should_load:
		check(app.simulation==old_sim and app.simulation.state_hash()==old_hash and app.replay==null and app.selected_fighters==old_selected,"拒绝后原对局和选人保持/"+label)
		check(app.paused and app.hud.settings.visible and app.dummy_cursor==1 and app.dummy_recording and app.recorder==old_recorder,"拒绝后暂停菜单和磁带游标保持/"+label)
		check(not app.message.is_empty(),"拒绝提供说明/"+label)
		if not reason.is_empty():check(reason in app.message,"拒绝原因准确/"+label)
	rows.append(row)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	UfeInputRouter.configure()
	app=TestApp.new();root.add_child(app);app.set_physics_process(false);app.start_match()
	var original:=source(["ultraman","zetton"],"standard")
	attempt(original,["ultraman","zetton"],"same_pair_control",true)
	attempt(original,["ultraman-taro","zetton"],"different_fighter",true)
	attempt(original,["zetton","ultraman"],"swapped_sides",true)
	var ex:=source(["ex_gomora","ultraman"],"ex_direct")
	attempt(ex,["ultraman","zetton"],"ex_direct_from_other_pair",true)
	var changed:=source(["ultraman","zetton"],"changed_round_rule",true)
	attempt(changed,["ultraman","zetton"],"real_rule_changed_rejected",false,"规则或招式数据已改变")
	# 同组合和不同组合都必须先安全验证元数据，不能靠无关的指纹错误偶然拒绝。
	var reasons: Dictionary={"unknown_id":"角色不存在", "path_id":"角色ID不合法", "non_string_id":"角色ID不合法", "wrong_pair_size":"需要两名角色", "invalid_frame":"方向或按键越界", "old_format":"旧回放", "wrong_tick_rate":"规则或招式数据已改变", "wrong_rules":"规则或招式数据已改变", "invalid_seed":"元数据无效", "invalid_difficulty":"元数据无效", "invalid_final_hash":"元数据无效"}
	for variant in reasons:
		var data: Dictionary=JSON.parse_string(original)
		match variant:
			"unknown_id":data.fighters=["missing_fighter_for_test","zetton"]
			"path_id":data.fighters=["../ultraman","zetton"]
			"non_string_id":data.fighters=[7,"zetton"]
			"wrong_pair_size":data.fighters=["ultraman"]
			"invalid_frame":data.frames=[[[99,0,0],[0,0,0]]]
			"old_format":data.format=5
			"wrong_tick_rate":data.tick_rate=30
			"wrong_rules":data.rules="other"
			"invalid_seed":data.match_seed={"value":1}
			"invalid_difficulty":data.ai_difficulty=[]
			"invalid_final_hash":data.final_hash={}
		var raw:=JSON.stringify(data)
		write_text(output.path_join(variant+".json"),raw)
		attempt(raw,["ultraman","zetton"],variant+"_same_pair",false,reasons[variant])
		attempt(raw,["ultraman-taro","zetton"],variant+"_other_pair",false,reasons[variant])
	# 指纹来自当前组合也不能绕过录制人物验证/当前规则重建。
	var forged: Dictionary=JSON.parse_string(original)
	forged.content=UfeBattleFormCatalog.match_for("ultraman-taro","zetton").content_fingerprint
	write_text(output.path_join("forged-current-fingerprint.json"),JSON.stringify(forged))
	attempt(JSON.stringify(forged),["ultraman-taro","zetton"],"forged_current_fingerprint",false,"规则或招式数据已改变")
	forged.fighters=["missing_fighter_for_test","zetton"]
	write_text(output.path_join("forged-unknown-fighter.json"),JSON.stringify(forged))
	attempt(JSON.stringify(forged),["ultraman-taro","zetton"],"forged_unknown_fighter",false,"角色不存在")
	write_text(output.path_join("broken-json.txt"),"{broken")
	attempt("{broken",["ultraman-taro","zetton"],"broken_json",false,"JSON格式错误")
	attempt("[]",["ultraman","zetton"],"invalid_root",false,"根数据不是对象")
	var result: Dictionary={"checks":checks,"errors":errors,"cases":rows,"test_input":"Input.action_press plus real App physics, synthetic F4/Esc InputEventKey and real pause-menu button signals; not physical hardware input"}
	write_text(output.path_join("result.json"),JSON.stringify(result,"\t"))
	print("REPLAY_MATCH_LOADING ",JSON.stringify(result))
	await app.shutdown(0 if errors.is_empty() else 1)
