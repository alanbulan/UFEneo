class_name UfeUltrasevenAirReview
extends UfePhase3ZettonAirReview
@warning_ignore_start("integer_division")
## 主游戏训练：复用已审真实输入驱动，不复制模拟，不在动作中摆坐标。
func _init() -> void: profile="stage4_ultraseven_air"
func section(frame: int) -> int: return mini(frame/240,16)
func length_frames() -> int: return 17*240
func action_id(frame: int) -> String:
	return "full_combo" if section(frame)==16 else ACTIONS[section(frame)]
func label(frame: int) -> String:
	return "赛文 · "+action_id(frame)+" · F1判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	chain_stage=0
	emitted.clear()
	active_player=0
	var id:=action_id(review_frame)
	var distance:=150 if id=="air_pulse" else 85 if id in ["diagonal_light","diagonal_heavy"] else 65
	sim.fighters[0].x=500
	sim.fighters[1].x=500+distance
func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练InputFrame；赛文P1对杰顿P2。只在各组开局设置站位，动作中不改坐标、状态、伤害或高度。全程F1。","trace":trace},"\t"))
@warning_ignore_restore("integer_division")
