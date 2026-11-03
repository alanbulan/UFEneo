extends SceneTree
## 可选逐相多矩形的整数接触与旧招逐tick兼容专项。
const OUT := "res://reports/review/2026-10-28/projectile-frame-hitboxes-core-v1/"
const CONTRACT := "res://reports/review/2026-10-28/ultraman-teo-s6/air-special-return-v1/beam-collision-contract-v1.json"
var errors: Array = []
var completed: Array = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		errors.append(label)
		printerr(label)

func write_json(name: String, value: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	FileAccess.open(OUT+name,FileAccess.WRITE).store_string(JSON.stringify(value,"\t",true)+"\n")

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
	var contract: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTRACT))
	var sim:=UfeContentDatabase.match_for()
	var a:=sim.fighters[0];var b:=sim.fighters[1]
	a.definition.moves=a.definition.moves.duplicate(true);b.definition.moves=b.definition.moves.duplicate(true)
	a.x=400;a.height=240;a.facing=facing
	b.x=400;b.height=240;b.facing=-facing
	var move: Dictionary=b.definition.moves.motion_22.duplicate(true)
	move.energy_cost=0;move.stamina_cost=0
	var frame: Dictionary=move.frames[0].duplicate(true)
	var local: Array=[int(world[0])-b.x if b.facing>0 else b.x-int(world[0])-int(world[2]),int(world[1])-b.height,int(world[2]),int(world[3])]
	frame.hurtboxes=[local];frame.hitboxes=[];frame.events=[];frame.cancel=[]
	frame.erase("projectile_guard");frame.erase("guard_box")
	if not mode.is_empty():
		frame.projectile_guard=mode;frame.guard_box=local
		frame.hurtboxes=[[1000,1000,1,1]]
	move.frames=[frame];b.definition.moves.motion_22=move
	sim._start(a,"pulse");sim._start(b,"motion_22")
	check(a.move_id=="pulse" and b.move_id=="motion_22","夹具必须实际进入发射/护屏招")
	var shot: Dictionary=contract.spawn_proposal.duplicate(true)
	shot.spawn=[0,0];shot.anchor=[0,0];shot.life=100;shot.box=[0,-280,400,280]
	UfeProjectileResolver.spawn(sim,0,shot,"pulse")
	sim.projectiles[0].age=maxi(0,phase*4-1)
	return sim

func test_contract() -> void:
	var contract: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTRACT))
	var rows: Array=[]
	for item in contract.cases:
		for mode in ["","block","reflect","absorb"]:
			var sim:=fixture(int(item.facing),item.world_hurt_box,int(item.phase),mode)
			var contacts: Array=[]
			UfeProjectileResolver.advance(sim,contacts)
			var found: bool=not contacts.is_empty() if mode.is_empty() else not sim.events.is_empty()
			check(found==bool(item.expected_contact),"分相双向束芯/包围框空白/%s/%s"%[item.id,mode])
			check(contacts.size()<=1 and sim.events.size()<=1,"多分段单次结算/%s/%s"%[item.id,mode])
			if found:
				var examples: Array=item.intersection_examples
				if mode.is_empty():
					var point: Vector2i=contacts[0].point
					check(examples.any(func(e):return point==Rect2i(int(e[0]),int(e[1]),int(e[2]),int(e[3])).get_center()),"命中点取实际分段交集/%s"%item.id)
					var again: Array=[];UfeProjectileResolver.advance(sim,again)
					check(again.is_empty(),"已接触束不重复伤害/%s"%item.id)
				elif mode=="reflect":
					check(sim.projectiles.size()==1 and sim.projectiles[0].owner==1 and int(sim.projectiles[0].facing)==-int(item.facing),"新束反射归属及朝向/%s"%item.id)
				elif mode=="absorb":
					check(sim.projectiles.is_empty() and sim.fighters[1].combat.absorbed==1,"新束吸收仅累计一次/%s"%item.id)
				else:check(sim.projectiles.is_empty(),"屏只挡真实束芯/%s"%item.id)
			rows.append({"case":item.id,"mode":mode,"expected":item.expected_contact,"actual":found})
	write_json("contract-result.json",rows)
	completed.append("contract")

func test_clock_and_copy() -> void:
	var p: Dictionary={"x":400,"height":240,"facing":1,"age":0,"box":[0,-20,100,20],"frame_hitboxes":[[[0,0,4,4],[0,0,4,4]],[],[[20,0,4,4]],[[30,0,4,4]]]}
	for age in range(32):
		p.age=age
		var phase: int=(age/4)%4
		for x in [0,20,30]:
			var point: Variant=UfeProjectileResolver.contact_point(p,Rect2i(400+x,240,1,1))
			check((point!=null)==((phase==0 and x==0) or (phase==2 and x==20) or (phase==3 and x==30)),"age/4相序及空有效相/%s/%s"%[age,x])
	var sim:=UfeContentDatabase.match_for()
	var shot: Dictionary={"spawn":[0,240],"speed":0,"frame_hitboxes":[[[0,0,4,4]]]}
	UfeProjectileResolver.spawn(sim,0,shot,"pulse")
	shot.frame_hitboxes[0][0][0]=99
	check(sim.projectiles[0].frame_hitboxes[0][0][0]==0,"显式新框深拷贝不与招式表共享可变数组")
	UfeProjectileResolver.spawn(sim,0,{"speed":0},"pulse")
	check(not sim.projectiles[1].has("frame_hitboxes"),"旧弹体不补缺省键")
	var overlap:=fixture(1,[500,184,1,1],0)
	var box: Array=[100,-56,2,2]
	overlap.projectiles[0].frame_hitboxes=[[box,box,box]]
	var contacts: Array=[];UfeProjectileResolver.advance(overlap,contacts)
	check(contacts.size()==1,"重叠多框只形成一次伤害接触")
	var invulnerable:=fixture(1,[500,184,1,1],0)
	invulnerable.fighters[1].combat.invulnerable=10
	contacts=[];UfeProjectileResolver.advance(invulnerable,contacts)
	check(contacts.is_empty(),"新框遵守原无敌")
	var expired:=fixture(1,[500,184,1,1],0)
	expired.projectiles[0].life=1
	contacts=[];UfeProjectileResolver.advance(expired,contacts)
	check(contacts.is_empty() and expired.projectiles.is_empty(),"到期先于分段接触")
	completed.append("clock_copy")

func test_validation() -> void:
	var valid: Dictionary=UfeContentDatabase.fighter("ultraman").moves.pulse.duplicate(true)
	var contract: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTRACT))
	valid.projectile.frame_hitboxes=contract.spawn_proposal.frame_hitboxes
	check(UfeMoveData.validate(valid),"实际四相整数束芯表通过数据门")
	for boxes in [[[]],[[[0.0,-2.0,4.0,4.0]]]]:
		var move:=valid.duplicate(true);move.projectile.frame_hitboxes=boxes
		check(UfeMoveData.validate(move),"允许无攻击相及JSON整数值")
	for boxes in [null,{},[],[null],[[null]],[[[0,0,0,2]]],[[[0,0,2,-1]]],[[[0,0,2.5,2]]],[[[false,0,2,2]]],[[[0,0,INF,2]]],[[[0,0,NAN,2]]],[[[0,0,2]]]]:
		var move:=valid.duplicate(true);move.projectile.frame_hitboxes=boxes
		check(not UfeMoveData.validate(move),"非法逐相整数框拒收/%s"%[boxes])
		move=valid.duplicate(true);move.projectile.erase("frame_hitboxes");move.frames[0].shots=[{"frame_hitboxes":boxes}]
		check(not UfeMoveData.validate(move),"逐帧shots同样拒收非法框/%s"%[boxes])
	completed.append("validation")

func test_replay() -> void:
	var rows: Array=[]
	for facing in [-1,1]:
		var world: Array=[500 if facing>0 else 299,184,1,1]
		var first:=fixture(facing,world,0)
		var replay:=fixture(facing,world,0)
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
	print("FRAME_HITBOXES ","PASS" if errors.is_empty() else errors)
	quit(0 if errors.is_empty() else 1)
