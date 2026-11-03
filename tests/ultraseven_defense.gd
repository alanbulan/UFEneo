extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,label: String) -> void:
	if not ok:failures.append(label)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var driver:=UfeUltrasevenDefenseReview.new()
	var view:=UfeSideView.new()
	var manifests:=[UfeContentDatabase.read_json("res://assets/fighters/ultraseven/animations/manifest.json"),UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")]
	var sim: UfeMatchDirector
	var twin: UfeMatchDirector
	var results:={}
	var trace:=[]
	for frame in range(driver.length_frames()):
		driver.review_frame=frame
		var part:=driver.section(frame)
		var id: String=driver.actions()[part]
		if part!=driver.last_section:
			sim=UfeContentDatabase.match_for("ultraseven","zetton",true)
			twin=UfeContentDatabase.match_for("ultraseven","zetton",true)
			driver.prepare_match(sim)
			driver.prepare_match(twin)
			driver.last_section=part
			results[id]={"available":driver.ready_action(id),"clips":[],"moves":[],"hits":[],"events":[]}
		var inputs:=[driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(inputs)
		twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"防御受击输入回放不一致 "+str(frame))
		var f:=sim.fighters[0]
		var anim:=view._animation(f,manifests[0])
		for pair in [["clips",anim.get("key","")],["moves",f.move_id]]:
			if not results[id][pair[0]].has(pair[1]):results[id][pair[0]].append(pair[1])
		for e in sim.events:
			if e.kind=="hit" and e.player==0:results[id].hits.append(e.move)
			if e.kind in ["hit","block","launch","bounce"]:results[id].events.append(e)
		trace.append({"frame":frame,"action":id,"state":f.state,"clip":anim.get("key",""),"sprite":anim.get("index",-1),"move":f.move_id,"move_tick":f.move_tick,"height":f.height,"x":f.x,"target_x":sim.fighters[1].x,"target_hp":sim.fighters[1].stats.hp,"events":sim.events.duplicate(true)})
	for id in results:
		if id=="full_chain" or not results[id].available:continue
		check(results[id].clips.has(id),"主游戏输入未触发 "+id+" "+str(results[id].clips))
		if sim.fighters[0].definition.moves.has(id):
			check(results[id].hits.has(id),"反击/起身/移动攻击未命中 "+id)
			check(UfeMoveData.validate(sim.fighters[0].definition.moves[id]),"招式数据不合法 "+id)
	FileAccess.open("res://reports/ultraseven-defense-evidence.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"actions":results,"trace":trace},"\t"))
	view.free()
	print("ULTRASEVEN_DEFENSE "+JSON.stringify({"failures":failures,"actions":results}))
	quit(0 if failures.is_empty() else 1)
