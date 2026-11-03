class_name UfePhase3AirReview
extends UfeReviewDriver
## 主游戏训练模式逐招输入。只在分组开始设站位，组内不改坐标/状态。
const ACTIONS := ["spin_heavy","ranged_forward","vertical_jump","flip_back","vertical_light","vertical_heavy","diagonal_light","air_crush","dive","air_pulse","chase_light2","chase_end","dash_light","dash_heavy","backstep","back_counter","dodge","dodge_counter","full_combo"]
const NAMES := ["回旋后踢 A+K","举掌八分光轮 D+I","垂直跳 W","后跳空翻 A+W","垂直跳轻击 W→J","垂直跳下击 W→K","斜跳膝撞 D+W→J","空中双拳下砸 W→O","俯冲踢 W→S+K","空中光弹 W→I","空轻二段 升击→追击→J→J","空中终结 升击→追击→J→J→K","冲刺拳 D,D→J","冲刺飞踢 D,D→K","后撤步 A,A","后撤反击 A,A→K","闪避 Q","闪避反击 Q→J","完整连段：升击→追击跳→空轻两段→砸地弹地→落地扫腿"]
var chain_stage: int = 0
var emitted: Dictionary = {}

func _init() -> void: profile = "phase3_air"
func section(frame: int) -> int: return mini(frame/180,ACTIONS.size()-1)
func length_frames() -> int: return (ACTIONS.size()+1)*180
func boxes(_frame: int) -> bool: return true
func label(frame: int) -> String: return NAMES[section(frame)]+" · F1判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	chain_stage = 0
	emitted.clear()
	var id: String = ACTIONS[section(review_frame)]
	sim.fighters[0].x = 470
	sim.fighters[1].x = 750 if id=="ranged_forward" else 650 if id=="air_pulse" else 600 if id in ["dash_light","dash_heavy"] else 555 if id=="diagonal_light" else 535
func second_sample(frame: int) -> UfeInputFrame:
	var id: String = ACTIONS[section(frame)]
	return UfeInputFrame.make(0,1 if frame%180==25 and id in ["vertical_light","vertical_heavy","diagonal_light","air_crush","dive"] else 0)
func once(key: String, input: UfeInputFrame) -> UfeInputFrame:
	if emitted.has(key): return UfeInputFrame.make()
	emitted[key] = true
	return input
func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
	var id: String = ACTIONS[section(frame)]
	var age := frame-(section(frame)*180)
	var f := sim.fighters[0]
	moves_seen[f.move_id] = true
	states_seen[f.state] = true
	if id in ["chase_light2","chase_end","full_combo"]:
		if age==30:
			chain_stage = 1
			return UfeInputFrame.make(1,0,UfeInputFrame.HEAVY)
		if chain_stage==1 and int(f.motion.chase_window)>0 and f.combat.confirmed:
			chain_stage = 2
			return UfeInputFrame.make(1,1)
		if chain_stage==2 and f.state=="air" and f.height>35:
			chain_stage = 3
			return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		if chain_stage==3 and f.move_id=="chase_light1" and f.combat.confirmed:
			chain_stage = 4
			return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		if chain_stage==4 and id!="chase_light2" and f.move_id=="chase_light2" and f.combat.confirmed:
			chain_stage = 5
			return UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		if chain_stage==5 and id=="full_combo" and f.state=="land" and int(f.motion.land_window)>0:
			chain_stage = 6
			return UfeInputFrame.make(0,-1,UfeInputFrame.HEAVY)
		return UfeInputFrame.make()
	if id in ["vertical_jump","flip_back"]:
		return UfeInputFrame.make(-1 if id=="flip_back" and age==30 else 0,1 if age==30 else 0)
	if id in ["vertical_light","vertical_heavy","diagonal_light","air_crush","dive","air_pulse"]:
		if age==25: return UfeInputFrame.make(1 if id=="diagonal_light" else 0,1)
		if age==29:
			var button := UfeInputFrame.LIGHT if id in ["vertical_light","diagonal_light"] else UfeInputFrame.CRUSH if id=="air_crush" else UfeInputFrame.RANGED if id=="air_pulse" else UfeInputFrame.HEAVY
			return UfeInputFrame.make(0,-1 if id=="dive" else 0,button)
		return UfeInputFrame.make()
	if id in ["dash_light","dash_heavy","backstep","back_counter"]:
		if age in [20,21,24,25]: return UfeInputFrame.make(-1 if id in ["backstep","back_counter"] else 1)
		if age==30 and id!="backstep":return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if id=="dash_light" else UfeInputFrame.HEAVY)
		if id=="dash_light" and f.move_id=="dash_light" and f.combat.confirmed: return once("dash_chain",UfeInputFrame.make(0,0,UfeInputFrame.LIGHT))
		return UfeInputFrame.make()
	if id in ["dodge","dodge_counter"]:
		return UfeInputFrame.make(0,0,UfeInputFrame.DODGE if age==24 else UfeInputFrame.LIGHT if age==30 and id=="dodge_counter" else 0)
	return UfeInputFrame.make(-1 if id=="spin_heavy" and age==30 else 1 if id=="ranged_forward" and age==30 else 0,0,UfeInputFrame.HEAVY if id=="spin_heavy" and age==30 else UfeInputFrame.RANGED if id=="ranged_forward" and age==30 else 0)
func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	var f := sim.fighters[0]
	var b := sim.fighters[1]
	var a := view._animation(f,view.manifests[0])
	trace.append({"movie_frame":frame,"section":section(frame),"action":ACTIONS[section(frame)],"inputs":last_inputs.duplicate(true),"boxes":view.show_boxes,"tick":sim.tick,"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"height":f.height,"vy":f.vy,"vx":f.vx,"x":f.x,"facing":f.facing,"sprite_index":a.get("index",-1),"texture":a.get("texture",""),"target_x":b.x,"target_height":b.height,"target_state":b.state,"target_hp":b.stats.hp,"bounced":b.combat.bounced,"land_window":f.motion.land_window,"chain_stage":chain_stage,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true)})
func save_file(path: String) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练InputFrame；分组开局reset_round并设置距离，组内不改坐标/状态/姿势；陪练空中组用真实跳跃输入；全程F1。","trace":trace},"\t"))
