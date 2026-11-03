class_name UfeUltrasevenReview
extends UfeReviewDriver
## 首批赛文主游戏真实输入；未安装动作明确跳过，不借用模板动画。
const ACTIONS := ["idle","walk_forward","walk_back","dash_sequence","turn","light_chain","heavy","launcher","spin_heavy","crush","tackle","pulse","ranged_forward","crouch_cycle","crouch_chain","sweep","slide","low_pulse"]
const START := [0,150,570,990,1230,1410,1680,1890,2100,2310,2520,2730,2940,3150,3390,3660,3870,4080]
var chain: int=0
var available: Dictionary={}
var selected_action: String=""
func _init() -> void:
	profile="stage4_ultraseven"
	available=UfeContentDatabase.read_json("res://assets/fighters/ultraseven/animations/manifest.json").clips
func section(frame: int) -> int:
	if selected_action in ACTIONS:return ACTIONS.find(selected_action)
	var result:=0
	for i in range(START.size()):
		if frame>=START[i]:result=i
	return result
func ready_action(id: String) -> bool:
	return available.has({"dash_sequence":"dash","crouch_cycle":"crouch","light_chain":"light3","crouch_chain":"crouch_light2"}.get(id,id))
func length_frames() -> int:return 4290
func boxes(_frame: int) -> bool:return true
func label(frame: int) -> String:
	var id: String=ACTIONS[section(frame)]
	return "赛文首批 · "+id+(" · F1判定框" if ready_action(id) else " · 待人工，未安装，跳过演示")
func prepare_match(sim: UfeMatchDirector) -> void:
	chain=0
	var id: String=ACTIONS[section(review_frame)]
	sim.fighters[0].x=470
	sim.fighters[1].x=530
	if id in ["pulse","ranged_forward","low_pulse"]:sim.fighters[1].x=750
	if id=="walk_forward":sim.fighters[0].x=160;sim.fighters[1].x=440
	if id=="walk_back":sim.fighters[0].x=900;sim.fighters[1].x=1180
	if id=="dash_sequence":sim.fighters[0].x=200;sim.fighters[1].x=650
	if id=="turn":sim.fighters[0].facing=-1
func second_sample(frame: int) -> UfeInputFrame:
	var id: String=ACTIONS[section(frame)];var age: int=frame if not selected_action.is_empty() else frame-int(START[section(frame)])
	if ready_action(id) and id in ["walk_forward","walk_back"] and age>=30 and age<390:return UfeInputFrame.make(1 if id=="walk_forward" else -1)
	if ready_action(id) and id=="dash_sequence" and age>=30:return UfeInputFrame.make(1)
	return UfeInputFrame.make()
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var id: String=ACTIONS[section(frame)];var age: int=frame if not selected_action.is_empty() else frame-int(START[section(frame)]);var f:=sim.fighters[0]
	if not ready_action(id):return UfeInputFrame.make()
	if id=="turn" or id=="idle":return UfeInputFrame.make()
	if id in ["walk_forward","walk_back"]:return UfeInputFrame.make((1 if id=="walk_forward" else -1) if age>=30 and age<390 else 0)
	if id=="dash_sequence":
		for start in [30,108,186]:
			if age-start in [0,1,4,5]:return UfeInputFrame.make(1)
		return UfeInputFrame.make()
	if id=="crouch_cycle":return UfeInputFrame.make(0,-1 if age>=30 and age<160 else 0)
	if id in ["light_chain","crouch_chain"]:
		var low:=id=="crouch_chain";var trigger: bool=age==30
		if f.combat.confirmed and ((f.move_id=="light1" and chain==0) or (f.move_id=="light2" and chain==1) or (f.move_id=="crouch_light" and chain==0)):
			chain+=1;trigger=true
		return UfeInputFrame.make(0,-1 if low and age<210 else 0,UfeInputFrame.LIGHT if trigger else 0)
	if age==30:
		var button:=UfeInputFrame.RANGED if id in ["pulse","ranged_forward","low_pulse"] else UfeInputFrame.CRUSH if id in ["crush","tackle","slide"] else UfeInputFrame.HEAVY
		return UfeInputFrame.make(-1 if id=="spin_heavy" else 1 if id in ["launcher","tackle","ranged_forward"] else 0,-1 if id in ["sweep","slide","low_pulse"] else 0,button)
	return UfeInputFrame.make(0,-1 if id in ["sweep","slide","low_pulse"] and age<150 else 0)
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var f:=sim.fighters[0];var animation:=view._animation(f,view.manifests[0])
	trace.append({"movie_frame":frame,"section":section(frame),"action":ACTIONS[section(frame)],"inputs":last_inputs.duplicate(true),"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"x":f.x,"height":f.height,"sprite_index":animation.get("index",-1),"clip":animation.get("key",""),"rect":animation.get("rect",[]),"texture":animation.get("texture",""),"target_hp":sim.fighters[1].stats.hp,"target_state":sim.fighters[1].state,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)})
func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"source":"主游戏训练InputFrame；每组只设置开局位置，组内不摆坐标、不设置伤害或受击；未安装项明确跳过。","trace":trace},"\t"))
