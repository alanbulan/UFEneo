extends SceneTree
var errors: Array=[]
func check(ok: bool,text: String) -> void:
	if not ok:errors.append(text);printerr(text)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var groups:=[]
	for part in range(12):
		var driver:=UfePhase3SuperReview.new()
		driver.review_frame=part*240
		var sim:=UfeContentDatabase.match_for()
		var twin:=UfeContentDatabase.match_for()
		driver.prepare_match(sim);driver.prepare_match(twin)
		var events:=[]
		var seen: Dictionary={}
		var pause_ticks:=0
		var attacker:=0 if part<6 else 1
		var level: int=(part%6)/2+1
		var wanted: String="special"+(str(level) if level>1 else "")
		for age in range(240):
			var was_paused:=bool(sim.fighters[attacker].frame().get("pause_clock",false))
			var old_remaining:=sim.remaining
			var inputs: Array=[driver.sample(part*240+age,sim),driver.second_sample(part*240+age)]
			sim.step(inputs);twin.step(inputs)
			check(sim.state_hash()==twin.state_hash(),"必杀确定性 "+str(part))
			if was_paused:
				check(sim.remaining==old_remaining,"三级演出暂停回合时间")
				pause_ticks+=1
			for e in sim.events:
				events.append(e.duplicate(true))
				if e.kind in ["hit","block"]:
					check(e.projectile and e.move==wanted,"光线/火球使用实体飞行物判定 "+str(part))
					check(int(e.feedback.hitstop)>=10,"必杀沿用模拟命中停顿且长于重击")
			var f:=sim.fighters[attacker]
			if f.move_id==wanted:seen[str(int(f.frame().sprite))]=true
			for p in sim.projectiles:
				if bool(p.get("beam",false)):
					check(UfeMatchDirector.projectile_box(p).size.x==int(p.length),"光线可见长度和判定一致")
		var move: Dictionary=sim.fighters[attacker].definition.moves[wanted]
		check(sim.fighters[1-attacker].stats.hp==1000-int(move.chip_damage if part%2==1 else move.damage),"各级命中伤害/防御削血 "+str(part))
		check(events.any(func(e):return e.kind==("block" if part%2==1 else "hit")),"真实P/双键输入必杀 "+str(part))
		check(int(sim.fighters[attacker].stats.energy)<1000,"每级能量全部消费")
		var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%sim.fighters[attacker].definition.id)
		var clip: Dictionary=manifest.clips[wanted]
		check(seen.size()==clip.rects.size(),"起手持续收势全部在模拟播放 "+str(part))
		check(int(clip.runtime_ticks)==move.frames.size() and UfeMoveData.validate(move),"必杀帧数据和动画总时长")
		check(level!=3 or pause_ticks>=move.frames.size(),"三级全演出时停")
		groups.append({"section":part,"label":driver.label(part*240),"hp":[sim.fighters[0].stats.hp,sim.fighters[1].stats.hp],"sprites_seen":seen.keys(),"events":events,"pause_ticks":pause_ticks})
	for id in ["ultraman","zetton"]:
		var sim:=UfeContentDatabase.match_for(id,"zetton" if id=="ultraman" else "ultraman")
		var f:=sim.fighters[0]
		f.stats.energy=3000;f.height=60;f.vy=2;f.enter("air")
		sim.step([UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL),UfeInputFrame.make()])
		check(f.move_id.is_empty() and int(f.stats.energy)==3000,"无原剧空中依据时P不触发 "+id)
	# 交叠点必须在双方交集内，不能使用被击者根点+常数。
	var near:=UfeContentDatabase.match_for()
	near.fighters[0].x=500;near.fighters[1].x=565
	near._start(near.fighters[0],"light1")
	var m: Dictionary=near.fighters[0].definition.moves.light1
	near.fighters[0].move_tick=int(m.startup)
	var a:=near.fighters[0];var b:=near.fighters[1]
	var point:=UfeHitResolver.contact_point(a,b)
	var inside:=false
	for hit in a.frame().hitboxes:
		for hurt in b.frame().hurtboxes:
			if UfeHitResolver.world_box(a,hit).intersection(UfeHitResolver.world_box(b,hurt)).has_point(point):inside=true
	check(inside,"近身火花锚点在真正交叠区域")
	var file:=FileAccess.open("res://reports/phase3-supers-evidence.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"groups":groups},"\t"))
	print("PHASE3_SUPERS "+("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
