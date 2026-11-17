extends SceneTree
## 共享能力夹具：只复制内存定义，真实THROW输入；不安装提欧待审人物或招式。
const Points = preload("res://core/combat/throw_hold_points.gd")
var OUT := "res://reports/review/2026-10-31/throw-hold-point-current/"
const CONTRACT := "res://tests/fixtures/throw-hold-contract.json"
var errors: Array=[]
var results: Array=[]
var replay_cases: Array=[]
var definitions: Dictionary={}
var payload: Dictionary={}
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	if not ok and not errors.has(label):errors.append(label);printerr(label)
func write_json(name: String,value: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	FileAccess.open(OUT+name,FileAccess.WRITE).store_string(JSON.stringify(value,"\t",true)+"\n")
func clone(id: String) -> UfeFighterDefinition:
	var source: UfeFighterDefinition=definitions[id]
	var f:=UfeFighterDefinition.new()
	f.id=source.id;f.display_name=source.display_name;f.max_health=source.max_health
	f.walk_speed=source.walk_speed;f.jump_speed=source.jump_speed;f.body_radius=source.body_radius
	f.moves=source.moves.duplicate(true);f.state_frames=source.state_frames.duplicate(true);f.command_table=source.command_table.duplicate(true)
	return f
func fixture(opponent: String, facing: int=1, edge: int=600, mode: String="valid") -> UfeMatchDirector:
	var actor:=clone("ultraman");var victim:=clone(opponent)
	var move: Dictionary=actor.moves.throw_forward
	for frame in move.frames:
		var target: Dictionary=frame.get("target",{})
		if str(target.get("mode",""))!="hold" or str(target.get("pose",""))!="grabbed":continue
		target.hold_point_overrides=payload.duplicate(true)
		# 实际腰点高于旧点；测试手位统一足够高，专门验证共享查点及落地规则。
		target.grip[1]=maxi(120,int(target.grip[1]))
		if mode=="missing_later":target.hold_point_overrides[opponent].grabbed.erase("2")
		if mode=="invalid":target.hold_point_overrides=[]
	if mode=="alias":victim.id=opponent+"-form"
	var sim:=UfeMatchDirector.new(actor,victim,load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	sim.fighters[0].x=edge;sim.fighters[1].x=edge+52*facing
	sim.fighters[0].facing=facing;sim.fighters[1].facing=-facing
	sim.fighters[0].stats.stamina=500
	return sim
func play(opponent: String,facing: int,edge: int,kind: String,mode: String="valid",record: bool=true) -> Dictionary:
	var sim:=fixture(opponent,facing,edge,mode)
	var rows: Array=[];var hits:=0;var slams:=0;var techs:=0;var captured:=false;var age:=0;var paid:=false;var held:=0
	for tick in range(110):
		var inputs:=[UfeInputFrame.make(),UfeInputFrame.make()]
		if tick==10:inputs[0]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		if kind=="guard":inputs[1]=UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
		if kind=="crouch_guard":inputs[1]=UfeInputFrame.make(0,-1,UfeInputFrame.GUARD)
		if kind=="air" and tick==9:inputs[1]=UfeInputFrame.make(0,1)
		if kind=="simultaneous" and tick==10:inputs[1]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		if captured:
			age+=1
			if (kind=="tech3" and age==3) or (kind=="tech4" and age==4):inputs[1]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		var old_stamina:=int(sim.fighters[0].stats.stamina)
		sim.step(inputs)
		var a:=sim.fighters[0];var b:=sim.fighters[1]
		if tick==10:paid=int(a.stats.stamina)==old_stamina-int(a.definition.moves.throw_forward.stamina_cost)
		if b.state=="thrown":captured=true
		if b.state=="thrown" and str(a.frame().get("target",{}).get("mode",""))=="hold":
			held+=1
			var target: Dictionary=a.frame().target
			var point: Array=payload[opponent][target.pose][str(int(b.frame().sprite))] if target.has("hold_point_overrides") else b.frame().grab_points.waist
			var offset: Array=target.get("root",[0,0]);var grip: Array=target.grip
			check(b.x+b.facing*int(point[0])==a.x+a.facing*(int(grip[0])+int(offset[0])),"双向真实抓点x/%s/%s/%s"%[opponent,facing,kind])
			check(b.height+int(point[1])==a.height+int(grip[1])+int(offset[1]),"双向真实抓点高度/%s/%s/%s"%[opponent,facing,kind])
		for event in sim.events:
			if event.kind=="hit" and event.player==0:hits+=1
			if event.kind=="throw_slam" and event.player==0:slams+=1
			if event.kind=="throw_tech":techs+=1
		if mode!="valid":
			check(b.state!="thrown" and int(b.stats.hp)==1000 and sim.hitstop==0,"白名单拒绝在捕获与停顿前/%s/%s/%d"%[mode,opponent,tick])
			check(sim.events.all(func(e):return str(e.kind) not in ["hit","block","throw_slam","throw_tech"]),"无伪命中事件/%s/%s/%d"%[mode,opponent,tick])
		check(a.x>=28 and a.x<=1252 and b.x>=28 and b.x<=1252,"墙边成对约束/%s/%s"%[opponent,edge])
		rows.append({"inputs":inputs.map(func(i):return i.pack()),"hash":sim.state_hash(),"events":JSON.stringify(sim.events,"",true)})
	var should_tech:=kind in ["tech3","simultaneous"] and mode=="valid"
	var should_land:=kind!="air" and not should_tech and mode=="valid"
	check(paid,"成功及落空均支付原费用/%s/%s"%[mode,kind])
	check(slams==(1 if should_land else 0),"只撞地一次或不撞地/%s/%s/%s"%[mode,opponent,kind])
	check(techs==(1 if should_tech else 0),"三tick拆投边界或无拆投/%s/%s/%s"%[mode,opponent,kind])
	check(int(sim.fighters[1].stats.hp)==1000-(int(sim.fighters[0].definition.moves.throw_forward.damage) if should_land else 0),"伤害守恒/%s/%s/%s"%[mode,opponent,kind])
	if mode=="valid" and kind not in ["air","simultaneous"]:check(captured and held>0 and hits==1,"实际输入捕获及hold消费/%s/%s"%[opponent,kind])
	var result:={"opponent":opponent,"facing":facing,"edge":edge,"kind":kind,"mode":mode,"hits":hits,"slams":slams,"techs":techs,"held_ticks":held,"paid":paid}
	if record:replay_cases.append({"fixture":result.duplicate(true),"rows":rows,"fingerprint":sim.content_fingerprint})
	return result
func unit_cases() -> void:
	var sim:=fixture("zetton");var a:=sim.fighters[0];var b:=sim.fighters[1]
	var target:={"mode":"hold","pose":"grabbed","sprite":0,"grip":[0,90],"root":[0,0],"hold_point_overrides":payload.duplicate(true)}
	# 两个数组位置引用同一sprite，覆盖按实际图片编号，而不是数组位置。
	b.definition.state_frames.grabbed[0].sprite=9
	target.hold_point_overrides.zetton.grabbed["9"]=[17,70]
	check(Points.point(b,target,b.definition.state_frames.grabbed[0])==[17,70],"实际sprite与state_frames索引分离")
	b.definition.state_frames.grabbed[1].sprite=9
	check(Points.point(b,target,b.definition.state_frames.grabbed[1])==[17,70],"重复数组索引共享实际sprite的同一覆盖")
	b.definition.state_frames.grabbed[1].sprite=1
	var move:={"frames":[{"target":target}]}
	check(UfeThrowResolver.can_capture(b,move),"重排sprite精确键可捕获")
	target.hold_point_overrides.zetton.grabbed.erase("9")
	check(not UfeThrowResolver.can_capture(b,move),"不按数组位置回退旧sprite")
	b.definition.state_frames.grabbed[0].sprite=0
	b.definition.state_frames.grabbed[0].throw_hold_variants=[0,1]
	b.definition.state_frames.grabbed[0].throw_hold_floor_variants=[2]
	check(UfeThrowResolver.can_capture(b,move),"全部可能变体均已声明")
	target.hold_point_overrides.zetton.grabbed.erase("1")
	check(not UfeThrowResolver.can_capture(b,move),"后段时序变体缺点在捕获前拒绝")
	target.hold_point_overrides=payload.duplicate(true);target.hold_point_overrides.zetton.grabbed.erase("2")
	check(not UfeThrowResolver.can_capture(b,move),"floor变体缺点在捕获前拒绝")
	target.hold_point_overrides=payload.duplicate(true)
	var missing_pose:=target.duplicate(true);missing_pose.pose="missing_pose"
	check(not UfeThrowResolver.can_capture(b,{"frames":[{"target":missing_pose}]}),"未声明姿势不猜旧grabbed")
	var invalid_sprite:=target.duplicate(true);invalid_sprite.sprite=99
	check(not UfeThrowResolver.can_capture(b,{"frames":[{"target":invalid_sprite}]}),"数组越界不夹到最后一相")
	# 真腰0高86不能放在67高，选择真腰2高61；旧waist0高67则会错误保留0。
	target.grip=[0,67]
	a.move_id="throw_forward";a.move_tick=0
	a.definition.moves.throw_forward.frames=[{"target":target}]
	check(UfeThrowResolver.victim_sprite(a,b,target)==2,"floor-safe选择读取真实腰点而非旧裆部")
	# release/root即使挂有无效覆盖也不读取，不扩大到其它模式。
	for mode in ["root","release"]:
		var release:=target.duplicate(true);release.mode=mode;release.hold_point_overrides=[]
		check(UfeThrowResolver.can_capture(b,{"frames":[{"target":release}]}),"非hold不查覆盖/%s"%mode)
	# held数据异常无伤退出，不能偷偷回退旧waist。
	sim=fixture("zetton");a=sim.fighters[0];b=sim.fighters[1]
	a.move_id="throw_forward"
	for tick in range(a.definition.moves.throw_forward.frames.size()):
		if a.definition.moves.throw_forward.frames[tick].get("target",{}).get("mode","")=="hold":a.move_tick=tick;break
	b.enter("thrown");UfeThrowResolver.begin(sim,0,a.definition.moves.throw_forward)
	a.frame().target.hold_point_overrides={}
	UfeThrowResolver.sync(sim)
	check(b.state=="down" and b.combat.thrower==-1 and a.move_id.is_empty(),"held异常确定性退出")
	check(int(a.stats.hp)==1000 and int(b.stats.hp)==1000 and sim.hitstop==0 and sim.events.size()==1 and sim.events[0].kind=="throw_hold_abort","held异常只有诊断且无伤害或停顿")
func nonhold_sync_cases() -> void:
	for mode in ["root","release"]:
		var sims: Array=[fixture("zetton"),fixture("zetton")]
		for index in range(2):
			var sim: UfeMatchDirector=sims[index];var a:=sim.fighters[0];var b:=sim.fighters[1]
			a.move_id="throw_forward"
			for tick in range(a.definition.moves.throw_forward.frames.size()):
				if a.definition.moves.throw_forward.frames[tick].get("target",{}).get("mode","")=="release":a.move_tick=tick;break
			a.frame().target.mode=mode
			if index==1:a.frame().target.hold_point_overrides=[]
			b.enter("thrown");UfeThrowResolver.begin(sim,0,a.definition.moves.throw_forward)
			UfeThrowResolver.sync(sim)
		check(sims[0].state_hash()==sims[1].state_hash() and sims[0].events==sims[1].events,"非hold挂无效覆盖仍逐值沿原同步/%s"%mode)
func invalid_simultaneous_cases() -> void:
	for opponent in ["ultraseven","zetton"]:
		for facing in [-1,1]:
			var sim:=fixture(opponent,facing,600,"invalid")
			var rows: Array=[];var opponent_slams:=0
			for tick in range(110):
				var inputs:=[UfeInputFrame.make(),UfeInputFrame.make()]
				if tick==10:inputs=[UfeInputFrame.make(0,0,UfeInputFrame.THROW),UfeInputFrame.make(0,0,UfeInputFrame.THROW)]
				sim.step(inputs)
				for event in sim.events:
					check(event.kind!="throw_tech","无效覆盖不参与同时投拆投/%s/%s"%[opponent,facing])
					if event.kind in ["hit","block","throw_slam"]:check(event.player==1,"无效投不生成己方命中/%s/%s"%[opponent,facing])
					if event.kind=="throw_slam" and event.player==1:opponent_slams+=1
				rows.append({"inputs":inputs.map(func(i):return i.pack()),"hash":sim.state_hash(),"events":JSON.stringify(sim.events,"",true)})
			check(opponent_slams==1 and int(sim.fighters[1].stats.hp)==1000,"同时合法对手投仍独立命中/%s/%s"%[opponent,facing])
			var result:={"opponent":opponent,"facing":facing,"edge":600,"kind":"invalid_simultaneous","mode":"invalid","opponent_slams":opponent_slams}
			results.append(result);replay_cases.append({"fixture":result.duplicate(true),"rows":rows,"fingerprint":sim.content_fingerprint})
func validation_cases() -> void:
	check(Points.valid(payload),"冻结真实腰点合同合法")
	var parsed: Variant=JSON.parse_string(JSON.stringify(payload))
	check(Points.valid(parsed),"JSON无小数数值合法")
	var move: Dictionary=definitions.ultraman.moves.throw_forward.duplicate(true)
	var frame: Dictionary=move.frames.filter(func(f):return f.get("target",{}).get("mode","")=="hold")[0]
	frame.target.hold_point_overrides=payload.duplicate(true)
	check(UfeMoveData.validate(move),"合法覆盖纳入招式schema")
	var invalid: Array=[null,[],{}, {"zetton":{}}, {"zetton":{"grabbed":{}}}, {"zetton":{"grabbed":{"01":[0,1]}}}, {"zetton":{"grabbed":{"-1":[0,1]}}}, {"zetton":{"grabbed":{0:[0,1]}}}, {"zetton":{"grabbed":{"0":[0,1.25]}}}, {"zetton":{"grabbed":{"0":[true,1]}}}, {"zetton":{"grabbed":{"0":[0,-1]}}}, {"zetton":{"grabbed":{"0":[0,NAN]}}}, {"zetton":{"grabbed":{"0":[INF,1]}}}, {"zetton":{"grabbed":{"0":[0]}}}]
	for index in range(invalid.size()):
		frame.target.hold_point_overrides=invalid[index]
		check(not UfeMoveData.validate(move),"非法覆盖schema拒绝/%d"%index)
	for mode in ["root","release"]:
		frame.target.mode=mode;frame.target.hold_point_overrides=[]
		check(UfeMoveData.validate(move),"非hold维持旧schema/%s"%mode)
func replay() -> void:
	var prior: Dictionary=UfeContentDatabase.read_json(OUT+"new-input-cases.json")
	for item in prior.cases:
		var f: Dictionary=item.fixture
		var sim:=fixture(str(f.opponent),int(f.facing),int(f.edge),str(f.mode))
		check(sim.content_fingerprint==str(item.fingerprint),"独立进程定义指纹相同")
		for index in range(item.rows.size()):
			var row: Dictionary=item.rows[index]
			var inputs: Array=row.inputs.map(func(p):return UfeInputFrame.unpack(p))
			sim.step(inputs)
			check(sim.state_hash()==str(row.hash) and JSON.stringify(sim.events,"",true)==str(row.events),"独立逐tick输入回放/%s/%s/%s/%d"%[f.opponent,f.kind,f.mode,index])
	write_json("new-replay-result.json",{"errors":errors,"cases":prior.cases.size()})
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--regression-out="):OUT=arg.trim_prefix("--regression-out=").trim_suffix("/")+"/"
	for id in ["ultraman","ultraseven","zetton","gomora"]:definitions[id]=UfeContentDatabase.fighter(id,true)
	payload=UfeContentDatabase.read_json(CONTRACT).payload
	if "--replay" in OS.get_cmdline_user_args():
		replay();print("THROW_HOLD_POINT_REPLAY ",JSON.stringify(errors));quit(0 if errors.is_empty() else 1);return
	validation_cases();unit_cases();nonhold_sync_cases()
	for opponent in ["ultraseven","zetton"]:
		for facing in [-1,1]:
			for edge in [100,600,1150]:results.append(play(opponent,facing,edge,"hit"))
			for kind in ["guard","crouch_guard","air","simultaneous","tech3","tech4"]:results.append(play(opponent,facing,600,kind))
			for mode in ["alias","missing_later","invalid"]:results.append(play(opponent,facing,600,"hit",mode))
	# 完全未列目标也须在命中事件前落空。
	results.append(play("gomora",1,600,"hit","unlisted"))
	invalid_simultaneous_cases()
	write_json("new-input-cases.json",{"cases":replay_cases})
	write_json("logic-result.json",{"errors":errors,"results":results,"scope":"共享内存夹具，真实THROW；不作为提欧41236美术/实际招式验收"})
	print("THROW_HOLD_POINT_LOGIC ",JSON.stringify({"errors":errors,"cases":results.size()}));quit(0 if errors.is_empty() else 1)
