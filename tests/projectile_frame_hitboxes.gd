extends SceneTree
@warning_ignore_start("integer_division")
## 可选逐相多矩形的整数接触与旧招逐tick兼容专项。
const OUT := "res://reports/projectile-frame-hitboxes-"
# 原点(400,240)，每相4tick；空相不回退到包围框。故意不声明tick_clock。
const FRAME_HITBOXES := [[ [0,0,4,4], [8,-8,4,4] ], [], [[20,0,4,4]], [[30,0,4,4]]]
# 世界框和交集中心均手算；右向x=400+local_x，左向x=400-local_x-width。
# phase0右向两框为[400,240,4,4]/[408,232,4,4]，左向为[396,240,4,4]/[388,232,4,4]。
const CASES := [
	{"id":"right_first","facing":1,"phase":0,"world":[401,241,2,2],"point":Vector2i(402,242)},
	{"id":"right_second","facing":1,"phase":0,"world":[409,233,2,2],"point":Vector2i(410,234)},
	{"id":"right_gap","facing":1,"phase":0,"world":[405,237,2,2],"point":null},
	{"id":"right_edge","facing":1,"phase":0,"world":[404,240,1,4],"point":null},
	{"id":"right_empty_phase","facing":1,"phase":1,"world":[401,241,2,2],"point":null},
	{"id":"right_phase2","facing":1,"phase":2,"world":[421,241,2,2],"point":Vector2i(422,242)},
	{"id":"right_phase3","facing":1,"phase":3,"world":[431,241,2,2],"point":Vector2i(432,242)},
	{"id":"left_first","facing":-1,"phase":0,"world":[397,241,2,2],"point":Vector2i(398,242)},
	{"id":"left_second","facing":-1,"phase":0,"world":[389,233,2,2],"point":Vector2i(390,234)},
	{"id":"left_gap","facing":-1,"phase":0,"world":[393,237,2,2],"point":null},
	{"id":"left_edge","facing":-1,"phase":0,"world":[395,240,1,4],"point":null},
	{"id":"left_empty_phase","facing":-1,"phase":1,"world":[397,241,2,2],"point":null},
	{"id":"left_phase2","facing":-1,"phase":2,"world":[377,241,2,2],"point":Vector2i(378,242)},
	{"id":"left_phase3","facing":-1,"phase":3,"world":[367,241,2,2],"point":Vector2i(368,242)},
]
var errors: Array = []
var completed: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr(label)

func write_json(name: String, value: Variant) -> void:
	var file:=FileAccess.open(OUT+name,FileAccess.WRITE)
	if file==null:
		check(false,"无法写入专项结果/%s/%s"%[name,FileAccess.get_open_error()])
		return
	file.store_string(JSON.stringify(value,"\t",true)+"\n")
	check(file.get_error()==OK,"专项结果写入失败/%s"%name)

func legacy() -> Dictionary:
	var result: Dictionary = {}
	for part in range(9):
		var driver := UfePhase3SpecialReview.new()
		driver.review_frame=driver.S_STARTS[part]
		var ids: Array=driver.matchup()
		var sim:=UfeContentDatabase.match_for(str(ids[0]),str(ids[1]))
		driver.prepare_match(sim)
		var rows: Array=[]
		for age in range(driver.S_STARTS[part+1]-driver.S_STARTS[part]):
			if driver.wants_intro() and age<75:continue
			var tick: int=driver.S_STARTS[part]+age
			sim.step([driver.sample(tick,sim),driver.second_sample(tick)])
			rows.append([sim.state_hash(),sim.events.duplicate(true),sim.projectiles.duplicate(true)])
		result[str(part)]={"fingerprint":sim.content_fingerprint,"rows":rows}
	return result

func fixture(facing: int, world: Array, phase: int, mode: String="") -> UfeMatchDirector:
	var sim:=UfeContentDatabase.match_for()
	if sim==null:
		check(false,"夹具对局创建失败")
		return null
	var a:=sim.fighters[0];var b:=sim.fighters[1]
	a.definition.moves=a.definition.moves.duplicate(true);b.definition.moves=b.definition.moves.duplicate(true)
	a.x=400;a.height=240;a.facing=facing
	# 分开躯干，避免回放首tick的推挤改变手算世界框。
	b.x=400+100*facing;b.height=240;b.facing=-facing
	var move: Dictionary=b.definition.moves.motion_22.duplicate(true)
	move.energy_cost=0;move.stamina_cost=0
	var local: Array=[int(world[0])-b.x if b.facing>0 else b.x-int(world[0])-int(world[2]),int(world[1])-b.height,int(world[2]),int(world[3])]
	var frame: Dictionary={"sprite":0,"dx":0,"dy":0,"hurtboxes":[local],"hitboxes":[],"events":[],"cancel":[]}
	if not mode.is_empty():
		frame.projectile_guard=mode;frame.guard_box=local;frame.guard_effect="impact_guard"
		frame.hurtboxes=[[1000,1000,1,1]]
	move.frames=[frame];b.definition.moves.motion_22=move
	sim._start(a,"pulse");sim._start(b,"motion_22")
	if a.move_id!="pulse" or b.move_id!="motion_22":
		check(false,"夹具必须实际进入发射/护屏招")
		return null
	var shot: Dictionary={"beam":true,"spawn":[0,0],"anchor":[0,0],"speed":0,"life":100,"box":[0,-8,34,12],"frame_hitboxes":FRAME_HITBOXES.duplicate(true)}
	UfeProjectileResolver.spawn(sim,0,shot,"pulse")
	if sim.projectiles.size()!=1:
		check(false,"夹具必须实际生成唯一旧时钟束")
		return null
	# advance先加age再接触：目标四相分别采样age=1/4/8/12。
	sim.projectiles[0].age=maxi(0,phase*4-1)
	check(not sim.projectiles[0].has("spawn_tick"),"未声明pose的夹具保持旧弹体时钟")
	return sim

func test_contract() -> void:
	var rows: Array=[]
	for item in CASES:
		for mode in ["","block","reflect","absorb"]:
			var sim:=fixture(int(item.facing),item.world,int(item.phase),mode)
			if sim==null:return
			var contacts: Array=[]
			UfeProjectileResolver.advance(sim,contacts)
			var expected: bool=item.point!=null
			var found: bool=not contacts.is_empty() if mode.is_empty() else not sim.events.is_empty()
			check(found==expected,"分相双向束芯/包围框空白/%s/%s"%[item.id,mode])
			check(contacts.size()==(1 if expected and mode.is_empty() else 0) and sim.events.size()==(1 if expected and not mode.is_empty() else 0),"多分段准确单次结算/%s/%s"%[item.id,mode])
			if expected and found:
				if mode.is_empty():
					check(contacts[0].get("point",null)==item.point,"命中点等于手算交集中心/%s"%item.id)
					var again: Array=[];UfeProjectileResolver.advance(sim,again)
					check(again.is_empty(),"已接触束不重复伤害/%s"%item.id)
				else:
					var event: Dictionary=sim.events[0]
					check(event.get("kind","")=="projectile_"+mode,"护屏必须产生对应事件/%s/%s"%[item.id,mode])
					check(Vector2i(int(event.get("x",-1)),int(event.get("height",-1)))==item.point,"护屏接触点等于手算中心/%s/%s"%[item.id,mode])
					if mode=="reflect":
						check(sim.projectiles.size()==1 and sim.projectiles[0].owner==1 and int(sim.projectiles[0].facing)==-int(item.facing),"新束反射归属及朝向/%s"%item.id)
					elif mode=="absorb":
						check(sim.projectiles.is_empty() and sim.fighters[1].combat.absorbed==1,"新束吸收仅累计一次/%s"%item.id)
					else:check(sim.projectiles.is_empty(),"屏只挡真实束芯/%s"%item.id)
			elif not expected:
				check(sim.projectiles.size()==1 and not bool(sim.projectiles[0].get("connected",false)) and int(sim.projectiles[0].owner)==0 and sim.fighters[1].combat.absorbed==0,"空白样本必须保留未命中的来束/%s/%s"%[item.id,mode])
			rows.append({"case":item.id,"mode":mode,"expected":expected,"actual":found})
	check(rows.size()==56,"14个固定案例乘四种交互必须全部执行，不能空PASS")
	write_json("contract-result.json",rows)
	completed.append("contract")

func test_clock_and_copy() -> void:
	var p: Dictionary={"x":400,"height":240,"facing":1,"age":0,"box":[0,-8,34,12],"frame_hitboxes":FRAME_HITBOXES.duplicate(true)}
	for age in range(32):
		p.age=age
		var phase: int=(age/4)%4
		for x in [0,20,30]:
			var point: Variant=UfeProjectileResolver.contact_point(p,Rect2i(400+x,240,1,1))
			var expected: Variant=null
			if (phase==0 and x==0) or (phase==2 and x==20) or (phase==3 and x==30):expected=Vector2i(400+x,240)
			check(point==expected,"age/4相序及空有效相/%s/%s"%[age,x])
	var sim:=UfeContentDatabase.match_for()
	if sim==null:
		check(false,"深拷贝夹具对局创建失败")
		return
	var shot: Dictionary={"spawn":[0,240],"speed":0,"frame_hitboxes":FRAME_HITBOXES.duplicate(true)}
	UfeProjectileResolver.spawn(sim,0,shot,"pulse")
	if sim.projectiles.size()!=1:
		check(false,"深拷贝夹具必须生成弹体")
		return
	shot.frame_hitboxes[0][0][0]=99
	check(sim.projectiles[0].frame_hitboxes[0][0][0]==0,"显式新框深拷贝不与招式表共享可变数组")
	UfeProjectileResolver.spawn(sim,0,{"speed":0},"pulse")
	check(sim.projectiles.size()==2,"旧弹体兼容分支必须生成第二弹体")
	if sim.projectiles.size()!=2:return
	check(not sim.projectiles[1].has("frame_hitboxes") and not sim.projectiles[1].has("spawn_tick"),"旧弹体不补缺省键")
	var overlap:=fixture(1,[401,241,2,2],0)
	if overlap==null:return
	var box: Array=[0,0,4,4]
	overlap.projectiles[0].frame_hitboxes=[[box,box,box]]
	var contacts: Array=[];UfeProjectileResolver.advance(overlap,contacts)
	check(contacts.size()==1,"重叠多框只形成一次伤害接触")
	var invulnerable:=fixture(1,[401,241,2,2],0)
	if invulnerable==null:return
	invulnerable.fighters[1].combat.invulnerable=10
	contacts=[];UfeProjectileResolver.advance(invulnerable,contacts)
	check(contacts.is_empty(),"新框遵守原无敌")
	var expired:=fixture(1,[401,241,2,2],0)
	if expired==null:return
	expired.projectiles[0].life=1
	contacts=[];UfeProjectileResolver.advance(expired,contacts)
	check(contacts.is_empty() and expired.projectiles.is_empty(),"到期先于分段接触")
	completed.append("clock_copy")

func test_validation() -> void:
	var valid: Dictionary=UfeContentDatabase.fighter("ultraman").moves.pulse.duplicate(true)
	valid.projectile.frame_hitboxes=FRAME_HITBOXES.duplicate(true)
	check(UfeMoveData.validate(valid),"最小四相整数多矩形表通过数据门")
	for boxes in [[[]],[[[0.0,-2.0,4.0,4.0]]]]:
		var move:=valid.duplicate(true);move.projectile.frame_hitboxes=boxes
		check(UfeMoveData.validate(move),"允许无攻击相及JSON整数值")
	for boxes in [null,{},[],[null],[[null]],[[[0,0,0,2]]],[[[0,0,2,-1]]],[[[0,0,2.5,2]]],[[[false,0,2,2]]],[[[0,0,INF,2]]],[[[0,0,NAN,2]]],[[[0,0,2]]]]:
		var move:=valid.duplicate(true);move.projectile.frame_hitboxes=boxes
		check(not UfeMoveData.validate(move),"非法逐相整数框拒收/%s"%[boxes])
		move=valid.duplicate(true);move.projectile.erase("frame_hitboxes");move.frames[0].shots=[{"frame_hitboxes":boxes}]
		check(not UfeMoveData.validate(move),"逐帧shots同样拒收非法框/%s"%[boxes])
	var pose_move: Dictionary=UfeContentDatabase.read_json("res://content/fighters/zoffy/moves/special.json")
	check(UfeMoveData.validate(pose_move),"姿势束边界夹具必须来自合法现用招式")
	var launch_frame:=int(pose_move.startup)
	var pose_shot: Dictionary=pose_move.frames[launch_frame].shots[0].duplicate(true)
	pose_move.frames[launch_frame].erase("shots")
	pose_move.frames[0].shots=[pose_shot]
	check(not UfeMoveData.validate(pose_move),"不可达的第0帧姿势束必须在加载期拒收")
	pose_move.frames[0].erase("shots")
	pose_move.frames[1].shots=[pose_shot]
	check(UfeMoveData.validate(pose_move),"首个可达的第1帧姿势束仍合法")
	pose_move.frames[1].erase("shots")
	pose_shot.erase("tick_clock")
	pose_move.frames[0].shots=[pose_shot]
	check(UfeMoveData.validate(pose_move),"旧时钟第0帧shots不受姿势束边界限制")
	completed.append("validation")

func test_replay() -> void:
	var rows: Array=[]
	for facing in [-1,1]:
		var world: Array=[401 if facing>0 else 397,241,2,2]
		var first:=fixture(facing,world,0)
		var replay:=fixture(facing,world,0)
		if first==null or replay==null:return
		for sim in [first,replay]:
			for f in sim.fighters:
				var frame: Dictionary=f.frame().duplicate(true)
				frame.hitboxes=[];frame.events=[];frame.cancel=[];frame.dx=0;frame.dy=0
				frame.erase("shots")
				var frames: Array=[]
				for i in range(100):frames.append(frame.duplicate(true))
				f.definition.moves[f.move_id].frames=frames
		var hashes: Array=[]
		for tick in range(40):
			var packed: Array=[0,0,0]
			first.step([UfeInputFrame.make(),UfeInputFrame.make()])
			replay.step([UfeInputFrame.unpack(packed),UfeInputFrame.unpack(packed)])
			check(first.state_hash()==replay.state_hash() and first.events==replay.events,"新束独立逐tick输入回放/%s/%s"%[facing,tick])
			hashes.append(first.state_hash())
		rows.append({"facing":facing,"hashes":hashes})
	write_json("new-replay-result.json",rows)
	completed.append("replay")

func run() -> void:
	if "--baseline" in OS.get_cmdline_user_args():
		write_json("legacy-before.json",legacy())
		print("FRAME_HITBOXES_BASELINE_SAVED");quit(0);return
	if "--compare" in OS.get_cmdline_user_args():
		var current:=legacy()
		var before: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OUT+"legacy-before.json"))
		check(before==JSON.parse_string(JSON.stringify(current)),"原有输入逐tick状态/事件/弹体字典/指纹保持")
		write_json("legacy-after.json",current)
	test_contract();test_clock_and_copy();test_validation();test_replay()
	check(completed==["contract","clock_copy","validation","replay"],"专项全部分支确实执行结束")
	write_json("logic-result.json",{"passed":errors.is_empty(),"completed":completed,"errors":errors})
	print("FRAME_HITBOXES ","PASS" if errors.is_empty() else str(errors))
	quit(0 if errors.is_empty() else 1)
@warning_ignore_restore("integer_division")
