extends SceneTree
## 明确失败入口证据：独立消费原物理键InputFrame，不加载driver、不调用sample、不伪造命中。
const Factory=preload("res://tools/rebuild/gomora/back_lift_resume/runtime/factory.gd")
var errors: Array=[]
func _initialize() -> void:call_deferred("run")
func need(ok: bool,label: String) -> void:
	if not ok:errors.append(label)
func canonical(value: Variant) -> String:return JSON.stringify(JSON.parse_string(JSON.stringify(value,"",true,true)),"",true,true)
func run() -> void:
	var contract: String="";var path: String="";var out: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="):contract=arg.trim_prefix("--contract=")
		elif arg.begins_with("--back-lift-trace="):path=arg.trim_prefix("--back-lift-trace=")
		elif arg.begins_with("--back-lift-replay-output="):out=arg.trim_prefix("--back-lift-replay-output=")
	assert(not out.is_empty() and not FileAccess.file_exists(out))
	var cfg: Dictionary=Factory.read_sealed(contract)
	var data: Dictionary=UfeContentDatabase.read_json(path)
	assert(str(data.candidate_contract_sha256)==str(cfg._contract_sha256) and not bool(data.found) and bool(data.physical_keys) and not bool(data.state_injection))
	assert(data.rows.size()==1,"失败独立回放只接受明确单次输入带")
	var row: Dictionary=data.rows[0]
	var sim:=Factory.make_match(cfg,int(row.owner),str(row.case))
	need(sim.content_fingerprint==str(row.content_fingerprint),"合同/规则指纹")
	var windows: Array=[]
	var view:=UfeSideView.new()
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json")
	var recorder:=UfeReplayRecorder.new();var captures:=0;var slams:=0;var whiffs:=0;var starts:=0
	for tick in range(row.original_inputs.size()):
		var pair: Array=row.original_inputs[tick]
		var before: String=sim.fighters[int(row.owner)].move_id
		var frames: Array=[UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])]
		sim.step(frames);recorder.append(frames,sim)
		var a:=sim.fighters[int(row.owner)];var b:=sim.fighters[1-int(row.owner)]
		if a.move_id=="special3" and a.move_tick>=int(cfg.move.throw_current_capture.first_tick) and a.move_tick<int(cfg.move.throw_current_capture.entry_tick):
			windows.append({"tick":sim.tick,"raw":a.move_tick,"actor_facing":a.facing,"victim_facing":b.facing,"victim_vx":b.vx,"victim_vy":b.vy,"jump_kind":b.motion.jump_kind,"state_tick":b.state_tick,"animation_key":b.animation_key(),"actual_animation":view._animation(b,manifest),"actor_root":[a.x,a.height],"victim_root":[b.x,b.height],"incoming_frame":b.frame().duplicate(true)})
		need(sim.state_hash()==str(row.state_hashes[tick]),"逐tick原输入hash/%d"%tick)
		need(canonical(sim.events)==canonical(row.events[tick]),"逐tick原输入事件/%d"%tick)
		if before!="special3" and sim.fighters[int(row.owner)].move_id=="special3":starts+=1
		for event in sim.events:
			if int(event.get("player",-1))!=int(row.owner):continue
			if event.kind=="hit" and str(event.get("move",""))=="special3":captures+=1
			if event.kind=="throw_slam":slams+=1
			if event.kind=="throw_whiff":whiffs+=1
	need(starts==1 and captures==0 and slams==0 and whiffs==1,"预期entry_blocked：真实起手一次、无捕获无撞地、落空一次")
	need(sim.fighters[1-int(row.owner)].stats.hp==1000,"失败入口0伤害")
	var tape_path:=out.get_base_dir().path_join("format6-entry-blocked.json")
	assert(not FileAccess.file_exists(tape_path));need(recorder.save_file(tape_path)==OK,"format6保存")
	var loaded:=UfeReplayRecorder.load_file(tape_path,sim.content_fingerprint)
	need(loaded!=null,"format6加载")
	if loaded!=null:
		var again:=Factory.make_match(cfg,int(row.owner),str(row.case))
		for tick in range(loaded.frames.size()):
			again.step([UfeInputFrame.unpack(loaded.frames[tick][0]),UfeInputFrame.unpack(loaded.frames[tick][1])])
			need(again.state_hash()==str(row.state_hashes[tick]),"format6独立逐tick/%d"%tick)
		need(again.state_hash()==loaded.final_hash,"format6终态")
	var file:=FileAccess.open(out,FileAccess.WRITE);assert(file!=null)
	file.store_string(JSON.stringify({"errors":errors,"expected":"entry_blocked","not_release_validation":true,"not_main_visual_validation":true,
		"source_sha256":FileAccess.get_sha256(path),"candidate_contract_sha256":cfg._contract_sha256,"ticks":row.original_inputs.size(),
		"windows":windows,"starts":starts,"captures":captures,"slams":slams,"whiffs":whiffs,"damage":1000-int(sim.fighters[1-int(row.owner)].stats.hp),
		"format6_path":tape_path,"loads_driver":false,"calls_sample":false,"state_injection":false}))
	file.close();view.free();quit(0 if errors.is_empty() else 1)
