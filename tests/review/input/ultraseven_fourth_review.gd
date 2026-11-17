class_name UfeUltrasevenFourthReview
extends UfePhase3ThrowReview
@warning_ignore_start("integer_division")
## 三种抓握配对及实际回合演出；仅开局布置训练资源，组内走真实输入。
const FOURTH_NAMES := ["赛文抓杰顿","杰顿抓赛文","赛文抓初代"]
const CEREMONIES := ["登场","赛文胜利","赛文战败","时间到","双方挑衅"]
var available: Dictionary={}
var throw_input:=UfePhase3ThrowReview.new()
func _init() -> void:profile="stage4_ultraseven_fourth"
func section(frame: int) -> int:return mini(frame/240,22)
func length_frames() -> int:return 5520
func matchup() -> Array:return ["ultraseven","ultraman"] if section(review_frame) in range(12,18) else ["ultraseven","zetton"]
func wants_intro() -> bool:return section(review_frame)>=18 and section(review_frame)<=20
func ready_action(part: int) -> bool:
	if available.has(part):return bool(available[part])
	available[part]=_ready_action_uncached(part)
	return bool(available[part])
func _ready_action_uncached(part: int) -> bool:
	var ids:=matchup()
	if part>=18:
		var required: String=["intro","victory","defeat","timeout","taunt"][part-18]
		return UfeContentDatabase.read_json("res://assets/fighters/ultraseven/animations/manifest.json").clips.has(required)
	var owner:=1 if part in range(6,12) else 0
	var actor:=str(ids[owner]);var victim:=str(ids[1-owner])
	var key: String=ACTIONS[part%6]
	var am: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%actor).clips
	var bm: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json"%victim).clips
	if key.begins_with("tech"):return am.has("throw_tech") and bm.has("throw_tech")
	var victim_key: String={"throw_forward":"thrown_forward","throw_back":"thrown_back","air_throw":"thrown_air","dash_throw":"thrown_dash"}[key]
	return am.has(key) and bm.has("grabbed") and bm.has(victim_key)
func label(frame: int) -> String:
	var part:=section(frame)
	var title: String=FOURTH_NAMES[part/6]+" · "+NAMES[part%6] if part<18 else CEREMONIES[part-18]
	return title+(" · F1抓点/判定框" if ready_action(part) else " · 正式素材未齐，待人工，跳过")
func prepare_match(sim: UfeMatchDirector) -> void:
	var part:=section(review_frame)
	active_player=1 if part in range(6,12) else 0
	capture_age=0
	throw_input.active_player=active_player
	throw_input.capture_age=0
	var action: String=ACTIONS[part%6] if part<18 else ""
	sim.fighters[0].x=500
	sim.fighters[1].x=610 if action=="dash_throw" else 552
	if part in [19,20]:sim.fighters[1 if part==19 else 0].stats.hp=45
	if part==21:sim.remaining=60
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var part:=section(frame)
	passive=UfeInputFrame.make()
	if not ready_action(part):return UfeInputFrame.make()
	var age:=frame%240
	if part<18:
		# 复用已审输入时序；父类按180帧分组，用局部age映射，动作索引保持。
		var first:=throw_input.sample((part%6)*180+mini(age,179),sim)
		passive=throw_input.second_sample(frame)
		return first
	if part==22 and age==30:
		passive=UfeInputFrame.make(0,0,UfeInputFrame.GUARD|UfeInputFrame.THROW)
		return passive
	if part in [19,20] and age in [100,160]:
		var input:=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		if part==20:passive=input;return UfeInputFrame.make()
		return input
	return UfeInputFrame.make()
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair:=[]
	for i in range(2):
		var f:=sim.fighters[i];var a:=view._animation(f,view.manifests[i])
		pair.append({"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"clip":a.get("key",""),"sprite":a.get("index",-1),"move":f.move_id,"hp":f.stats.hp,"data":f.frame().duplicate(true)})
	trace.append({"movie_frame":frame,"section":section(frame),"label":label(frame),"available":ready_action(section(frame)),"player":active_player,"inputs":last_inputs.duplicate(true),"pair":pair,"events":sim.events.duplicate(true),"finished":sim.finished,"winner":sim.winner,"intro_tick":view.intro_tick,"ending_tick":view.ending_tick})
func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"source":"主游戏训练真实InputFrame；仅每组开局设距离、KO组初始体力和时间到组剩余时间；未安装组明确跳过，不冒充演示。","trace":trace},"\t"))
@warning_ignore_restore("integer_division")
