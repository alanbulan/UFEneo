extends SceneTree
## 待根串行窗口运行的纯逻辑夹具；直接内存同步，不冒称真实键盘/main/输入回放验收。
const Roots = preload("res://core/combat/throw_root_offsets.gd")
var OUT: String=""
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
func fingerprint_and_loader_case() -> void:
	var sim:=fixture({"mode":"root","pose":"thrown_back","sprite":0,"facing":1,"root":[7,11]})
	var forms: Array=[]
	for f in sim.fighters:forms.append(UfeBattleTransform.simulation_data(f.battle_form))
	var legacy_payload:=[6,60,sim.rules.simulation_data(),sim.fighters[0].definition.simulation_data(),sim.fighters[1].definition.simulation_data(),forms,["round_end_identity",1],["move_start_conditions",UfeMatchDirector.MOVE_START_RULE_REVISION],["hit_pushback_bounds",UfeHitResolver.PUSHBACK_BOUNDARY_REVISION],["throw_target_air",UfeHitResolver.THROW_TARGET_RULE_REVISION],["throw_current_capture",UfeHitResolver.THROW_CURRENT_CAPTURE_REVISION],["body_pushbox_2d",UfeMatchDirector.BODY_PUSHBOX_2D_REVISION]]
	var legacy_sha:=JSON.stringify(legacy_payload,"",true).sha256_text()
	check(sim.content_fingerprint!=legacy_sha,"无覆盖字段也显式改变root语义指纹")
	var replay:=UfeReplayRecorder.new();replay.append([UfeInputFrame.make(),UfeInputFrame.make()],sim)
	var current_path:=OUT+"synthetic-current-fingerprint.json";check(replay.save_file(current_path)==OK,"写独立报告合成回放")
	check(UfeReplayRecorder.load_file(current_path,sim.content_fingerprint)!=null,"同规则合成格式6可读")
	var data: Variant=JSON.parse_string(FileAccess.get_file_as_string(current_path));data.content=legacy_sha
	var old_path:=OUT+"synthetic-prior-fingerprint.json";write_json(old_path,data)
	check(UfeReplayRecorder.load_file(old_path,sim.content_fingerprint)==null and UfeReplayRecorder.last_error=="规则或招式数据已改变，无法播放该回放","明确拒绝旧语义指纹，不覆盖用户回放")
	results.append({"case":"fingerprint","before_root_semantics":legacy_sha,"new":sim.content_fingerprint,"revision":Roots.REVISION,"synthetic_loader_only_not_input_replay":true})
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--logic-out="):OUT=arg.trim_prefix("--logic-out=").trim_suffix("/")+"/"
	assert(OUT.begins_with("res://reports/review/") and not OUT.contains("..") and not DirAccess.dir_exists_absolute(OUT))
	DirAccess.make_dir_recursive_absolute(OUT)
	for identity in ["ultraman","ultraseven"]:definitions[identity]=UfeContentDatabase.fighter(identity,true)
	schema_cases();root_and_legacy_cases();floor_and_hold_cases();release_cases();invalid_midhold_case();fingerprint_and_loader_case()
	write_json(OUT+"synthetic-logic-result.json",{"errors":errors,"results":results,"scope":"synthetic direct sync/schema/fingerprint; not actual main or input replay"})
	print("THROW_ROOT_OVERRIDE_SYNTHETIC ",JSON.stringify({"errors":errors,"report":OUT}));quit(0 if errors.is_empty() else 1)
