extends SceneTree
## 正式模拟root覆盖回归；不代表背掀美术或主游戏验收。
const Roots = preload("res://core/combat/throw_root_offsets.gd")
var OUT: String="user://throw-root-overrides/"
var errors: Array=[]
var results: Array=[]
var definitions: Dictionary={}

func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	if not ok:errors.append(label);printerr(label)
func write_json(path: String,data: Variant) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(data,"\t",true)+"\n")
func clone(identity: String) -> UfeFighterDefinition:
	var source: UfeFighterDefinition=definitions[identity]
	var f:=UfeFighterDefinition.new()
	f.id=source.id;f.display_name=source.display_name;f.max_health=source.max_health
	f.walk_speed=source.walk_speed;f.jump_speed=source.jump_speed;f.body_radius=source.body_radius
	f.moves=source.moves.duplicate(true);f.state_frames=source.state_frames.duplicate(true);f.command_table=source.command_table.duplicate(true)
	return f
func fixture(target: Dictionary,facing: int=1,height: int=0) -> UfeMatchDirector:
	var actor:=clone("ultraman");var victim:=clone("ultraseven")
	actor.moves.throw_forward.frames=[{"sprite":0,"dx":0,"dy":0,"hitboxes":[],"hurtboxes":[[-8,0,16,64]],"cancel":[],"events":[],"target":target.duplicate(true)}]
	var sim:=UfeMatchDirector.new(actor,victim,load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	var a:=sim.fighters[0];var b:=sim.fighters[1]
	a.x=600;a.facing=facing;a.height=height;a.move_id="throw_forward";a.move_tick=0
	b.x=a.x-30*facing;b.height=90;b.facing=facing;b.enter("thrown")
	UfeThrowResolver.begin(sim,0,a.definition.moves.throw_forward)
	return sim
func schema_cases() -> void:
	var test_victim: UfeFighter=fixture({"mode":"root","pose":"thrown_back","root":[0,0]}).fighters[1]
	for table in [{},{"ultraseven":[-19,90]},{"other_identity":[0,-3]}]:check(Roots.valid(table),"合法覆盖表含空表/负高度")
	check(Roots.valid(JSON.parse_string('{"ultraseven":[-19,90]}')),"JSON整值float允许")
	var invalid: Array=[null,[],false,{0:[0,1]},{" ":[0,1]},{" ultraseven":[0,1]},{"ultraseven ":[0,1]},{"ultraseven":null},{"ultraseven":{}},{"ultraseven":[0]},{"ultraseven":[0,1,2]},{"ultraseven":[true,1]},{"ultraseven":[0,1.25]},{"ultraseven":[NAN,1]},{"ultraseven":[0,INF]}]
	for mode in ["hold","root","release"]:
		var move: Dictionary=definitions.ultraman.moves.throw_forward.duplicate(true)
		var frame: Dictionary=move.frames[0]
		frame.target={"mode":mode,"pose":"thrown_back","sprite":0,"facing":1,"root":[7,11]}
		for table in invalid:
			frame.target.root_overrides=table
			check(not UfeMoveData.validate(move),"MoveData全部模式拒绝非法覆盖/%s/%s"%[mode,str(table)])
			check(not UfeThrowResolver.can_capture(test_victim,move),"捕获前拒绝非法覆盖")
		frame.target.root_overrides={"ultraseven":[-19,90]}
		check(UfeMoveData.validate(move),"MoveData合法覆盖/%s"%mode)
func root_and_legacy_cases() -> void:
	for facing in [-1,1]:
		for height in [0,64]:
			var target:={"mode":"root","pose":"thrown_back","sprite":0,"facing":1,"root":[7,11]}
			var states: Array=[]
			for mode in ["absent","missing_identity","empty_map","matching_identity"]:
				var t:=target.duplicate(true)
				if mode=="missing_identity":t.root_overrides={"unlisted_identity":[999,999]}
				elif mode=="empty_map":t.root_overrides={}
				elif mode=="matching_identity":t.root_overrides={"ultraseven":[-19,90]}
				var sim:=fixture(t,facing,height);UfeThrowResolver.sync(sim)
				var a:=sim.fighters[0];var b:=sim.fighters[1]
				var expected: Array=[-19,90] if mode=="matching_identity" else [7,11]
				check(b.x==a.x+facing*int(expected[0]) and b.height==height+int(expected[1]),"root双向/空中/%s/%s/%s"%[mode,facing,height])
				states.append(sim.state_hash())
				results.append({"case":"root","mode":mode,"facing":facing,"actor_height":height,"victim_root":[b.x-a.x,b.height],"hash":sim.state_hash()})
			check(states[0]==states[1] and states[0]==states[2],"缺字段/身份/空表完整状态hash沿旧路径")
func floor_and_hold_cases() -> void:
	for facing in [-1,1]:
		for with_override in [false,true]:
			var t:={"mode":"hold","pose":"grabbed","sprite":0,"facing":1,"grip":[0,67],"root":[0,0]}
			if with_override:t.root_overrides={"ultraseven":[0,30]}
			var sim:=fixture(t,facing);var a:=sim.fighters[0];var b:=sim.fighters[1]
			b.definition.state_frames.grabbed=[
				{"sprite":0,"hurtboxes":[[-8,0,16,100]],"grab_points":{"waist":[0,86]},"throw_hold_floor_variants":[1]},
				{"sprite":1,"hurtboxes":[[-8,0,16,80]],"grab_points":{"waist":[0,61]}}]
			check(UfeThrowResolver.victim_sprite(a,b,a.frame().target)==(0 if with_override else 1),"floor-safe与sync读取同一root覆盖")
			UfeThrowResolver.sync(sim)
			var expected_height:=11 if with_override else 6
			check(b.height==expected_height and b.x==a.x,"hold同步采用floor-safe同一offset")
			results.append({"case":"floor_hold","override":with_override,"facing":facing,"pose_sprite":b.motion.pose_sprite,"height":b.height})
func release_cases() -> void:
	for facing in [-1,1]:
		var t:={"mode":"release","pose":"thrown_back","sprite":0,"facing":1,"root":[120,0],"root_overrides":{"ultraseven":[240,30]},"progress":[1,3],"ground":true}
		var sim:=fixture(t,facing);var a:=sim.fighters[0];var b:=sim.fighters[1]
		var actual: Array=[]
		for numerator in [1,2,3]:
			a.frame().target.progress=[numerator,3]
			UfeThrowResolver.sync(sim)
			actual.append([(b.x-a.x)*facing,b.height])
		check(actual==[[60,70],[150,50],[240,30]],"release落地目标/高度同用覆盖且整数推进")
		check(int(b.motion.release_goal_x)==240,"release首次记忆覆盖目标")
		results.append({"case":"release","facing":facing,"relative_roots":actual})
func invalid_midhold_case() -> void:
	var t:={"mode":"root","pose":"thrown_back","sprite":0,"facing":1,"root":[7,11],"root_overrides":{"ultraseven":[0,1.25]}}
	var sim:=fixture(t);UfeThrowResolver.sync(sim)
	check(sim.fighters[1].state=="down" and sim.fighters[0].move_id.is_empty(),"运行时非法覆盖有界退出")
	check(sim.events.size()==1 and sim.events[0].reason=="invalid_root_override" and sim.hitstop==0,"非法覆盖不静默回零或制造命中")
# 人工对照：保留当前全部全局规则，仅省root扩展；不代表真实历史全局版本。
func fingerprint_without_root_rule(sim: UfeMatchDirector) -> String:
	var forms: Array=[]
	for f in sim.fighters:forms.append(UfeBattleTransform.simulation_data(f.battle_form))
	var payload:=[6,60,sim.rules.simulation_data(),sim.fighters[0].definition.simulation_data(),sim.fighters[1].definition.simulation_data(),forms,["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION],["hit_pushback_bounds",UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],["throw_target_air",UfeHitResolver.THROW_TARGET_RULE_REVISION],["chase_interrupt",UfeMatchDirector.CHASE_INTERRUPT_RULE_REVISION],["projectile_contact_direction",UfeHitResolver.PROJECTILE_DIRECTION_RULE_REVISION],["projectile_move_isolation",UfeHitResolver.PROJECTILE_MOVE_ISOLATION_RULE_REVISION], ["projectile_beam_reflection", UfeProjectileResolver.BEAM_REFLECTION_RULE_REVISION],["crouch_guard_resume_hold",UfeMatchDirector.CROUCH_GUARD_RESUME_RULE_REVISION],["hit_crouch_guard_resume_pose",UfeMatchDirector.HIT_CROUCH_GUARD_RESUME_RULE_REVISION]]
	return JSON.stringify(payload,"",true).sha256_text()

func fingerprint_and_loader_case() -> void:
	for enabled in [false,true]:
		var target:={"mode":"root","pose":"thrown_back","sprite":0,"facing":1,"root":[7,11]}
		if enabled:target.root_overrides={"ultraseven":[-19,90]}
		var sim:=fixture(target);var baseline_sha:=fingerprint_without_root_rule(sim)
		check((sim.content_fingerprint!=baseline_sha)==enabled,"仅覆盖内容绑定新语义")
		var replay:=UfeReplayRecorder.new();replay.append([UfeInputFrame.make(),UfeInputFrame.make()],sim)
		var current_path:=OUT+"current-%s.json"%enabled;check(replay.save_file(current_path)==OK,"隔离合成回放保存")
		check(UfeReplayRecorder.load_file(current_path,sim.content_fingerprint)!=null,"同规则文件可读")
		var data: Variant=JSON.parse_string(FileAccess.get_file_as_string(current_path));data.content=baseline_sha
		var old_path:=OUT+"prior-%s.json"%enabled;write_json(old_path,data)
		check((UfeReplayRecorder.load_file(old_path,sim.content_fingerprint)==null)==enabled,"无覆盖时当前规则去root基线可读/覆盖语义隔离")
		results.append({"case":"fingerprint","uses_overrides":enabled,"current_rules_without_root":baseline_sha,"new":sim.content_fingerprint})
	var actor:=clone("ultraman");var victim:=clone("ultraseven");var changed:=clone("ultraseven")
	changed.moves.throw_forward.frames[0].target.root_overrides={"ultraman":[1,2]}
	for enabled in [false,true]:
		var choice:={"id":"test-form","enabled":enabled,"mode":"temporary","target_definition":changed}
		var form:={"id":"test-choice","enabled":true,"mode":"temporary","target_definition":victim,"choices":{"test":choice}}
		var sim:=UfeMatchDirector.new(actor,victim,load("res://content/rules/neo.tres"),UfeContentDatabase.states(),{"ultraman":form})
		check((sim.content_fingerprint!=fingerprint_without_root_rule(sim))==enabled,"只对可达开放形态绑定版本")

func input_fixture(facing: int,edge: int,invalid: bool=false) -> UfeMatchDirector:
	var actor:=clone("ultraman");var victim:=clone("ultraseven")
	for frame in actor.moves.throw_forward.frames:
		var target: Dictionary=frame.get("target",{})
		if target.is_empty():continue
		var root_rule: Array=target.get("root",[0,0])
		target.root_overrides={"ultraseven":[int(root_rule[0])+4,int(root_rule[1])+(6 if str(target.get("mode",""))=="hold" else 0)]}
		if invalid:target.root_overrides.ultraseven=[0,1.25]
	var sim:=UfeMatchDirector.new(actor,victim,load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	sim.fighters[0].x=edge;sim.fighters[1].x=edge+52*facing
	sim.fighters[0].facing=facing;sim.fighters[1].facing=-facing;sim.fighters[0].stats.stamina=500
	return sim

func actual_input_cases() -> void:
	for facing in [-1,1]:
		for edge in [120,600,1160]:
			for kind in ["land","tech3","miss","invalid"]:
				var sim:=input_fixture(facing,edge,kind=="invalid");var second:=input_fixture(facing,edge,kind=="invalid")
				var recorder:=UfeReplayRecorder.new();var hashes: Array=[]
				var captured:=false;var age:=0;var slams:=0;var techs:=0;var held:=0
				for tick in range(110):
					var inputs:=[UfeInputFrame.make(),UfeInputFrame.make()]
					if tick==10:inputs[0]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
					if kind=="miss" and tick==9:inputs[1]=UfeInputFrame.make(0,1)
					if captured:
						age+=1
						if kind=="tech3" and age==3:inputs[1]=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
					sim.step(inputs);second.step(inputs.map(func(i):return UfeInputFrame.unpack(i.pack())))
					recorder.append(inputs,sim);hashes.append(sim.state_hash())
					check(sim.state_hash()==second.state_hash(),"逐tick输入重放")
					check(JSON.stringify(sim.events,"",true)==JSON.stringify(second.events,"",true),"逐tick事件一致")
					var a:=sim.fighters[0];var b:=sim.fighters[1]
					if b.state=="thrown":captured=true
					if b.state=="thrown" and str(a.frame().get("target",{}).get("mode",""))=="hold":
						held+=1
						var target: Dictionary=a.frame().target;var offset: Array=Roots.offset(b,target);var point: Array=b.frame().grab_points.waist
						check(b.x+b.facing*int(point[0])==a.x+a.facing*(int(target.grip[0])+int(offset[0])),"真实抓点x")
						check(b.height+int(point[1])==a.height+int(target.grip[1])+int(offset[1]),"真实抓点高度")
					for event in sim.events:
						if event.kind=="throw_slam":slams+=1
						if event.kind=="throw_tech":techs+=1
				var damage:=int(sim.fighters[0].definition.moves.throw_forward.damage) if kind=="land" else 0
				check(slams==(1 if kind=="land" else 0),"落地/拆投/落空/非法拒绝")
				check(techs==(1 if kind=="tech3" else 0),"三tick拆投")
				check(int(sim.fighters[1].stats.hp)==1000-damage,"伤害守恒")
				if kind=="land":check(held>0,"真实hold消费")
				if kind in ["miss","invalid"]:check(not captured,"无错误捕获")
				var path:=OUT+"inputs-%s-%s-%s.json"%[facing,edge,kind]
				check(recorder.save_file(path)==OK,"真实输入文件写入隔离目录")
				var loaded:=UfeReplayRecorder.load_file(path,sim.content_fingerprint)
				check(loaded!=null,"真实输入文件可按本规则读取")
				if loaded!=null:
					var restored:=input_fixture(facing,edge,kind=="invalid")
					for tick in range(loaded.frames.size()):
						restored.step(loaded.frames[tick].map(func(i):return UfeInputFrame.unpack(i)))
						check(restored.state_hash()==hashes[tick],"独立文件重放逐tick相同")
					check(restored.state_hash()==loaded.final_hash,"独立文件重放终态相同")
				results.append({"case":"actual_input","facing":facing,"edge":edge,"kind":kind,"held":held,"slams":slams,"techs":techs})

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--logic-out="):OUT=arg.trim_prefix("--logic-out=").trim_suffix("/")+"/"
	assert((OUT.begins_with("res://reports/review/") or OUT=="user://throw-root-overrides/") and not OUT.contains(".."))
	DirAccess.make_dir_recursive_absolute(OUT)
	for identity in ["ultraman","ultraseven"]:definitions[identity]=UfeContentDatabase.fighter(identity,true)
	schema_cases();root_and_legacy_cases();floor_and_hold_cases();release_cases();invalid_midhold_case();fingerprint_and_loader_case();actual_input_cases()
	write_json(OUT+"synthetic-logic-result.json",{"errors":errors,"results":results,"scope":"sync/schema/fingerprint and packed-input dual-instance and isolated saved-file replay; not main/back-lift visual acceptance"})
	print("THROW_ROOT_OVERRIDE_SYNTHETIC ",JSON.stringify({"errors":errors,"report":OUT}));quit(0 if errors.is_empty() else 1)
