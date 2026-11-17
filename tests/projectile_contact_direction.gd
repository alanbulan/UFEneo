extends SceneTree
## 正式杰顿Q蓄能→I脸部火球→收招后↙I瞬移，初代只保持中立或U。
## 只初始化双方站位/朝向；不赋能量、硬直、弹体，不更改任何角色数据。
## 回放按相同站位fixture重建，不冒称默认470/750起点的普通录像。
var out := "user://projectile-contact-direction/"
var failures: Array = []
var summaries: Array = []
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("PROJECTILE_CONTACT_DIRECTION_FAIL "+label)
func write_json(path: String, value: Variant) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	check(file!=null,"写证据/"+path)
	if file!=null:file.store_string(JSON.stringify(value,"\t",true)+"\n")
func fixture(facing: int) -> UfeMatchDirector:
	var sim:=UfeContentDatabase.match_for("zetton","ultraman")
	sim.fighters[0].x=400 if facing>0 else 880
	sim.fighters[1].x=780 if facing>0 else 500
	sim.fighters[0].facing=facing
	sim.fighters[1].facing=-facing
	return sim
func observe(sim: UfeMatchDirector) -> Dictionary:
	var pair: Array=[]
	for f in sim.fighters:
		pair.append({"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"hp":f.stats.hp,"energy":f.stats.energy,"stamina":f.stats.stamina,"vy":f.vy,"vx":f.vx})
	return {"tick":sim.tick,"hash":sim.state_hash(),"hitstop":sim.hitstop,"pair":pair,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)}
func legacy_fingerprint(sim: UfeMatchDirector) -> String:
	# 与当前同一角色/招式/追击规则，只缺本轮弹体接触方向规则项。
	var forms: Array=[]
	for f in sim.fighters:forms.append(UfeBattleTransform.simulation_data(f.battle_form))
	var data: Array=[6,60,sim.rules.simulation_data(),sim.fighters[0].definition.simulation_data(),sim.fighters[1].definition.simulation_data(),forms,["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION],["hit_pushback_bounds",UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],["throw_target_air",UfeHitResolver.THROW_TARGET_RULE_REVISION],["chase_interrupt",UfeMatchDirector.CHASE_INTERRUPT_RULE_REVISION]]
	if UfeThrowResolver.RootOffsets.used_in(data):data.append(["throw_root_overrides",UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION])
	if UfeThrowResolver.CurrentCapture.used_in(data):data.append(["throw_current_capture",UfeThrowResolver.CurrentCapture.REVISION])
	return JSON.stringify(data,"",true).sha256_text()
func test_case(facing: int, crossing: bool, guard: bool) -> void:
	var label: String=("cross" if crossing else "front")+"-"+("guard" if guard else "neutral")+"-%s"%facing
	var sim:=fixture(facing)
	var record:=UfeReplayRecorder.new()
	var rows: Array=[]
	var phase: String="charge"
	var fired:=false
	var jumped_side:=false
	var charged:=false
	var charge_ticks:=0
	var pulse_start: int=-1
	var teleport_tick: int=-1
	var first_hand_tick: int=-1
	var pulse_contact: Dictionary={}
	for tick in range(200):
		var a:=sim.fighters[0]
		var first:=UfeInputFrame.make()
		if phase=="charge":
			if int(a.stats.energy)<100:
				first=UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
				charge_ticks+=1
			else:
				charged=true
				phase="release"
		elif phase=="release" and a.state=="idle":
			first=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
			fired=true
			pulse_start=sim.tick+1
			phase="recover"
		elif phase=="recover" and crossing and a.state=="idle" and a.move_id.is_empty():
			first=UfeInputFrame.make(-facing,-1,UfeInputFrame.RANGED)
			jumped_side=true
			phase="done"
		var inputs: Array=[first,UfeInputFrame.make(0,0,UfeInputFrame.GUARD if guard else 0)]
		var before:=observe(sim)
		sim.step(inputs)
		record.append(inputs,sim)
		var after:=observe(sim)
		rows.append(after)
		for event in sim.events:
			if event.kind=="teleport" and int(event.player)==0:teleport_tick=sim.tick
			if event.kind in ["hit","block"] and int(event.player)==0:
				if str(event.move)=="motion_214" and first_hand_tick<0:first_hand_tick=sim.tick
				if str(event.move)=="pulse" and pulse_contact.is_empty():
					pulse_contact={"event":event.duplicate(true),"before":before,"after":after,"relative_tick":sim.tick-pulse_start+1}
	check(charged and charge_ticks>0 and fired,label+"/真实Q付足瞬移能量后I发球")
	check(jumped_side==crossing and (teleport_tick>0)==crossing,label+"/真实后H瞬移或未越身对照")
	check(not pulse_contact.is_empty(),label+"/正式火球真实接触")
	if not pulse_contact.is_empty():
		var event: Dictionary=pulse_contact.event
		var before: Dictionary=pulse_contact.before
		var after: Dictionary=pulse_contact.after
		var expected_block:=guard and not crossing
		check(bool(event.projectile) and str(event.kind)==("block" if expected_block else "hit"),label+"/防御只挡来自正面的火球")
		check(first_hand_tick<0 or first_hand_tick>int(after.tick),label+"/首火球接触早于瞬移手刀，排除近战干扰")
		var shots: Array=before.projectiles.filter(func(p):return str(p.move)=="pulse")
		check(shots.size()==1 and int(shots[0].facing)==facing,label+"/离手火球保持真实方向")
		if crossing:
			check(teleport_tick<int(after.tick) and int(before.pair[0].facing)==-facing and int(before.pair[1].facing)==facing,label+"/接触前射手已越身反向且受方朝射手")
		if str(event.kind)=="hit":
			var push_speed := int(sim.fighters[0].definition.moves.pulse.pushback)
			check(int(after.pair[1].x)-int(before.pair[1].x)==facing*push_speed,label+"/击退沿火球方向滑出初速")
			check(int(after.pair[1].facing)==-facing,label+"/受击朝向真实来弹侧")
			check(int(before.pair[1].hp)-int(after.pair[1].hp)==65,label+"/保持正式65伤害")
		elif expected_block:
			check(int(before.pair[1].hp)==int(after.pair[1].hp),label+"/正常前防无伤害")
	var replay_path:=out+label+"-replay.json"
	check(record.save_file(replay_path)==OK,label+"/真实原输入保存")
	var loaded:=UfeReplayRecorder.load_file(replay_path,sim.content_fingerprint)
	check(loaded!=null,label+"/正式loader载入")
	var replay:=fixture(facing)
	if loaded!=null:
		for index in range(loaded.frames.size()):
			var pair: Array=loaded.frames[index]
			replay.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
			check(observe(replay)==rows[index],label+"/独立回放逐tick状态事件弹体/%s"%index)
		check(replay.state_hash()==loaded.final_hash,label+"/回放末hash")
	var old:=legacy_fingerprint(sim)
	check(old!=sim.content_fingerprint,label+"/方向规则指纹变化")
	record.fingerprint=old
	var old_path:=out+label+"-old-rule.json"
	check(record.save_file(old_path)==OK,label+"/旧规则指纹夹具保存")
	check(UfeReplayRecorder.load_file(old_path,sim.content_fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放",label+"/旧规则明确拒绝")
	var result: Dictionary={"old_fingerprint":old,"case":label,"charge_ticks":charge_ticks,"pulse_start_tick":pulse_start,"teleport_tick":teleport_tick,"first_hand_tick":first_hand_tick,"pulse_contact":pulse_contact,"fingerprint":sim.content_fingerprint,"final_hash":sim.state_hash()}
	summaries.append(result)
	write_json(out+label+"-trace.json",{"setup":{"fighters":["zetton","ultraman"],"facing":facing,"crossing":crossing,"guard":guard,"ticks":200},"summary":result,"rows":rows})
func resolver_units() -> void:
	# 底层方向参数单元：采用正式艾斯垂直断头刀数据；不作为真实越身路径证据。
	for direction in [1,-1]:
		var sim:=UfeContentDatabase.match_for("ultraman-ace","ultraman")
		var a:=sim.fighters[0]
		var b:=sim.fighters[1]
		a.x=600+direction*100
		a.facing=-direction
		b.x=600
		var move: Dictionary=a.definition.moves.motion_623
		check(str(move.kind)=="projectile" and bool(move.launch),"底层单元/正式艾斯挑空弹体数据")
		var result:=UfeHitResolver.apply(a,b,move,false,sim.rules,direction)
		check(result=="hit" and b.state=="launch" and b.vx==direction*2 and b.facing==-direction,"底层单元/弹体挑空vx与来向/%s"%direction)
		check(a.facing==-direction,"底层单元/不临时或永久改射手朝向/%s"%direction)
		var first:=fixture(direction)
		var second:=fixture(direction)
		var melee: Dictionary=first.fighters[0].definition.moves.launcher
		UfeHitResolver.apply(first.fighters[0],first.fighters[1],melee,false,first.rules)
		UfeHitResolver.apply(second.fighters[0],second.fighters[1],melee,false,second.rules,0)
		check(first.state_hash()==second.state_hash(),"底层单元/省略参数与显式0的近战状态逐位一致/%s"%direction)
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--test-out="):out=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(out)
	resolver_units()
	for facing in [1,-1]:
		for crossing in [false,true]:
			for guard in [false,true]:test_case(facing,crossing,guard)
	check(summaries.size()==8,"八组正式用例全部实际执行")
	write_json(out+"summary.json",{"failures":failures,"cases":summaries})
	print("PROJECTILE_CONTACT_DIRECTION_RESULT "+JSON.stringify({"failures":failures,"cases":summaries}))
	quit(0 if failures.is_empty() else 1)
