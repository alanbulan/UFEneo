extends "res://tools/rebuild/gomora/super3_back_lift_contract_20261102_v1/main_candidate_driver.gd"
## 复用旧真实物理键驱动；仅切换初代对象及密封候选记录，不设模拟字段。
var candidate_contract: Dictionary={}
var failures: Array=[]
var rear_stage: String="approach"
var rear_preparation: Array=[]
func _init() -> void:
	super._init() # 保留旧driver的owner/gap/delay参数解析。
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--candidate-case="):
			kind=arg.trim_prefix("--candidate-case=")
			assert(kind in ["rear_vertical_hit","rear_vertical_tech1","rear_vertical_tech2","rear_vertical_tech3","rear_vertical_tech4"])
func prepare_match(sim: UfeMatchDirector) -> void:
	super.prepare_match(sim)
	rear_stage="approach";rear_preparation=[]
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	if not kind.begins_with("rear_vertical_"):return super.sample(frame,sim)
	sampled_frame=frame;before=snapshot(sim);decision={"request":"保持Q，真实越身后背侧垂直跳"}
	var a:=sim.fighters[owner];var b:=sim.fighters[1-owner]
	var own:=UfeInputFrame.make(0,0,UfeInputFrame.CHARGE if cast_age<0 else 0)
	var other:=UfeInputFrame.make()
	var prior: String=rear_stage
	if rear_stage=="approach":
		if absi(a.x-b.x)>gap:other=UfeInputFrame.make(signi(a.x-b.x))
		elif b.state=="idle" and a.state=="charge" and int(a.stats.energy)==3000:
			other=UfeInputFrame.make(signi(a.x-b.x),1)
			rear_stage="cross_jump";decision.request="保持Q朝向；受方第一次真实前跳越身"
	elif rear_stage=="cross_jump":
		if b.height==0 and b.state=="idle":
			if (b.x-a.x)*a.facing<0:rear_stage="rear_walk"
			else:rear_stage="cross_failed"
	elif rear_stage=="rear_walk":
		var relative: int=(b.x-a.x)*a.facing
		if relative < -44:other=UfeInputFrame.make(a.facing)
		elif relative > -36:other=UfeInputFrame.make(-a.facing)
		elif b.state=="idle" and a.state=="charge":
			other=UfeInputFrame.make(0,1)
			jump_tick=sim.tick;rear_stage="vertical_jump";decision.request="背后36至44px真实垂直跳"
	elif rear_stage=="vertical_jump":
		if sim.tick-jump_tick>=jump_delay and a.state in ["charge","charge_stop"]:
			own=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
			cast_age=frame;rear_stage="cast";decision.request="保持原朝向由Q直接P，不经过idle"
	if cast_age>=0:
		if b.state=="thrown" and captured_at<0:captured_at=sim.tick
		if kind.begins_with("rear_vertical_tech") and captured_at>=0 and sim.tick-captured_at==int(kind.trim_prefix("rear_vertical_tech"))-1:
			other=UfeInputFrame.make(0,0,UfeInputFrame.THROW);decision.counter="捕后真实L拆投 "+kind
	if prior!=rear_stage:
		rear_preparation.append({"tick":sim.tick,"stage":rear_stage,"actor_state":a.state,"actor_facing":a.facing,"victim_facing":b.facing,"actor_root":[a.x,a.height],"victim_root":[b.x,b.height],"energy":a.stats.energy})
	decision.rear_stage=rear_stage
	var pairs: Array=[UfeInputFrame.make(),UfeInputFrame.make()]
	pairs[owner]=own;pairs[1-owner]=other
	physical_keys=[]
	for i in range(2):
		var codes: Array=Keys.keys_for(i,5,1,pairs[i].buttons)
		if pairs[i].x!=0:codes.append(UfeInputRouter.KEYS[i][0 if pairs[i].x<0 else 1])
		if pairs[i].y!=0:codes.append(UfeInputRouter.KEYS[i][2 if pairs[i].y>0 else 3])
		physical_keys.append_array(codes)
	Keys.set_keys(physical_keys);passive=UfeInputRouter.poll(1)
	return UfeInputRouter.poll(0)
func matchup() -> Array:
	var target: String="ultraseven" if kind=="unsupported" else str(candidate_contract.opponent)
	return ["gomora",target] if owner==0 else [target,"gomora"]
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	super.observe_walk(frame,sim,view)
	if trace.is_empty():return
	var row: Dictionary=trace[-1]
	row.full_alpha_viewport_bounds=[]
	for i in range(2):
		var bounds: Rect2=view.get_global_transform()*view._sprite_bounds(view.fighters[i])
		row.full_alpha_viewport_bounds.append([bounds.position.x,bounds.position.y,bounds.size.x,bounds.size.y])
		if bounds.position.x<0 or bounds.position.y<0 or bounds.end.x>640 or bounds.end.y>360:
			failures.append({"frame":frame,"kind":"full_body_outside_viewport","player":i})
func save_file(path: String) -> void:
	# game在最后截图flush后明确调用，不在倒数第二帧提前写。
	if trace_saved or trace.size()<capture_length():return
	Keys.release_all();assert(not FileAccess.file_exists(path))
	var file:=FileAccess.open(path,FileAccess.WRITE);assert(file!=null)
	file.store_string(JSON.stringify({"profile":"gomora_back_lift_210_memory_candidate","trace":trace,"stills":stills,"failures":failures,
		"owner":owner,"case":kind,"rear_preparation":rear_preparation,"candidate_contract_sha256":candidate_contract._contract_sha256,
		"automated_physical_keys":true,"hardware_human_tested":false,"temporary_candidate_only":true,"installed":false,
		"source":"正式main默认470/750零能量开局；Q/走位/跳跃/P或J+K经InputRouter；无坐标、HP、能量和状态夹具。"}))
	file.close();trace_saved=true
