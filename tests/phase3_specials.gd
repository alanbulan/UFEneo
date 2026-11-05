extends SceneTree
var out := "user://phase3-specials/"
var errors: Array = []
func check(ok: bool, text: String) -> void:
	if not ok:errors.append(text);printerr(text)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--test-out="):out=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(out)
	var summaries:=[]
	for part in range(13):
		var driver:=UfePhase3SpecialReview.new()
		driver.review_frame=driver.S_STARTS[part]
		var ids: Array=driver.matchup()
		var sim:=UfeContentDatabase.match_for(str(ids[0]),str(ids[1]))
		var twin:=UfeContentDatabase.match_for(str(ids[0]),str(ids[1]))
		driver.prepare_match(sim);driver.prepare_match(twin)
		var events:=[]
		var seen: Dictionary={}
		for age in range(driver.S_STARTS[part+1]-driver.S_STARTS[part]):
			var frame: int=driver.S_STARTS[part]+age
			if driver.wants_intro() and age<75:continue
			var inputs: Array=[driver.sample(frame,sim),driver.second_sample(frame)]
			sim.step(inputs);twin.step(inputs)
			check(sim.state_hash()==twin.state_hash(),"专属/盾/瞬移逐tick确定性 "+str(part))
			for e in sim.events:
				var item: Dictionary=e.duplicate(true);item.age=age;events.append(item)
				if e.kind=="teleport":check(bool(sim.fighters[int(e.player)].frame().get("conceal",false)),"瞬移坐标改变必须在消失帧")
			for f in sim.fighters:
					if not f.move_id.is_empty():seen[f.definition.id+"/"+f.move_id+"/"+str(int(f.frame().sprite))]=true
		var summary:={"part":part,"label":driver.S_LABELS[part],"hp":[sim.fighters[0].stats.hp,sim.fighters[1].stats.hp],"events":events,"frames_seen":seen.keys(),"finished":sim.finished,"winner":sim.winner}
		summaries.append(summary)
		var has:=func(kind):return events.any(func(e):return e.kind==kind)
		if part in [0,1,2,3]:check(int(sim.fighters[1].stats.hp)<1000,"初代专属实际命中 "+str(part))
		if part in [4,5,6,7]:check(int(sim.fighters[0].stats.hp)<1000,"杰顿专属实际命中 "+str(part))
		if part==3:check(has.call("projectile_reflect"),"奥特屏障实际反射")
		if part==5:check(has.call("projectile_absorb") and has.call("absorb_counter"),"杰顿先吸收后反击")
		if part==8:check(has.call("projectile_block"),"杰顿盾实际挡飞行物 "+str(part))
		if part==6:check(has.call("teleport"),"瞬移消失后到达对手身后")
		if part==9:
			check(seen.has("ultraman/taunt/5") and seen.has("zetton/taunt/5"),"双方真实组合键完整挑衅")
			check(sim.fighters[0].stats.hp==1000 and sim.fighters[1].stats.hp==1000,"挑衅不造成伤害")
		if part==10:check(sim.finished and sim.fighters[0].state=="timeout" and sim.fighters[1].state=="timeout","时间到状态")
		if part in [11,12]:check(sim.finished and sim.winner==(0 if part==11 else 1),"完整输入KO回合 "+str(part))
	# 没吸收到不发射、背面飞行物不被屏障拦下、资源/时长和无敌窗口。
	var no_shot:=UfeContentDatabase.match_for()
	no_shot.fighters[1].stats.energy=1000
	no_shot._start(no_shot.fighters[1],"motion_623")
	for tick in range(50):no_shot.step([UfeInputFrame.make(),UfeInputFrame.make()])
	check(no_shot.fighters[0].stats.hp==1000 and no_shot.projectiles.is_empty(),"未吸收时不能凭空反击")
	var back:=UfeContentDatabase.match_for()
	back.fighters[1].stats.energy=1000
	back._start(back.fighters[1],"motion_22");back.fighters[1].move_tick=13
	UfeProjectileResolver.spawn(back,0,{"spawn":[330,100],"box":[-8,-8,16,16],"speed":0},"pulse")
	back.projectiles[0].x=back.fighters[1].x+4
	var contacts:=[];UfeProjectileResolver.advance(back,contacts)
	check(contacts.size()==1,"盾的背面仍会被飞行物命中")
	for id in ["ultraman","zetton"]:
		var def:=UfeContentDatabase.fighter(id)
		var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%id)
		for a in ["motion_236","motion_623","motion_214","motion_22","taunt"]:
			var m: Dictionary=def.moves[a]
			check(UfeMoveData.validate(m),id+"数据合法 "+a)
			var clip: Dictionary=manifest.clips[a]
			check(int(clip.ticks.reduce(func(total,t):return total+int(t),0))==m.frames.size(),id+"图/数据时长一致 "+a)
			check(clip.rects.size()==(6 if a=="taunt" else 8),id+"独立帧数 "+a)
	var file:=FileAccess.open(out+"phase3-specials-evidence.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"groups":summaries},"\t"))
	print("PHASE3_SPECIALS "+("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
