extends SceneTree
var failed: Array[String] = []
func check(condition: bool, title: String) -> void:
	if not condition:
		failed.append(title)
		printerr("FAIL: "+title)

func neutral() -> UfeInputFrame:
	return UfeInputFrame.make()

func advance(sim: UfeMatchDirector, count: int) -> void:
	for i in range(count): sim.step([neutral(),neutral()])

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var sim := UfeContentDatabase.match_for()
	var copy := UfeContentDatabase.match_for()
	var record := UfeReplayRecorder.new()
	var computers: Array=[UfeComputerController.new(301,"normal",0),UfeComputerController.new(301,"normal",1)]
	for i in range(1800):
		var inputs := [computers[0].sample(sim),computers[1].sample(sim)]
		sim.step(inputs)
		copy.step(inputs)
		record.append(inputs,sim)
		check(sim.state_hash()==copy.state_hash(),"同输入每 tick 确定性")
	record.save_file("user://logic-replay.json")
	var loaded := UfeReplayRecorder.load_file("user://logic-replay.json",sim.content_fingerprint)
	check(loaded != null and UfeReplayRecorder.FORMAT==6,"格式6回放载入")
	var replay_sim := UfeContentDatabase.match_for()
	if loaded != null:
		for pair in loaded.frames: replay_sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
		check(replay_sim.state_hash()==loaded.final_hash,"回放还原所有模拟状态")
	check(UfeReplayRecorder.load_file("user://logic-replay.json","changed")==null,"内容指纹不同拒绝回放")
	var old := FileAccess.open("user://old-replay.json",FileAccess.WRITE)
	old.store_string('{"format":3}')
	old.close()
	check(UfeReplayRecorder.load_file("user://old-replay.json",sim.content_fingerprint)==null and UfeReplayRecorder.last_error.contains("旧回放"),"旧格式明确提示")
	var definition := sim.fighters[0].definition
	for move in definition.moves.values(): check(UfeMoveData.validate(move),"逐帧数据合法："+str(move.id))
	var signatures := {}
	for entry in definition.command_table:
		check(definition.moves.has(entry.move),"招式表资源存在")
		for state in entry.states:
			for direction in entry.directions:
				var key := str([state,direction,entry.buttons,entry.motion,entry.priority])
				check(not signatures.has(key),"同优先级输入唯一："+key)
				signatures[key] = true
	var resolver := UfeCommandResolver.new()
	resolver.resolve(UfeInputFrame.make(0,-1),1,"idle",definition.command_table)
	resolver.resolve(UfeInputFrame.make(1,-1),1,"idle",definition.command_table)
	var result := resolver.resolve(UfeInputFrame.make(1,0,1),1,"idle",definition.command_table)
	check(result.move=="motion_236","236 优先于方向普通技")
	resolver = UfeCommandResolver.new()
	resolver.resolve(UfeInputFrame.make(0,0,1),1,"idle",definition.command_table)
	resolver.resolve(UfeInputFrame.make(0,0,1),1,"idle",definition.command_table)
	result = resolver.resolve(UfeInputFrame.make(0,0,3),1,"light1",definition.command_table)
	check(result.move=="special","3 tick 同时按与必杀优先级")
	resolver = UfeCommandResolver.new()
	result = resolver.resolve(UfeInputFrame.make(-1,0,2),-1,"idle",definition.command_table)
	check(result.move=="launcher","面向左时的相对前输入")
	sim = UfeContentDatabase.match_for()
	sim.fighters[0].x = 540
	sim.fighters[1].x = 600
	sim.step([UfeInputFrame.make(0,0,1),neutral()])
	advance(sim,7)
	check(sim.fighters[1].stats.hp < 1000,"攻击在实际攻击框重叠时命中")
	var hp: int = sim.fighters[1].stats.hp
	advance(sim,5)
	check(sim.fighters[1].stats.hp==hp,"命中停顿不重复结算")
	sim.step([UfeInputFrame.make(0,0,1),neutral()])
	check(sim.fighters[0].combat.buffer=="light2" or sim.fighters[0].move_id=="light2","命中停顿接收连段缓冲")
	advance(sim,8)
	check(sim.fighters[0].move_id=="light2","确认命中才取消接第二段")
	sim = UfeContentDatabase.match_for()
	sim.fighters[0].x=540
	sim.fighters[1].x=600
	for i in range(12): sim.step([UfeInputFrame.make(0,0,1 if i==0 else 0),UfeInputFrame.make(0,0,8)])
	check(sim.fighters[1].stats.hp==1000,"站立防御中段")
	check(not sim.fighters[0].combat.confirmed,"防御不提供命中取消")
	sim = UfeContentDatabase.match_for()
	sim.step([UfeInputFrame.make(1,1),neutral()])
	advance(sim,45)
	check(sim.fighters[0].height==0 and sim.fighters[0].x>470,"斜跳有水平轨迹并落地")
	sim = UfeContentDatabase.match_for()
	sim.fighters[0].x=540
	sim.fighters[1].x=600
	sim.step([UfeInputFrame.make(1,0,2),neutral()])
	advance(sim,10)
	sim.step([UfeInputFrame.make(1,1),neutral()])
	advance(sim,7)
	check(sim.fighters[0].motion.jump_kind=="chase" and sim.fighters[0].height>0,"升击确认衔接追击跳")
	sim = UfeContentDatabase.match_for()
	sim.step([UfeInputFrame.make(0,0,32),neutral()])
	check(sim.fighters[0].move_id.is_empty(),"能量不足不可发动必杀")
	sim.fighters[0].stats.energy=3000
	sim.step([neutral(),neutral()])
	sim.step([UfeInputFrame.make(0,0,32),neutral()])
	check(sim.fighters[0].move_id=="special3" and sim.fighters[0].stats.energy==0 and sim.fighters[0].combat.power==1,"三级必杀使用独立数据并消耗三格")
	sim = UfeContentDatabase.match_for()
	sim.remaining = 1
	sim.step([neutral(),neutral()])
	check(sim.finished and sim.winner==-1,"时间到平局流程")
	var reverse := UfeContentDatabase.match_for("zetton","ultraman")
	check(reverse.fighters[0].definition.id=="zetton","导演接收任意两份角色定义")
	print("LOGIC_2D "+("PASS" if failed.is_empty() else "FAIL: "+str(failed)))
	quit(0 if failed.is_empty() else 1)
