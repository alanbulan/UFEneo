extends SceneTree
## 正式杰克I短束对初代屏障，默认470/750、零初始能量，双方仅真实InputFrame。
## 初代先Q蓄能并完整松Q，随后2H；杰克在屏障有效时I。不中途写模拟状态。
var out := "user://projectile-beam-reflection/"
var legacy_directory := ""
var failures: Array = []
var cases: Array = []
var models: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("PROJECTILE_BEAM_REFLECTION_FAIL "+label)

func write_json(path: String, value: Variant) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	check(file!=null,"写证据/"+path)
	if file!=null:file.store_string(JSON.stringify(value,"\t",true)+"\n")

func fixture(shooter: int, source_id: String = "ultraman-jack") -> UfeMatchDirector:
	return UfeContentDatabase.match_for(source_id if shooter==0 else "ultraman","ultraman" if shooter==0 else source_id)

func observe(sim: UfeMatchDirector) -> Dictionary:
	var pair: Array = []
	for f in sim.fighters:
		pair.append({"id":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,
			"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,
			"hp":f.stats.hp,"energy":f.stats.energy,"stamina":f.stats.stamina})
	return {"tick":sim.tick,"hash":sim.state_hash(),"hitstop":sim.hitstop,"pair":pair,
		"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)}

func test_case(shooter: int, shield: bool, fireball: bool = false) -> void:
	var label := ("fireball-" if fireball else "")+"p%s-%s"%[shooter+1,"shield" if shield else "neutral"]
	var source_id := "zetton" if fireball else "ultraman-jack"
	var sim := fixture(shooter,source_id)
	var initial := observe(sim)
	var record := UfeReplayRecorder.new()
	var rows: Array = []
	var reflections: Array = []
	var contacts: Array = []
	var charge_ticks := 0
	var shield_tick := -1
	var fire_tick := -1
	var phase := "charge"
	check(sim.fighters[0].x==470 and sim.fighters[1].x==750,label+"/正式默认站位")
	check(sim.fighters[0].stats.energy==0 and sim.fighters[1].stats.energy==0,label+"/零初始能量")
	var source_move: Dictionary=sim.fighters[shooter].definition.moves.pulse
	check(bool(source_move.projectile.get("beam",false))==not fireball and source_move.energy_cost==0,label+"/正式零能量束或普通火球")
	for tick in range(1,151):
		var target := sim.fighters[1-shooter]
		var inputs: Array = [UfeInputFrame.make(),UfeInputFrame.make()]
		if phase=="charge":
			if int(target.stats.energy)<200:
				inputs[1-shooter]=UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
				charge_ticks+=1
			else:phase="release"
		elif phase=="release" and target.state=="idle" and target.move_id.is_empty():
			if fireball:
				fire_tick=tick
				inputs[shooter]=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
				shield_tick=tick+20
				phase="shield"
			else:
				shield_tick=tick
				if shield:inputs[1-shooter]=UfeInputFrame.make(0,-1,UfeInputFrame.SKILL)
				phase="fire"
		elif phase=="shield" and tick==shield_tick:
			if shield:inputs[1-shooter]=UfeInputFrame.make(0,-1,UfeInputFrame.SKILL)
			phase="done"
		elif phase=="fire" and tick==shield_tick+8:
			inputs[shooter]=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
			fire_tick=tick
			phase="done"
		var before := observe(sim)
		sim.step(inputs)
		record.append(inputs,sim)
		var after := observe(sim)
		rows.append(after)
		if tick==shield_tick and shield:
			check(target.move_id=="motion_22" and target.move_tick==1,label+"/真实2H启动屏障")
			check(int(before.pair[1-shooter].energy)-int(target.stats.energy)==150,label+"/屏障真实支付150能量")
		if tick==fire_tick:
			check(sim.fighters[shooter].move_id=="pulse",label+"/真实I启动短束")
			check(int(before.pair[shooter].stamina)-int(sim.fighters[shooter].stats.stamina)==30,label+"/短束真实支付30体力")
		for event in sim.events:
			if event.kind=="projectile_reflect":reflections.append({"tick":tick,"before":before,"after":after})
			if event.kind in ["hit","block"]:contacts.append({"tick":tick,"event":event.duplicate(true),"before":before,"after":after})
	check(charge_ticks>0 and shield_tick>0 and fire_tick>0,label+"/完整真实Q松Q与发射路径")
	if shield:
		check(reflections.size()==1,label+"/持续束确实接触正式反射屏障一次")
		check(contacts.size()==1,label+"/反射之后仍须真实接触原发射者")
		check(sim.fighters[shooter].stats.hp==935 and sim.fighters[1-shooter].stats.hp==1000,label+"/反射归属应让原发射者承受正式65伤害")
		if contacts.size()==1:check(int(contacts[0].event.player)==1-shooter and contacts[0].event.projectile,label+"/反射伤害属于屏障方")
		if not fireball and reflections.size()==1 and contacts.size()==1:
			var reflected: Dictionary=reflections[0].after.projectiles[0]
			var connected: Dictionary=contacts[0].after.projectiles[0]
			check(bool(reflected.get("beam_reflected",false)),label+"/仅实际束反射登记独立标志")
			for key in ["x","height","facing","box","length","thickness","speed","source_owner"]:
				check(reflected[key]==connected[key],label+"/反射后固定原点方向且不改原几何/%s"%key)
			check(int(connected.life)==int(reflected.life)-1 and int(connected.age)==int(reflected.age)+1,label+"/无新增寿命或速度")
			check(str(contacts[0].after.pair[shooter].move).is_empty(),label+"/反射实打中断原发射招")
			var cleared: bool=false
			for index in range(int(contacts[0].tick),rows.size()):
				if int(rows[index-1].hitstop)>0:continue
				check(rows[index].projectiles.is_empty(),label+"/源头中断后首个推进tick撤束")
				cleared=true
				break
			check(cleared,label+"/确实覆盖命中停顿后的撤束时刻")
	else:
		check(reflections.is_empty(),label+"/无屏障对照不反射")
		check(contacts.size()==1 and sim.fighters[1-shooter].stats.hp==935 and sim.fighters[shooter].stats.hp==1000,label+"/正常短束仍真实造成65伤害")
	var replay_path := out+label+"-replay.json"
	check(record.save_file(replay_path)==OK,label+"/保存真实原始输入")
	var loaded := UfeReplayRecorder.load_file(replay_path,sim.content_fingerprint)
	check(loaded!=null,label+"/正式loader读取本规则录像")
	var replay := fixture(shooter,source_id)
	var matched := 0
	if loaded!=null:
		check(loaded.frames.size()==rows.size(),label+"/独立回放完整帧数")
		for index in range(loaded.frames.size()):
			var inputs: Array = loaded.frames[index].map(func(p):return UfeInputFrame.unpack(p))
			replay.step(inputs)
			var equal: bool = observe(replay)==rows[index]
			check(equal,label+"/独立回放逐tick状态事件弹体/%s"%index)
			if equal:matched+=1
		check(replay.state_hash()==loaded.final_hash,label+"/独立回放最终hash")
	var compatibility: Dictionary={}
	if not legacy_directory.is_empty():
		var old_path := legacy_directory.path_join(label+"-replay.json")
		var old := UfeReplayRecorder.read_candidate(old_path)
		check(old!=null,label+"/真实修前录像可读取")
		if old!=null:
			var identical: bool=old.frames.size()==record.frames.size()
			for i in range(mini(old.frames.size(),record.frames.size())):
				var pair: Array=old.frames[i].map(func(p):return UfeInputFrame.unpack(p).pack())
				identical=identical and pair==record.frames[i]
			check(identical,label+"/修前后双方原输入逐tick完全相同")
			var rejected: bool=UfeReplayRecorder.load_file(old_path,sim.content_fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放"
			check(rejected,label+"/真实修前录像明确拒绝")
			compatibility={"same_inputs":identical,"real_before_rejected":rejected,"old_fingerprint":old.fingerprint}
		var old_trace: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(legacy_directory.path_join(label+"-trace.json")))
		var changed: Array=[]
		check(old_trace.rows.size()==rows.size(),label+"/修前后轨迹完整")
		for i in range(mini(old_trace.rows.size(),rows.size())):
			if str(old_trace.rows[i].hash)!=str(rows[i].hash):changed.append(i+1)
		compatibility.changed_hash_ticks=changed
		if not shield or fireball:check(changed.is_empty(),label+"/未反射束或普通火球逐tick旧hash保持")
	var post_reflection: Dictionary={}
	if reflections.size()==1:
		var index: int=int(reflections[0].tick)
		post_reflection=rows[index] if index<rows.size() else {}
	var summary: Dictionary={"case":label,"shooter":shooter,"shield":shield,"charge_ticks":charge_ticks,
		"shield_input_tick":shield_tick,"fire_input_tick":fire_tick,"fingerprint":sim.content_fingerprint,
		"final_hash":sim.state_hash(),"hp":[sim.fighters[0].stats.hp,sim.fighters[1].stats.hp],
		"reflections":reflections,"tick_after_reflection":post_reflection,"contacts":contacts,"replay_ticks_matched":matched,"compatibility":compatibility}
	cases.append(summary)
	write_json(out+label+"-trace.json",{"initial":initial,"summary":summary,"rows":rows})

func reflection_model() -> UfeMatchDirector:
	# 仅模型夹具：直接布置同时持屏者和人工束，不冒称真实输入可达的双反射实战。
	var sim:=UfeContentDatabase.match_for("ultraman","ultraman")
	for f in sim.fighters:
		f.definition.moves=f.definition.moves.duplicate(true)
		f.stats.energy=200
		sim._start(f,"motion_22")
		f.move_tick=10
	UfeProjectileResolver.spawn(sim,0,{"effect":"beam_loop","beam":true,"spawn":[40,100],"anchor":[40,100],"life":10,"length":450,"thickness":8,"box":[0,-4,450,8],"speed":0},"motion_22")
	return sim

func test_models() -> void:
	var sim:=reflection_model()
	var contacts: Array=[]
	UfeProjectileResolver.advance(sim,contacts)
	check(sim.projectiles.size()==1 and int(sim.projectiles[0].owner)==1,"模型/首次真实解析反射")
	UfeProjectileResolver.advance(sim,contacts)
	check(sim.projectiles.size()==1 and int(sim.projectiles[0].owner)==0,"模型/第二次真实解析反射回原owner")
	var p: Dictionary=sim.projectiles[0]
	var second:=p.duplicate(true)
	check(bool(p.get("beam_reflected",false)) and int(p.x)==550 and int(p.source_owner)==0,"模型/双反射保留显式标志和第二屏外缘")
	sim.fighters[1].clear_move();sim.fighters[1].enter("idle")
	UfeProjectileResolver.advance(sim,contacts)
	check(int(p.x)==550 and int(p.height)==100 and int(p.facing)==1,"模型/回到原owner也不重贴原发射点510")
	check(int(p.life)==7 and int(p.age)==3 and int(p.speed)==0 and int(p.length)==450,"模型/双反射不改寿命速度长度")
	check(contacts.size()==1 and int(contacts[0].owner)==0,"模型/双反射后的伤害归属回原owner")
	models.append({"case":"double-reflection-model-only","after_second":second,"after_third":p.duplicate(true),"contacts":contacts.duplicate(true)})
	var interrupted:=reflection_model()
	var ignored: Array=[]
	UfeProjectileResolver.advance(interrupted,ignored)
	interrupted.fighters[0].clear_move()
	check(interrupted.fighters[1].move_id=="motion_22","模型/新owner仍恰在原同名招")
	UfeProjectileResolver.advance(interrupted,ignored)
	check(interrupted.projectiles.is_empty() and ignored.is_empty(),"模型/原source中断即撤束不借新owner同名招续命")
	models.append({"case":"source-interrupt-same-name-model-only","projectiles":interrupted.projectiles.duplicate(true)})
	var visual:=reflection_model()
	var original:=fixture(0)
	var original_hash:=original.state_hash()
	var view:=UfeKoFinishPresentation.new()
	view.source=original;view.scene=visual
	var tail: Dictionary=visual.projectiles[0]
	tail.beam_reflected=true;tail.x=550;tail.height=100;tail.end_alpha=1000
	visual.fighters[0].frame().beam_origin=[200,150]
	view.projectile_rows=[{"projectile":tail,"budget":18,"detached_at":-1}]
	for tick in range(1,8):
		view.slow_age=tick;view._advance_projectiles()
		check(int(tail.x)==550 and int(tail.height)==100,"模型/KO同名发射相也不重贴/%s"%tick)
	check(visual.projectiles.is_empty() and int(view.projectile_rows[0].detached_at)==1,"模型/KO反射束仍走原有界短尾")
	check(original.state_hash()==original_hash,"模型/KO束尾不回写原模拟")
	models.append({"case":"ko-reflected-tail-model-only","tail":tail.duplicate(true),"original_hash_unchanged":original.state_hash()==original_hash})

func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--test-out="):out=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
		if argument.begins_with("--legacy-dir="):legacy_directory=argument.trim_prefix("--legacy-dir=")
	DirAccess.make_dir_recursive_absolute(out)
	for shooter in [0,1]:
		for shield in [true,false]:test_case(shooter,shield)
		test_case(shooter,true,true)
	check(cases.size()==6,"双向束屏障/中立与普通火球反射对照均完成")
	test_models()
	check(models.size()==3,"双反射/同名招中断/KO仅模型检查均完成")
	write_json(out+"summary.json",{"failures":failures,"cases":cases,"models":models})
	print("PROJECTILE_BEAM_REFLECTION_RESULT "+JSON.stringify({"failures":failures,"cases":cases.size(),"models":models.size()}))
	quit(0 if failures.is_empty() else 1)
