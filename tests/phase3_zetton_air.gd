extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,label: String) -> void:
	if not ok:failures.append(label)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var driver:=UfePhase3ZettonAirReview.new();var view:=UfeSideView.new()
	var manifests:=[UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json"),UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")]
	var sim:=UfeContentDatabase.match_for();var twin:=UfeContentDatabase.match_for();var results:={};var chain_hits:={};var all_trace:=[]
	for movie_frame in range(driver.length_frames()):
		driver.review_frame=movie_frame
		var section:=driver.section(movie_frame);var action: String=driver.ACTIONS[section]
		if section!=driver.last_section:
			sim=UfeContentDatabase.match_for();twin=UfeContentDatabase.match_for();driver.prepare_match(sim);driver.prepare_match(twin);driver.last_section=section
			results[action]={"frames":[],"hits":[],"clips":{},"max_height":0};chain_hits[action]=[]
		var inputs:=[driver.sample(movie_frame,sim),driver.second_sample(movie_frame)]
		sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"杰顿跳跃批确定性 "+str(movie_frame))
		var f:=sim.fighters[driver.active_player];var b:=sim.fighters[1-driver.active_player];var a:=view._animation(f,manifests[driver.active_player]);var clip: String=a.get("key","")
		results[action].max_height=maxi(results[action].max_height,f.height)
		if not clip.is_empty():
			if not results[action].clips.has(clip):results[action].clips[clip]=[]
			if not results[action].clips[clip].has(a.index):results[action].clips[clip].append(a.index)
		for e in sim.events:
			if e.kind=="hit" and e.player==driver.active_player:results[action].hits.append(e.move);chain_hits[action].append(e.move)
		all_trace.append({"movie_frame":movie_frame,"action":action,"player":driver.active_player,"state":f.state,"move":f.move_id,"move_tick":f.move_tick,"height":f.height,"vy":f.vy,"x":f.x,"target_height":b.height,"target_state":b.state,"target_x":b.x,"clip":clip,"sprite":a.get("index",-1),"chain_stage":driver.chain_stage,"events":sim.events.duplicate(true)})
	for action in driver.ACTIONS:
		if action in ["full_combo","camera_ultraman"]:continue
		var clip: Dictionary=manifests[1].clips.get(action,{})
		check(not clip.is_empty(),action+"缺动画")
		if sim.fighters[1].definition.moves.has(action):
			var move: Dictionary=sim.fighters[1].definition.moves[action]
			check(UfeMoveData.validate(move),action+"帧数据无效")
			check(view._clip_ticks(clip)==move.frames.size(),action+"时长不同步")
			check(action in results[action].hits,action+"未实际命中初代")
		check(results[action].clips.has(action),action+"未实播")
	for a in ["full_combo","camera_ultraman"]:check(chain_hits[a]==["launcher","chase_light1","chase_light2","chase_end","sweep"],a+"完整链未命中 "+str(chain_hits[a]))
	check(results.vertical_jump.max_height==105,"杰顿常规跳105像素顶点")
	check(sim.fighters[0].definition.jump_speed==16 and sim.fighters[1].definition.jump_speed==14,"角色跳跃参数")
	var file:=FileAccess.open("res://reports/phase3-zetton-air-evidence.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"failures":failures,"actions":results,"trace":all_trace},"\t"))
	view.free();print("PHASE3_ZETTON_AIR "+JSON.stringify({"failures":failures,"actions":results}));quit(0 if failures.is_empty() else 1)
