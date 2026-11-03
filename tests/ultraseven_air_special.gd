extends SceneTree
var failures: Array=[]
func check(ok: bool,label: String) -> void:
	if not ok and label not in failures:failures.append(label);printerr(label)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var sections:=[]
	for side in [1,-1]:
		var driver:=UfeUltrasevenAirSpecialReview.new()
		var sim:=UfeContentDatabase.match_for("ultraseven","zetton",true)
		var twin:=UfeContentDatabase.match_for("ultraseven","zetton",true)
		driver.prepare_match(sim);driver.prepare_match(twin)
		if side<0:
			for s in [sim,twin]:s.fighters[0].x=680;s.fighters[1].x=500;s.fighters[0].facing=-1;s.fighters[1].facing=1
		var hits:=[];var returned:=0;var poses:={};var path:=[];var starts:=0
		for age in range(180):
			var inputs:=[driver.sample(age,sim),driver.second_sample(age)]
			sim.step(inputs);twin.step(inputs)
			check(sim.state_hash()==twin.state_hash(),"相同InputFrame逐tick确定性 "+str(side))
			var f:=sim.fighters[0]
			if f.move_id=="air_special":
				poses[str(f.frame().sprite)]=true
				if int(f.move_tick)==1:starts+=1
			for p in sim.projectiles:
				if p.move!="air_special":continue
				path.append([age,int(p.x),int(p.height),int(p.age),int(p.hits)])
				check(typeof(p.x)==TYPE_INT and typeof(p.height)==TYPE_INT,"头镖轨迹只能用整数")
				check(UfeReturningProjectile.blocks_move(sim,f,"ranged_forward"),"在外锁住6I")
				check(UfeReturningProjectile.blocks_move(sim,f,"air_special"),"在外锁住空中P")
				var move_before:=f.move_id;var energy_before:=int(f.stats.energy)
				sim._start(f,"ranged_forward");twin._start(twin.fighters[0],"ranged_forward")
				check(f.move_id==move_before and int(f.stats.energy)==energy_before,"武器在外拒绝重复投掷且不扣能量")
			for event in sim.events:
				if event.kind=="hit" and event.move=="air_special":hits.append(age)
				if event.kind=="weapon_return":
					returned+=1
					check(int(f.frame().sprite)==10,"回手时序对齐接镖首帧")
					var grip: Array=f.frame().weapon_return_anchor
					check(int(event.x)==f.x+f.facing*int(grip[0]) and int(event.height)==f.height+int(grip[1]),"返回终点精确落在实际手掌")
		check(hits.size()==3,"前下弧线必须真实命中杰顿三段 "+str(side))
		check(returned==1,"飞镖仅回手一次 "+str(side))
		check(poses.size()==14,"摸冠到护架14个新人物帧实际播放 "+str(side))
		check(int(sim.fighters[1].stats.hp)==820,"三段每段60伤害")
		check(int(sim.fighters[0].stats.energy)==270,"只消耗一格，保留正常三次命中能量收益")
		check(not UfeReturningProjectile.blocks_move(sim,sim.fighters[0],"ranged_forward"),"回收解除武器锁")
		sections.append({"side":side,"hits":hits,"returned":returned,"poses":poses.keys(),"path":path,"final_hash":sim.state_hash(),"hp":sim.fighters[1].stats.hp})
	# 落地仍推进真实物理；不能打断接回，更不能把角色留在无冠姿势。
	var low:=UfeContentDatabase.match_for("ultraseven","zetton",true)
	low.fighters[0].height=8;low.fighters[0].vy=-1;low.fighters[0].stats.energy=1000;low.fighters[0].enter("air")
	var return_count:=0
	for age in range(100):
		low.step([UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL if age==0 else 0),UfeInputFrame.make()])
		for e in low.events:
			if e.kind=="weapon_return":return_count+=1
	check(return_count==1 and low.fighters[0].height==0 and low.fighters[0].move_id.is_empty(),"低空发出后落地完成接回装回，物理未悬停")
	for id in ["ultraman","zetton"]:
		var old:=UfeContentDatabase.match_for(id,"zetton" if id=="ultraman" else "ultraman")
		old.fighters[0].height=30;old.fighters[0].vy=3;old.fighters[0].stats.energy=1000;old.fighters[0].enter("air")
		old.step([UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL),UfeInputFrame.make()])
		check(old.fighters[0].move_id.is_empty() and int(old.fighters[0].stats.energy)==1000,"保持旧角色空中P禁用 "+id)
	FileAccess.open("res://reports/review/2026-10-22/seven-air-special/logic-evidence.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"sections":sections},"\t"))
	print("ULTRASEVEN_AIR_SPECIAL "+JSON.stringify({"failures":failures,"sections":sections.map(func(s):return {"side":s.side,"hits":s.hits,"returned":s.returned,"poses":s.poses})}))
	quit(0 if failures.is_empty() else 1)
