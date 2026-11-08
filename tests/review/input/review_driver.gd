class_name UfeReviewDriver
extends RefCounted
@warning_ignore_start("integer_division")
const STARTS := [0,180,480,690,1050,1410]
const FINAL_STARTS := [0,240,660,1020,1440,1920]
const LABELS := ["待机","前走 / 后走","冲刺起步 / 跑步关键帧 / 刹停","轻击三连","斜跳重击 / 起跳 / 空翻 / 落地","升击 → 追击跳 → 空中轻击"]
var last_section: int = -1
var moves_seen: Dictionary = {}
var states_seen: Dictionary = {}
var launched: bool = false
var aerial_struck: bool = false
var trace: Array = []
var profile: String = "gate_a"
var last_inputs: Array = []
var review_frame: int = 0
const PHASE3_ACTIONS := ["heavy","spin_heavy","crush","tackle","pulse","ranged_forward","crouch_light","crouch_light2","sweep","slide","low_pulse"]
const PHASE3_LABELS := ["重击 K","回旋重击 A+K","超重击 O","突进撞击 D+O","光弹 I","八分光轮 D+I","下段轻击 S+J","下段轻击二段 S+J→J","扫腿 S+K","滑铲 S+O","低姿光弹 S+I"]

func remember_inputs(inputs: Array) -> void:
	# 记录真正送进模拟的输入；观察时不再调用有状态的sample。
	last_inputs = [inputs[0].pack(),inputs[1].pack()]

func prepare_match(sim: UfeMatchDirector) -> void:
	if profile == "phase3_standing":
		sim.fighters[0].x = 470
		sim.fighters[1].x = 750 if PHASE3_ACTIONS[mini(review_frame/180,10)] in ["pulse","ranged_forward","low_pulse"] else 535
	elif profile == "forward_walk":
		# 仅设置训练开局站位，录制期间不重置位置、不越过边界、不改镜头。
		sim.fighters[0].x = 160
		sim.fighters[1].x = 440
	elif profile == "back_walk":
		sim.fighters[0].x = 900
		sim.fighters[1].x = 1180
	elif profile == "dash_once":
		sim.fighters[0].x = 220
		sim.fighters[1].x = 620
	elif profile in ["locomotion_switches","color_switches"]:
		sim.fighters[0].x = 300
		sim.fighters[1].x = 680

func dash_input(frame: int) -> int:
	# 每次真实双击前触发；前次dash结束后先静止30tick，再输入下一次双击。
	for start in [60,116,172]:
		if frame-start in [0,1,4,5]: return 1
	return 0

func switch_input(frame: int) -> int:
	if (frame >= 24 and frame < 64) or (frame >= 202 and frame < 230) or (frame >= 258 and frame < 286): return 1
	if (frame >= 88 and frame < 128) or (frame >= 230 and frame < 258): return -1
	return 1 if frame in [152,153,156,157,287,289] else 0

func is_walk_review() -> bool:
	return profile in ["forward_walk","back_walk"]

func walk_input(frame: int) -> int:
	return (1 if profile == "forward_walk" else -1) if is_walk_review() and held_walk(frame) else 0

func held_walk(frame: int) -> bool:
	return frame >= 60 and frame < 420

func second_sample(frame: int) -> UfeInputFrame:
	# 陪练通过InputFrame同向移动，连续六秒保持距离，不改坐标或镜头。
	if profile == "dash_once": return UfeInputFrame.make(1 if frame >= 60 else 0)
	return UfeInputFrame.make(walk_input(frame))

func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	if not is_walk_review() and profile not in ["dash_once","locomotion_switches","color_switches","gate_a_final","phase3_standing"]: return
	var f := sim.fighters[0]
	var animation := view._animation(f,view.manifests[0])
	var first := UfeInputFrame.unpack(last_inputs[0]) if last_inputs.size()==2 else UfeInputFrame.make()
	var second := UfeInputFrame.unpack(last_inputs[1]) if last_inputs.size()==2 else UfeInputFrame.make()
	trace.append({"movie_frame":frame,"section":section(frame),"boxes":view.show_boxes,"tick":sim.tick,"held_forward":profile == "forward_walk" and held_walk(frame),"held_backward":profile == "back_walk" and held_walk(frame),"input_p1_x":first.x,"input_p2_x":second.x,"inputs":last_inputs.duplicate(true),"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"x":f.x,"target_x":sim.fighters[1].x,"target_height":sim.fighters[1].height,"facing":f.facing,"height":f.height,"camera_x":view.camera_x,"sprite_index":animation.get("index",-1),"texture":animation.get("texture","")})
	if profile == "phase3_standing":
		trace[-1].events = sim.events.duplicate(true)
		trace[-1].target_hp = sim.fighters[1].stats.hp
		trace[-1].projectiles = sim.projectiles.duplicate(true)

func length_frames() -> int:
	if profile == "phase3_standing": return 1980
	if profile == "dash_once": return 240
	if profile == "locomotion_switches": return 360
	if profile == "color_switches": return 420
	if profile == "gate_a_final": return 2400
	return 480 if is_walk_review() else 1800

func label(frame: int) -> String:
	if profile == "phase3_standing": return PHASE3_LABELS[section(frame)]+" · F1判定框"
	if profile == "forward_walk": return "前走循环 · 持续前进6秒 · 陪练同步后退保持距离"
	if profile == "back_walk": return "后走循环 · 持续后退6秒 · 陪练同步前进保持距离"
	if profile == "dash_once": return "一次性冲刺 · 双击前共3次 · 每次之间静止半秒"
	if profile == "locomotion_switches": return "移动切换色差观察 · 待机 / 前走 / 后走 / 冲刺 · 只记录不修图"
	if profile == "color_switches": return "远侧色统一后 · 待机 / 前后走 / 冲刺 / 轻击切换"
	return str(LABELS[section(frame)])

func boxes(frame: int) -> bool:
	if profile == "phase3_standing": return true
	if is_walk_review() or profile in ["dash_once","locomotion_switches","color_switches"]: return false
	var part := section(frame)
	if profile == "gate_a_final":
		var finish: int = FINAL_STARTS[part+1] if part<5 else 2400
		return frame >= (int(FINAL_STARTS[part])+finish)/2
	return frame-int(STARTS[part]) > (60 if part in [4,5] else 120)

func section(frame: int) -> int:
	if profile == "phase3_standing": return mini(frame/180,10)
	if is_walk_review() or profile in ["dash_once","locomotion_switches","color_switches"]: return 0
	var result := 0
	var starts: Array = FINAL_STARTS if profile == "gate_a_final" else STARTS
	for i in range(starts.size()):
		if frame >= starts[i]: result = i
	return result

func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
	if profile == "phase3_standing":
		var id: String = PHASE3_ACTIONS[section(frame)]
		var age := frame%180
		var low := id in ["crouch_light","crouch_light2","sweep","slide","low_pulse"]
		var button := UfeInputFrame.RANGED if id in ["pulse","ranged_forward","low_pulse"] else UfeInputFrame.CRUSH if id in ["crush","tackle","slide"] else UfeInputFrame.LIGHT if id.begins_with("crouch_light") else UfeInputFrame.HEAVY
		var horizontal := -1 if id=="spin_heavy" else 1 if id in ["tackle","ranged_forward"] else 0
		var trigger := age==30 or (id=="crouch_light2" and age==43)
		return UfeInputFrame.make(horizontal if trigger else 0,-1 if low and age<125 else 0,button if trigger else 0)
	if profile == "dash_once": return UfeInputFrame.make(dash_input(frame))
	if profile == "locomotion_switches": return UfeInputFrame.make(switch_input(frame))
	if profile == "color_switches": return UfeInputFrame.make(switch_input(frame) if frame<286 else 0,0,UfeInputFrame.LIGHT if frame==320 else 0)
	if is_walk_review(): return UfeInputFrame.make(walk_input(frame))
	var part := section(frame)
	var age: int = frame-int(FINAL_STARTS[part] if profile == "gate_a_final" else STARTS[part])
	if profile == "gate_a_final" and part>=3:
		age = age% (210 if part==3 else 240)
		if part==5 and age==0:
			launched = false
			aerial_struck = false
	var f := sim.fighters[0]
	moves_seen[f.move_id] = true
	states_seen[f.state] = true
	if profile not in ["gate_a_final","phase3_standing"] and frame%2==0: trace.append({"movie_frame":frame,"section":part,"tick":sim.tick,"state":f.state,"move":f.move_id,"move_tick":f.move_tick,"x":f.x,"height":f.height,"target_height":sim.fighters[1].height})
	match part:
		1: return UfeInputFrame.make(1 if age%120<60 else -1)
		2:
			var cycle := age%70
			return UfeInputFrame.make(1 if cycle in [0,1,4,5,6] else 0)
		3:
			if age<104: return UfeInputFrame.make(1)
			if age<290: return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if age%9==0 else 0)
		4:
			if age<50: return UfeInputFrame.make(1)
			if age==70: return UfeInputFrame.make(1,1)
			if age==90: return UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		5:
			if age<120: return UfeInputFrame.make(1)
			if age==126: return UfeInputFrame.make(1,0,UfeInputFrame.HEAVY)
			if int(f.motion.chase_window)>0 and f.combat.confirmed:
				launched = true
				return UfeInputFrame.make(1,1)
			if launched and f.state=="air" and f.height>35 and not aerial_struck:
				aerial_struck = true
				return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
	return UfeInputFrame.make()

func save_file(path: String) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file == null: return
	var source := "主游戏训练模式 InputFrame 脚本输入；未改写坐标、姿势或镜头"
	if profile == "forward_walk":
		source = "主游戏训练模式 InputFrame 脚本输入；前走专用开局站位160/440，之后不重置坐标、姿势或镜头；陪练同步InputFrame退走保持距离"
	elif profile == "back_walk":
		source = "主游戏训练模式 InputFrame 脚本输入；后走专用开局站位900/1180，之后不重置坐标、姿势或镜头；陪练同步InputFrame前走保持距离"
	elif profile in ["dash_once","locomotion_switches","color_switches"]:
		source = "主游戏训练模式真实方向InputFrame；只设开局站位，录制期间不重置坐标、姿势或镜头；冲刺由双击前触发，22tick由模拟决定"
	elif profile == "gate_a_final":
		source = "主游戏训练模式真实InputFrame，40秒六组；每组开始reset_round一次，组内不重置人物/姿势/镜头；后半F1，攻击及跳跃在两半各演示。"
	elif profile == "phase3_standing":
		source = "主游戏训练模式真实InputFrame；逐招分组reset_round，近战间距65、远程280；组内不重置坐标/姿势/镜头，F1全程；每招记录命中事件与对手HP。"
	file.store_string(JSON.stringify({"profile":profile,"input_source":source, "moves":moves_seen.keys(),"states":states_seen.keys(),"chase_jump":launched,"aerial_light":aerial_struck,"trace":trace},"\t"))
@warning_ignore_restore("integer_division")
