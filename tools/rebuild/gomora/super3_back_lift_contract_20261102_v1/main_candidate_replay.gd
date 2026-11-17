extends SceneTree
## 不加载review driver；正式默认开局只消费原双方InputFrame，不设状态或站位。
var errors: Array=[]
func _initialize() -> void:call_deferred("run")
func canonical(value: Variant) -> String:
	return JSON.stringify(JSON.parse_string(JSON.stringify(value,"",true,true)),"",true,true)
func need(ok: bool,message: String) -> void:
	if not ok:errors.append(message)
func pair_equal(sim: UfeMatchDirector,row: Dictionary) -> bool:
	for i in range(2):
		var f: UfeFighter=sim.fighters[i]
		var p: Dictionary=row.pair[i]
		for key in ["x","height","facing","state","state_tick","move_tick","vx","vy"]:
			if canonical(f.get(key))!=canonical(p[key]):return false
		if f.move_id!=p.move or canonical(f.motion)!=canonical(p.motion) or canonical(f.combat)!=canonical(p.combat):return false
		if canonical(f.frame())!=canonical(p.frame):return false
		for key in ["hp","energy","stamina"]:
			if int(f.stats[key])!=int(p[key]):return false
	return true
func run() -> void:
	var path: String=""
	var output_path: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--back-lift-trace="):path=arg.trim_prefix("--back-lift-trace=")
		if arg.begins_with("--back-lift-replay-output="):output_path=arg.trim_prefix("--back-lift-replay-output=")
	if path.is_empty() or output_path.is_empty() or not FileAccess.file_exists(path) or FileAccess.file_exists(output_path):
		push_error("背掀原trace必需，输出拒绝覆盖");quit(2);return
	var data: Variant=JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Dictionary or not data.get("trace",null) is Array or data.trace.is_empty():
		push_error("背掀trace结构无效");quit(2);return
	need(data.get("temporary_candidate_only",false) and data.get("automated_physical_keys",false),"必须是明确标记的临时候选真实键trace")
	var owner: int=int(data.get("owner",-1))
	need(owner in [0,1],"投者编号非法")
	if owner not in [0,1]:quit(2);return
	var kind: String=str(data.get("case",""))
	var expected_ids: Array=["gomora","ultraseven" if kind=="unsupported" else "zetton"] if owner==0 else ["ultraseven" if kind=="unsupported" else "zetton","gomora"]
	var setup: Dictionary={"fighters":expected_ids,"positions":[470,750],"facings":[1,-1]}
	var sim: UfeMatchDirector=UfeBattleFormCatalog.match_for(str(expected_ids[0]),str(expected_ids[1]),false)
	var recorder:=UfeReplayRecorder.new()
	var observations: int=0
	var captures: Array=[]
	var slams: Array=[]
	var techs: Array=[]
	var whiffs: Array=[]
	var costs: Array=[]
	var preserved_ticks: Array=[]
	var first_capture: Dictionary={}
	var expected_steps: Array=[]
	for row in data.trace:
		var frame: int=int(row.movie_frame)
		if frame!=observations or int(row.section)!=0 or canonical(row.case_setup)!=canonical(setup):
			errors.append(str(frame)+"必须唯一默认开局且观察连续");break
		if str(row.content_fingerprint)!=sim.content_fingerprint or int(row.pre.tick)!=sim.tick or str(row.pre.state_hash)!=sim.state_hash():
			errors.append(str(frame)+"内容指纹/推进前时钟或hash不同");break
		var stepped: bool=bool(row.simulation_stepped)
		if stepped:
			var inputs: Array=[UfeInputFrame.unpack(row.inputs[0]),UfeInputFrame.unpack(row.inputs[1])]
			sim.step(inputs);recorder.append(inputs,sim)
			expected_steps.append({"tick":sim.tick,"hash":sim.state_hash(),"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)})
		elif canonical(row.inputs)!=canonical([[0,0,0],[0,0,0]]):
			errors.append(str(frame)+"未推进观察带旧输入");break
		if sim.tick!=int(row.tick) or sim.state_hash()!=str(row.state_hash) or not pair_equal(sim,row):
			errors.append(str(frame)+"原双方输入重放状态/hash/完整人物帧不同");break
		if canonical(sim.events)!=canonical(row.events) or canonical(sim.projectiles)!=canonical(row.projectiles):
			errors.append(str(frame)+"完整事件/弹体不同");break
		var a: UfeFighter=sim.fighters[owner]
		var b: UfeFighter=sim.fighters[1-owner]
		if stepped and a.move_id=="special3" and row.pre.pair[owner].move!="special3":
			var cost: Dictionary={"tick":sim.tick,"energy":int(row.pre.pair[owner].energy)-int(a.stats.energy),"stamina":int(row.pre.pair[owner].stamina)-int(a.stats.stamina)}
			costs.append(cost)
			need(cost.energy==3000 and cost.stamina==50,str(frame)+"实际起手必须扣3000能量/50体力")
		if stepped:
			for event in sim.events:
				if int(event.get("player",-1))!=owner:continue
				if str(event.kind)=="hit" and str(event.get("move",""))=="special3":
					captures.append({"tick":sim.tick,"raw":a.move_tick,"memory":b.motion.get("throw_current_capture",{}).duplicate(true)})
					need(a.move_tick>=16 and a.move_tick<=19,"捕获必须在raw16..19")
					need(b.state=="thrown" and int(b.stats.hp)==int(row.pre.pair[1-owner].hp),"捕获不得先扣490")
					first_capture=b.motion.get("throw_current_capture",{}).duplicate(true)
				if str(event.kind)=="throw_slam" and str(event.get("move",""))=="special3":
					var damage: int=int(row.pre.pair[1-owner].hp)-int(b.stats.hp)
					slams.append({"tick":sim.tick,"raw":a.move_tick,"damage":damage})
					need(a.move_tick==52 and damage==490,"唯一raw52实际撞地须扣490")
				if str(event.kind)=="throw_tech":techs.append({"tick":sim.tick,"captured_real_tick":int(row.get("captured_at",-1))})
				if str(event.kind)=="throw_whiff" and str(event.get("move",""))=="special3":whiffs.append({"tick":sim.tick,"raw":a.move_tick})
		if b.state=="thrown" and bool(b.motion.get("throw_current_capture",{}).get("active",false)):
			var memory: Dictionary=b.motion.throw_current_capture
			need(not first_capture.is_empty() and canonical(memory)==canonical(first_capture),"捕获起相快照不得在持续中换相")
			need(b.x==int(memory.x) and b.height==int(memory.height) and b.facing==int(memory.facing) and canonical(b.frame())==canonical(memory.frame),"raw16..19须保真实当前完整相/根/朝向")
			preserved_ticks.append({"tick":sim.tick,"raw":a.move_tick})
		observations+=1
	need(observations==data.trace.size(),"完整观察未消费")
	need(costs.size()==1,"必须真实启动一次三级，不能无招当用例完成")
	if kind in ["hit_p","hit_pair","tech4"]:
		need(captures.size()==1 and slams.size()==1 and techs.is_empty() and not preserved_ticks.is_empty(),"指定命中用例尚未真实捕获并完成唯一撞地")
	if kind in ["tech1","tech2","tech3"]:
		need(captures.size()==1 and techs.size()==1 and slams.is_empty(),"前三个真实tick拆投未实际成立")
		if not captures.is_empty() and not techs.is_empty():need(int(techs[0].tick)-int(captures[0].tick)==int(kind.trim_prefix("tech")),"拆投的实际tick边界不同")
	if kind in ["ground","stand_guard","crouch_guard","whiff","high_jump","unsupported"]:
		need(captures.is_empty() and slams.is_empty() and not whiffs.is_empty(),"负向未实际落空或意外捕获")
	# 将同一批原InputFrame存成正式格式6，再由加载器独立重建第二次；不使用driver/sample。
	var replay_path: String=output_path.get_base_dir().path_join("format6-original-inputs.json")
	var format6_ok: bool=false
	if errors.is_empty():
		need(not FileAccess.file_exists(replay_path),"格式6证据已存在，拒绝覆盖")
		if not FileAccess.file_exists(replay_path):
			need(recorder.save_file(replay_path)==OK,"格式6原输入保存失败")
			var loaded: UfeReplayRecorder=UfeReplayRecorder.load_file(replay_path,sim.content_fingerprint)
			need(loaded!=null,"正式格式6加载器拒绝本次原输入")
			if loaded!=null:
				var again: UfeMatchDirector=UfeBattleFormCatalog.match_for(str(loaded.fighter_ids[0]),str(loaded.fighter_ids[1]),false)
				need(loaded.frames.size()==expected_steps.size(),"格式6输入数不同")
				for index in range(loaded.frames.size()):
					var packed: Array=loaded.frames[index]
					again.step([UfeInputFrame.unpack(packed[0]),UfeInputFrame.unpack(packed[1])])
					var expected: Dictionary=expected_steps[index]
					if again.tick!=int(expected.tick) or again.state_hash()!=str(expected.hash) or canonical(again.events)!=canonical(expected.events) or canonical(again.projectiles)!=canonical(expected.projectiles):
						errors.append("格式6独立原输入逐tick状态/事件/弹体不同 "+str(index));break
				need(again.state_hash()==loaded.final_hash,"格式6终态hash不同")
				format6_ok=errors.is_empty()
	var output:=FileAccess.open(output_path,FileAccess.WRITE)
	if output==null:push_error("背掀回放输出无法保存");quit(2);return
	output.store_string(JSON.stringify({"errors":errors,"observations":observations,"simulation_steps":expected_steps.size(),"trace_sha256":FileAccess.get_sha256(path),
		"case":kind,"owner":owner,"costs":costs,"captures":captures,"slams":slams,"techs":techs,"whiffs":whiffs,"preserved_ticks":preserved_ticks,
		"format6_independent_replay":format6_ok,"format6_path":replay_path if format6_ok else "","loads_driver":false,"calls_sample":false,"allow_pilot":false,
		"sets_start_positions":false,"sets_states":false,"adds_ticks":false,"generated_videos":0,"visual_acceptance":false,
		"scope":"正式main原InputFrame及默认470/750开局独立重放；逐观察pre/后hash、时钟、完整人物帧/motion、事件/弹体；实测命中/拆投/费用仅在真实发生时通过。"}))
	output.close()
	for error in errors:push_error(str(error))
	quit(0 if errors.is_empty() else 1)
