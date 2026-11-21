extends SceneTree
const ContactEvent = preload("res://core/combat/contact_event.gd")
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
	var event_trace: Array = []
	var computers: Array=[UfeComputerController.new(301,"normal",0),UfeComputerController.new(301,"normal",1)]
	for i in range(1800):
		var inputs := [computers[0].sample(sim),computers[1].sample(sim)]
		sim.step(inputs)
		copy.step(inputs)
		record.append(inputs,sim)
		check(sim.state_hash()==copy.state_hash(),"同输入每 tick 确定性")
		check(sim.events == copy.events,"同输入每 tick 事件确定性")
		event_trace.append(sim.events.duplicate(true))
	record.save_file("user://logic-replay.json")
	var loaded := UfeReplayRecorder.load_file("user://logic-replay.json",sim.content_fingerprint)
	check(loaded != null and UfeReplayRecorder.FORMAT==6,"格式6回放载入")
	var replay_sim := UfeContentDatabase.match_for()
	var replay_event_trace: Array = []
	if loaded != null:
		for pair in loaded.frames:
			replay_sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
			replay_event_trace.append(replay_sim.events.duplicate(true))
		check(replay_sim.state_hash()==loaded.final_hash,"回放还原所有模拟状态")
		check(replay_event_trace == event_trace,"回放逐 tick 还原命中事件")
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
				check(not entry.has("motion"),"招式表不再保留搓招字段")
				var key := str([state,direction,entry.buttons,entry.priority])
				check(not signatures.has(key),"同优先级输入唯一："+key)
				signatures[key] = true
	var resolver := UfeCommandResolver.new()
	var result := resolver.resolve(UfeInputFrame.make(-1,0,UfeInputFrame.HEAVY),-1,"idle",definition.command_table)
	check(result.move=="launcher","面向左时的相对前输入")
	# 旧方向历史和J+K别名必须失效；保留技能ID不等于保留搓招入口。
	for facing in [-1,1]:
		for legacy in [[[2,3,6],UfeInputFrame.LIGHT],[[2,6],UfeInputFrame.LIGHT],[[6,2,3],UfeInputFrame.HEAVY],[[6,3,2,3],UfeInputFrame.HEAVY],[[3,2,3],UfeInputFrame.HEAVY],[[2,1,4],UfeInputFrame.RANGED],[[2,4],UfeInputFrame.RANGED],[[2,5,2],UfeInputFrame.CRUSH],[[4,1,2,3,6],UfeInputFrame.THROW]]:
			resolver = UfeCommandResolver.new()
			var directions: Array = legacy[0]
			for index in range(directions.size()):
				var direction := int(directions[index])
				var x := -1 if direction in [1,4,7] else 1 if direction in [3,6,9] else 0
				var y := -1 if direction in [1,2,3] else 1 if direction in [7,8,9] else 0
				result = resolver.resolve(UfeInputFrame.make(x*facing,y,int(legacy[1]) if index==directions.size()-1 else 0),facing,"idle",definition.command_table,3000)
			check(not str(result.move).begins_with("motion_"),"旧序列不再启动方向技能 "+str([legacy,facing]))
		for delayed in [false,true]:
			resolver = UfeCommandResolver.new()
			if delayed:
				resolver.resolve(UfeInputFrame.make(0,0,UfeInputFrame.LIGHT),facing,"idle",definition.command_table,3000)
			result = resolver.resolve(UfeInputFrame.make(0,0,UfeInputFrame.LIGHT|UfeInputFrame.HEAVY),facing,"light1" if delayed else "idle",definition.command_table,3000)
			check(not str(result.move).begins_with("special"),"同按/错开J+K不再启动P必杀")
	# 五个技能只用I+当前相对方向；上方向不跳，显式JUMP也不被技能吞掉。
	var quick := {"motion_236":[1,1],"motion_623":[1,-1],"motion_214":[-1,-1],"motion_41236":[-1,1],"motion_22":[0,1]}
	for facing in [-1,1]:
		for move in quick:
			var axes: Array = quick[move]
			for jump in [false,true]:
				resolver = UfeCommandResolver.new()
				result = resolver.resolve(UfeInputFrame.make(int(axes[0])*facing,int(axes[1]),UfeInputFrame.RANGED|(UfeInputFrame.JUMP if jump else 0)),facing,"idle",definition.command_table,9999)
				check(result.move==move and bool(result.jump)==jump,"I+方向双向直出且保留显式跳跃 "+str([move,facing,jump]))
		for x in [-1,0,1]:
			resolver = UfeCommandResolver.new()
			result = resolver.resolve(UfeInputFrame.make(x,1),facing,"idle",definition.command_table)
			check(not result.jump,"W/上方向本身不跳跃")
	check(resolver.snapshot().size()==6 and UfeCommandResolver.RULE_REVISION==6,"输入快照六字段与新规则版本")
	resolver = UfeCommandResolver.new()
	result = resolver.resolve(UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL),1,"idle",definition.command_table,3000)
	check(result.move=="special","独立P键解析为必杀入口，真实能量档位由启动层选择")
	resolver = UfeCommandResolver.new()
	result = resolver.resolve(UfeInputFrame.make(0,0,UfeInputFrame.GUARD|UfeInputFrame.THROW),1,"idle",definition.command_table,3000)
	check(result.move=="taunt","L+U独立挑衅保留")
	resolver = UfeCommandResolver.new()
	result = resolver.resolve(UfeInputFrame.make(0,0,UfeInputFrame.GUARD|UfeInputFrame.CHARGE),1,"hit",definition.command_table,3000)
	check(result.move=="burst","GUARD+CHARGE爆气保留")
	for probe in [["pulse",0,0,"idle"],["ranged_forward",1,0,"idle"],["pulse",-1,0,"idle"],["low_pulse",0,-1,"crouch"]]:
		resolver = UfeCommandResolver.new()
		result = resolver.resolve(UfeInputFrame.make(int(probe[1]),int(probe[2]),UfeInputFrame.RANGED),1,str(probe[3]),definition.command_table,9999)
		check(result.move==probe[0],"远程原招保留 "+str(probe[0]))
	sim = UfeContentDatabase.match_for()
	sim.fighters[0].x = 540
	sim.fighters[1].x = 600
	var hit_event: Dictionary = {}
	var hit_event_count: int = 0
	sim.step([UfeInputFrame.make(0,0,1),neutral()])
	if not sim.events.is_empty():
		hit_event = sim.events[0].duplicate(true)
		hit_event_count = sim.events.size()
	for i in range(7):
		sim.step([neutral(),neutral()])
		if not sim.events.is_empty():
			hit_event = sim.events[0].duplicate(true)
			hit_event_count = sim.events.size()
	check(sim.fighters[1].stats.hp < 1000,"攻击在实际攻击框重叠时命中")
	check(hit_event_count == 1 and ContactEvent.matches_contract(hit_event),"轻击命中输出稳定事件契约")
	check(hit_event.get("kind","") == "hit" and hit_event.get("move","") == "light1" and not bool(hit_event.get("projectile",true)),"轻击命中事件字段")
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
	var block_event: Dictionary = {}
	var block_event_count: int = 0
	for i in range(12):
		sim.step([UfeInputFrame.make(0,0,1 if i==0 else 0),UfeInputFrame.make(0,0,8)])
		if not sim.events.is_empty():
			block_event = sim.events[0].duplicate(true)
			block_event_count = sim.events.size()
	check(sim.fighters[1].stats.hp==1000,"站立防御中段")
	check(block_event_count == 1 and ContactEvent.matches_contract(block_event),"轻击被防输出稳定事件契约")
	check(block_event.get("kind","") == "block" and block_event.get("move","") == "light1" and not bool(block_event.get("projectile",true)),"轻击被防事件字段")
	check(not sim.fighters[0].combat.confirmed,"防御不提供命中取消")
	sim = UfeContentDatabase.match_for()
	sim.step([UfeInputFrame.make(1,1,UfeInputFrame.JUMP),neutral()])
	advance(sim,45)
	check(sim.fighters[0].height==0 and sim.fighters[0].x>470,"斜跳有水平轨迹并落地")
	sim = UfeContentDatabase.match_for()
	sim.fighters[0].x=540
	sim.fighters[1].x=600
	sim.step([UfeInputFrame.make(1,0,2),neutral()])
	advance(sim,10)
	sim.step([UfeInputFrame.make(1,1,UfeInputFrame.JUMP),neutral()])
	# 重击命中停顿改为 12 tick，原来的 7 tick 推进还停在停顿里。
	advance(sim,16)
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
