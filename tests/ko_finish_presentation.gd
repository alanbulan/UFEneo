extends SceneTree
## 纯逻辑夹具：真实step结算一次致命接触，再只读播放；不替代主游戏画面/真实输入/F4。
var errors: Array = []
var cases: Array = []

func _initialize() -> void:call_deferred("run")

func check(ok: bool, message: String) -> void:
	if not ok:errors.append(message)

func definition(id: String, beam_end: int = 22) -> UfeFighterDefinition:
	var data:=UfeFighterDefinition.new()
	data.id=id
	var idle: Dictionary={"sprite":0,"hurtboxes":[[-15,0,30,120]],"hitboxes":[],"cancel":[],"events":[],"dx":0,"dy":0}
	data.state_frames={"idle":[idle.duplicate(true)],"victory":[idle.duplicate(true)],"defeat":[idle.duplicate(true)],"timeout":[idle.duplicate(true)],"down":[],"hit_mid":[],"hit_high":[]}
	for i in range(24):
		var reaction:=idle.duplicate(true);reaction.sprite=i
		data.state_frames.down.append(reaction.duplicate(true))
		data.state_frames.hit_mid.append(reaction.duplicate(true))
		data.state_frames.hit_high.append(reaction.duplicate(true))
	var frames: Array=[]
	for i in range(22):
		var frame:=idle.duplicate(true)
		frame.sprite=i;frame.dx=1
		if i<beam_end:frame.beam_origin=[42+i%3,1000]
		if i>=1 and i<20:frame.hitboxes=[[20,0,60,120]]
		frames.append(frame)
	data.moves.fixture={"id":"fixture","kind":"strike","frames":frames,"damage":200,"energy_cost":0,"stamina_cost":0,"stun":0,
		"hitstun":24,"blockstun":8,"pushback":0,"level":"mid","unblockable":false,"launch":false,"bounce":false,"knockdown":false,
		"feedback":{"spark":"impact_heavy","block_spark":"impact_guard","hitstop":6,"blockstop":3,"shake":4,"flash":2}}
	return data

func fatal_match(beam: bool, beam_end: int = 22) -> UfeMatchDirector:
	var sim:=UfeMatchDirector.new(definition("ex_red_king",beam_end),definition("zetton"),load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	var attacker:=sim.fighters[0]
	attacker.base_definition=definition("red_king")
	attacker.form_id="fixture-specific-ex"
	attacker.transformed_this_round=true
	attacker.x=500;attacker.move_id="fixture";attacker.enter("attack")
	sim.fighters[1].x=545;sim.fighters[1].stats.hp=100
	if beam:UfeProjectileResolver.spawn(sim,0,{"effect":"beam_loop","beam":true,"spawn":[42,1000],"anchor":[42,1000],"life":40,"length":240,"speed":0},"fixture")
	sim.step([UfeInputFrame.make(),UfeInputFrame.make()])
	return sim

func terminal_case(beam: bool, beam_end: int = 22) -> void:
	var sim:=fatal_match(beam,beam_end)
	var key:="beam-detach" if beam_end<22 else "beam" if beam else "melee"
	check(sim.finished and int(sim.fighters[1].stats.hp)==0,key+"真实致命接触")
	check(sim.events.filter(func(e):return str(e.kind)=="hit").size()==1,key+"模拟只结算一次hit")
	check(not sim.terminal_view.is_empty(),key+"自动捕获终局快照")
	if sim.terminal_view.is_empty():return
	var record: Dictionary=sim.terminal_view.fighters[0]
	check(record.definition.id=="ex_red_king" and record.form_id=="fixture-specific-ex",key+"清理前具体EX/形态保全")
	check(str(record.snapshot[8])=="fixture" and int(record.snapshot[9])==1,key+"清招前真实招式tick保全")
	check(sim.fighters[0].definition.id=="ex_red_king" and sim.fighters[0].form_id=="fixture-specific-ex",key+"原模拟终局保留具体EX身份")
	var before:=sim.state_hash()
	var original_events:=sim.events.duplicate(true)
	var original_projectiles:=sim.projectiles.duplicate(true)
	var clock:=UfeKoFinishPresentation.new()
	var visual:=clock.sample(sim,false)
	check(not is_same(visual,sim) and not visual.finished,key+"HUD/胜利延后且模拟已结束")
	check(visual.fighters[0].definition.id=="ex_red_king",key+"显示仍是末击本人EX")
	check(not clock.can_pause_replay(sim,0),key+"原输入耗尽仍等待KO尾段")
	var start_tick:=visual.tick
	var start_move_tick:=visual.fighters[0].move_tick
	for i in range(30):clock.sample(sim,true)
	check(clock.real_age==0 and visual.tick==start_tick and visual.fighters[0].move_tick==start_move_tick and clock.effect_steps==0,key+"暂停所有KO/整相/FX整数时钟")
	var seen_ticks: Dictionary={}
	var terminal_hits:=0
	var sprites: Array=[]
	var effect_ticks:=0
	var max_alpha:=1000
	var detached:=false
	for real_tick in range(62):
		if real_tick>0:visual=clock.sample(sim,false)
		if not seen_ticks.has(visual.tick):
			seen_ticks[visual.tick]=true
			terminal_hits+=visual.events.filter(func(e):return str(e.kind)=="hit").size()
		if clock.active:
			var sprite:=int(visual.fighters[0].frame().sprite)
			if sprite not in sprites:sprites.append(sprite)
			effect_ticks+=clock.effect_steps
			for p in visual.projectiles:
				if not bool(p.get("beam",false)):continue
				check(int(p.end_alpha)<=max_alpha,key+"束尾透明度不得回升")
				max_alpha=int(p.end_alpha)
				var f:=visual.fighters[int(p.owner)]
				if f.frame().has("beam_origin"):
					var anchor: Array=f.frame().beam_origin
					check(int(p.x)==f.x+f.facing*int(anchor[0]) and int(p.height)==f.height+int(anchor[1]),key+"发射相逐相贴本人发射点")
				else:detached=true
		if real_tick<=6:check(visual.tick==start_tick,key+"六tick短停")
		check(sim.state_hash()==before and sim.events==original_events and sim.projectiles==original_projectiles,key+"终局播放未改变原模拟/伤害/事件/弹体")
	check(terminal_hits==1,key+"致命事件仅消费一次，无额外hit")
	check(sprites.size()>1 and effect_ticks==18,key+"真实整相和FX时钟推进，非截图冻结")
	check(not clock.active and visual.finished and visual.projectiles.is_empty(),key+"有界结束并恢复正常胜败")
	check(visual.fighters[0].definition.id=="ex_red_king" and visual.fighters[0].form_id=="fixture-specific-ex" and visual.fighters[0].state=="victory",key+"本人EX形态贯穿胜败结算")
	check(not clock.can_pause_replay(sim,89) and clock.can_pause_replay(sim,90),key+"F4正常结算尾段后自动暂停")
	if beam_end<22:check(detached,key+"离发射相后确实走短尾")
	cases.append({"case":key,"source_tick":sim.tick,"sprites":sprites,"effect_ticks":effect_ticks,"terminal_hits":terminal_hits,"final_hash":before})
	clock.reset()
	check(clock.scene==null and clock.source==null and not clock.active and clock.projectile_rows.is_empty(),key+"再战/新回放/退出释放快照")

func timeout_case() -> void:
	var sim:=UfeMatchDirector.new(definition("ultraman"),definition("zetton"),load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	sim.remaining=1
	sim.step([UfeInputFrame.make(),UfeInputFrame.make()])
	var clock:=UfeKoFinishPresentation.new()
	check(sim.finished and sim.remaining<=0 and sim.terminal_view.is_empty(),"超时不创建KO慢放")
	check(is_same(clock.sample(sim,false),sim) and not clock.active,"超时沿原正常演出")
	check(not clock.can_pause_replay(sim,0) and clock.can_pause_replay(sim,90),"超时回放仍展示正常结算尾段")
	var fresh:=UfeMatchDirector.new(definition("ultraman"),definition("zetton"),load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	check(is_same(clock.sample(fresh,false),fresh) and clock.scene==null,"换局不串旧快照")
	cases.append({"case":"timeout-and-reset","source_tick":sim.tick})

func flash_case() -> void:
	var feedback:=UfeCombatFeedback.new()
	feedback.flash=[0,2];feedback.shake_ticks=4;feedback.particles=[]
	check(feedback.advance_flash(false)[1]==2 and feedback.advance_flash(false)[1]==2,"呈现帧不再消耗闪白")
	var clock_sim:=UfeMatchDirector.new(definition("ultraman"),definition("zetton"),load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	feedback.last_tick=clock_sim.tick
	clock_sim.tick+=1
	feedback.sync(clock_sim,0,0)
	check(feedback.flash[1]==1,"闪白随模拟tick减少")
	clock_sim.tick+=1
	feedback.sync(clock_sim,0,0)
	check(feedback.flash[1]==0,"两tick后闪白结束")
	feedback.particles=[{"age":0}]
	check(int(feedback.particles[0].age)==0 and feedback.shake_ticks==4,"真实闪白时钟不再偷跑FX")
	feedback.advance_effects(0)
	check(int(feedback.particles[0].age)==0,"暂停FX零推进")
	feedback.advance_effects(1)
	check(int(feedback.particles[0].age)==1 and feedback.shake_ticks==3,"独立整数FX时钟")
	feedback.free()
	cases.append({"case":"flash-and-fx-clocks"})

func run() -> void:
	terminal_case(false)
	terminal_case(true)
	terminal_case(true,6)
	timeout_case()
	flash_case()
	print("KO_FINISH_PRESENTATION "+JSON.stringify({"errors":errors,"cases":cases,"synthetic_logic_fixture":true,"main_game_review_completed":false}))
	quit(0 if errors.is_empty() else 1)
