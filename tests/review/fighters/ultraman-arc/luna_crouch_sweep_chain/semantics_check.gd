extends SceneTree
const Factory=preload("res://tests/review/fighters/ultraman-arc/luna_crouch_sweep_chain/candidate_factory.gd")
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var path: String=""
	var out: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="):path=arg.trim_prefix("--contract=")
		elif arg.begins_with("--out="):out=arg.trim_prefix("--out=")
	assert(not path.is_empty() and not out.is_empty() and not FileAccess.file_exists(out))
	var cfg: Dictionary=Factory.read_sealed(path)
	var results: Array=[]
	var errors: Array=[]
	var requests: Array=[]
	for facing in [1,-1]:
		for kind in ["hit","block","whiff"]:
			for press in [28,30,32,34,36,37,39,42,46,50,55,60,70]:requests.append({"facing":facing,"kind":kind,"second_tick":press,"x":0,"y":-1,"gap":260 if kind=="whiff" else 75,"held":false})
		for gap in [36,55,65,70,75,80,85,90,100,120,160,260]:requests.append({"facing":facing,"kind":"hit","second_tick":37,"x":0,"y":-1,"gap":gap,"held":false})
		requests.append({"facing":facing,"kind":"hit","second_tick":37,"x":0,"y":-1,"gap":75,"held":true})
	for request in requests:
		var local_cfg: Dictionary=cfg.duplicate(true)
		local_cfg.initial_gaps[request.kind]=request.gap
		var sim:=Factory.make_match(local_cfg,int(request.facing),str(request.kind))
		var pairs: Array=[]
		var hashes: Array=[]
		var events: Array=[]
		var transitions: Array=[]
		var contacts: Array=[]
		var second_starts: Array=[]
		var receiver_timeline: Array=[]
		for tick in range(180):
			var buttons: int=UfeInputFrame.LIGHT if tick in [20,27] else (UfeInputFrame.HEAVY if ((tick>=int(request.second_tick) and tick<=80) if bool(request.held) else tick==int(request.second_tick)) else 0)
			var first:=UfeInputFrame.make(int(request.x) if tick==int(request.second_tick) else 0,int(request.y) if tick==int(request.second_tick) else -1,buttons)
			var second:=UfeInputFrame.make(0,-1 if request.kind=="block" else 0,UfeInputFrame.GUARD if request.kind=="block" else 0)
			pairs.append([first.pack(),second.pack()])
			var f:=sim.fighters[0]
			var before: Dictionary={"move":f.move_id,"move_tick":f.move_tick,"confirmed":f.combat.confirmed,"buffer":f.combat.buffer,"buffer_ticks":f.combat.buffer_ticks,"state":f.state,"cancel":f.frame().cancel.duplicate(),"gap":absi(sim.fighters[1].x-f.x)}
			var receiver_before: Dictionary={"state":sim.fighters[1].state,"state_tick":sim.fighters[1].state_tick,"height":sim.fighters[1].height}
			receiver_timeline.append({"frame":tick,"state":sim.fighters[1].state,"state_tick":sim.fighters[1].state_tick,"gap":absi(sim.fighters[1].x-sim.fighters[0].x)})
			sim.step([first,second]);hashes.append(sim.state_hash());events.append(sim.events.duplicate(true))
			if before.move!=f.move_id:
				var transition: Dictionary={"input_frame":tick,"before":before,"after_move":f.move_id,"after_state":f.state,"after_move_tick":f.move_tick,"gap":absi(sim.fighters[1].x-f.x)}
				transitions.append(transition)
				if f.move_id=="sweep":
					transition["is_cancel"]=before.move=="crouch_light2"
					second_starts.append(transition)
					if bool(transition.is_cancel) and (not bool(before.confirmed) or not "sweep" in before.cancel):errors.append({"kind":"invalid_cancel","request":request,"transition":transition})
			for event in sim.events:
				if str(event.get("kind","")) in ["hit","block"] and int(event.get("player",-1))==0:contacts.append({"input_frame":tick,"event":event.duplicate(true),"receiver_before":receiver_before,"gap":absi(sim.fighters[1].x-f.x)})
		if bool(request.held) and second_starts.size()>1:errors.append({"kind":"held_retrigger","request":request})
		if request.kind in ["block","whiff"] and second_starts.any(func(row):return bool(row.is_cancel)):errors.append({"kind":"unconfirmed_cancel","request":request})
		var replay:=Factory.make_match(local_cfg,int(request.facing),str(request.kind))
		for tick in range(180):
			replay.step([UfeInputFrame.unpack(pairs[tick][0]),UfeInputFrame.unpack(pairs[tick][1])])
			if replay.state_hash()!=hashes[tick] or JSON.stringify(replay.events,"",true)!=JSON.stringify(events[tick],"",true):errors.append({"kind":"replay_mismatch","request":request,"tick":tick})
		results.append({"request":request,"transitions":transitions,"receiver_timeline":receiver_timeline,"second_starts":second_starts,"contacts":contacts,"damage":1000-int(sim.fighters[1].stats.hp),"final_hash":sim.state_hash(),"replay_hash":replay.state_hash()})
	var file:=FileAccess.open(out,FileAccess.WRITE);assert(file!=null)
	file.store_string(JSON.stringify({"candidate_contract_sha256":cfg._candidate_contract_sha256,"cases":results,"errors":errors,"post_sim_mutation":false,"rules_changed":false,"receiver":"formal_zetton","graphical_review":false},"\t"));file.close()
	print("二拳输入取消语义矩阵：",results.size(),"，错误：",errors.size());quit(0 if errors.is_empty() else 1)
