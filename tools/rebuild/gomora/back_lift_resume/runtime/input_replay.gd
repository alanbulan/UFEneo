extends SceneTree
## 独立消费搜索所录原物理键InputFrame；不加载driver、不调用sample。成功、拆投与失败分别断言。
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
	assert(str(data.candidate_contract_sha256)==str(cfg._contract_sha256) and bool(data.physical_keys) and not bool(data.state_injection))
	assert(data.rows.size()==1,"独立回放只接受明确单次输入带")
	var row: Dictionary=data.rows[0]
	var test_kind: String=str(row.case)
	var broken: bool=test_kind in ["rear_vertical_tech1","rear_vertical_tech2","rear_vertical_tech3"]
	var success: bool=test_kind in ["rear_vertical_hit","rear_vertical_tech4"]
	var expected: String="tech" if broken else "hit" if success else "entry_blocked"
	var has_release: bool=cfg.move.frames.any(func(f):return str(f.get("target",{}).get("mode",""))=="release")
	var capture_snapshots: Array=[];var root_samples: Array=[]
	var tech_ticks: Array=[];var capture_ticks: Array=[];var release_transitions: int=0
	var was_released: bool=false
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
		if a.move_id=="special3" and b.state=="thrown" and str(a.frame().get("target",{}).get("mode",""))=="root":
			var target: Dictionary=a.frame().target
			var offset: Array=UfeThrowResolver.RootOffsets.offset(b,target)
			need((b.x-a.x)*a.facing==int(offset[0]) and b.height==int(offset[1])+(0 if bool(target.get("ground",false)) else a.height),"逐tick独立root遵循合同/%d"%tick)
			root_samples.append({"tick":sim.tick,"raw":a.move_tick,"relative_root":[(b.x-a.x)*a.facing,b.height-a.height],"pose":b.animation_key(),"sprite":int(b.frame().sprite)})
		var released: bool=bool(b.motion.get("throw_released",false))
		if released and not was_released:release_transitions+=1
		was_released=released
		need(sim.state_hash()==str(row.state_hashes[tick]),"逐tick原输入hash/%d"%tick)
		need(canonical(sim.events)==canonical(row.events[tick]),"逐tick原输入事件/%d"%tick)
		if before!="special3" and sim.fighters[int(row.owner)].move_id=="special3":starts+=1
		for event in sim.events:
			if int(event.get("player",-1))!=int(row.owner):continue
			if event.kind=="hit" and str(event.get("move",""))=="special3":
				captures+=1;capture_ticks.append(sim.tick)
				capture_snapshots.append({"tick":sim.tick,"raw":a.move_tick,"memory":b.motion.get("throw_current_capture",{}).duplicate(true),"actual_animation":view._animation(b,manifest)})
				need(b.stats.hp==1000,"捕获不提前扣伤")
			if event.kind=="throw_slam":
				slams+=1;need(a.move_tick==int(cfg._impact_tick) and b.height==0,"唯一合同impact落地")
			if event.kind=="throw_tech":tech_ticks.append(sim.tick)
			if event.kind=="throw_whiff":whiffs+=1
	need(starts==1,"真实三级起手一次")
	need(captures==(1 if broken or success else 0),"预期捕获数量")
	need(slams==(1 if success else 0),"预期唯一撞地数量")
	need(whiffs==(0 if broken or success else 1),"预期落空数量")
	need(tech_ticks.size()==(1 if broken else 0),"预期拆投数量")
	if broken and tech_ticks.size()==1 and capture_ticks.size()==1:
		need(int(tech_ticks[0])-int(capture_ticks[0])==int(test_kind.trim_prefix("rear_vertical_tech")),"真实tick拆投边界")
	need(release_transitions==(1 if success and has_release else 0),"释放标记符合合同是否声明release")
	need(sim.fighters[1-int(row.owner)].stats.hp==1000-(int(cfg.move.damage) if success else 0),"实际伤害守恒")
	var victim:=sim.fighters[1-int(row.owner)]
	need(victim.state!="thrown" and int(victim.combat.thrower)==-1,"正常结束或拆投已退出thrown关系")
	need(not victim.motion.has("throw_current_capture"),"结束清除空接快照")
	var final_victim: Dictionary={"state":victim.state,"height":victim.height,"thrower":victim.combat.thrower,"motion":victim.motion.duplicate(true)}
	var tape_path:=out.get_base_dir().path_join("format6-original-inputs.json")
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
	file.store_string(JSON.stringify({"errors":errors,"expected":expected,"not_release_validation":not (success and has_release),"contract_has_mode_release":has_release,"not_main_visual_validation":true,
		"source_sha256":FileAccess.get_sha256(path),"candidate_contract_sha256":cfg._contract_sha256,"ticks":row.original_inputs.size(),
		"capture_snapshots":capture_snapshots,"root_samples":root_samples,"final_victim":final_victim,"case":test_kind,"owner":row.owner,"capture_ticks":capture_ticks,"tech_ticks":tech_ticks,"release_transitions":release_transitions,"windows":windows,"starts":starts,"captures":captures,"slams":slams,"whiffs":whiffs,"damage":1000-int(sim.fighters[1-int(row.owner)].stats.hp),
		"format6_path":tape_path,"loads_driver":false,"calls_sample":false,"state_injection":false}))
	file.close();view.free();quit(0 if errors.is_empty() else 1)
