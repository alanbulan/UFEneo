extends SceneTree
var errors: Array=[]
func check(ok: bool,what: String) -> void:
	if not ok:errors.append(what);printerr(what)
func _initialize() -> void:call_deferred("run")
func scan(value: Variant,path: String) -> void:
	if value is Dictionary:
		if value.has("display_scale") or value.has("visual_scale") or value.has("effect") or str(value.get("texture","")).begins_with("res://assets/effects/"):
			check(UfeEffectGeometry.valid(value),"特效比例违规 "+path)
		if value.has("texture") and value.has("rects"):
			var tex: Texture2D=load(value.texture)
			check(tex!=null,"特效纹理缺失 "+path)
			if tex!=null:
				for r in value.rects:check(Rect2(Vector2.ZERO,tex.get_size()).encloses(Rect2(r[0],r[1],r[2],r[3])),"特效裁片越界 "+path)
		for key in value:scan(value[key],path+"/"+str(key))
	elif value is Array:
		for i in range(value.size()):scan(value[i],path+"/"+str(i))
func files(path: String) -> void:
	for file in DirAccess.get_files_at(path):
		if file.ends_with(".json"):scan(UfeContentDatabase.read_json(path+"/"+file),path+"/"+file)
	for dir in DirAccess.get_directories_at(path):files(path+"/"+dir)
func finish_pending_audio_mix() -> Dictionary:
	# AudioStreamPlayer已free；等混音线程实际接收停止队列，避免退出仍持WAV/playback。
	var started: int=Time.get_ticks_usec()
	var previous: float=AudioServer.get_time_since_last_mix()
	var advances: int=0
	while advances<2 and Time.get_ticks_usec()-started<500000:
		await process_frame
		var current: float=AudioServer.get_time_since_last_mix()
		if current<previous:advances+=1
		previous=current
	check(advances>=2,"测试退出前实际混音线程未完成两轮播放退役")
	return {"observed_mix_advances":advances,"elapsed_usec":Time.get_ticks_usec()-started,"limit_usec":500000,"driver":str(AudioServer.call("get_driver_name"))}
func check_audio_sources(audio: UfeSideAudio,sources: Dictionary) -> void:
	var raw_records: Variant=sources.get("records")
	check(raw_records is Array,"声音来源records必须为数组")
	var records: Array=raw_records if raw_records is Array else []
	var raw_sounds: Variant=audio.catalog.get("sounds")
	check(raw_sounds is Dictionary,"运行声音sounds必须为字典")
	var sounds: Dictionary=raw_sounds if raw_sounds is Dictionary else {}
	var installed_count: int=0
	for index in range(records.size()):
		var value: Variant=records[index]
		check(value is Dictionary,"声音来源记录必须为字典 #"+str(index))
		if not (value is Dictionary):continue
		var record: Dictionary=value
		var id: String=str(record.get("id","<record #"+str(index)+">"))
		for field in ["id","path","license","duration_seconds","true_peak_dbfs","purpose","source_kind"]:
			check(record.has(field),"声音来源缺字段 "+id+"/"+str(field))
		check(record.get("id") is String and not id.is_empty(),"声音ID格式 "+id)
		var path: String=str(record.get("path",""))
		var path_valid: bool=record.get("path") is String and not path.is_empty()
		var license_value: Variant=record.get("license")
		var license_valid: bool=license_value is String and not str(license_value).is_empty()
		check(path_valid and FileAccess.file_exists(path) and license_valid,"声音文件与许可 "+id)
		var duration: Variant=record.get("duration_seconds")
		var peak: Variant=record.get("true_peak_dbfs")
		var numbers_valid: bool=typeof(duration) in [TYPE_INT,TYPE_FLOAT] and typeof(peak) in [TYPE_INT,TYPE_FLOAT]
		check(numbers_valid and float(duration)>0 and float(peak)<=-1.8,"音频非空且预留峰值 "+id)
		var status: String=str(record.get("runtime_status","installed"))
		check(status in ["installed","installed_pending_user_listening","pending_install"],"声音接入状态合法 "+id)
		if status in ["installed","installed_pending_user_listening"]:installed_count+=1
		if status=="pending_install":
			check(not sounds.has(id),"待装声音不得提前写入运行映射 "+id)
			check(path_valid and FileAccess.file_exists(path) and load(path) is AudioStreamWAV,"待装声音文件仍须可加载 "+id)
		else:
			check(sounds.has(id) and audio.stream(id)!=null and audio.resolve(id)==id,"直接声音ID不能被旧别名覆盖 "+id)
		var purpose: String=str(record.get("purpose",""))
		check(record.get("purpose") is String and not purpose.is_empty(),"声音用途必须声明 "+id)
		var source_kind: String=str(record.get("source_kind",""))
		check(record.get("source_kind") is String and not source_kind.is_empty(),"声音来源类型必须声明 "+id)
		if purpose in ["voice","music"]:check(source_kind=="episode","剧集来源显式标记 "+id)
	check(sounds.size()==installed_count,"已安装声音来源清单覆盖运行时")
func capture_phase_audio_key(index: int,stage: Dictionary) -> String:
	# 捕获首相由capture_begin进入，其余相由capture_phase进入；受方不重复播state_entry。
	return "capture_begin" if index==0 else "capture_phase:"+str(stage.id)
func capture_external_audio(audio: UfeSideAudio,actor: UfeFighterDefinition,victim: UfeFighterDefinition,clips: Dictionary) -> Dictionary:
	var coverage: Dictionary={}
	for move_id in actor.moves:
		var move: Dictionary=actor.moves[move_id]
		if not move.has("capture") or not UfeCaptureResolver.valid_move(move):continue
		if not actor.command_table.any(func(entry):return str(entry.move)==str(move_id)):continue
		var stages: Array=move.capture.stages
		for index in range(stages.size()):
			var stage: Dictionary=stages[index]
			var event_key: String=capture_phase_audio_key(index,stage)
			var binding: String=str(move.get("audio",{}).get(event_key,""))
			var sound_id: String=audio.resolve(binding)
			# 必须是当前招式的明确专属声音绑定，通用受击声/别名不能补受方空事件。
			if binding.is_empty() or sound_id!=binding or not audio.catalog.sounds.has(sound_id):continue
			if not str(audio.catalog.sounds[sound_id].path).begins_with("res://assets/audio/characters/"+actor.id+"/capture/"):continue
			if audio.stream(sound_id)==null:continue
			var references: Dictionary={}
			for frame in stage.victim_frames:
				var clip: String=str(frame.animation) if frame is Dictionary else str(stage.victim_animation)
				var frame_index: int=int(frame.frame) if frame is Dictionary else int(frame)
				if not clips.has(clip) or frame_index<0 or frame_index>=victim.state_frames.get(clip,[]).size():continue
				if not references.has(clip):references[clip]=[]
				if not references[clip].has(frame_index):references[clip].append(frame_index)
			for clip in references:
				if not coverage.has(clip):coverage[clip]=[]
				coverage[clip].append({"actor":actor.id,"move":str(move_id),"phase":str(stage.id),"event":event_key,"sound":sound_id,"victim":victim.id,"frames":references[clip]})
	return coverage
func capture_input(frame: int) -> UfeInputFrame:
	# 与已装主游戏捕获审计相同的真实41236×；命中/落空两组逐tick输入相同。
	match frame:
		20:return UfeInputFrame.make(-1,0)
		21:return UfeInputFrame.make(-1,-1)
		22:return UfeInputFrame.make(0,-1)
		23:return UfeInputFrame.make(1,-1)
		24:return UfeInputFrame.make(1,0,UfeInputFrame.THROW)
	return UfeInputFrame.make()
func capture_audio_case(hit: bool) -> Dictionary:
	var sim: UfeMatchDirector=UfeBattleFormCatalog.match_for("ultraman-teo","zetton",true)
	# 仅设置开局站位与费用；之后不摆动作、事件、生命值或命中结果。
	sim.fighters[0].x=430
	sim.fighters[1].x=580 if hit else 1130
	sim.fighters[0].stats.energy=500
	var audio: UfeSideAudio=UfeSideAudio.new()
	root.add_child(audio)
	var move: Dictionary=sim.fighters[0].definition.moves.motion_41236
	var expected: Dictionary={}
	for index in range(move.capture.stages.size()):
		var stage: Dictionary=move.capture.stages[index]
		expected[capture_phase_audio_key(index,stage)]=str(move.audio[capture_phase_audio_key(index,stage)])
	var stage_events: Array=[]
	var stage_played: Array=[]
	var seen_clips: Array=[]
	var trace: Array=[]
	var all_inputs: Array=[]
	var starts: int=0
	var failures: int=0
	var cursor: int=audio.played.size()
	for frame in range(180):
		var inputs: Array=[capture_input(frame),UfeInputFrame.make()]
		var packed: Array=[inputs[0].pack(),inputs[1].pack()]
		all_inputs.append(packed)
		sim.step(inputs)
		var before_audio: String=sim.state_hash()
		audio.sync(sim,false)
		check(sim.state_hash()==before_audio,"捕获音频只读模拟 "+str(hit)+"/"+str(sim.tick))
		var actual: Array=audio.played.slice(cursor).duplicate(true)
		cursor=audio.played.size()
		audio.sync(sim,false)
		check(audio.played.size()==cursor,"同tick捕获声音不重复 "+str(hit)+"/"+str(sim.tick))
		var clip: String=sim.fighters[1].animation_key()
		if clip.begins_with("capture_") and not seen_clips.has(clip):seen_clips.append(clip)
		for event in sim.events:
			if event.kind=="capture_start":starts+=1
			if event.kind=="capture_fail":failures+=1
			var event_key: String=str(event.kind)
			if event_key=="capture_phase":event_key+=":"+str(event.phase)
			if not expected.has(event_key):continue
			var sound_id: String=str(expected[event_key])
			var matches: Array=actual.filter(func(row):return str(row.id)==sound_id and int(row.tick)==sim.tick and int(row.player)==0)
			var active: bool=audio.voices.any(func(node):return node.playing and node.stream==audio.cache.get(sound_id))
			check(hit and matches.size()==1 and active,"捕获阶段由真实事件播放专属声 "+event_key)
			stage_events.append({"tick":sim.tick,"event":event.duplicate(true),"sound":sound_id,"played":matches,"active_player":active})
		for row in actual:
			if str(row.id) in expected.values():stage_played.append(row)
		trace.append({"tick":sim.tick,"inputs":packed,"state_hash":before_audio,"events":sim.events.duplicate(true),"played":actual,"victim_clip":clip})
	check(starts==1,"真实41236×只起一次捕获 "+str(hit))
	if hit:
		check(stage_events.size()==expected.size() and stage_played.size()==expected.size(),"命中完整捕获阶段各播一次专属声")
		for clip in ["capture_enclosed","capture_shrinking","capture_restore"]:check(clip in seen_clips,"真实捕获消费受方动作 "+clip)
		check(failures==0 and int(sim.fighters[1].stats.hp)==sim.fighters[1].definition.max_health-int(move.damage),"捕获自然完成并扣本人招式伤害")
	else:
		check(failures==1 and stage_events.is_empty() and stage_played.is_empty() and seen_clips.is_empty(),"相同输入未抓中不误播包罩缩小恢复阶段")
		check(int(sim.fighters[1].stats.hp)==sim.fighters[1].definition.max_health,"未抓中基线无捕获伤害")
	check(not sim.fighters[0].motion.has("capture") and not sim.fighters[1].motion.has("capture_victim"),"捕获/落空自然收招清关系 "+str(hit))
	var result: Dictionary={"case":"hit" if hit else "miss","initial_positions":[430,580 if hit else 1130],"initial_energy":500,"starts":starts,"failures":failures,"expected_stage_audio":expected,"stage_events":stage_events,"stage_played":stage_played,"victim_clips":seen_clips,"victim_hp":int(sim.fighters[1].stats.hp),"inputs":all_inputs,"inputs_sha256":JSON.stringify(all_inputs).sha256_text(),"trace":trace}
	audio.free()
	return result
func run() -> void:
	for bad in [{"display_scale":[0.5,1]},{"visual_scale":1.25},{"display_scale":[2,2]},{"display_scale":[1,1],"visual_scale":4}]:check(not UfeEffectGeometry.valid(bad),"拒绝未声明或分数比例")
	check(UfeEffectGeometry.valid({}) and UfeEffectGeometry.valid({"display_scale":[1,1]}),"默认特效1倍")
	check(UfeEffectGeometry.valid({"display_scale":[2,2],"pixel_integer_scale":true}),"显式整数倍允许")
	files("res://content/presentation")
	files("res://content/fighters")
	var audio:=UfeSideAudio.new()
	root.add_child(audio)
	var sources: Dictionary=UfeContentDatabase.read_json("res://content/audio/sources.json")
	check_audio_sources(audio,sources)
	var capture_actor: UfeFighterDefinition=UfeBattleFormCatalog.prepare("ultraman-teo",true).definition
	var external_audio: Dictionary={}
	for id in ["ultraman","zetton"]:
		var clips: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%id).clips
		var victim: UfeFighterDefinition=UfeContentDatabase.fighter(id,true)
		var covered: Dictionary=capture_external_audio(audio,capture_actor,victim,clips)
		external_audio[id]=covered
		for key in clips:
			check(not clips[key].get("audio_events",[]).is_empty() or not covered.get(key,[]).is_empty(),id+"动作缺声音事件 "+key)
			for e in clips[key].get("audio_events",[]):check(audio.stream(audio.resolve(e.id))!=null,id+"声音事件无法播放 "+key)
	audio.configure_battle_music(["ultraseven","ultraman-taro"],UfeBattleStageCatalog.default_id(),{"battle_music":"auto","dynamic_music":true})
	for context in ["menu","select","battle"]:
		audio.set_context(context)
		var director:=audio.music_director
		var expected_id: String="seven-battle" if context=="battle" else context
		check(audio.context==context and director.context==context and director.current_id==expected_id,"流程音乐上下文与自动选曲 "+context)
		var slot: int=director.slot_ids.find(expected_id)
		check(slot>=0 and director.players[slot].playing and director.players[slot].stream==director.music_cache.get(expected_id),"流程音乐实际活动槽 "+context)
	audio.preview_music("off")
	check(audio.context=="preview" and audio.music_director.current_id.is_empty(),"关闭BGM预览发起淡出")
	audio.set_context("select")
	check(audio.context=="select" and audio.music_director.context=="select" and audio.music_director.current_id=="select","预览后相同选人上下文可恢复")
	var driver:=UfePhase3AudioReview.new()
	var sim:=UfeContentDatabase.match_for()
	driver.prepare_match(sim)
	var hits: Dictionary={}
	for tick in range(75,driver.length_frames()):
		if sim.finished:break
		sim.step([driver.sample(tick,sim),driver.second_sample(tick)])
		for e in sim.events:
			if e.kind=="hit":hits[str(e.player)+"/"+str(e.move)]=true
	check(hits.has("0/special3") and hits.has("1/special3"),"有声回合双方三级必杀真实命中")
	check(sim.finished and sim.winner==0,"有声单回合由真实攻击打至KO")
	var capture_hit: Dictionary=capture_audio_case(true)
	var capture_miss: Dictionary=capture_audio_case(false)
	check(capture_hit.inputs==capture_miss.inputs,"捕获命中/落空使用完全相同的真实输入")
	audio.free()
	var audio_cleanup: Dictionary=await finish_pending_audio_mix()
	var evidence: FileAccess=FileAccess.open("res://reports/phase3-fx-audio-evidence.json",FileAccess.WRITE)
	check(evidence!=null,"声音回归证据文件可写")
	if evidence!=null:
		evidence.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"round_hits":hits.keys(),"winner":sim.winner,"tick":sim.tick,"capture_external_audio":external_audio,"capture_cases":[capture_hit,capture_miss],"audio_exit_cleanup":audio_cleanup},"\t"))
		evidence.close()
	print("PHASE3_FX_AUDIO "+("PASS" if errors.is_empty() else str(errors)))
	# 先退回事件循环释放本次测试局部引用，再退出，避免即时quit残留测试对象。
	call_deferred("quit",0 if errors.is_empty() else 1)
