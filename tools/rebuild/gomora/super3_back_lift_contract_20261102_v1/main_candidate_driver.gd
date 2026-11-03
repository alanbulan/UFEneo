extends "res://tests/review/fighters/ultraman-teo/codex_super1_arrow_review_driver.gd"
## 正式默认开局；全程只按物理键→InputRouter，不设置站位/HP/能量/高度/状态。
const Keys = preload("res://tools/rebuild/shared/stamina_quick_input_common.gd")
const BACK_CASES := ["hit_p","hit_pair","ground","stand_guard","crouch_guard","whiff","high_jump","dodge_escape","interrupt_startup","punish_recovery","tech1","tech2","tech3","tech4","unsupported"]
var owner: int=0
var kind: String="hit_p"
var jump_delay: int=13
var gap: int=68
var jump_tick: int=-1
var captured_at: int=-1
var approach_done: bool=false
var physical_keys: Array=[]
func _init() -> void:
	profile="gomora_back_lift_minimal_main_candidate_v1"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--back-lift-case="):kind=arg.trim_prefix("--back-lift-case=")
		if arg.begins_with("--back-lift-owner="):owner=int(arg.trim_prefix("--back-lift-owner="))
		if arg.begins_with("--back-lift-jump-delay="):jump_delay=int(arg.trim_prefix("--back-lift-jump-delay="))
		if arg.begins_with("--back-lift-gap="):gap=int(arg.trim_prefix("--back-lift-gap="))
	assert(kind in BACK_CASES and owner in [0,1] and jump_delay>=0 and jump_delay<=24 and gap>=40 and gap<=120)
func matchup() -> Array:
	var target: String="ultraseven" if kind=="unsupported" else "zetton"
	return ["gomora",target] if owner==0 else [target,"gomora"]
func setup_data() -> Dictionary:return {"fighters":matchup(),"positions":[470,750],"facings":[1,-1]}
func section(_frame: int) -> int:return 0
func capture_length() -> int:return 760
func length_frames() -> int:return capture_length()+2
func case_id(_frame: int) -> String:return kind
func boxes(_frame: int) -> bool:return false
func label(_frame: int) -> String:return "哥莫拉背掀·临时动态候选·"+kind+"·"+("1P" if owner==0 else "2P")+"真实Q/P/跳跃"
func prepare_match(sim: UfeMatchDirector) -> void:
	Keys.default_configuration()
	assert(sim.fighters[owner].definition.id=="gomora")
	for i in range(2):
		assert(sim.fighters[i].x==[470,750][i] and sim.fighters[i].facing==[1,-1][i])
		assert(sim.fighters[i].height==0 and sim.fighters[i].stats.energy==0 and sim.fighters[i].stats.hp==1000 and sim.fighters[i].stats.stamina==1000)
	assert(UfeMoveData.validate(sim.fighters[owner].definition.moves.special3))
	jump_tick=-1;captured_at=-1;approach_done=false;cast_age=-1;charge_complete_age=-1;sampled_frame=-1
	sent_counter=false;sent_evade=false;sent_cancel=false
	before={};decision={};passive=UfeInputFrame.make();physical_keys=[]
func snapshot(sim: UfeMatchDirector) -> Dictionary:
	var value: Dictionary=super.snapshot(sim)
	for i in range(2):
		value.pair[i].motion=sim.fighters[i].motion.duplicate(true)
		value.pair[i].vx=sim.fighters[i].vx;value.pair[i].vy=sim.fighters[i].vy
	return value
func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
	sampled_frame=frame;before=snapshot(sim);decision={"request":""}
	var a: UfeFighter=sim.fighters[owner]
	var b: UfeFighter=sim.fighters[1-owner]
	var own := UfeInputFrame.make()
	var other := UfeInputFrame.make()
	var wanted_gap: int=220 if kind=="whiff" else gap
	if cast_age<0:
		if a.stats.energy<3000:
			own=UfeInputFrame.make(0,0,UfeInputFrame.CHARGE);decision.request="真实Q蓄能"
		elif charge_complete_age<0:charge_complete_age=sim.tick
		if not approach_done:
			if absi(a.x-b.x)>wanted_gap:other=UfeInputFrame.make(signi(a.x-b.x))
			else:approach_done=true
		var ready: bool=approach_done and a.stats.energy==3000 and a.state=="idle" and b.state=="idle"
		var grounded: bool=kind in ["ground","stand_guard","crouch_guard","dodge_escape","interrupt_startup","punish_recovery"]
		if grounded and ready:
			cast_age=frame;own=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
			decision.request="满三格实际P·对地应空抓"
		elif not grounded:
			if jump_tick<0 and ready:
				jump_tick=sim.tick;other=UfeInputFrame.make(0 if kind=="high_jump" else signi(a.x-b.x),1)
				decision.request="陪练真实方向+上跳，未设空中夹具"
			elif jump_tick>=0 and sim.tick-jump_tick>=jump_delay and a.state in ["idle","turn"]:
				cast_age=frame;own=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT|UfeInputFrame.HEAVY if kind=="hit_pair" else UfeInputFrame.SPECIAL)
				decision.request="真实J+K" if kind=="hit_pair" else "真实P迎实际空中受方"
	if cast_age>=0:
		if kind=="stand_guard":other=UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
		elif kind=="crouch_guard":other=UfeInputFrame.make(0,-1,UfeInputFrame.GUARD)
		elif kind=="dodge_escape" and not sent_evade and a.move_id=="special3":
			sent_evade=true;other=UfeInputFrame.make(0,0,UfeInputFrame.DODGE);decision.counter="真实N"
		elif kind=="interrupt_startup" and not sent_counter and a.move_id=="special3" and a.move_tick>=4:
			sent_counter=true;other=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT);decision.counter="真实J打断起手"
		elif kind=="punish_recovery" and not sent_counter and a.move_id=="special3" and a.move_tick>=56:
			sent_counter=true;other=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT);decision.counter="真实J尝试惩罚空抓收势"
		if b.state=="thrown" and captured_at<0:captured_at=sim.tick
		if kind.begins_with("tech") and captured_at>=0 and sim.tick-captured_at==int(kind.trim_prefix("tech"))-1:
			other=UfeInputFrame.make(0,0,UfeInputFrame.THROW);decision.counter="捕后真实L拆投 "+kind
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
func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	super.observe_walk(frame,sim,view)
	if trace.is_empty():return
	var row: Dictionary=trace[-1]
	row.owner=owner;row.physical_keys=physical_keys.duplicate() if row.simulation_stepped else []
	row.active_attachments=view.attachments_for(owner).duplicate(true)
	row.attached_nodes=[]
	for node in view.attached_slots[owner]:row.attached_nodes.append(node_data(node))
	row.jump_tick=jump_tick;row.captured_at=captured_at;row.jump_delay=jump_delay;row.approach_gap=gap
	row.cinematic_background=node_data(view.cinematic.background);row.cinematic_portrait=node_data(view.cinematic.portrait)
	row.camera_zoom=view.camera_zoom;row.screen_bounds=[]
	for node in view.fighters:
		var bounds: Rect2=view._sprite_bounds(node)
		row.screen_bounds.append([bounds.position.x,bounds.position.y,bounds.size.x,bounds.size.y])
func release_keys() -> void:Keys.release_all()
func save_file(path: String) -> void:
	if trace_saved:return
	Keys.release_all();assert(not FileAccess.file_exists(path))
	var file := FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"trace":trace,"stills":stills,"owner":owner,"case":kind,
		"generated_videos":0,"automated_physical_keys":true,"hardware_human_tested":false,"temporary_candidate_only":true,
		"source":"正式main非训练默认470/750开局；真实Q3000/走位/跳跃/P或J+K，无x/height/HP/能量/状态夹具；冻结与上背捕获由正式模拟推进。"}))
	file.close();trace_saved=true
