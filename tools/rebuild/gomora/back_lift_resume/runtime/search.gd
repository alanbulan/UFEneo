extends SceneTree
## 仅搜索真实Q/走位/跳跃/P的时序，不制造空中、根点或能量夹具；不是主游戏视觉证据。
const Factory=preload("res://tools/rebuild/gomora/back_lift_resume/runtime/factory.gd")
const Driver=preload("res://tools/rebuild/gomora/back_lift_resume/runtime/driver.gd")
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var contract: String=""
	var out: String=""
	var gaps: PackedStringArray="56,64,68,72,80".split(",")
	var delays: PackedStringArray="10,12,13,14,16".split(",")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="):contract=arg.trim_prefix("--contract=")
		elif arg.begins_with("--search-output="):out=arg.trim_prefix("--search-output=")
		elif arg.begins_with("--search-gaps="):gaps=arg.trim_prefix("--search-gaps=").split(",")
		elif arg.begins_with("--search-delays="):delays=arg.trim_prefix("--search-delays=").split(",")
	assert(not out.is_empty() and not FileAccess.file_exists(out))
	var cfg: Dictionary=Factory.read_sealed(contract)
	var rows: Array=[]
	var found: bool=false
	for gap_value in gaps:
		if found:break
		for delay_value in delays:
			var driver=Driver.new();driver.candidate_contract=cfg
			driver.gap=int(gap_value);driver.jump_delay=int(delay_value)
			assert(driver.gap>=40 and driver.gap<=120 and driver.jump_delay>=0 and driver.jump_delay<=24)
			var sim:=Factory.make_match(cfg,driver.owner,driver.kind)
			driver.prepare_match(sim)
			var captures: Array=[];var slams: Array=[];var techs: Array=[];var windows: Array=[];var inputs: Array=[];var hashes: Array=[];var events: Array=[];var started: bool=false
			for frame in range(driver.capture_length()):
				var first: UfeInputFrame=driver.sample(frame,sim)
				var second: UfeInputFrame=driver.second_sample(frame)
				sim.step([first,second])
				inputs.append([first.pack(),second.pack()]);hashes.append(sim.state_hash());events.append(sim.events.duplicate(true))
				if sim.fighters[driver.owner].move_id=="special3":
					started=true
					var a:=sim.fighters[driver.owner];var b:=sim.fighters[1-driver.owner]
					if a.move_tick>=int(cfg.move.throw_current_capture.first_tick) and a.move_tick<int(cfg.move.throw_current_capture.entry_tick):
						var entry: Dictionary=cfg.move.frames[int(cfg.move.throw_current_capture.entry_tick)].target
						var pose: Dictionary=b.definition.state_frames[str(entry.pose)][int(entry.sprite)]
						var point: Array=UfeThrowResolver.HoldPoints.point(b,entry,pose)
						var offset: Array=UfeThrowResolver.RootOffsets.offset(b,entry)
						var desired:=Vector2i(a.x+a.facing*(int(entry.grip[0])+int(offset[0])-int(entry.get("facing",-1))*int(point[0])),a.height+int(entry.grip[1])+int(offset[1])-int(point[1]))
						var contact: bool=false
						var body: int=int(cfg.move.throw_current_capture.body_hurtbox_index)
						if body<b.frame().hurtboxes.size():
							for hit in a.frame().hitboxes:
								if UfeHitResolver.world_box(a,hit).intersects(UfeHitResolver.world_box(b,b.frame().hurtboxes[body])):contact=true
						windows.append({"tick":sim.tick,"raw":a.move_tick,"relative_root":[(b.x-a.x)*a.facing,b.height-a.height],"state":b.state,"sprite":int(b.frame().sprite),"victim_hurtboxes":b.frame().hurtboxes,"actor_hitboxes":a.frame().hitboxes,"body_contact":contact,"entry_delta":[absi(b.x-desired.x),absi(b.height-desired.y)],"eligible_after_step":UfeThrowResolver.CurrentCapture.eligible(a,b,cfg.move),"incoming_facing":b.facing,"incoming_velocity":[b.vx,b.vy],"incoming_root":[b.x,b.height],"actor_root":[a.x,a.height],"actor_facing":a.facing,"jump_kind":b.motion.jump_kind,"incoming_frame":b.frame().duplicate(true),"capture_memory":b.motion.get("throw_current_capture",{}).duplicate(true)})
				for event in sim.events:
					if int(event.get("player",-1))!=driver.owner:continue
					if event.kind=="hit" and str(event.get("move",""))=="special3":captures.append({"tick":sim.tick,"raw":sim.fighters[driver.owner].move_tick})
					if event.kind=="throw_tech":techs.append({"tick":sim.tick})
					if event.kind=="throw_slam":slams.append({"tick":sim.tick,"raw":sim.fighters[driver.owner].move_tick,"height":sim.fighters[1-driver.owner].height})
				if started and sim.fighters[driver.owner].move_id.is_empty():break
			driver.release_keys()
			rows.append({"gap":driver.gap,"jump_delay":driver.jump_delay,"owner":driver.owner,"case":driver.kind,"preparation":driver.rear_preparation,"started":started,"captures":captures,"slams":slams,"techs":techs,"damage":1000-int(sim.fighters[1-driver.owner].stats.hp),"windows":windows,"original_inputs":inputs,"state_hashes":hashes,"events":events,"content_fingerprint":sim.content_fingerprint,"final_hash":sim.state_hash()})
			if captures.size()==1 and slams.size()==1 and int(slams[0].height)==0:
				found=true;break
	var file:=FileAccess.open(out,FileAccess.WRITE);assert(file!=null)
	file.store_string(JSON.stringify({"candidate_contract_sha256":cfg._contract_sha256,"found":found,"rows":rows,"physical_keys":true,"state_injection":false,"main_visual_evidence":false}))
	file.close();quit(0)
