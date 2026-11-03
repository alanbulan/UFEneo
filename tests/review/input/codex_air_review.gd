extends UfePhase3ZettonAirReview
## 共用空中审片输入。节内只送真实双方 InputFrame，不调整状态或轨迹。
const ORDER := ["vertical_jump","flip_forward","flip_back","vertical_light","vertical_heavy","diagonal_light","diagonal_heavy","air_crush","dive","chase_light1","chase_light2","chase_end","full_combo","air_tech"]
const GROUP := 240
var fighter_id := "ultraman-blazar"
var review_order: Array = []
var mirrored := false

func _init() -> void:
	active_player=0
	var only_actions: Array = ORDER.duplicate()
	var facings: Array = ["right","left"]
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--air-fighter="):fighter_id=arg.trim_prefix("--air-fighter=")
		if arg.begins_with("--air-actions="):only_actions=Array(arg.trim_prefix("--air-actions=").split(","))
		if arg.begins_with("--air-facing="):facings=[arg.trim_prefix("--air-facing=")]
	profile="codex_air_"+fighter_id
	for facing in facings:
		for action in only_actions:
			assert(ORDER.has(action),"未声明空中动作："+str(action))
			review_order.append(str(action)+"_"+str(facing))

func section(frame: int) -> int:return mini(frame/GROUP,review_order.size()-1)
func action_id(frame: int) -> String:return str(review_order[section(frame)]).trim_suffix("_left").trim_suffix("_right")
func length_frames() -> int:return review_order.size()*GROUP
func label(frame: int) -> String:return fighter_id+" 空中 · "+str(review_order[section(frame)])+" · 训练真实输入 / F1"

func prepare_match(sim: UfeMatchDirector) -> void:
	chain_stage=0
	emitted.clear()
	active_player=0
	mirrored=str(review_order[section(review_frame)]).ends_with("_left")
	var id := action_id(review_frame)
	var distance := 85 if id in ["diagonal_light","diagonal_heavy"] else 65
	sim.fighters[0].x=650
	sim.fighters[1].x=650+distance*(-1 if mirrored else 1)
	sim.fighters[0].facing=-1 if mirrored else 1
	sim.fighters[1].facing=1 if mirrored else -1

func target_sample(id: String,age: int,sim: UfeMatchDirector) -> UfeInputFrame:
	if id=="air_tech":
		var f := sim.fighters[0]
		if age==30:return UfeInputFrame.make(0,1)
		if f.state=="air" and f.vy<0:return once("air_tech",UfeInputFrame.make(0,0,UfeInputFrame.GUARD))
		return UfeInputFrame.make()
	return super.target_sample(id,age,sim)

func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"fighter":fighter_id,"review_order":review_order,"input_source":"原主游戏训练，每节只初始化站位/朝向，节内只送真实双方InputFrame；不改状态/高度/轨迹/伤害。","trace":trace},"\t"))
