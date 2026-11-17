extends SceneTree
var failures: Array[String]=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	if not ok:failures.append(label)
func run() -> void:
	var driver:=UfeZettonCounterReview.new();var sim:=UfeContentDatabase.match_for();var twin:=UfeContentDatabase.match_for();var hits:=[0,0];var seen:=[false,false];var evidence:=[]
	for frame in range(driver.length_frames()):
		driver.review_frame=frame
		var part:=driver.section(frame)
		if part!=driver.last_section:
			sim=UfeContentDatabase.match_for();twin=UfeContentDatabase.match_for();driver.prepare_match(sim);driver.prepare_match(twin);driver.last_section=part
		var inputs:=[driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"真实侧闪输入确定性 "+str(frame))
		check(sim.fighters[0].height==0,"目标不应跳起迁就手刀")
		if sim.fighters[1].move_id=="dodge_counter":seen[part]=true
		for event in sim.events:
			if event.kind=="hit" and event.player==1 and event.move=="dodge_counter":hits[part]+=1
		evidence.append({"frame":frame,"section":part,"target_state":sim.fighters[0].state,"target_hp":sim.fighters[0].stats.hp,"move":sim.fighters[1].move_id,"move_tick":sim.fighters[1].move_tick,"events":sim.events.duplicate(true)})
	check(seen[0] and seen[1],"两组都应真实触发侧闪反击")
	check(hits[0]==1,"站姿初代必须被手掌实际命中 "+str(hits))
	check(hits[1]==1,"保留中段设定，蹲姿头部仍在横切覆盖内 "+str(hits))
	check(str(sim.fighters[1].definition.moves.dodge_counter.level)=="mid","保留原中段属性，不为命中改规则")
	var file:=FileAccess.open("res://reports/zetton-counter-evidence.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"failures":failures,"hits":hits,"trace":evidence},"\t"))
	print("ZETTON_COUNTER "+JSON.stringify({"failures":failures,"hits":hits}));quit(0 if failures.is_empty() else 1)
