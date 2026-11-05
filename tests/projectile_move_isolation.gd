extends SceneTree
## 默认470/750站位，双方角色及招式均从正式内容装配。
## 杰顿t1、t36各按一次I：上一颗离手弹体不得消耗下一次起手的发射许可。
## 全程不改站位、能量、状态、招式或弹体；初代中立/U及雷欧真实蹲避为对照。
var out := "user://projectile-move-isolation/"
var legacy_directory := ""
var failures: Array = []
var summaries: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("PROJECTILE_MOVE_ISOLATION_FAIL "+label)

func write_json(path: String, value: Variant) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	check(file!=null,"写证据/"+path)
	if file!=null:file.store_string(JSON.stringify(value,"\t",true)+"\n")

func fixture(shooter: int, target: String) -> UfeMatchDirector:
	return UfeContentDatabase.match_for("zetton" if shooter==0 else target,target if shooter==0 else "zetton")

func before_isolation_fingerprint(sim: UfeMatchDirector) -> String:
	# 修前ccefbcd7真实全局规则，方向revision2已生效，但尚无跨招隔离项。
	var forms: Array = []
	for f in sim.fighters:forms.append(UfeBattleTransform.simulation_data(f.battle_form))
	var data: Array = [6,60,sim.rules.simulation_data(),sim.fighters[0].definition.simulation_data(),sim.fighters[1].definition.simulation_data(),forms,["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION],["hit_pushback_bounds",UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],["throw_target_air",UfeHitResolver.THROW_TARGET_RULE_REVISION],["chase_interrupt",UfeMatchDirector.CHASE_INTERRUPT_RULE_REVISION],["projectile_contact_direction",2]]
	if UfeThrowResolver.RootOffsets.used_in(data):data.append(["throw_root_overrides",UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION])
	if UfeThrowResolver.CurrentCapture.used_in(data):data.append(["throw_current_capture",UfeThrowResolver.CurrentCapture.REVISION])
	return JSON.stringify(data,"",true).sha256_text()

func observe(sim: UfeMatchDirector) -> Dictionary:
	var pair: Array = []
	for f in sim.fighters:
		pair.append({"id":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,
			"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,
			"hp":f.stats.hp,"energy":f.stats.energy,"stamina":f.stats.stamina,
			"connected":f.combat.connected,"confirmed":f.combat.confirmed})
	return {"tick":sim.tick,"hash":sim.state_hash(),"hitstop":sim.hitstop,"pair":pair,
		"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)}

func test_case(shooter: int, mode: String, second_tick: int = 36) -> void:
	var target := "ultraman-leo" if mode=="crouch" else "ultraman"
	var label := "p%s-%s-second-%s"%[shooter+1,mode,second_tick]
	var sim := fixture(shooter,target)
	var initial := observe(sim)
	var source := sim.fighters[shooter]
	var move: Dictionary = source.definition.moves.pulse
	check(sim.fighters[0].x==470 and sim.fighters[1].x==750,label+"/正式默认站位")
	check(source.stats.energy==0 and source.stats.stamina==1000,label+"/零能量正常开局")
	check(int(move.energy_cost)==0 and int(move.stamina_cost)==30 and move.frames.size()==35,label+"/正式火球成本与总帧")
	check(str(move.kind)=="projectile" and int(move.startup)==12,label+"/正式自动发射起手")
	var record := UfeReplayRecorder.new()
	var rows: Array = []
	var starts: Array = []
	var births: Array = []
	var contacts: Array = []
	var old_contact_during_startup: Array = []
	var second_active_frames: Array = []
	for tick in range(1,121):
		var inputs: Array = [UfeInputFrame.make(),UfeInputFrame.make()]
		if tick in [1,second_tick]:inputs[shooter]=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
		if mode=="guard":inputs[1-shooter]=UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
		elif mode=="crouch":inputs[1-shooter]=UfeInputFrame.make(0,-1,0)
		var before := observe(sim)
		sim.step(inputs)
		record.append(inputs,sim)
		var after := observe(sim)
		rows.append(after)
		var actor: Dictionary = after.pair[shooter]
		if tick in [1,second_tick]:
			var began: bool=str(before.pair[shooter].move).is_empty() and str(actor.move)=="pulse" and int(actor.move_tick)==1
			check(began,label+"/t%s真实I成功启动"%tick)
			check(int(before.pair[shooter].stamina)-int(actor.stamina)==int(move.stamina_cost),label+"/t%s真实支付体力"%tick)
			check(int(before.pair[shooter].energy)==int(actor.energy),label+"/t%s无额外能量条件"%tick)
			if began:starts.append({"tick":tick,"before":before,"after":after})
		for projectile in sim.projectiles:
			if int(projectile.owner)==shooter and str(projectile.move)=="pulse" and int(projectile.age)==1:
				births.append({"tick":tick,"move_tick":actor.move_tick,"projectile":projectile.duplicate(true)})
		if tick>=second_tick and str(actor.move)=="pulse" and not source.frame().hitboxes.is_empty():
			second_active_frames.append({"tick":tick,"move_tick":actor.move_tick,"connected":actor.connected,"births":births.size()})
		for event in sim.events:
			if event.kind not in ["hit","block"] or int(event.player)!=shooter or str(event.move)!="pulse":continue
			contacts.append({"tick":tick,"event":event.duplicate(true),"before":before,"after":after})
			check(bool(event.projectile),label+"/接触确实来自离手弹体")
			if tick>=second_tick and births.size()==1 and str(actor.move)=="pulse" and int(actor.move_tick)<int(move.startup):
				old_contact_during_startup.append(contacts.back())
				check(not bool(before.pair[shooter].connected),label+"/旧弹接触前新招未发射")
				check(not bool(actor.connected),label+"/旧弹接触不能消耗新招发射许可")
				check(bool(actor.confirmed)==(str(event.kind)=="hit"),label+"/旧弹命中确认与格挡语义保持")
	check(starts.size()==2,label+"/两次真实有效I起手")
	check(births.size()==2,label+"/两次起手必须各自产生一颗火球")
	if births.size()>=2:
		check(int(births[0].tick)<second_tick and int(births[1].tick)>=second_tick,label+"/每次起手各发射一次")
		check(int(births[0].move_tick)==12 and int(births[1].move_tick)==12,label+"/保留双方12tick发射点")
	check(not second_active_frames.is_empty(),label+"/第二次起手真实进入有效帧")
	if mode=="crouch":
		check(contacts.is_empty(),label+"/雷欧真实蹲姿躲过两颗高球")
		check(int(sim.fighters[1-shooter].stats.hp)==1000,label+"/蹲避无伤害")
	else:
		check(contacts.size()==2,label+"/两颗火球均到达并真实接触")
		for contact in contacts:
			check(str(contact.event.kind)==("block" if mode=="guard" else "hit"),label+"/站立或持U结果")
		check(int(sim.fighters[1-shooter].stats.hp)==(1000 if mode=="guard" else 870),label+"/维持正式65伤害或格挡无伤")
		if second_tick==36:check(old_contact_during_startup.size()==1,label+"/旧弹确在第二招发射前接触")
		else:check(old_contact_during_startup.is_empty(),label+"/延后起手排除跨招重叠")
	var replay_path := out+label+"-replay.json"
	check(record.save_file(replay_path)==OK,label+"/原始输入保存")
	var loaded := UfeReplayRecorder.load_file(replay_path,sim.content_fingerprint)
	check(loaded!=null,label+"/正式loader载入")
	var replay := fixture(shooter,target)
	if loaded!=null:
		check(loaded.frames.size()==rows.size(),label+"/独立回放帧数")
		for index in range(loaded.frames.size()):
			var pair: Array = loaded.frames[index]
			var replay_inputs: Array = [UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])]
			# JSON数值经正式unpack/pack规范化，避免int/float假差异。
			check([replay_inputs[0].pack(),replay_inputs[1].pack()]==record.frames[index],label+"/输入规范化/%s"%index)
			replay.step(replay_inputs)
			check(observe(replay)==rows[index],label+"/独立回放逐tick状态事件弹体/%s"%index)
		check(replay.state_hash()==loaded.final_hash,label+"/独立回放末hash")
	var old_fingerprint := before_isolation_fingerprint(sim)
	check(old_fingerprint!=sim.content_fingerprint,label+"/跨招隔离规则指纹变化")
	var compatibility: Dictionary = {"old_fingerprint":old_fingerprint,"actual_checked":false}
	if not legacy_directory.is_empty():
		var old_path := legacy_directory.path_join(label+"-replay.json")
		var old := UfeReplayRecorder.read_candidate(old_path)
		check(old!=null,label+"/真实修前文件可解析")
		if old!=null:
			compatibility.actual_checked=true
			check(old.fingerprint==old_fingerprint,label+"/真实修前文件确属方向2无隔离基线")
			check(old.frames.size()==record.frames.size(),label+"/修前后原输入帧数相同")
			var same_input := old.frames.size()==record.frames.size()
			for index in range(mini(old.frames.size(),record.frames.size())):
				var old_pair: Array = old.frames[index]
				var normalized: Array = [UfeInputFrame.unpack(old_pair[0]).pack(),UfeInputFrame.unpack(old_pair[1]).pack()]
				same_input=same_input and normalized==record.frames[index]
			check(same_input,label+"/修前后双方原输入完全相同")
			compatibility.same_input=same_input
			compatibility.actual_rejected=UfeReplayRecorder.load_file(old_path,sim.content_fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放"
			check(compatibility.actual_rejected,label+"/真实修前回放按新规则明确拒绝")
		var old_trace: Variant = JSON.parse_string(FileAccess.get_file_as_string(legacy_directory.path_join(label+"-trace.json")))
		check(old_trace is Dictionary and old_trace.get("rows",[]).size()==rows.size(),label+"/真实修前逐tick轨迹可读")
		if old_trace is Dictionary and old_trace.get("rows",[]).size()==rows.size():
			var changed_ticks: Array = []
			for index in range(rows.size()):
				if str(old_trace.rows[index].hash)!=str(rows[index].hash):changed_ticks.append(index+1)
			compatibility.changed_hash_ticks=changed_ticks
			if mode=="crouch":check(changed_ticks.is_empty(),label+"/无接触蹲避对照逐tickhash保持")
			# 延迟对照允许idle.connected旧残留清除引起hash变化；不冒称无关状态逐位相同。
	var summary: Dictionary = {"case":label,"shooter":shooter,"target":target,"mode":mode,
		"second_input_tick":second_tick,"fingerprint":sim.content_fingerprint,"final_hash":sim.state_hash(),
		"starts":starts,"births":births,"contacts":contacts,"old_contact_during_startup":old_contact_during_startup,
		"second_active_frames":second_active_frames,"receiver_hp":sim.fighters[1-shooter].stats.hp,"compatibility":compatibility}
	summaries.append(summary)
	write_json(out+label+"-trace.json",{"initial":initial,"summary":summary,"rows":rows})

func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--test-out="):out=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
		if argument.begins_with("--legacy-dir="):legacy_directory=argument.trim_prefix("--legacy-dir=")
	DirAccess.make_dir_recursive_absolute(out)
	for shooter in [0,1]:
		for mode in ["neutral","guard","crouch"]:test_case(shooter,mode)
		test_case(shooter,"neutral",65)
	check(summaries.size()==8,"八组真实输入路径全部执行")
	write_json(out+"summary.json",{"failures":failures,"cases":summaries})
	print("PROJECTILE_MOVE_ISOLATION_RESULT "+JSON.stringify({"failures":failures,"cases":summaries.size()}))
	quit(0 if failures.is_empty() else 1)
