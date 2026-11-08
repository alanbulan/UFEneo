extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,label: String) -> void:
	if not ok and label not in failures:failures.append(label)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var driver:=UfeUltrasevenFourthReview.new();var view:=UfeSideView.new()
	var sim: UfeMatchDirector;var twin: UfeMatchDirector;var results:={};var trace:=[];var manifests:=[]
	for frame in range(driver.length_frames()):
		driver.review_frame=frame;var part:=driver.section(frame);var key:=str(part)
		if part!=driver.last_section:
			var ids:=driver.matchup();sim=UfeContentDatabase.match_for(ids[0],ids[1],true);twin=UfeContentDatabase.match_for(ids[0],ids[1],true)
			driver.prepare_match(sim);driver.prepare_match(twin);driver.last_section=part
			manifests=[UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%ids[0]),UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%ids[1])]
			results[key]={"label":driver.label(frame),"available":driver.ready_action(part),"clips":[{},{}],"slams":[],"tech":false,"max_grip_error":0,"minimum_height":0}
		var inputs:=[driver.sample(frame,sim),driver.second_sample(frame)];sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"投技演出输入确定性 "+key)
		var pair:=[]
		for i in range(2):
			var f:=sim.fighters[i];var a:=view._animation(f,manifests[i]);var clip: String=a.get("key","")
			if not results[key].clips[i].has(clip):results[key].clips[i][clip]=[]
			if not a.get("index",-1) in results[key].clips[i][clip]:results[key].clips[i][clip].append(a.get("index",-1))
			results[key].minimum_height=mini(results[key].minimum_height,f.height)
			check(f.height>=0,"受投脚底不得穿地 "+key)
			pair.append({"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"clip":clip,"sprite":a.get("index",-1),"data":f.frame().duplicate(true)})
		var owner:=driver.active_player;var actor:=sim.fighters[owner];var victim:=sim.fighters[1-owner]
		if victim.state=="thrown" and actor.frame().get("target",{}).get("mode","")=="hold":
			var target: Dictionary=actor.frame().target;var grip: Array=target.grip;var grab: Array=victim.frame().grab_points.waist;var root_rule: Array=target.get("root",[0,0])
			var error:=absi(actor.x+actor.facing*(int(grip[0])+int(root_rule[0]))-victim.x-victim.facing*int(grab[0]))+absi(actor.height+int(grip[1])+int(root_rule[1])-victim.height-int(grab[1]))
			check(error==0,"抓握点/被抓点对齐 "+key);results[key].max_grip_error=maxi(results[key].max_grip_error,error)
		for e in sim.events:
			if e.kind=="throw_slam":results[key].slams.append(e.move)
			if e.kind=="throw_tech":results[key].tech=true
		trace.append({"movie_frame":frame,"section":part,"available":driver.ready_action(part),"player":owner,"pair":pair,"events":sim.events.duplicate(true)})
		if frame%240==239 and results[key].available and part<18:
			if part%6>=4:check(results[key].tech,"拆投实际触发 "+key)
			else:check(results[key].slams==[driver.ACTIONS[part%6]],"投技仅结算一次 "+key)
		if frame%240==239 and results[key].available and part==22:
			for i in range(2):check(results[key].clips[i].has("taunt"),"防御+投技必须触发挑衅 玩家"+str(i+1))
	FileAccess.open("res://reports/ultraseven-fourth-evidence.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"sections":results,"trace":trace},"\t"))
	view.free();print("ULTRASEVEN_FOURTH "+JSON.stringify({"failures":failures,"sections":results}));quit(0 if failures.is_empty() else 1)
