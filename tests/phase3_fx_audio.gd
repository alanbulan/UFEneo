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
	# 与已装主游戏捕获审计相同的真实I+后上；命中/落空两组逐tick输入相同。
	if frame==24:return UfeInputFrame.make(-1,1,UfeInputFrame.RANGED)
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
	check(starts==1,"真实I+后上只起一次捕获 "+str(hit))
	if hit:
		check(stage_events.size()==expected.size() and stage_played.size()==expected.size(),"命中完整捕获阶段各播一次专属声")
		for clip in ["capture_enclosed","capture_shrinking","capture_restore"]:check(clip in seen_clips,"真实捕获消费受方动作 "+clip)
		check(failures==0 and int(sim.fighters[1].stats.hp)==sim.fighters[1].definition.max_health-int(move.damage),"捕获自然完成并扣本人招式伤害")
	else:
		check(failures==1 and stage_events.is_empty() and stage_played.is_empty() and seen_clips.is_empty(),"相同输入未抓中不误播包罩缩小恢复阶段")
		check(int(sim.fighters[1].stats.hp)==sim.fighters[1].definition.max_health,"未抓中基线无捕获伤害")
	check(not sim.fighters[0].motion.has_capture() and not sim.fighters[1].motion.has_capture_victim(),"捕获/落空自然收招清关系 "+str(hit))
	var result: Dictionary={"case":"hit" if hit else "miss","initial_positions":[430,580 if hit else 1130],"initial_energy":500,"starts":starts,"failures":failures,"expected_stage_audio":expected,"stage_events":stage_events,"stage_played":stage_played,"victim_clips":seen_clips,"victim_hp":int(sim.fighters[1].stats.hp),"inputs":all_inputs,"inputs_sha256":JSON.stringify(all_inputs).sha256_text(),"trace":trace}
	audio.free()
	return result
func check_zoffy_startup_attachments() -> void:
	var registry: Dictionary=UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	var q_effects: Dictionary={"zoffy_fx_q_charge_start":true,"zoffy_fx_q_charge":true,"zoffy_fx_q_charge_stop":true}
	var specs: Array=[
		{"move":"special","effect":"zoffy_fx_zap_charge_start","startup":24},
		{"move":"special2","effect":"zoffy_fx_frost_charge_start","startup":32},
		{"move":"special3","effect":"zoffy_fx_m87_charge_start","startup":46}
	]
	for raw_spec: Variant in specs:
		if not (raw_spec is Dictionary):
			check(false,"佐菲起手回归配置格式错误")
			continue
		var spec: Dictionary=raw_spec as Dictionary
		var move_id: String=str(spec.get("move",""))
		var effect_id: String=str(spec.get("effect",""))
		var move: Dictionary=UfeContentDatabase.read_json("res://content/fighters/zoffy/moves/%s.json"%move_id)
		var startup: int=int(move.get("startup",-1))
		var expected_startup: int=int(spec.get("startup",-1))
		check(startup==expected_startup,move_id+"起手长度与回归契约不一致")
		var raw_frames: Variant=move.get("frames",[])
		if not (raw_frames is Array):
			check(false,move_id+"招式帧数据不是数组")
			continue
		var frames: Array=raw_frames as Array
		if not registry.has(effect_id):
			check(false,move_id+"起手正式FX未登记 "+effect_id)
			continue
		var seen_sprites: Array=[]
		for tick in range(startup):
			check(tick<frames.size(),move_id+"起手帧缺失 "+str(tick))
			if tick>=frames.size():continue
			var raw_frame: Variant=frames[tick]
			check(raw_frame is Dictionary,move_id+"起手帧不是字典 "+str(tick))
			if not (raw_frame is Dictionary):continue
			var frame: Dictionary=raw_frame as Dictionary
			var raw_attachments: Variant=frame.get("attachments",[])
			if not (raw_attachments is Array):
				check(false,move_id+"起手逐tick缺附件 "+str(tick))
				continue
			var attachments: Array=raw_attachments as Array
			check(not attachments.is_empty(),move_id+"起手逐tick缺附件 "+str(tick))
			if attachments.is_empty():continue
			var matching: Array=[]
			for raw_attachment: Variant in attachments:
				check(raw_attachment is Dictionary,move_id+"附件不是字典 "+str(tick))
				if not (raw_attachment is Dictionary):continue
				var attachment_data: Dictionary=raw_attachment as Dictionary
				var actual_effect: String=str(attachment_data.get("effect",""))
				check(not q_effects.has(actual_effect),move_id+"起手误用Q周身圈 "+str(tick))
				check(registry.has(actual_effect),move_id+"附件未登记 "+actual_effect)
				if actual_effect==effect_id:matching.append(attachment_data)
			if matching.is_empty():
				check(false,move_id+"起手缺少正式FX "+str(tick))
				continue
			check(matching.size()==1,move_id+"起手正式FX数量异常 "+str(tick))
			var attachment: Dictionary=matching[0] as Dictionary
			var clip: Dictionary=registry[effect_id] as Dictionary
			var raw_rects: Variant=clip.get("rects",[])
			if not (raw_rects is Array):
				check(false,move_id+"正式FX无裁片")
				continue
			var rects: Array=raw_rects as Array
			check(not rects.is_empty(),move_id+"正式FX无裁片")
			if rects.is_empty():continue
			var sprite: int=int(attachment.get("sprite",-1))
			check(sprite>=0 and sprite<rects.size(),move_id+"起手FX索引越界 "+str(tick))
			if sprite<0 or sprite>=rects.size():continue
			var expected_sprite: int=UfeEffectTimeline.phase(clip,tick,bool(clip.get("loop",false)))
			check(sprite==expected_sprite,move_id+"起手FX未按正式ticks序列 "+str(tick))
			seen_sprites.append(sprite)
		check(seen_sprites.size()==startup,move_id+"起手FX未逐tick覆盖")
		var unique_sprites: Dictionary={}
		for sprite in seen_sprites:unique_sprites[sprite]=true
		check(unique_sprites.size()>1,move_id+"起手FX静止复用单帧")
func zoffy_origin_has_pixel(image: Image,clip: Dictionary,sprite: int,origin: Array) -> bool:
	# 这里只核束根2px邻域有本人像素，不能据此签收手部解剖或动作观感。
	var rects: Array=clip.get("rects",[])
	if image==null or sprite<0 or sprite>=rects.size() or origin.size()!=2:return false
	var rect: Array=rects[sprite]
	var anchors: Array=clip.get("anchors",[])
	var anchor: Array=anchors[sprite] if sprite<anchors.size() else clip.get("anchor",[])
	if rect.size()!=4 or anchor.size()!=2:return false
	var point:=Vector2i(int(anchor[0])+int(origin[0]),int(anchor[1])-int(origin[1]))
	for dy in range(-2,3):
		for dx in range(-2,3):
			if dx*dx+dy*dy>4:continue
			var local:=point+Vector2i(dx,dy)
			var pixel:=local+Vector2i(int(rect[0]),int(rect[1]))
			if local.x<0 or local.y<0 or local.x>=int(rect[2]) or local.y>=int(rect[3]):continue
			if pixel.x>=0 and pixel.y>=0 and pixel.x<image.get_width() and pixel.y<image.get_height() and image.get_pixelv(pixel).a>=200.0/255.0:return true
	return false
func check_zoffy_special_timelines() -> void:
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/zoffy/animations/manifest.json")
	for move_id in ["special","special2","special3","air_special"]:
		var move: Dictionary=UfeContentDatabase.read_json("res://content/fighters/zoffy/moves/%s.json"%move_id)
		var frames: Array=move.get("frames",[])
		var clip: Dictionary=manifest.clips[move_id]
		var texture:=load(str(clip.texture)) as Texture2D
		var image: Image=texture.get_image() if texture!=null else null
		check(image!=null,move_id+"正式人物图集可读")
		check(frames.size()==int(move.startup)+int(move.active)+int(move.recovery) and UfeEffectTimeline.length(clip)==frames.size(),move_id+"人物时长与完整招式计时一致")
		var shot_ticks: Array[int]=[]
		for tick in range(frames.size()):
			var frame: Dictionary=frames[tick]
			check(int(frame.sprite)==UfeEffectTimeline.phase(clip,tick,bool(clip.get("loop",false))),move_id+"人物准备发射持势收势与清单逐tick一致 "+str(tick))
			for shot_value in frame.get("shots",[]):
				var shot: Dictionary=shot_value
				shot_ticks.append(tick)
				var origins: Dictionary=shot.get("origin_by_frame",{})
				var origin: Array=origins.get(str(tick),shot.get("anchor",shot.get("spawn",[])))
				# 发射闪光可以不额外挂载；若挂载，不能沿用另一招的旧手点。
				for attachment_value in frame.get("attachments",[]):
					var attachment: Dictionary=attachment_value
					if not str(attachment.get("effect","")).ends_with("_start"):continue
					var point: Array=attachment.get("anchor",[])
					var aligned: bool=point.size()==2 and origin.size()==2
					if aligned:
						var delta:=Vector2i(int(point[0])-int(origin[0]),int(point[1])-int(origin[1]))
						aligned=delta.length_squared()<=4
					check(aligned,move_id+"发射附件偏离同帧束根2px/tick"+str(tick))
				var end_tick: int=tick+int(shot.get("life",1)) if bool(shot.get("beam",false)) else tick+1
				check(end_tick<=frames.size(),move_id+"束寿命不越过人物招式结尾")
				for beam_tick in range(tick,mini(end_tick,frames.size())):
					var beam_origin: Array=origins.get(str(beam_tick),shot.get("anchor",shot.get("spawn",[])))
					check(zoffy_origin_has_pixel(image,clip,int(frames[beam_tick].sprite),beam_origin),move_id+"发射及持束阶段束根2px内有本人像素/tick"+str(beam_tick))
		check(shot_ticks==[int(move.startup)],move_id+"仅在起手结束的指定tick发射一次")
func check_zoffy_pose_clock_validation() -> void:
	var valid: Dictionary=UfeContentDatabase.read_json("res://content/fighters/zoffy/moves/special.json")
	check(UfeMoveData.validate(valid),"姿势束正式数据通过验证")
	for overrides in [{"tick_clock":true},{"tick_clock":"unknown"},{"beam":false},{"speed":1},{"vy":-1},{"life":0},{"life":26.5},{"life":73},{"integer_path":[[0,0]]},{"capture":true}]:
		var bad: Dictionary=valid.duplicate(true)
		var shot: Dictionary=bad.frames[int(bad.startup)].shots[0]
		shot.merge(overrides,true)
		check(not UfeMoveData.validate(bad),"非法姿势束时钟拒收 "+str(overrides))
	for container in ["projectile","counter_shot"]:
		var bad: Dictionary=valid.duplicate(true)
		var shot: Dictionary=bad.frames[int(bad.startup)].shots[0].duplicate(true)
		if container=="projectile":bad.projectile=shot
		else:bad.frames[int(bad.startup)].counter_shot=shot
		check(not UfeMoveData.validate(bad),"姿势束必须由显式shots触发 "+container)
func check_zoffy_beam_clock() -> void:
	var registry: Dictionary=UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/zoffy/animations/manifest.json")
	var cinematic:=UfeSuperCinematic.new()
	root.add_child(cinematic)
	for move_id in ["special","special3","air_special"]:
		var move: Dictionary=UfeContentDatabase.read_json("res://content/fighters/zoffy/moves/%s.json"%move_id)
		var shot: Dictionary=move.frames[int(move.startup)].shots[0]
		var clip: Dictionary=registry[str(shot.effect)]
		var texture:=load(str(manifest.clips[move_id].texture)) as Texture2D
		var image: Image=texture.get_image()
		for facing in [1,-1]:
			for contact in [false,true]:
				# 真按P（空中先按独立跳跃）；不中断全程逐tick看正式束Sprite。
				var sim:=UfeContentDatabase.match_for("zoffy","ultraman")
				var actor:=sim.fighters[0]
				actor.x=640-facing*350; actor.facing=facing
				actor.stats.energy=int(move.energy_cost)
				sim.fighters[1].x=actor.x+facing*(220 if contact else 700)
				sim.fighters[1].facing=-facing
				var label: String="%s束时钟/%d/%s/"%[move_id,facing,"命中" if contact else "落空"]
				var ages: Array[int]=[]
				var bad_pose_ticks: Array[int]=[]
				var bad_origins: Array[int]=[]
				var bad_rects: Array[int]=[]
				var frozen_samples: int=0
				var hit_count: int=0
				var sent: bool=false
				for tick in range(160):
					var buttons: int=0
					if move_id=="air_special":
						if tick==0:buttons=UfeInputFrame.JUMP
						elif not sent and actor.state=="air" and actor.height>0:
							buttons=UfeInputFrame.SPECIAL; sent=true
					elif tick==0:buttons=UfeInputFrame.SPECIAL
					sim.step([UfeInputFrame.make(0,0,buttons),UfeInputFrame.make()])
					for event in sim.events:
						if event.kind=="hit" and str(event.move)==move_id:hit_count+=1
					var before: String=sim.state_hash()
					cinematic.sync(sim,0,0)
					check(sim.state_hash()==before,label+"表现只读模拟")
					var beams: Array=sim.projectiles.filter(func(p):return bool(p.get("beam",false)) and str(p.move)==move_id)
					var visible: Array=cinematic.beam_parts.filter(func(sprite):return sprite.visible)
					check(visible.size()==beams.size(),label+"正式表现不留残束")
					if beams.is_empty():continue
					var projectile: Dictionary=beams[0]
					var age: int=int(projectile.age)
					if not ages.is_empty() and ages.back()==age:frozen_samples+=1
					else:ages.append(age)
					if actor.move_tick!=int(move.startup)+age:bad_pose_ticks.append(actor.move_tick)
					var origin: Array=UfeProjectileResolver.beam_origin(actor,projectile)
					if not zoffy_origin_has_pixel(image,manifest.clips[move_id],int(actor.frame().sprite),origin):bad_origins.append(actor.move_tick)
					var expected: Array=clip.rects[clampi(age,0,clip.rects.size()-1)]
					if visible.size()!=1 or visible[0].region_rect!=Rect2(expected[0],expected[1],expected[2],expected[3]):bad_rects.append(age)
				check(ages==range(int(shot.life)),label+"首相0到尾相各走一tick，age="+str(ages))
				check(bad_pose_ticks.is_empty(),label+"发射持势与束相同tick "+str(bad_pose_ticks))
				check(bad_origins.is_empty(),label+"每个实际显示tick束根贴本人 "+str(bad_origins))
				check(bad_rects.is_empty(),label+"正式Sprite逐相对应 "+str(bad_rects))
				if contact and move_id!="air_special":check(hit_count==1 and frozen_samples>0,label+"命中一次且停顿不吞束相")
				elif not contact:check(hit_count==0,label+"远处真实落空")
	cinematic.free()
func check_zoffy_air_special_fx_cleanup() -> void:
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/zoffy/animations/manifest.json")
	var view:=UfeSideView.new()
	for facing in [1,-1]:
		for after_shot in [false,true]:
			var sim:=UfeContentDatabase.match_for("zoffy","ultraman")
			view.simulation=sim
			view.manifests=[manifest,{}]
			var actor:=sim.fighters[0]
			actor.x=640-facing*350; actor.facing=facing; actor.stats.energy=1000
			sim.fighters[1].x=640+facing*350; sim.fighters[1].facing=-facing
			var label: String="空中必杀FX/%d/%s/"%[facing,"发射后落地" if after_shot else "发射前落地"]
			var sent: bool=false
			var started: bool=false
			var landed: bool=false
			var seen_beam: bool=false
			for tick in range(90):
				var input:=UfeInputFrame.make(0,0,UfeInputFrame.JUMP if tick==0 else 0)
				var ready: bool=actor.vy<=0 if after_shot else actor.vy<0 and actor.height<=actor.definition.jump_speed*2
				if not sent and actor.state=="air" and ready:
					input=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL); sent=true
				var previous_height: int=actor.height
				sim.step([input,UfeInputFrame.make()])
				started=started or actor.move_id=="air_special"
				var live_beams: Array=sim.projectiles.filter(func(projectile):return int(projectile.get("source_owner",projectile.owner))==0 and str(projectile.move)=="air_special")
				seen_beam=seen_beam or not live_beams.is_empty()
				if started and not landed and previous_height>0 and actor.height==0:
					landed=true
					check(actor.state=="land" and actor.move_id.is_empty() and view._animation(actor,manifest).get("key","")=="land",label+"触地当tick显示land且清空招式")
				if landed:
					check(live_beams.is_empty(),label+"触地当tick及以后无残束或补发/tick"+str(tick))
					check(view.attachments_for(0).is_empty(),label+"触地当tick及以后无人物遗留FX/tick"+str(tick))
			check(sent and started and landed and seen_beam==after_shot,label+"真实跳跃输入覆盖发射前后触地")
	view.free()
func check_target_footsteps() -> void:
	for fighter_id in ["zoffy","ultraman-king","ultraman-justice","ultraman-zero","mother-of-ultra","ultraman-gaia","father-of-ultra"]:
		var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%fighter_id)
		for direction in [1,-1]:
			var walk_key: String="walk_forward" if direction==1 else "walk_back"
			var clip: Dictionary=manifest.clips[walk_key]
			var duration:=0
			for ticks in clip.ticks:duration+=int(ticks)
			for facing in [1,-1]:
				var foot_audio:=UfeSideAudio.new()
				root.add_child(foot_audio)
				var binding: Dictionary=foot_audio.catalog.footsteps[fighter_id][walk_key]
				check(int(binding.cycle_ticks)==duration,fighter_id+"/"+walk_key+"脚步周期与本人动作一致")
				var foot_sim:=UfeContentDatabase.match_for(fighter_id,"ultraman")
				foot_sim.fighters[0].x=300 if facing==1 else 980
				foot_sim.fighters[0].facing=facing
				foot_sim.fighters[1].x=500 if facing==1 else 780
				foot_sim.fighters[1].facing=-facing
				var expected:=0
				for tick in range(duration*2):
					var movement:=UfeInputFrame.make(direction*facing)
					foot_sim.step([movement,movement])
					var actor:=foot_sim.fighters[0]
					check(actor.state=="walk" and actor.facing==facing,fighter_id+"脚步真实双向行走")
					var contact: bool=binding.contacts.any(func(phase):return int(phase)==actor.state_tick%duration)
					if contact:expected+=1
					var before:=foot_audio.played.size()
					foot_audio.sync(foot_sim,false)
					var actual:=foot_audio.played.slice(before).filter(func(row):return int(row.player)==0 and str(row.id) in binding.sounds)
					check(actual.size()==(1 if contact else 0),fighter_id+"/"+walk_key+"两周期脚步不偏离接触相位/"+str(tick)+" expected="+str(contact)+" actual="+str(actual.size()))
				check(expected==binding.contacts.size()*2,fighter_id+"/"+walk_key+"完整两周期脚步触发")
				foot_audio.free()

func check_target_voice_routes() -> void:
	for fighter_id in ["zoffy","ultraman-king","ultraman-justice","ultraman-zero","mother-of-ultra","ultraman-gaia","father-of-ultra"]:
		var voice_audio:=UfeSideAudio.new()
		root.add_child(voice_audio)
		var voice_sim:=UfeContentDatabase.match_for(fighter_id,"ultraman")
		var wanted:=str(voice_audio.catalog.voices.get(fighter_id,{}).get("taunt",""))
		var started:=false
		for tick in range(100):
			voice_sim.step([UfeInputFrame.make(0,0,UfeInputFrame.GUARD|UfeInputFrame.THROW if tick==5 else 0),UfeInputFrame.make()])
			started=started or voice_sim.fighters[0].move_id=="taunt"
			voice_audio.sync(voice_sim,false)
			var count:=voice_audio.played.size()
			voice_audio.sync(voice_sim,false)
			check(voice_audio.played.size()==count,fighter_id+"挑衅同tick不重复声音")
		var matching:=voice_audio.played.filter(func(row):return row.id==wanted and int(row.player)==0 and row.bus=="UFE_voice")
		check(started and not wanted.is_empty() and matching.size()==1,fighter_id+"真实组合键挑衅专属声恰播一次 started="+str(started)+" count="+str(matching.size()))
		voice_audio.free()
	var return_audio:=UfeSideAudio.new()
	root.add_child(return_audio)
	var return_sim:=UfeContentDatabase.match_for("ultraman-zero","ultraman")
	return_sim.fighters[0].x=100
	return_sim.fighters[1].x=1150
	return_sim.fighters[0].stats.energy=3000
	var returns:=0
	for tick in range(150):
		return_sim.step([UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL if tick==5 else 0),UfeInputFrame.make()])
		for event in return_sim.events:
			if event.kind=="weapon_return" and event.move=="special3":
				returns+=1
				check(event.get("sound","")=="omega_super1_catch","赛罗双头镖归位引用已登记原创音源")
		return_audio.sync(return_sim,false)
	var catches:=return_audio.played.filter(func(row):return row.id=="omega_super1_catch" and int(row.player)==0 and row.bus=="UFE_sfx")
	check(returns==2 and catches.size()==2,"赛罗真实三格必杀双镖返回各发一次收镖声")
	return_audio.free()

func run() -> void:
	for bad in [{"display_scale":[0.5,1]},{"visual_scale":1.25},{"display_scale":[2,2]},{"display_scale":[1,1],"visual_scale":4}]:check(not UfeEffectGeometry.valid(bad),"拒绝未声明或分数比例")
	check(UfeEffectGeometry.valid({}) and UfeEffectGeometry.valid({"display_scale":[1,1]}),"默认特效1倍")
	check(UfeEffectGeometry.valid({"display_scale":[2,2],"pixel_integer_scale":true}),"显式整数倍允许")
	files("res://content/presentation")
	files("res://content/fighters")
	check_zoffy_startup_attachments()
	check_zoffy_special_timelines()
	check_zoffy_pose_clock_validation()
	check_zoffy_beam_clock()
	check_zoffy_air_special_fx_cleanup()
	check_target_footsteps()
	check_target_voice_routes()
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
