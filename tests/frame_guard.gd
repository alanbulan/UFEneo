extends SceneTree
## 新增逐帧护屏的整数接触规则；先保存旧输入逐tick基线，再比较。
var OUT := "user://frame-guard/"
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
			rows.append([sim.state_hash(),sim.events.duplicate(true)])
		result[str(part)]={"fingerprint":sim.content_fingerprint,"rows":rows}
	return result

func fixture(facing: int=1, body_contact: bool=false) -> UfeMatchDirector:
	var sim:=UfeContentDatabase.match_for()
	var a:=sim.fighters[0];var b:=sim.fighters[1]
	a.definition.moves=a.definition.moves.duplicate(true)
	b.definition.moves=b.definition.moves.duplicate(true)
	a.x=500 if facing>0 else 700;a.facing=facing
	b.x=600;b.facing=-facing
	var attack: Dictionary=a.definition.moves.light1.duplicate(true)
	attack.damage=40;attack.kind="strike";attack.unblockable=false;attack.level="mid"
	attack.launch=false;attack.bounce=false;attack.knockdown=false;attack.stamina_cost=0;attack.energy_cost=0
	var af: Dictionary=attack.frames[0].duplicate(true)
	af.hitboxes=[[40,60,20,20]]
	if body_contact:af.hitboxes.append([90,60,20,20])
	af.events=[];af.cancel=[];af.dx=0;af.dy=0
	attack.frames=[]
	for i in range(100):attack.frames.append(af.duplicate(true))
	a.definition.moves.light1=attack
	var screen: Dictionary=b.definition.moves.motion_22.duplicate(true)
	screen.kind="guard";screen.damage=0;screen.stamina_cost=0;screen.energy_cost=0
	var sf: Dictionary=screen.frames[0].duplicate(true)
	sf.hitboxes=[];sf.hurtboxes=[[-10,0,20,130]];sf.events=[];sf.cancel=[];sf.dx=0;sf.dy=0
	sf.melee_guard="block";sf.projectile_guard="block";sf.guard_box=[40,50,20,50]
	sf.guard_respects_unblockable=true;sf.guard_effect="teo_episode12_hex_ripple";sf.guard_sound="teo_hex_shield_guard"
	screen.frames=[]
	for i in range(100):screen.frames.append(sf.duplicate(true))
	b.definition.moves.motion_22=screen
	sim._start(a,"light1");sim._start(b,"motion_22")
	return sim

func test_melee() -> void:
	for facing in [-1,1]:
		var sim:=fixture(facing)
		var twin:=fixture(facing)
		check(UfeHitResolver.can_hit(sim.fighters[0],sim.fighters[1]),"攻击只碰屏框也能形成接触/%s"%facing)
		for tick in range(8):
			sim.step([UfeInputFrame.make(),UfeInputFrame.make()])
			twin.step([UfeInputFrame.unpack([0,0,0]),UfeInputFrame.unpack([0,0,0])])
			check(sim.state_hash()==twin.state_hash(),"护屏独立输入回放/%s/%s"%[facing,tick])
			if tick==0:
				check(sim.fighters[1].stats.hp==1000 and sim.fighters[1].move_id=="motion_22","屏挡招不扣血且保持本动作/%s"%facing)
				check(sim.fighters[1].stats.stamina==990,"每次40伤屏接触只扣10体/%s"%facing)
				check(sim.events.size()==1 and sim.events[0].kind=="block" and sim.events[0].guarded_by==1,"屏事件只结算一次/%s"%facing)
				check(sim.events[0].guard_sound=="teo_hex_shield_guard" and sim.events[0].feedback.block_spark=="teo_episode12_hex_ripple" and int(sim.events[0].effect_facing)==-facing,"本人防御声/屏涟漪/朝向/%s"%facing)
		var exhausted:=fixture(facing)
		exhausted.fighters[1].stats.stamina=5
		exhausted.step([UfeInputFrame.make(),UfeInputFrame.make()])
		check(exhausted.fighters[1].state=="guardbreak" and exhausted.fighters[1].move_id.is_empty() and exhausted.fighters[1].stats.stamina==0,"屏耗尽进入破防并撤动作/%s"%facing)
		for bypass in ["low","back","unblockable","throw","inactive"]:
			var hit:=fixture(facing,true)
			var a:=hit.fighters[0];var b:=hit.fighters[1]
			if bypass=="low":
				for frame in a.definition.moves.light1.frames:frame.hitboxes=[[90,0,20,20]]
			elif bypass=="back":b.facing=facing
			elif bypass=="unblockable":a.definition.moves.light1.unblockable=true
			elif bypass=="throw":
				a.definition.moves.light1.kind="throw"
				check(UfeFrameGuard.melee_point(a,b,a.definition.moves.light1)==null,"投技跳过屏框/%s"%facing)
				check(UfeHitResolver.apply(a,b,a.definition.moves.light1,false,hit.rules)=="hit" and b.state=="thrown","投技正常抓中屏后人物/%s"%facing)
				continue
			elif bypass=="inactive":
				for frame in b.definition.moves.motion_22.frames:frame.erase("melee_guard")
			hit.step([UfeInputFrame.make(),UfeInputFrame.make()])
			check(hit.events.any(func(e):return e.kind=="hit") and not hit.events.any(func(e):return e.has("guarded_by")),"屏外低段/背面/不可防/投技/非有效帧正常命中/%s/%s"%[facing,bypass])
	completed.append("melee")

func test_projectile() -> void:
	for facing in [-1,1]:
		for unblockable in [false,true]:
			var sim:=fixture(facing)
			sim.fighters[0].definition.moves.pulse=sim.fighters[0].definition.moves.pulse.duplicate(true)
			sim.fighters[0].definition.moves.pulse.unblockable=unblockable
			UfeProjectileResolver.spawn(sim,0,{"spawn":[50,70],"box":[-5,-5,10,10],"speed":0},"pulse")
			var new_contacts: Array=[]
			UfeProjectileResolver.advance(sim,new_contacts)
			check(sim.events.any(func(e):return e.kind=="projectile_block")==not unblockable,"新屏遵守不可防弹体/%s/%s"%[facing,unblockable])
			if not unblockable:
				check(sim.events[0].guard_effect=="teo_episode12_hex_ripple" and sim.events[0].guard_sound=="teo_hex_shield_guard","弹体防御使用屏专属光声/%s"%facing)
			else:
				check(sim.projectiles.size()==1,"不可防弹体经过屏框继续飞行/%s"%facing)
		# 旧屏没有显式选项时仍保留原有拦截不可防弹体行为。
		var old:=fixture(facing)
		for frame in old.fighters[1].definition.moves.motion_22.frames:
			for key in ["melee_guard","guard_effect","guard_sound","guard_respects_unblockable"]:frame.erase(key)
		old.fighters[0].definition.moves.pulse.unblockable=true
		UfeProjectileResolver.spawn(old,0,{"spawn":[50,70],"box":[-5,-5,10,10],"speed":0},"pulse")
		var contacts: Array=[];UfeProjectileResolver.advance(old,contacts)
		check(old.events==[{"kind":"projectile_block","player":1,"move":"motion_22"}],"未声明新字段的屏事件字节结构保持/%s"%facing)
	completed.append("projectile")

func test_validation() -> void:
	var sim:=fixture()
	var valid: Dictionary=sim.fighters[1].definition.moves.motion_22
	check(UfeMoveData.validate(valid),"合法整数屏框通过数据门")
	for box in [null,[],[0,0,0,20],[0,0,10,-2],[0,0,1.5,20],[false,0,10,20],[0,0,INF,20],[0,0,10]]:
		var move:=valid.duplicate(true);move.frames[0].guard_box=box
		check(not UfeMoveData.validate(move),"非法屏框拒收/%s"%[box])
	for mode in ["absorb","",1]:
		var move:=valid.duplicate(true);move.frames[0].melee_guard=mode
		check(not UfeMoveData.validate(move),"近战屏模式只接受block/%s"%mode)
	completed.append("validation")

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	for argument in args:
		if argument.begins_with("--test-out="):OUT=argument.trim_prefix("--test-out=").trim_suffix("/")+"/"
	if "--baseline" in args:
		write_json("legacy-before.json",legacy())
		print("FRAME_GUARD_BASELINE_SAVED");quit(0);return
	if "--compare" in args:
		var current:=legacy()
		var baseline: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OUT+"legacy-before.json"))
		check(baseline==JSON.parse_string(JSON.stringify(current)),"原有专属/盾/反射/吸收逐tick状态、事件或指纹变化")
		write_json("legacy-after.json",current)
	test_melee();test_projectile();test_validation()
	check(completed==["melee","projectile","validation"],"全部测试分支必须执行结束，脚本中途异常不能记为通过")
	write_json("logic-result.json",{"passed":errors.is_empty(),"errors":errors})
	print("FRAME_GUARD ","PASS" if errors.is_empty() else str(errors))
	quit(0 if errors.is_empty() else 1)
