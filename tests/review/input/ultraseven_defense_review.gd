class_name UfeUltrasevenDefenseReview
extends UfePhase3ReactionReview
## 主游戏训练：杰顿真实输入攻击赛文；不在动作中摆状态、坐标或判定。
const EXTRA := ["backstep","back_counter","dodge","dodge_counter","dash_light","dash_heavy"]
var available: Dictionary = {}
func _init() -> void:
	profile="stage4_ultraseven_defense"
	target_player=0
	complete_chain=true
	available=UfeContentDatabase.read_json("res://assets/fighters/ultraseven/animations/manifest.json").clips
func actions() -> Array: return ACTIONS+EXTRA
func names() -> Array: return NAMES+["后撤 A,A","后撤反击 A,A→K","闪避 Q","侧闪手刀 Q→J","冲刺拳 D,D→J","冲刺飞踢 D,D→K"]
func section_length() -> int: return 240
func length_frames() -> int: return actions().size()*section_length()
func label(frame: int) -> String:
	var id: String=actions()[section(frame)]
	var suffix:=" · F1判定框" if ready_action(id) else " · 待人工，未安装，跳过"
	if id in ["wake","wake_low","wake_mid","roll_forward","roll_back"] and not available.has("down"):suffix+=" · 前置倒地帧待人工"
	return "赛文 · "+names()[section(frame)]+suffix
func ready_action(id: String) -> bool:
	if id=="full_chain":return ["launch_rise","launch_fall","bounce","down","roll_forward"].all(func(a):return available.has(a))
	return available.has(id)
func prepare_match(sim: UfeMatchDirector) -> void:
	super.prepare_match(sim)
	var id: String=actions()[section(review_frame)]
	if id in ["dash_light","dash_heavy"]: sim.fighters[1].x=600
	if id in ["backstep","back_counter"]: sim.fighters[1].x=520
	if id=="crouch_turn":
		# 开局背向对手；输入下蹲后模拟负责转身。
		sim.fighters[0].facing=1
	if id=="turn":sim.fighters[0].facing=1
func target_sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var id: String=actions()[section(frame)]
	var age:=frame-section(frame)*section_length()
	p2=UfeInputFrame.make()
	if not ready_action(id):return UfeInputFrame.make()
	if id in ["backstep","back_counter","dash_light","dash_heavy"]:
		if age in [20,21,24,25]:return UfeInputFrame.make(-1 if id in ["backstep","back_counter"] else 1)
		if age==30 and id!="backstep":return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if id=="dash_light" else UfeInputFrame.HEAVY)
		return UfeInputFrame.make()
	if id in ["dodge","dodge_counter"]:
		return UfeInputFrame.make(0,0,UfeInputFrame.DODGE if age==24 else UfeInputFrame.LIGHT if age==30 and id=="dodge_counter" else 0)
	return super.target_sample(frame,sim)
func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"source":"主游戏训练InputFrame；每组开局只设站位和资源；杰顿使用自己的正式动作；组内不改状态、轨迹、伤害或判定。未安装动作明确跳过。","trace":trace},"\t"))
