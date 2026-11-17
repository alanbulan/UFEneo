extends SceneTree
## 正式模拟8例和独立原输入回放；不运行图形，不冒充动作实速验收。
const Factory=preload("res://tests/review/fighters/zetton/crouch_block/candidate_factory.gd")
const Driver=preload("res://tests/review/fighters/zetton/crouch_block/main_driver.gd")
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var path: String=""
	var out: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="):path=arg.trim_prefix("--contract=")
		elif arg.begins_with("--out="):out=arg.trim_prefix("--out=")
		else:assert(false,"未知候选逻辑参数")
	assert(not path.is_empty() and not out.is_empty())
	out=ProjectSettings.globalize_path(out).simplify_path()
	assert(out.begins_with(ProjectSettings.globalize_path("res://reports/zetton-crouch-block-resume/")) and not FileAccess.file_exists(out))
	var cfg: Dictionary=Factory.read_sealed(path)
	var errors: Array=[]
	var results: Array=[]
	var probe:=UfeSideView.new()
	probe.intro_tick=-1
	var manifests: Array=[]
	for id in ["ultraman","zetton"]:manifests.append(UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%id))
	manifests[1].clips.crouch_blockstun=cfg.clip.duplicate(true)
	for direction in [1,-1]:
		for kind in Factory.CASES:
			var sim:=Factory.make_match(cfg,direction,kind)
			var driver:=Driver.new()
			driver.candidate_contract=cfg;driver.direction=direction;driver.kind=kind
			driver.prepare_match(sim)
			var trace: Array=[]
			for frame in range(Factory.LENGTH):
				var first: UfeInputFrame=driver.sample(frame,sim)
				var second: UfeInputFrame=driver.second_sample(frame)
				sim.step([first,second])
				var pair: Array=[]
				for i in range(2):pair.append(Driver.fighter_record(sim.fighters[i],probe._animation(sim.fighters[i],manifests[i])))
				trace.append({"movie_frame":frame,"tick":sim.tick,"pair":pair,"state_hash":sim.state_hash(),"original_inputs":[first.pack(),second.pack()],"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"hitstop":sim.hitstop})
			var tape: Dictionary={"candidate_contract_sha256":cfg._candidate_contract_sha256,"simulation_fingerprint":sim.content_fingerprint,"direction":direction,"kind":kind,
				"original_pairs":trace.map(func(row):return row.original_inputs),"state_hashes":trace.map(func(row):return row.state_hash),"events":trace.map(func(row):return row.events),"projectiles":trace.map(func(row):return row.projectiles)}
			var replay: Dictionary=Factory.verify_original_inputs(cfg,tape)
			var case_errors: Array=Factory.verify_trace(cfg,kind,trace)
			case_errors.append_array(replay.errors)
			var record: Dictionary={"direction":direction,"kind":kind,"trace":trace,"replay":replay,"errors":case_errors,"final_hash":sim.state_hash()}
			results.append(record)
			if not case_errors.is_empty():errors.append({"direction":direction,"kind":kind,"errors":case_errors})
	probe.free()
	var file:=FileAccess.open(out,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify({"cases":results,"errors":errors,"installed":false,"graphical_review":false,"real_speed_art_accepted":false,"candidate_contract_sha256":cfg._candidate_contract_sha256},"\t"));file.close()
	print("杰顿低蹲硬直逻辑用例：",results.size(),"，错误：",errors.size())
	quit(0 if errors.is_empty() else 1)
