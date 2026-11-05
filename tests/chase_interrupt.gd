extends SceneTree
## 集成用例仅初始化站位；升击、互击与跳跃均由正式输入/真实判定产生。
## 状态入口单元单独标注，不作为真实互击复现的替代。
var out := "user://chase-interrupt/"
var failures: Array = []
var summary: Array = []
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("CHASE_INTERRUPT_FAIL "+label)
func fixture(facing: int, kind: String) -> UfeMatchDirector:
	var sim := UfeContentDatabase.match_for("ultraman","ultraman")
	var left:=300 if kind=="whiff" else 540
	var right:=980 if kind=="whiff" else 600
	sim.fighters[0].x=left if facing>0 else right
	sim.fighters[1].x=right if facing>0 else left
	sim.fighters[0].facing=facing
	sim.fighters[1].facing=-facing
	return sim
func observe(sim: UfeMatchDirector) -> Dictionary:
	var pair: Array=[]
	for f in sim.fighters:
		pair.append({"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"height":f.height,"vy":f.vy,"hp":f.stats.hp,"window":f.motion.chase_window,"confirmed":f.combat.confirmed,"jump_kind":f.motion.jump_kind})
	return {"tick":sim.tick,"hash":sim.state_hash(),"hitstop":sim.hitstop,"pair":pair,"events":sim.events.duplicate(true)}
func write_json(path: String, value: Variant) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	check(file!=null,"写入证据/"+path)
	if file!=null:file.store_string(JSON.stringify(value,"\t",true)+"\n")
func fingerprint_without_chase_rule(sim: UfeMatchDirector) -> String:
	# 人工负面夹具：从当前规则构成只移除chase_interrupt项，保留全部弹体项；不是历史版本指纹。
	var forms: Array=[]
	for f in sim.fighters:forms.append(UfeBattleTransform.simulation_data(f.battle_form))
	var data: Array=[6,60,sim.rules.simulation_data(),sim.fighters[0].definition.simulation_data(),sim.fighters[1].definition.simulation_data(),forms,["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION],["hit_pushback_bounds",UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],["throw_target_air",UfeHitResolver.THROW_TARGET_RULE_REVISION],["projectile_contact_direction",UfeHitResolver.PROJECTILE_DIRECTION_RULE_REVISION],["projectile_move_isolation",UfeHitResolver.PROJECTILE_MOVE_ISOLATION_RULE_REVISION], ["projectile_beam_reflection", UfeProjectileResolver.BEAM_REFLECTION_RULE_REVISION]]
	if UfeThrowResolver.RootOffsets.used_in(data):data.append(["throw_root_overrides",UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION])
	if UfeThrowResolver.CurrentCapture.used_in(data):data.append(["throw_current_capture",UfeThrowResolver.CurrentCapture.REVISION])
	return JSON.stringify(data,"",true).sha256_text()
func test_case(facing: int, kind: String, jumper: int=0) -> void:
	var sim:=fixture(facing,kind)
	var recorder:=UfeReplayRecorder.new()
	var rows: Array=[]
	var sent_jump:=false
	var seen_launcher: Array=[false,false]
	var chased:=false
	var jump_row: Dictionary={}
	var trade:=kind.begins_with("trade")
	var trade_jump_sent:=false
	for tick in range(180):
		var inputs: Array=[UfeInputFrame.make(),UfeInputFrame.make()]
		if tick==0:
			inputs[0]=UfeInputFrame.make(facing,0,UfeInputFrame.HEAVY)
			if trade:inputs[1]=UfeInputFrame.make(-facing,0,UfeInputFrame.HEAVY)
		var f:=sim.fighters[jumper]
		var ready: bool=seen_launcher[0] and (not trade or seen_launcher[1]) and sim.hitstop==0
		if kind=="late":ready=ready and f.move_id.is_empty() and int(f.motion.chase_window)>0
		elif kind=="expired":ready=ready and tick>40 and int(f.motion.chase_window)==0
		elif kind=="whiff":ready=tick==40
		elif kind=="trade_stop":ready=seen_launcher[0] and seen_launcher[1] and sim.hitstop>0
		elif kind=="trade_recovered":
			# 先在真实硬直中试跳，随后不再输入；等自然落地/倒地/起身完成再按新跳键。
			if ready and not trade_jump_sent:
				inputs[jumper]=UfeInputFrame.make(0,1,UfeInputFrame.JUMP)
				trade_jump_sent=true
			ready=trade_jump_sent and tick>50 and f.state=="idle" and f.height==0
		if ready and not sent_jump:
			jump_row.before=observe(sim)
			inputs[jumper]=UfeInputFrame.make(0,1,UfeInputFrame.JUMP)
			sent_jump=true
		sim.step(inputs)
		recorder.append(inputs,sim)
		rows.append(observe(sim))
		for event in sim.events:
			if event.kind=="hit" and event.move=="launcher":seen_launcher[int(event.player)]=true
		if sent_jump and not jump_row.has("after") and sim.hitstop==0 and (kind!="trade_stop" or f.state_tick>0):
			jump_row.after=observe(sim)
			chased=f.motion.jump_kind=="chase"
		if trade and seen_launcher[0] and seen_launcher[1]:
			check(sim.fighters[0].motion.chase_window==0 and sim.fighters[1].motion.chase_window==0,"互击双方窗口立即失效/%s/%s/%s"%[kind,facing,tick])
	var label: String=kind+"-%s-p%s"%[facing,jumper]
	check(seen_launcher[0]==(kind!="whiff") and (not trade or seen_launcher[1]),label+"/真实升击命中或落空")
	check(sent_jump and jump_row.has("after"),label+"/真实跳键送入并推进")
	check(chased==(kind in ["normal","late"]),label+"/只允许未中断合法追击")
	if kind in ["trade","trade_stop"]:
		check(jump_row.after.pair[jumper].state=="launch",label+"/跳键不取消真实挑空硬直")
	if kind in ["trade_recovered","expired","whiff"]:
		check(jump_row.after.pair[jumper].state=="takeoff" and jump_row.after.pair[jumper].jump_kind=="vertical",label+"/恢复后只能正常跳")
	var path:=out+label+"-replay.json"
	check(recorder.save_file(path)==OK,label+"/原输入回放保存")
	var loaded:=UfeReplayRecorder.load_file(path,sim.content_fingerprint)
	check(loaded!=null,label+"/当前指纹回放载入")
	var replay:=fixture(facing,kind)
	if loaded!=null:
		for i in range(loaded.frames.size()):
			var pair: Array=loaded.frames[i]
			replay.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
			check(observe(replay)==rows[i],label+"/独立回放逐tick状态事件 %s"%i)
		check(replay.state_hash()==loaded.final_hash,label+"/回放末hash")
	var old:=fingerprint_without_chase_rule(sim)
	check(old!=sim.content_fingerprint,label+"/移除追击规则项后指纹不同")
	recorder.fingerprint=old
	var old_path:=out+label+"-missing-chase-rule.json"
	check(recorder.save_file(old_path)==OK,label+"/缺追击规则项的人工指纹夹具保存")
	check(UfeReplayRecorder.load_file(old_path,sim.content_fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放",label+"/缺追击规则项的人工指纹夹具明确拒绝")
	var result: Dictionary={"case":label,"jump":jump_row,"chased":chased,"hits":seen_launcher,"hash":sim.state_hash(),"fingerprint":sim.content_fingerprint,"missing_chase_fingerprint":old}
	summary.append(result)
	write_json(out+label+"-trace.json",{"summary":result,"rows":rows})
func state_entry_units() -> void:
	# 明确为底层入口单元：直接设置窗口覆盖所有中断入口；真实整段另见以上互击。
	var sim:=fixture(1,"normal")
	var f:=sim.fighters[0]
	for state in ["hit","launch","bounce","down","thrown","captured","blockstun","crouch_blockstun","guardbreak","stun","burst","transform","form_entry","defeat","victory","timeout"]:
		f.motion.chase_window=24
		f.enter(state)
		check(f.motion.chase_window==0 and not f.chase_allowed(),"入口单元/中断清追击/"+state)
	f.enter("attack")
	f.motion.chase_window=12
	f.clear_move()
	f.enter("idle")
	check(f.motion.chase_window==12 and f.chase_allowed(),"入口单元/自然收招保留未中断窗口")
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--test-out="): out=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(out)
	state_entry_units()
	for facing in [1,-1]:
		for kind in ["normal","late","expired","whiff"]:test_case(facing,kind)
		for jumper in [0,1]:
			for kind in ["trade","trade_stop","trade_recovered"]:test_case(facing,kind,jumper)
	write_json(out+"summary.json",{"failures":failures,"cases":summary})
	print("CHASE_INTERRUPT_RESULT "+JSON.stringify({"failures":failures,"cases":summary}))
	quit(0 if failures.is_empty() else 1)
