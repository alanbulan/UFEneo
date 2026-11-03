class_name UfePhase3ZettonReview
extends UfeReviewDriver
## 玩家二真实输入；只在各组开局设置训练站位。
const ACTIONS := ["idle","walk_forward","walk_back","dash_sequence","light_chain","heavy","launcher","spin_heavy","crush","tackle","pulse","ranged_forward","crouch_cycle","crouch_chain","sweep","slide","low_pulse"]
const START := [0,180,600,1020,1290,1560,1800,2040,2280,2520,2760,3000,3240,3480,3780,4020,4260]
const TITLES := ["杰顿 · 沉重待机","玩家二前走 · 连续6秒","后走候选待人工 · 本段为现有静态占位","双击前 · 一次性冲刺三次","双臂手刀三连 · 小键盘1","重手刀 · 小键盘2","上挑手刀 · 前+小键盘2","转背回旋手刀 · 后+小键盘2","双臂猛砸 · 小键盘0","甲壳冲撞 · 前+小键盘0","脸部小火球 · 小键盘7","杰顿光线 · 前+小键盘7","下蹲 → 保持 → 起身","下段手刀两段 · 下+小键盘1","低位扫腿 · 下+小键盘2","低姿滑撞 · 下+小键盘0","贴地火球 · 下+小键盘7"]
var p2 := UfeInputFrame.make()
var chain: int = 0
func _init() -> void: profile="phase3_zetton"
func section(frame: int) -> int:
	var result:=0
	for i in range(START.size()):
		if frame>=int(START[i]):result=i
	return result
func length_frames() -> int:return 4500
func boxes(_frame: int) -> bool:return true
func label(frame: int) -> String:return TITLES[section(frame)]+" · F1判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	chain=0
	var id: String=ACTIONS[section(review_frame)]
	# 玩家二在左、面向右，完整显示正向杰顿。玩家一初代在右受击。
	sim.fighters[1].x=470
	sim.fighters[0].x=540
	sim.fighters[1].facing=1
	sim.fighters[0].facing=-1
	if id in ["pulse","ranged_forward","low_pulse"]:sim.fighters[0].x=750
	if id=="walk_forward":sim.fighters[1].x=130;sim.fighters[0].x=410
	if id=="walk_back":sim.fighters[1].x=870;sim.fighters[0].x=1150
	if id=="dash_sequence":sim.fighters[1].x=200;sim.fighters[0].x=650
	if id=="heavy":sim.fighters[0].x=535
func second_sample(_frame: int) -> UfeInputFrame:return p2
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var id: String=ACTIONS[section(frame)]
	var age:=frame-int(START[section(frame)])
	var f:=sim.fighters[1]
	p2=UfeInputFrame.make()
	if id=="idle":return UfeInputFrame.make()
	if id in ["walk_forward","walk_back"]:
		var direction: int=(1 if id=="walk_forward" else -1) if age>=30 and age<390 else 0
		p2=UfeInputFrame.make(direction)
		return UfeInputFrame.make(direction)
	if id=="dash_sequence":
		for start in [30,108,186]:
			if age-start in [0,1,4,5]:p2=UfeInputFrame.make(1)
		return UfeInputFrame.make(1 if age>=30 else 0)
	if id=="crouch_cycle":
		p2=UfeInputFrame.make(0,-1 if age>=30 and age<170 else 0)
		return UfeInputFrame.make()
	if id in ["light_chain","crouch_chain"]:
		var low:=id=="crouch_chain"
		var trigger:=age==30
		if f.combat.confirmed and ((f.move_id=="light1" and chain==0) or (f.move_id=="light2" and chain==1) or (f.move_id=="crouch_light" and chain==0)):
			chain+=1
			trigger=true
		p2=UfeInputFrame.make(0,-1 if low and age<210 else 0,UfeInputFrame.LIGHT if trigger else 0)
		return UfeInputFrame.make()
	if age==30:
		var button:=UfeInputFrame.RANGED if id in ["pulse","ranged_forward","low_pulse"] else UfeInputFrame.CRUSH if id in ["crush","tackle","slide"] else UfeInputFrame.HEAVY
		var direction: int=-1 if id=="spin_heavy" else 1 if id in ["launcher","tackle","ranged_forward"] else 0
		p2=UfeInputFrame.make(direction,-1 if id in ["sweep","slide","low_pulse"] else 0,button)
	elif id in ["sweep","slide","low_pulse"] and age<150:p2=UfeInputFrame.make(0,-1)
	return UfeInputFrame.make()
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var f:=sim.fighters[1]
	var a:=view._animation(f,view.manifests[1])
	trace.append({"movie_frame":frame,"section":section(frame),"action":ACTIONS[section(frame)],"inputs":last_inputs.duplicate(true),"boxes":view.show_boxes,"state":f.state,"state_tick":f.state_tick,"clip":f.animation_key(),"move":f.move_id,"move_tick":f.move_tick,"x":f.x,"height":f.height,"facing":f.facing,"sprite_index":a.get("index",-1),"texture":a.get("texture",""),"p1_state":sim.fighters[0].state,"p1_hp":sim.fighters[0].stats.hp,"p1_x":sim.fighters[0].x,"projectiles":sim.projectiles.duplicate(true),"events":sim.events.duplicate(true)})
func save_file(path: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"source":"主游戏训练模式玩家二杰顿真实InputFrame；玩家一初代受击；只在每组开局设置站位，组内不摆姿势/坐标，全程F1。","trace":trace},"\t"))
