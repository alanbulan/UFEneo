extends SceneTree
@warning_ignore_start("integer_division")
func _init() -> void:
	var driver:=UfeUltrasevenReview.new()
	var sim: UfeMatchDirector
	var hits: Dictionary={}
	var previous: int=-1
	for frame in range(driver.length_frames()):
		driver.review_frame=frame
		var part:=driver.section(frame)
		if part!=previous:
			sim=UfeContentDatabase.match_for("ultraseven","zetton",true)
			driver.prepare_match(sim);previous=part
		var pair: Array=[driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(pair)
		for event in sim.events:
			if event.kind in ["hit","launch","bounce","knockdown"] and int(event.get("player",-1))==0:hits[event.move]=true
	var fighter:=UfeContentDatabase.fighter("ultraseven",true)
	for action in ["light1","light2","light3","heavy","launcher","spin_heavy","crush","tackle","pulse","ranged_forward","crouch_light","crouch_light2","sweep","slide","low_pulse"]:
		if not driver.available.has(action):continue
		assert(hits.has(action),"赛文正式动作没有真实输入命中杰顿："+action)
		var move: Dictionary=fighter.moves[action]
		var clip: Dictionary=driver.available[action]
		var total:=0
		for ticks in clip.ticks:total+=int(ticks)
		assert(move.frames.size()==total)
	var definition: Dictionary=UfeContentDatabase.read_json("res://content/fighters/ultraseven/definition.json")
	assert(definition.playable and definition.pilot_playable and definition.pilot_manual_ready and definition.walks_installed)
	for entry in fighter.command_table:assert(str(entry.move) not in definition.unsupported_moves)
	# 三个clip共用九帧图集，模拟精灵编号须先减各段起点，不能夹到末帧。
	if driver.available.has("dash"):
		var actor:=UfeContentDatabase.match_for("ultraseven","zetton",true).fighters[0]
		var view:=UfeSideView.new()
		var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/ultraseven/animations/manifest.json")
		actor.enter("dash",22)
		var counts: Dictionary={}
		for tick in range(22):
			actor.state_tick=tick
			var animation:=view._animation(actor,manifest)
			var atlas_frame:=int(animation.rect[0])/int(animation.cell)
			assert(atlas_frame==int(actor.frame().sprite),"冲刺三段图集索引与模拟帧不一致")
			counts[atlas_frame]=int(counts.get(atlas_frame,0))+1
		var expected: Array=[]
		for clip_name in ["dash_start","dash","dash_stop"]:expected.append_array(manifest.clips[clip_name].ticks)
		assert(counts.size()==9,"冲刺必须播到完整九帧")
		for index in range(9):assert(int(counts[index])==int(expected[index]),"冲刺帧持续时长不符")
		view.free()
	print("ULTRASEVEN_FIRST PASS：已安装招式真实输入命中、整帧时长、未制作指令禁用一致。命中：",hits.keys())
	quit()
@warning_ignore_restore("integer_division")
