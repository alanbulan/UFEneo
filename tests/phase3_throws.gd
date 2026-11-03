extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,label: String) -> void:
	if not ok and label not in failures:failures.append(label)
func neutral() -> UfeInputFrame:return UfeInputFrame.make()
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var driver:=UfePhase3ThrowReview.new()
	var view:=UfeSideView.new()
	var manifests:=[UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json"),UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")]
	var sim:=UfeContentDatabase.match_for();var twin:=UfeContentDatabase.match_for();var results:={};var trace:=[]
	for movie_frame in range(driver.length_frames()):
		driver.review_frame=movie_frame
		var section:=driver.section(movie_frame)
		var action: String=driver.ACTIONS[section%6]
		var key:=str(section)+"/"+action
		if section!=driver.last_section:
			sim=UfeContentDatabase.match_for();twin=UfeContentDatabase.match_for();driver.prepare_match(sim);driver.prepare_match(twin);driver.last_section=section
			results[key]={"player":driver.active_player,"clips":[{},{}],"hits":[],"slams":[],"tech":false,"max_grip_error":0,"minimum_height":0}
		var inputs:=[driver.sample(movie_frame,sim),driver.second_sample(movie_frame)]
		sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"投技逐tick确定性")
		var pair:=[]
		for i in range(2):
			var f:=sim.fighters[i];var a:=view._animation(f,manifests[i]);var clip: String=a.get("key","")
			if not clip.is_empty():
				if not results[key].clips[i].has(clip):results[key].clips[i][clip]=[]
				if not a.index in results[key].clips[i][clip]:results[key].clips[i][clip].append(a.index)
			results[key].minimum_height=mini(results[key].minimum_height,f.height)
			check(f.height>=0,"受投根点不得穿过地面 "+key)
			pair.append({"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"move":f.move_id,"move_tick":f.move_tick,"clip":clip,"sprite":a.get("index",0),"hp":f.stats.hp,"data":f.frame().duplicate(true)})
		var owner:=driver.active_player;var a:=sim.fighters[owner];var b:=sim.fighters[1-owner]
		if b.state=="thrown" and a.frame().get("target",{}).get("mode","")=="hold":
			var grip: Array=a.frame().target.grip;var grab: Array=b.frame().grab_points.waist
			var error:=absi(a.x+a.facing*int(grip[0])-b.x-b.facing*int(grab[0]))+absi(a.height+int(grip[1])-b.height-int(grab[1]))
			results[key].max_grip_error=maxi(results[key].max_grip_error,error)
			check(error==0,"抓点整数世界坐标完全相接 "+key)
		for e in sim.events:
			if e.kind=="hit":results[key].hits.append(e.move)
			if e.kind=="throw_slam":
				results[key].slams.append(e.move)
				check((b.x-a.x)*a.facing<0 if action=="throw_back" else (b.x-a.x)*a.facing>0,"撞地时前后投落点方向 "+key)
			if e.kind=="throw_tech":results[key].tech=true
		trace.append({"movie_frame":movie_frame,"section":section,"action":action,"player":owner,"pair":pair,"events":sim.events.duplicate(true)})
		if movie_frame%180==179:
			if action.begins_with("tech"):
				check(results[key].tech,"实际拆投 "+key)
				check(a.stats.hp==1000 and b.stats.hp==1000,"拆投不扣双方体力 "+key)
				for i in range(2):check(results[key].clips[i].get("throw_tech",[]).size()==4,"双方拆投各4格 "+key)
				check(absi(a.x-b.x)>=80,"拆投双方弹开 "+key)
			else:
				check(results[key].hits==[action],"只抓中一次 "+key+str(results[key].hits))
				check(results[key].slams==[action],"只在撞地结算一次 "+key)
				check(b.stats.hp==1000-int(a.definition.moves[action].damage),"投技伤害 "+key)
				check(results[key].clips[owner].get(action,[]).size()==(8 if action in ["throw_forward","throw_back"] else 6),"攻击方完整帧序 "+key)
				var victim_clip: String={"throw_forward":"thrown_forward","throw_back":"thrown_back","air_throw":"thrown_air","dash_throw":"thrown_dash"}[action]
				check(results[key].clips[1-owner].get(victim_clip,[]).size()==4,"被投方完整4格 "+key)
	for owner in range(2):
		for delay in [1,3,4]:check_tech_boundary(owner,delay)
		for edge in [28,1200]:check_corner(owner,edge)
	for f in sim.fighters:
		for id in ["throw_forward","throw_back","air_throw","dash_throw"]:
			var move: Dictionary=f.definition.moves[id]
			check(UfeMoveData.validate(move),"投技逐帧数据合法 "+f.definition.id+id)
			check(move.frames.size()==view._clip_ticks(manifests[0 if f.definition.id=="ultraman" else 1].clips[id]),"投技图片时长与模拟一致 "+f.definition.id+id)
	var evidence_path:="res://reports/phase3-throws-evidence.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--throw-results="):evidence_path=arg.trim_prefix("--throw-results=")
	var file:=FileAccess.open(evidence_path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"failures":failures,"actions":results,"trace":trace},"\t"))
	view.free();print("PHASE3_THROWS "+JSON.stringify({"failures":failures,"actions":results}));quit(0 if failures.is_empty() else 1)

func check_tech_boundary(owner: int,delay: int) -> void:
	var sim:=UfeContentDatabase.match_for();sim.fighters[0].x=500;sim.fighters[1].x=552
	var captured:=false;var age:=0;var broke:=false
	for tick in range(100):
		var pair:=[neutral(),neutral()]
		if tick==0:pair[owner]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		if captured:
			age+=1
			if age==delay:pair[1-owner]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		sim.step(pair)
		if sim.fighters[1-owner].state=="thrown":captured=true
		for event in sim.events:
			if event.kind=="throw_tech":broke=true
	check(captured,"边界测试实际抓中")
	check(broke==(delay<=3),"拆投窗口 "+str([owner,delay]))
	check(sim.fighters[1-owner].stats.hp==1000 if delay<=3 else sim.fighters[1-owner].stats.hp<1000,"拆投边界伤害 "+str([owner,delay]))

func check_corner(owner: int,edge: int) -> void:
	var sim:=UfeContentDatabase.match_for();sim.fighters[0].x=edge;sim.fighters[1].x=edge+52
	for tick in range(90):
		var pair:=[neutral(),neutral()]
		if tick==0:pair[owner]=UfeInputFrame.make(-sim.fighters[owner].facing,0,UfeInputFrame.THROW)
		sim.step(pair)
		for f in sim.fighters:check(f.x>=28 and f.x<=1252,"靠墙配对仍在场地")
	check(sim.fighters[1-owner].stats.hp<1000,"靠墙后投实际命中")
