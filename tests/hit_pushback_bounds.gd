extends SceneTree
## 真实step造成边界命中；只在fixture初始化设站位/HP/本测Definition，不在组内补救状态。
const DAMAGE: int = 80
const PUSH: int = 6
const ENERGY_COST: int = 100
const STAMINA_COST: int = 23
const STOP: int = 7
const LENGTH: int = 120
const MOVE: String = "bounds_probe"
const CASES: Array = ["front_wall", "near_wall", "rear_wall", "middle", "front_wall_ko"]
var errors: Array = []
var records: Array = []
var completed: Array = []
var run_out: String = "res://reports/review/2026-11-01/hit-pushback-bounds-v1/logic-run-v1/"

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok and not errors.has(label):
		errors.append(label)
		printerr("HIT_PUSHBACK_BOUNDS_FAIL " + label)

func canonical(value: Variant) -> String:
	return JSON.stringify(JSON.parse_string(JSON.stringify(value,"",true,true)),"",true,true)

func write_json(path: String, value: Variant) -> void:
	check(not FileAccess.file_exists(path), "拒绝覆盖证据/" + path)
	if FileAccess.file_exists(path): return
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		check(false,"无法写证据/" + path)
		return
	file.store_string(JSON.stringify(value,"\t",true) + "\n")
	file.close()

func pose() -> Dictionary:
	return {"sprite":0,"dx":0,"dy":0,"hitboxes":[],"hurtboxes":[[-18,0,36,128]],"cancel":[],"events":[]}

func definition(projectile: bool, attacker: bool) -> UfeFighterDefinition:
	var data := UfeFighterDefinition.new()
	data.id = "bounds_attacker" if attacker else "bounds_defender"
	data.display_name = "边界纯逻辑夹具"
	data.body_radius = 18
	# 所有状态沿用Fighter.frame的标准fallback；无防护屏/无敌/位移/额外攻击干扰。
	data.state_frames = {}
	data.moves = {}
	data.command_table = []
	if not attacker: return data
	var move: Dictionary = {"id":MOVE,"display_name":"真实输入边界探针","kind":"projectile" if projectile else "strike",
		"startup":2,"active":1,"recovery":9,"damage":DAMAGE,"stun":0,"hitstun":8,"blockstun":8,"pushback":PUSH,
		"energy_cost":ENERGY_COST,"stamina_cost":STAMINA_COST,"level":"mid","unblockable":false,
		"launch":false,"bounce":false,"knockdown":false,"chip_damage":0,"frames":[],
		"feedback":{"spark":"impact_light","block_spark":"impact_guard","hitstop":STOP,"blockstop":3,"shake":0,"flash":0}}
	for index in range(12):
		var frame := pose()
		if index == 2: frame.hitboxes = [[85,45,30,30]]
		move.frames.append(frame)
	if projectile:
		move.projectile = {"spawn":[70,60],"speed":16,"vy":0,"life":30,"box":[-12,-10,24,20],"effect":"pulse"}
	check(UfeMoveData.validate(move),"夹具招式必须先通过数据合法性/"+str(projectile))
	data.moves[MOVE] = move
	data.command_table = [{"move":MOVE,"states":["idle"],"directions":[5],"buttons":UfeInputFrame.LIGHT,"priority":10,"motion":[]}]
	return data

func setup(facing: int, kind: String) -> Dictionary:
	var target: int = 600
	if kind in ["front_wall","front_wall_ko"]: target = 1252 if facing > 0 else 28
	elif kind == "near_wall": target = 1245 if facing > 0 else 35
	elif kind == "rear_wall": target = 128 if facing > 0 else 1152
	return {"actor":target-facing*100,"target":target,"hp":DAMAGE if kind=="front_wall_ko" else 1000}

func fixture(facing: int, kind: String, projectile: bool) -> UfeMatchDirector:
	var sim := UfeMatchDirector.new(definition(projectile,true),definition(projectile,false),load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	var initial := setup(facing,kind)
	sim.fighters[0].x = int(initial.actor)
	sim.fighters[1].x = int(initial.target)
	sim.fighters[0].facing = facing
	sim.fighters[1].facing = -facing
	sim.fighters[1].stats.hp = int(initial.hp)
	return sim

func observe(sim: UfeMatchDirector) -> Dictionary:
	var pair: Array = []
	for fighter in sim.fighters:
		pair.append({"x":fighter.x,"height":fighter.height,"vx":fighter.vx,"vy":fighter.vy,"state":fighter.state,"state_tick":fighter.state_tick,
			"move":fighter.move_id,"move_tick":fighter.move_tick,"hp":fighter.stats.hp,"energy":fighter.stats.energy,"stamina":fighter.stats.stamina})
	var terminal_roots: Array = []
	for fighter in sim.terminal_view.get("fighters",[]): terminal_roots.append(int(fighter.snapshot[1]))
	return {"tick":sim.tick,"remaining":sim.remaining,"hash":sim.state_hash(),"hitstop":sim.hitstop,"finished":sim.finished,"winner":sim.winner,
		"pair":pair,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"terminal_roots":terminal_roots}

func in_bounds(sim: UfeMatchDirector) -> bool:
	return sim.fighters.all(func(f): return f.x >= 28 and f.x <= 1252)

func legacy_fingerprint(sim: UfeMatchDirector) -> String:
	var forms: Array = []
	for fighter in sim.fighters: forms.append(UfeBattleTransform.simulation_data(fighter.battle_form))
	var values: Array = [6,60,sim.rules.simulation_data(),sim.fighters[0].definition.simulation_data(),sim.fighters[1].definition.simulation_data(),forms,
		["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION]]
	return JSON.stringify(values,"",true).sha256_text()

func replay_and_fingerprint(sim: UfeMatchDirector, recorder: UfeReplayRecorder, rows: Array, facing: int, kind: String, projectile: bool, tag: String) -> Dictionary:
	var legacy := legacy_fingerprint(sim)
	check(UfeHitResolver.PUSHBACK_BOUNDARY_REVISION==2,tag+"/显式边界规则revision")
	check(sim.content_fingerprint==fixture(facing,kind,projectile).content_fingerprint,tag+"/相同规则重复建局指纹一致")
	check(sim.content_fingerprint!=legacy,tag+"/同招式数据旧规则指纹必须不同")
	var path := run_out + tag + "-replay.json"
	check(not FileAccess.file_exists(path),tag+"/拒绝覆盖回放")
	if FileAccess.file_exists(path): return {}
	check(recorder.save_file(path)==OK,tag+"/保存原输入回放")
	var loaded := UfeReplayRecorder.load_file(path,sim.content_fingerprint)
	check(loaded!=null,tag+"/当前规则回放可载入")
	var replay := fixture(facing,kind,projectile)
	if loaded != null:
		check(loaded.frames.size()==rows.size(),tag+"/回放完整输入长度")
		for index in range(loaded.frames.size()):
			var pair: Array = loaded.frames[index]
			replay.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
			check(canonical(observe(replay))==canonical(rows[index].post),tag+"/原输入逐tick完整状态事件弹体/%s"%index)
			check(in_bounds(replay),tag+"/回放双方每步根合法/%s"%index)
		check(replay.state_hash()==loaded.final_hash and loaded.final_hash==sim.state_hash(),tag+"/回放末hash精确一致")
	# 只改保存文件的规则指纹，原输入/招式数据保持；核真实loader拒绝与明确原因。
	var old_path := run_out + tag + "-old-rule-replay.json"
	recorder.fingerprint = legacy
	check(not FileAccess.file_exists(old_path),tag+"/拒绝覆盖旧规则夹具")
	if not FileAccess.file_exists(old_path):
		check(recorder.save_file(old_path)==OK,tag+"/保存旧规则同输入夹具")
		check(UfeReplayRecorder.load_file(old_path,sim.content_fingerprint)==null,tag+"/旧规则同输入必须被拒绝")
		check(UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放",tag+"/旧规则明确拒绝原因")
	return {"current":sim.content_fingerprint,"legacy_same_data":legacy,"final_hash":sim.state_hash(),"ticks":rows.size()}

func test_case(facing: int, kind: String, projectile: bool) -> void:
	var tag: String = "%s-%s-%s"%["projectile" if projectile else "melee","right" if facing>0 else "left",kind]
	var sim := fixture(facing,kind,projectile)
	var twin := fixture(facing,kind,projectile)
	var recorder := UfeReplayRecorder.new()
	var initial := setup(facing,kind)
	var rows: Array = []
	var cast_sent: bool = false
	var starts: int = 0
	var hits: int = 0
	var paused_ticks: int = 0
	var finished_ticks: int = 0
	var natural_charge: bool = false
	for index in range(LENGTH):
		var before := observe(sim)
		var actor := sim.fighters[0]
		var first := UfeInputFrame.make()
		if not cast_sent:
			if int(actor.stats.energy)<ENERGY_COST:
				first = UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
				natural_charge = true
			elif actor.state=="idle":
				first = UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
				cast_sent = true
		var inputs: Array = [first,UfeInputFrame.make()]
		sim.step(inputs)
		twin.step([UfeInputFrame.unpack(first.pack()),UfeInputFrame.unpack([0,0,0])])
		recorder.append(inputs,sim)
		var post := observe(sim)
		rows.append({"observation":index,"inputs":[first.pack(),[0,0,0]],"pre":before,"post":post})
		check(in_bounds(sim),tag+"/真实step后双方根始终合法/%s"%index)
		check(canonical(post)==canonical(observe(twin)),tag+"/独立同输入双模拟一致/%s"%index)
		if before.pair[0].move!=MOVE and post.pair[0].move==MOVE:
			starts += 1
			check(first.pack()==[0,0,UfeInputFrame.LIGHT] and before.pair[0].state=="idle",tag+"/真实J从idle启动")
			check(before.pair[0].energy==ENERGY_COST and post.pair[0].energy==0 and before.pair[0].stamina-post.pair[0].stamina==STAMINA_COST,tag+"/真实启动费用一次")
		for event in sim.events:
			if str(event.kind)=="hit" and int(event.player)==0:
				hits += 1
				check(str(event.move)==MOVE and bool(event.projectile)==projectile,tag+"/实体弹体真实接触类型")
				check(before.pair[1].hp-post.pair[1].hp==DAMAGE and post.pair[1].hp==(0 if kind=="front_wall_ko" else 920),tag+"/单次伤害保持")
				check(post.pair[0].energy==90 and post.pair[1].energy==40 and post.pair[0].stamina==1000-STAMINA_COST,tag+"/命中能量体力保持")
				check(post.hitstop==STOP,tag+"/实际命中触发hitstop")
				var room := (1252-int(before.pair[1].x)) if facing>0 else (int(before.pair[1].x)-28)
				var applied := mini(PUSH, room)
				check(post.pair[1].x-before.pair[1].x==facing*applied,tag+"/命中当帧只滑出初速或到墙")
				check(post.pair[0].x-before.pair[0].x==-facing*(PUSH-applied),tag+"/贴墙的剩余推退转给攻击方")
		if int(before.hitstop)>0 and not before.finished:
			paused_ticks += 1
			check(post.hitstop==int(before.hitstop)-1 and post.pair==before.pair and post.projectiles==before.projectiles,tag+"/hitstop全程边界合法且人物费用冻结/%s"%index)
		if before.finished:
			finished_ticks += 1
			check(post.hash==before.hash and post.tick==before.tick,tag+"/KO后不推进或补救根坐标/%s"%index)
	check(natural_charge and cast_sent and starts==1 and hits==1,tag+"/自然蓄能真实J唯一启动唯一命中")
	if kind=="front_wall_ko":
		check(sim.finished and sim.winner==0 and finished_ticks>=STOP,tag+"/末击KO后持续观察")
		var terminal_roots: Array = observe(sim).terminal_roots
		check(not sim.terminal_view.is_empty() and terminal_roots.size()==2 and terminal_roots.all(func(x):return x>=28 and x<=1252),tag+"/KO清理前只读终相根也合法")
	else:
		check(not sim.finished and paused_ticks==STOP,tag+"/完整命中停顿持续且未误KO")
		check(sim.fighters[1].stats.hp==920,tag+"/末状态不重复伤害")
	if kind in ["middle","rear_wall"]:
		check(sim.fighters[0].x==int(initial.actor),tag+"/中场攻击方不被推退带走")
	else:
		check(sim.fighters[0].x!=int(initial.actor),tag+"/贴墙后攻击方必须被推开")
	var replay_result := replay_and_fingerprint(sim,recorder,rows,facing,kind,projectile,tag)
	write_json(run_out+tag+"-trace.json",{"rows":rows,"setup":initial,"projectile":projectile,"facing":facing,"case":kind,"replay":replay_result,
		"starts":starts,"hits":hits,"paused_ticks":paused_ticks,"finished_ticks":finished_ticks})
	records.append({"case":tag,"starts":starts,"hits":hits,"paused_ticks":paused_ticks,"finished_ticks":finished_ticks,"final":observe(sim),"replay":replay_result})
	completed.append(tag)

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--test-out="): run_out = arg.trim_prefix("--test-out=").trim_suffix("/")+"/"
	if DirAccess.dir_exists_absolute(run_out):
		printerr("拒绝覆盖已有回归证据目录 " + run_out)
		quit(2)
		return
	check(DirAccess.make_dir_recursive_absolute(run_out)==OK,"创建独立证据目录")
	for projectile in [false,true]:
		for facing in [-1,1]:
			for kind in CASES: test_case(facing,str(kind),projectile)
	check(completed.size()==2*2*CASES.size(),"所有逻辑分支必须真正执行至末尾")
	write_json(run_out+"logic-result.json",{"passed":errors.is_empty(),"errors":errors,"completed":completed,"records":records,
		"pushback_boundary_revision":UfeHitResolver.PUSHBACK_BOUNDARY_REVISION,"scope":"纯模拟真实step/输入/接触/费用/KO与独立原输入回放；不代替画面或硬件验收。"})
	print("HIT_PUSHBACK_BOUNDS " + ("PASS" if errors.is_empty() else str(errors)))
	quit(0 if errors.is_empty() else 1)
