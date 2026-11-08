extends SceneTree
## 只用正式角色与原InputFrame。初始站位/朝向fixture外不赋模拟状态。
## 杰顿Q→I→↙I→跳；雷德王N避开瞬移手刀→↙I投岩。
var out := "user://projectile-air-knockdown-direction/"
var failures: Array = []
var results: Array = []
var legacy_directory := ""
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("AIR_KNOCKDOWN_FAIL "+label)
func write_json(path: String, value: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null: file.store_string(JSON.stringify(value,"\t",true)+"\n")
func fixture(direction: int, gap: int, rock_fighter: String) -> UfeMatchDirector:
	var sim := UfeContentDatabase.match_for("zetton",rock_fighter)
	sim.fighters[0].x = 250 if direction > 0 else 1030
	sim.fighters[1].x = sim.fighters[0].x + direction * gap
	sim.fighters[0].facing = direction
	sim.fighters[1].facing = -direction
	return sim
func observe(sim: UfeMatchDirector) -> Dictionary:
	var pair: Array = []
	for f in sim.fighters:
		pair.append({"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"hp":f.stats.hp,"energy":f.stats.energy,"stamina":f.stats.stamina,"vx":f.vx,"vy":f.vy})
	return {"tick":sim.tick,"hash":sim.state_hash(),"hitstop":sim.hitstop,"pair":pair,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)}
func revision_one_fingerprint(sim: UfeMatchDirector) -> String:
	# 当前招式/其它规则不变，唯独方向revision=1；只是明确标注的负面夹具。
	var forms: Array=[]
	for f in sim.fighters:forms.append(UfeBattleTransform.simulation_data(f.battle_form))
	var data: Array=[6,60,sim.rules.simulation_data(),sim.fighters[0].definition.simulation_data(),sim.fighters[1].definition.simulation_data(),forms,["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION],["hit_pushback_bounds",UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],["throw_target_air",UfeHitResolver.THROW_TARGET_RULE_REVISION],["chase_interrupt",UfeMatchDirector.CHASE_INTERRUPT_RULE_REVISION],["projectile_contact_direction",1]]
	if UfeThrowResolver.RootOffsets.used_in(data):data.append(["throw_root_overrides",UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION])
	if UfeThrowResolver.CurrentCapture.used_in(data):data.append(["throw_current_capture",UfeThrowResolver.CurrentCapture.REVISION])
	return JSON.stringify(data,"",true).sha256_text()
func case_run(direction: int, gap: int, rock_fighter: String, attack_tick: int, jump_tick: int, default_start: bool=false) -> void:
	var label := "%s-gap%d-attack%d-jump%d-dir%d" % [rock_fighter,gap,attack_tick,jump_tick,direction]
	if default_start:label+="-default-walk"
	var sim := UfeContentDatabase.match_for("zetton",rock_fighter) if default_start else fixture(direction,gap,rock_fighter)
	var rock_move: Dictionary=sim.fighters[1].definition.moves.motion_214
	check(str(rock_move.kind)=="projectile" and bool(rock_move.knockdown) and not bool(rock_move.launch) and not bool(rock_move.bounce),label+"/现装投岩明确走knockdown非launch分支")
	var recorder := UfeReplayRecorder.new()
	var rows: Array = []
	var contacts: Array = []
	var phase := "charge"
	var charge_ticks := 0
	var command_evidence: Dictionary={}
	if default_start:
		# 默认470/750：真实后走68/69tick到334/888，再中立4tick；不赋位置/状态。
		for pre in range(73):
			var pair: Array=[UfeInputFrame.make(-1 if pre<68 else 0,0,0),UfeInputFrame.make(1 if pre<69 else 0,0,0)]
			sim.step(pair)
			recorder.append(pair,sim)
			rows.append(observe(sim))
		if sim.fighters[0].x!=334 or sim.fighters[1].x!=888:failures.append(label+"/真实后走未到预期站位")
	for t in range(1,201):
		var a := sim.fighters[0]
		var first := UfeInputFrame.make()
		var second := UfeInputFrame.make()
		if phase == "charge":
			if int(a.stats.energy) < 100: first=UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
			else: phase="release"
		elif phase == "release" and a.state == "idle":
			first=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
			phase="recover"
		elif phase == "recover" and a.state == "idle" and a.move_id.is_empty():
			first=UfeInputFrame.make(-direction,-1,UfeInputFrame.RANGED)
			phase="done"
		if jump_tick>0 and t >= jump_tick and t < jump_tick + 3: first=UfeInputFrame.make(direction,1,0)
		if t == 80: second=UfeInputFrame.make(0,0,UfeInputFrame.DODGE)
		if t == attack_tick: second=UfeInputFrame.make(-direction,-1,UfeInputFrame.RANGED)
		var before := observe(sim)
		var inputs: Array = [first,second]
		sim.step(inputs)
		recorder.append(inputs,sim)
		var after := observe(sim)
		if first.held(UfeInputFrame.CHARGE):charge_ticks+=1
		if first.held(UfeInputFrame.RANGED) and first.x==0:
			command_evidence.pulse={"tick":sim.tick,"before":before.pair[0],"after":after.pair[0]}
			check(a.move_id=="pulse",label+"/真实I启动火球")
		if first.held(UfeInputFrame.RANGED) and first.x!=0:
			command_evidence.teleport={"tick":sim.tick,"before":before.pair[0],"after":after.pair[0]}
			check(a.move_id=="motion_214" and int(before.pair[0].energy)-int(after.pair[0].energy)==100,label+"/真实↙I扣100能量")
		if second.held(UfeInputFrame.DODGE):
			command_evidence.dodge={"tick":sim.tick,"after":after.pair[1]}
			check(sim.fighters[1].state=="dodge",label+"/真实N进入闪避")
		if second.held(UfeInputFrame.RANGED) and second.x!=0:
			command_evidence.rock={"tick":sim.tick,"before":before.pair[1],"after":after.pair[1]}
			check(sim.fighters[1].move_id=="motion_214" and int(before.pair[1].stamina)-int(after.pair[1].stamina)==50,label+"/真实↙I投岩扣50体力")
		rows.append(after)
		for event in sim.events:
			if event.kind in ["hit","block","teleport","move_denied"]:
				var entry: Dictionary={"event":event.duplicate(true),"before":before,"after":after}
				contacts.append(entry)
				print("AIR_KNOCKDOWN_CONTACT "+JSON.stringify({"case":label,"tick":t,"event":event,"pair":after.pair}))
	var replay_path := out+label+"-replay.json"
	var replay_ok := recorder.save_file(replay_path)==OK
	var loaded := UfeReplayRecorder.load_file(replay_path,sim.content_fingerprint)
	replay_ok = replay_ok and loaded != null
	if loaded != null:
		var replay := UfeContentDatabase.match_for("zetton",rock_fighter) if default_start else fixture(direction,gap,rock_fighter)
		for i in range(loaded.frames.size()):
			var inputs: Array=loaded.frames[i]
			replay.step([UfeInputFrame.unpack(inputs[0]),UfeInputFrame.unpack(inputs[1])])
			if observe(replay)!=rows[i]:replay_ok=false
		replay_ok=replay_ok and replay.state_hash()==loaded.final_hash
	var defects: Array=[]
	var rock_contacts: Array=[]
	for contact in contacts:
		var event: Dictionary=contact.event
		if event.kind!="hit" or int(event.player)!=1 or str(event.move)!="motion_214" or not bool(event.projectile):continue
		rock_contacts.append(contact)
		if int(contact.after.pair[0].height)<=0:continue
		var shots: Array=contact.after.projectiles.filter(func(p):return int(p.owner)==1 and str(p.move)=="motion_214")
		check(shots.size()==1,label+"/命中时唯一真实离手岩块存在")
		if shots.is_empty():continue
		var shot_direction:=int(shots[0].facing)
		check(shot_direction==direction,label+"/岩块保持发射方向")
		check(str(contact.after.pair[0].state)=="launch" and int(contact.after.pair[0].vy)<=-6 and int(contact.before.pair[0].hp)-int(contact.after.pair[0].hp)==100,label+"/正式100伤空中击倒分支")
		check(int(contact.after.pair[0].facing)==-direction,label+"/受方朝向真实来弹侧")
		if jump_tick==107:
			check(int(contact.after.pair[1].facing)==-direction,label+"/旧火球将射手转向离手岩块反方向")
			var hit_events: Array=contact.after.events.filter(func(e):return e.kind=="hit")
			check(hit_events.size()==2 and str(hit_events[0].move)=="pulse" and str(hit_events[1].move)=="motion_214",label+"/同tick先旧火球后投岩真实互击")
		else:check(int(contact.after.pair[1].facing)==direction,label+"/未翻面对照射手仍同向")
		if int(contact.after.pair[0].vx)!=shot_direction*2:
			defects.append({"tick":int(contact.after.tick),"shot_facing":shot_direction,"shooter_facing":int(contact.after.pair[1].facing),"receiver_vx":int(contact.after.pair[0].vx),"receiver_height":int(contact.after.pair[0].height)})
	if rock_contacts.size()!=1:failures.append(label+"/正式投岩未恰好命中一次")
	elif jump_tick>0 and int(rock_contacts[0].after.pair[0].height)<=0:failures.append(label+"/真实跳跃未在空中被岩块命中")
	elif jump_tick==0 and (int(rock_contacts[0].after.pair[0].height)!=0 or str(rock_contacts[0].after.pair[0].state)!="down"):failures.append(label+"/地面对照未正常倒地")
	check(defects.is_empty(),label+"/空中击倒水平速度必须等于离手岩块方向乘2")
	check(charge_ticks>0 and command_evidence.size()==4,label+"/Q蓄能与I/↙I/N/↙I全部真实输入")
	var compatibility: Dictionary={}
	if UfeHitResolver.PROJECTILE_DIRECTION_RULE_REVISION>1:
		var v1:=revision_one_fingerprint(sim)
		check(v1!=sim.content_fingerprint,label+"/方向revision1与当前指纹不同")
		recorder.fingerprint=v1
		var negative_path:=out+label+"-synthetic-revision1.json"
		check(recorder.save_file(negative_path)==OK,label+"/保存明确标注的revision1负面夹具")
		compatibility.synthetic_rejected=UfeReplayRecorder.load_file(negative_path,sim.content_fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放"
		check(bool(compatibility.synthetic_rejected),label+"/正式loader拒绝revision1负面夹具")
		if not legacy_directory.is_empty():
			var actual_path:=legacy_directory.path_join(label+"-replay.json")
			var actual:=UfeReplayRecorder.read_candidate(actual_path)
			check(actual!=null,label+"/读取真正修前录像")
			if actual!=null:
				# 两份都经正式JSON loader读取，避免内存int与JSON数值类型差异误报。
				compatibility.actual_same_inputs=loaded!=null and actual.frames==loaded.frames
				compatibility.actual_revision1=actual.fingerprint==v1
				compatibility.actual_rejected=UfeReplayRecorder.load_file(actual_path,sim.content_fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放"
				check(bool(compatibility.actual_same_inputs) and bool(compatibility.actual_revision1) and bool(compatibility.actual_rejected),label+"/真实修前录像同输入并由正式loader拒绝")
				if jump_tick in [0,101]:
					compatibility.unaffected_control_hash=actual.final_hash==sim.state_hash()
					check(bool(compatibility.unaffected_control_hash),label+"/未翻面及地面对照修前后末hash不变")
	var result: Dictionary={"case":label,"default_start":default_start,"defects":defects,"charge_ticks":charge_ticks,"command_evidence":command_evidence,"compatibility":compatibility,"independent_replay":replay_ok,"contacts":contacts,"fingerprint":sim.content_fingerprint,"final_hash":sim.state_hash()}
	results.append(result)
	write_json(out+label+"-trace.json",{"setup":{"fighters":["zetton",rock_fighter],"direction":direction,"gap":gap,"attack_tick":attack_tick,"jump_tick":jump_tick,"default_start":default_start,"scenario_ticks":200,"ticks":rows.size()},"result":result,"rows":rows})
	if not replay_ok:failures.append(label+"/独立回放不一致")
	print("AIR_KNOCKDOWN_CASE "+JSON.stringify({"case":label,"defects":defects,"independent_replay":replay_ok}))
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--test-out="):out=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
		if argument.begins_with("--legacy-dir="):legacy_directory=argument.trim_prefix("--legacy-dir=")
	DirAccess.make_dir_recursive_absolute(out)
	for direction in [1,-1]:
		for gap in [553,554]:case_run(direction,gap,"red_king",91,107)
	case_run(1,554,"red_king",91,107,true)
	case_run(1,610,"red_king",91,101)
	case_run(1,554,"red_king",91,0)
	check(results.size()==7,"七组真实输入场景均实际完成")
	write_json(out+"summary.json",{"failures":failures,"cases":results})
	quit(0 if failures.is_empty() else 1)
