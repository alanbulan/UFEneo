extends SceneTree
## 只验证声音事件、资源归属和确定性；不评价音色或画面。
const OUT="res://audio/work/qa-2026-10-23/audioqa-dispatch-evidence.json"
var errors: Array=[]
var releases: Array=[]
var slams: Array=[]

func _initialize() -> void:call_deferred("run")
func check(ok: bool,why: String) -> void:
	if not ok:errors.append(why);printerr(why)
func fresh_audio() -> UfeSideAudio:
	var audio:=UfeSideAudio.new()
	root.add_child(audio)
	audio.played.clear()
	return audio
func empty_pair() -> Array:return [UfeInputFrame.make(),UfeInputFrame.make()]

func release_case(id: String,level: int,record: bool) -> Array:
	var sim:=UfeContentDatabase.match_for(id,"zetton")
	sim.fighters[0].x=100;sim.fighters[1].x=1150
	sim.fighters[1].combat.invulnerable=10000
	var fighter:=sim.fighters[0]
	fighter.stats.energy=level*1000
	sim._start(fighter,"special")
	var move:=fighter.move_id
	var release_ids: Array=[]
	for frame in fighter.definition.moves[move].frames:
		if frame.get("shots",[]).is_empty():continue
		for e in frame.events:
			if e.kind=="sound" and not release_ids.has(str(e.id)):release_ids.append(str(e.id))
	check(not release_ids.is_empty(),id+"/"+move+" shots帧声明释放声")
	var audio:=fresh_audio()
	var hashes: Array=[]
	var shot_count:=0
	for tick in range(fighter.definition.moves[move].frames.size()+2):
		var frame:=fighter.frame().duplicate(true)
		var move_tick:=fighter.move_tick
		var shooting: bool=fighter.move_id==move and not frame.get("shots",[]).is_empty() and sim.hitstop==0
		sim.step(empty_pair())
		var cursor:=audio.played.size()
		audio.sync(sim,false)
		var played: Array=audio.played.slice(cursor)
		for sid in release_ids:
			var expected:=sim.events.filter(func(e):return e.kind=="sound" and str(e.id)==sid and int(e.player)==0).size()
			var actual:=played.filter(func(e):return str(e.id)==audio.resolve(sid) and int(e.player)==0).size()
			check(actual==expected,id+"/"+move+" tick="+str(sim.tick)+" 释放声只取帧事件")
		if shooting:
			shot_count+=1
			check(not played.filter(func(e):return str(e.id) in release_ids and int(e.player)==0).is_empty(),id+"/"+move+" shots与释放声同tick")
			check(not sim.projectiles.filter(func(p):return int(p.owner)==0 and str(p.move)==move and int(p.age)<=1).is_empty(),id+"/"+move+" 真实shots发射")
			if record:releases.append({"fighter":id,"move":move,"move_tick":move_tick,"sim_tick":sim.tick,"release_ids":release_ids,"played":played})
		var count:=audio.played.size()
		audio.sync(sim,false)
		check(count==audio.played.size(),"同一tick重复sync不重播")
		hashes.append([sim.state_hash(),JSON.stringify(played)])
	check(shot_count>0,id+"/"+move+" 必杀真实发射")
	audio.free()
	return hashes

func slam_case(id: String,move: String) -> void:
	var sim:=UfeContentDatabase.match_for(id,"ultraman")
	sim.fighters[0].x=500;sim.fighters[1].x=552
	sim.fighters[0].stats.energy=3000
	sim._start(sim.fighters[0],move)
	var audio:=fresh_audio()
	var found:=false
	for tick in range(180):
		sim.step(empty_pair())
		var cursor:=audio.played.size()
		audio.sync(sim,false)
		for e in sim.events:
			if e.kind!="throw_slam":continue
			found=true
			var custom:=audio.data_contact_id(sim,e)
			var played: Array=audio.played.slice(cursor)
			var land:=played.filter(func(p):return p.id=="land" and int(p.player)==1).size()
			check(land==(1 if custom.is_empty() else 0),id+"/"+move+" 专属重摔替换land，普通投保留land")
			if not custom.is_empty():check(played.filter(func(p):return p.id==custom).size()==1,id+"专属重摔只响一次")
			slams.append({"fighter":id,"move":move,"tick":sim.tick,"custom":custom,"played":played,"suppressed":audio.suppressed.duplicate(true)})
	check(found,id+"/"+move+" 真实投技撞地")
	audio.free()

func routing_case() -> void:
	var sim:=UfeContentDatabase.match_for("gomora","gomora")
	var audio:=fresh_audio()
	audio.sync(sim,false)
	var mix_bus:=AudioServer.get_bus_index("UFE_mix")
	check(mix_bus>0 and AudioServer.get_bus_volume_db(mix_bus)<=-3.0,"混音输出保留3dB线性余量")
	for key in ["sfx","voice","music"]:
		check(AudioServer.get_bus_send(AudioServer.get_bus_index("UFE_"+key))=="UFE_mix","全部声音统一经过混音余量，不改变分类音量设置")
	check(str(audio.character_states[0])=="idle","呼吸绑定待机状态")
	check(audio.character_players[0].stream==audio.stream("gomora_breath"),"待机呼吸使用角色播放器")
	sim.step([UfeInputFrame.make(1),UfeInputFrame.make()])
	audio.sync(sim,false)
	check(audio.stopped.any(func(e):return int(e.player)==0 and e.reason=="state_exit" and int(e.tick)==sim.tick),"离开待机同tick停止呼吸")
	check(str(audio.character_states[0]).is_empty() and not audio.character_players[0].playing,"状态退出立即停声")
	sim._start(sim.fighters[0],"taunt")
	sim.step(empty_pair())
	audio.sync(sim,false)
	# 期望声键从招式数据读取，换声（原声/合成备选）后不需改测试。
	var taunt_id:=str(sim.fighters[0].definition.moves["taunt"].frames[0].events[0].id)
	check(audio.character_players[0].stream==audio.stream(taunt_id),"挑衅帧发声覆盖自动起手声")
	check(audio.played.filter(func(e):return e.id==taunt_id and e.bus!="UFE_voice").is_empty(),"帧发声不进入一次性池")
	# 同角色双方同时发声必须各响一次，不能用全局tick+id去重。
	sim.tick+=1
	sim.events=[{"kind":"sound","id":"gomora_roar_hurt","player":0},{"kind":"sound","id":"gomora_roar_hurt","player":1}]
	var cursor:=audio.played.size()
	audio.sync(sim,false)
	check(audio.played.slice(cursor).filter(func(e):return e.id=="gomora_roar_hurt").size()==2,"同角色双方发声互不吞声")
	for i in range(2):check(audio.character_players[i].stream==audio.stream("gomora_roar_hurt"),"角色发声播放器互相覆盖")
	sim.tick+=1
	sim.events=[{"kind":"sound","id":"gomora_roar_hurt","player":0},{"kind":"sound","id":"gomora_roar_hurt","player":0},{"kind":"sound","id":"gomora_roar_threat","player":0},{"kind":"sound","id":"gomora_roar_hurt","player":0}]
	cursor=audio.played.size();audio.sync(sim,false)
	check(audio.played.size()-cursor==3 and audio.character_players[0].stream==audio.stream("gomora_roar_hurt"),"相邻重复发声合并，不同发声按最后事件覆盖")
	audio.ceremony(sim,75,0)
	check(audio.character_players[0].stream==audio.stream(str(audio.catalog.voices["gomora"]["intro"])),"登场选择声音配置的intro")
	for id in audio.catalog.voices:
		for sid in audio.catalog.voices[id].values():check(audio.catalog.sounds[sid].get("usage")=="character_voice","发声映射必须声明用途 "+sid)
	# 测试同tick另一玩家的land不被连带吞掉，以及无效专属资源的通用回退。
	var seven:=UfeContentDatabase.match_for("ultraseven","ultraman")
	seven.tick=sim.tick+1
	seven.events=[{"kind":"throw_slam","player":0,"move":"motion_41236"},{"kind":"sound","player":1,"id":"land"},{"kind":"sound","player":0,"id":"land"}]
	cursor=audio.played.size();audio.sync(seven,false)
	check(audio.played.slice(cursor).filter(func(e):return e.id=="land" and int(e.player)==0).size()==1,"只替换受投者该次land")
	seven.fighters[0].definition.moves.motion_41236=seven.fighters[0].definition.moves.motion_41236.duplicate(true)
	seven.fighters[0].definition.moves.motion_41236.audio.throw_slam="missing_audioqa_fixture"
	seven.tick+=1;cursor=audio.played.size();audio.sync(seven,false)
	check(audio.played.slice(cursor).filter(func(e):return e.id=="land" and int(e.player)==1).size()==1,"无效专属资源仍保留通用land")
	audio.free()
	var preview:=fresh_audio()
	preview.cue("gomora_roar_threat")
	preview.cue("gomora_roar_threat")
	check(preview.played.size()==2 and int(preview.played[0].player)!=int(preview.played[1].player),"兼容旧VS的无player发声接口，双方各用一个角色声道")
	check(preview.played.all(func(e):return e.bus=="UFE_voice"),"VS发声也不进入一次性池")
	preview.free()

func run() -> void:
	for id in ["ultraman","zetton","ultraseven","gomora"]:
		for level in [1,2,3]:check(release_case(id,level,true)==release_case(id,level,false),id+str(level)+" 重放逐tick模拟与声音调度一致")
	for pair in [["ultraseven","motion_41236"],["gomora","throw_forward"],["ultraman","throw_forward"],["zetton","throw_forward"]]:slam_case(pair[0],pair[1])
	routing_case()
	DirAccess.make_dir_recursive_absolute(OUT.get_base_dir())
	FileAccess.open(OUT,FileAccess.WRITE).store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"releases":releases,"slams":slams},"\t"))
	print("AUDIOQA_DISPATCH "+("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
