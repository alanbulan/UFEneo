class_name UfePhase3ZettonAirReview
extends UfeReviewDriver
@warning_ignore_start("integer_division")
## 主游戏训练输入：P2逐招，末组P1完整空连验证镜头。
const ACTIONS := ["vertical_jump","flip_forward","flip_back","takeoff","land","vertical_light","vertical_heavy","diagonal_light","diagonal_heavy","air_crush","dive","air_pulse","chase_takeoff","chase_light1","chase_light2","chase_end","dash_light","dash_heavy","backstep","back_counter","dodge","dodge_counter","full_combo","camera_ultraman"]
const NAMES := ["杰顿垂直跳","杰顿前跳空翻","杰顿后跳空翻","杰顿起跳","杰顿落地","垂直跳手刀","空中下劈","斜跳膝撞","斜跳重踢","双臂下砸","俯冲踢","斜下脸部火球","杰顿追击跳","追击手刀一段","追击手刀二段","双臂砸地终结","冲刺手刀","冲刺重臂扫","后撤步","后撤反手刀","侧闪","侧闪手刀","杰顿完整空连→落地扫腿","初代完整空连打杰顿·镜头边界"]
var chain_stage: int = 0
var emitted: Dictionary = {}
var passive := UfeInputFrame.make()
var active_player: int = 1
func _init() -> void: profile="phase3_zetton_air"
func section(frame: int) -> int: return mini(frame/240,ACTIONS.size()-1)
func action_id(frame: int) -> String: return ACTIONS[section(frame)]
func length_frames() -> int: return ACTIONS.size()*240
func boxes(_frame: int) -> bool: return true
func label(frame: int) -> String: return NAMES[section(frame)]+" · F1判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	chain_stage=0;emitted.clear()
	var id: String=action_id(review_frame)
	active_player=0 if id=="camera_ultraman" else 1
	var distance:=130 if id in ["dash_light","dash_heavy"] else 150 if id=="air_pulse" else 85 if id in ["diagonal_light","diagonal_heavy"] else 65
	sim.fighters[0].x=500
	sim.fighters[1].x=500+distance
func second_sample(_frame: int) -> UfeInputFrame: return passive
func once(key: String,input: UfeInputFrame) -> UfeInputFrame:
	if emitted.has(key):return UfeInputFrame.make()
	emitted[key]=true;return input
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var id: String=action_id(frame)
	var age:=frame-section(frame)*240
	passive=UfeInputFrame.make()
	if age==25 and id in ["vertical_light","vertical_heavy","diagonal_light","diagonal_heavy","air_crush","dive"]:passive=UfeInputFrame.make(0,1)
	var action_input:=target_sample(id,age,sim)
	if active_player==0:return action_input
	var first:=passive;passive=action_input;return first
func target_sample(id: String,age: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var f:=sim.fighters[active_player]
	var direction:=f.facing
	if id in ["chase_takeoff","chase_light1","chase_light2","chase_end","full_combo","camera_ultraman"]:
		if age==30:
			chain_stage=1;return UfeInputFrame.make(direction,0,UfeInputFrame.HEAVY)
		if chain_stage==1 and int(f.motion.chase_window)>0 and (active_player==0 or int(f.motion.chase_window)<=19) and f.combat.confirmed:
			chain_stage=2;return UfeInputFrame.make(direction,1)
		if chain_stage==2 and id!="chase_takeoff" and f.state=="air" and f.height>35:
			chain_stage=3;return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		if chain_stage==3 and id!="chase_light1" and f.move_id=="chase_light1" and f.combat.confirmed:
			chain_stage=4;return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		if chain_stage==4 and id!="chase_light2" and f.move_id=="chase_light2" and f.combat.confirmed:
			chain_stage=5;return UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		if chain_stage==5 and id in ["full_combo","camera_ultraman"] and f.state=="land" and int(f.motion.land_window)>0:
			chain_stage=6;return UfeInputFrame.make(0,-1,UfeInputFrame.HEAVY)
		return UfeInputFrame.make()
	if id in ["vertical_jump","flip_forward","flip_back","takeoff","land"]:
		return UfeInputFrame.make(direction*(1 if id=="flip_forward" else -1 if id=="flip_back" else 0) if age==30 else 0,1 if age==30 else 0)
	if id in ["vertical_light","vertical_heavy","diagonal_light","diagonal_heavy","air_crush","dive","air_pulse"]:
		if age==25:return UfeInputFrame.make(direction if id.begins_with("diagonal") else 0,1)
		if age==29:
			var button:=UfeInputFrame.LIGHT if id in ["vertical_light","diagonal_light"] else UfeInputFrame.CRUSH if id=="air_crush" else UfeInputFrame.RANGED if id=="air_pulse" else UfeInputFrame.HEAVY
			return UfeInputFrame.make(0,-1 if id=="dive" else 0,button)
		return UfeInputFrame.make()
	if id in ["dash_light","dash_heavy","backstep","back_counter"]:
		if age in [20,21,24,25]:return UfeInputFrame.make(direction*(-1 if id in ["backstep","back_counter"] else 1))
		if age==30 and id!="backstep":return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if id=="dash_light" else UfeInputFrame.HEAVY)
		if id=="dash_light" and f.move_id=="dash_light" and f.combat.confirmed:return once("dash_chain",UfeInputFrame.make(0,0,UfeInputFrame.LIGHT))
		return UfeInputFrame.make()
	if id in ["dodge","dodge_counter"]:return UfeInputFrame.make(0,0,UfeInputFrame.DODGE if age==24 else UfeInputFrame.LIGHT if age==30 and id=="dodge_counter" else 0)
	return UfeInputFrame.make()
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var f:=sim.fighters[active_player];var b:=sim.fighters[1-active_player]
	var a:=view._animation(f,view.manifests[active_player]);var visible:=[]
	for i in range(2):
		var rect:=view._sprite_bounds(view.fighters[i])
		visible.append({"player":i,"top":rect.position.y,"bottom":rect.end.y,"height":sim.fighters[i].height,"scale":[view.fighters[i].scale.x,view.fighters[i].scale.y]})
	trace.append({"movie_frame":frame,"section":section(frame),"action":action_id(frame),"player":active_player,"inputs":last_inputs.duplicate(true),"boxes":view.show_boxes,"tick":sim.tick,"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"clip":a.get("key",""),"height":f.height,"vy":f.vy,"vx":f.vx,"x":f.x,"facing":f.facing,"sprite_index":a.get("index",-1),"texture":a.get("texture",""),"target_x":b.x,"target_height":b.height,"target_state":b.state,"target_hp":b.stats.hp,"bounced":b.combat.bounced,"land_window":f.motion.land_window,"chain_stage":chain_stage,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"camera_y":view.camera_y,"visible":visible})
func save_file(path: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练真实InputFrame；仅分组设站位，组内不改状态/坐标/高度；全程F1。末组初代P1攻杰顿P2，其余杰顿P2攻初代P1。","trace":trace},"\t"))
@warning_ignore_restore("integer_division")
