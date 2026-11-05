extends SceneTree
func _initialize() -> void:call_deferred("run")
func require(value: bool,message: String) -> void:
	if not value:push_error(message);quit(1)
func run() -> void:
	test_air_recovery()
	var a:=UfeContentDatabase.match_for();var b:=UfeContentDatabase.match_for()
	var ai:=UfeComputerController.new(301,"hard",1);var copy:=UfeComputerController.new(301,"hard",1)
	var player:=UfeComputerController.new(917,"normal",0)
	var record:=UfeReplayRecorder.new();record.match_seed=301;record.ai_difficulty="hard"
	var moves:={}
	for tick in range(5400):
		var before:=a.state_hash()
		var second:=ai.sample(a);var same:=copy.sample(b)
		require(before==a.state_hash(),"AI不得改变模拟任何状态")
		require(second.pack()==same.pack() and ai.sample(a).pack()==second.pack(),"同种子/难度/观察必须生成同输入；同tick不能重复推进随机")
		var first:=player.sample(a);var inputs: Array=[first,second]
		a.step(inputs);b.step([UfeInputFrame.unpack(first.pack()),same]);record.append(inputs,a)
		require(a.state_hash()==b.state_hash(),"确定性电脑对局分叉")
		for f in a.fighters:
			if not f.move_id.is_empty():moves[f.move_id]=true
		if a.finished:break
	var replay_sim:=UfeContentDatabase.match_for()
	for pair in record.frames:replay_sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
	require(replay_sim.state_hash()==a.state_hash(),"电脑对局必须通过普通输入回放还原")
	record.save_file("user://ai-test.json")
	var loaded:=UfeReplayRecorder.load_file("user://ai-test.json",a.content_fingerprint)
	require(loaded!=null and loaded.match_seed==301 and loaded.ai_difficulty=="hard","回放必须保留对局种子与难度")
	# 起手可见后，三档按规定延迟响应；守低段的输入真实进入蹲防状态。
	for level in ["easy","normal","hard"]:
		var sim:=UfeContentDatabase.match_for();sim.fighters[0].x=650;sim.fighters[1].x=750
		var guard_ai:=UfeComputerController.new(301,level,1)
		var delay: int=UfeComputerController.LEVELS[level].delay
		for t in range(delay):
			sim.tick=t;sim.fighters[0].move_id="sweep";sim.fighters[0].move_tick=t
			require(guard_ai.sample(sim).pack()==[0,0,0],"反应延迟前不能读取当前攻击决策")
		var samples:={}
		for seed in range(1,80):
			var test:=UfeComputerController.new(seed,level,1)
			var low:=test.decide(sim,{"x":650,"height":0,"move":"sweep","move_start":0,"level":"low","threat":true})
			if low.held(UfeInputFrame.GUARD):
				require(low.y==-1,"低攻击必须蹲防");samples.low=true
			var overhead:=test.decide(sim,{"x":650,"height":0,"move":"heavy","move_start":100,"level":"overhead","threat":true})
			if overhead.held(UfeInputFrame.GUARD):require(overhead.y==0,"中段头顶攻击应站防");samples.high=true
			sim.fighters[1].enter("wake")
			test.queue.clear();test.defend=false
			var wake:=test.decide(sim,{"x":650,"height":0,"move":"","move_start":0,"level":"mid","threat":false})
			require(wake.buttons&(UfeInputFrame.LIGHT|UfeInputFrame.HEAVY)!=0,"起身应通过攻击输入反击")
			sim.fighters[1].enter("idle")
		require(samples.has("low") and samples.has("high"),"两种高度的防御都应可发生")
	require(moves.has("motion_236") or moves.has("motion_214"),"真实指令输入应解析为专属技")
	# 投技落点会改变混战的后续选择；独立的安静靶局验证真实蓄能与必杀，
	# 不要求某一场固定种子的混战必定活到蓄能完成。
	var charged_sim:=UfeContentDatabase.match_for();charged_sim.fighters[0].x=330
	var charged_ai:=UfeComputerController.new(301,"hard",1)
	var saw_super:=false;var energy_peak:=0
	for t in range(720):
		var before_energy:=int(charged_sim.fighters[1].stats.energy)
		var before_move:=charged_sim.fighters[1].move_id
		charged_sim.step([UfeInputFrame.make(),charged_ai.sample(charged_sim)])
		energy_peak=maxi(energy_peak,int(charged_sim.fighters[1].stats.energy))
		if before_move.is_empty() and charged_sim.fighters[1].move_id.begins_with("special"):
			require(before_energy>=1000 and int(charged_sim.fighters[1].stats.energy)<=before_energy-1000,"电脑必杀须消耗真实积攒的能量")
			saw_super=true
		if saw_super:break
	require(charged_ai.actions.has("charge") and energy_peak>=1000 and saw_super,"实际积攒能量后应使用必杀")
	print("确定性三档电脑输入、反应延迟、高低防御、起身反击和普通输入回放验证完成；招式 ",moves.keys()," 行为 ",ai.actions," 回合 ",a.tick)
	quit()

# 只使用现有空中受身规则与GUARD输入，不注入受身状态。
func test_air_recovery() -> void:
	var seen: Dictionary={"x":450,"height":0,"move":"","move_start":0,"level":"mid","threat":false}
	var recovery_counts: Array=[]
	for level in ["easy","normal","hard"]:
		var accepted:=0
		var sim:=UfeContentDatabase.match_for()
		for seed in range(1,101):
			var f:=sim.fighters[1]
			var ai:=UfeComputerController.new(seed,level,1)
			f.enter("launch");f.height=160;f.vy=2;f.state_tick=30
			ai.queue=[[1,0,UfeInputFrame.HEAVY]]
			var rng_before:=ai.rng
			require(ai.decide(sim,seen).buttons==0 and ai.queue.is_empty(),"上升不受身，也不继续执行被击飞前指令队列")
			require(ai.rng==rng_before,"上升阶段不提前抽受身概率")
			f.vy=-1;f.state_tick=maxi(13,int(UfeComputerController.LEVELS[level].delay))-1
			require(ai.decide(sim,seen).buttons==0 and ai.rng==rng_before,"受身遵守规则及各档反应时限")
			f.state_tick+=1
			var chosen:=ai.decide(sim,seen)
			var decided_rng:=ai.rng
			if chosen.held(UfeInputFrame.GUARD):accepted+=1
			for stop_tick in range(5):
				require(ai.decide(sim,seen).pack()==chosen.pack() and ai.rng==decided_rng,"hitstop状态帧冻结也不重掷")
			for tick in range(25):
				f.state_tick+=1
				require(ai.decide(sim,seen).pack()==chosen.pack() and ai.rng==decided_rng,"每次击飞只判定一次，不逐tick重掷成必受身")
			f.state_tick=0;f.vy=2
			ai.decide(sim,seen)
			require(not ai.recovery_decided,"连续击飞状态帧回退须清除旧决定")
			f.state_tick=30;f.vy=-1;ai.decide(sim,seen)
			require(ai.recovery_decided and ai.rng!=decided_rng,"连续击飞在新下降期重新判定")
			decided_rng=ai.rng
			f.enter("hit",10);ai.decide(sim,seen)
			require(not ai.recovery_decided,"离开击飞状态清理受身记忆")
			f.enter("launch");f.height=160;f.vy=-1;f.state_tick=30
			ai.decide(sim,seen)
			require(ai.recovery_decided and ai.rng!=decided_rng,"下一次击飞重新判定")
		require(accepted>0 and accepted<100,"每档均应有成功与失败，不是强制受身")
		recovery_counts.append(accepted)
	require(recovery_counts[0]<recovery_counts[1] and recovery_counts[1]<recovery_counts[2],"同种子样本中受身率须随难度递增")
	for facing in [-1,1]:
		var sim:=recovery_match(facing)
		var replay_sim:=recovery_match(facing)
		var ai:=UfeComputerController.new(301,"hard",1)
		var record:=UfeReplayRecorder.new()
		var saw_launch:=false;var saw_recovery:=false
		for tick in range(100):
			var first:=UfeInputFrame.make(facing,0,UfeInputFrame.HEAVY) if tick==0 else UfeInputFrame.make()
			var before:=sim.state_hash()
			var second:=ai.sample(sim) if sim.fighters[1].state=="launch" else UfeInputFrame.make()
			require(sim.state_hash()==before,"受身决策不修改模拟")
			if sim.fighters[1].state=="launch":require(ai.sample(sim).pack()==second.pack(),"受身同tick重复取样一致")
			var pair: Array=[first,second]
			sim.step(pair);record.append(pair,sim)
			saw_launch=saw_launch or sim.fighters[1].state=="launch"
			saw_recovery=saw_recovery or sim.fighters[1].state=="air_tech"
		require(saw_launch and saw_recovery,"双向真实升击后电脑GUARD必须进入已有空中受身")
		var path:="user://ai-recovery-%d.json"%facing
		record.save_file(path)
		var loaded:=UfeReplayRecorder.load_file(path,sim.content_fingerprint)
		require(loaded!=null,"受身原始输入回放应能加载")
		if loaded!=null:
			for pair in loaded.frames:replay_sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
			require(sim.state_hash()==replay_sim.state_hash(),"无AI参与的双向独立回放必须还原受身")
	print("电脑空中受身：三档延迟/单次概率、队列中断、真实双向升击、存盘加载原输入回放通过")

func recovery_match(facing: int) -> UfeMatchDirector:
	var sim:=UfeContentDatabase.match_for()
	sim.fighters[0].x=650 if facing==1 else 725
	sim.fighters[1].x=725 if facing==1 else 650
	sim.fighters[0].facing=facing;sim.fighters[1].facing=-facing
	return sim
