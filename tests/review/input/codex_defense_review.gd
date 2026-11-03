extends UfePhase3ReactionReview
## 防御受击共用审片输入；每节只设初始训练条件，节内用双方真实输入。
const ITEMS := ["guard","crouch_guard","blockstun","crouch_blockstun","guardbreak","guard_counter","hit_high","hit_mid","hit_crouch","hit_air","launch_rise","launch_fall","bounce","down","wake","wake_low","wake_mid","roll_forward","roll_back","stun","defeat"]
const GROUP := 240
var fighter_id := "ultraman-arc"
var review_order: Array = []
var review_facings: Array = []
var mirrored := false

func _init() -> void:
	target_player=0
	complete_chain=true
	var selected: Array=ITEMS.duplicate()
	var facings: Array=["right","left"]
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--defense-fighter="):fighter_id=arg.trim_prefix("--defense-fighter=")
		if arg.begins_with("--defense-actions="):selected=Array(arg.trim_prefix("--defense-actions=").split(","))
		if arg.begins_with("--defense-facing="):facings=[arg.trim_prefix("--defense-facing=")]
	for facing in facings:
		assert(facing in ["right","left"])
		for action in selected:
			assert(ITEMS.has(action),"未声明的防御受击动作："+str(action))
			review_order.append(action)
			review_facings.append(facing)
	profile="codex_defense_"+fighter_id

func actions() -> Array:return review_order
func section(frame: int) -> int:return mini(frame/GROUP,review_order.size()-1)
func section_length() -> int:return GROUP
func action_id(frame: int) -> String:return str(review_order[section(frame)])
func length_frames() -> int:return review_order.size()*GROUP
func label(frame: int) -> String:return fighter_id+" · "+action_id(frame)+" · "+str(review_facings[section(frame)])+" · 训练真实输入 / F1"

func prepare_match(sim: UfeMatchDirector) -> void:
	current_sim=sim
	chain_stage=0
	p2=UfeInputFrame.make()
	mirrored=review_facings[section(review_frame)]=="left"
	sim.fighters[0].x=850 if mirrored else 350
	sim.fighters[1].x=sim.fighters[0].x+65*(-1 if mirrored else 1)
	sim.fighters[0].facing=-1 if mirrored else 1
	sim.fighters[1].facing=1 if mirrored else -1
	var id:=action_id(review_frame)
	if id=="guardbreak":sim.fighters[0].stats.stamina=1
	if id=="stun":sim.fighters[0].stats.stun=sim.rules.stun_threshold-1
	if id=="guard_counter":sim.fighters[0].stats.energy=1000
	if id=="defeat":sim.fighters[0].stats.hp=1

func target_sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var id:=action_id(frame)
	var age:=frame-section(frame)*GROUP
	if id in ["hit_mid","defeat"]:
		p2=UfeInputFrame.make(0,-1,UfeInputFrame.LIGHT if age==30 else 0)
		return UfeInputFrame.make()
	if sim.fighters[1].definition.id=="ultraseven":
		if id=="crouch_blockstun":
			p2=UfeInputFrame.make(0,-1,UfeInputFrame.LIGHT if age==30 else 0)
			return UfeInputFrame.make(0,-1,UfeInputFrame.GUARD if age<160 else 0)
		if id=="hit_high":
			p2=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY if age==30 else 0)
			return UfeInputFrame.make()
		if id=="hit_air":
			p2=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY if age==20 else 0)
			return UfeInputFrame.make(0,1 if age==26 else 0)
	return super.target_sample(frame,sim)

func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair: Array=[]
	for i in range(2):
		var f:=sim.fighters[i]
		var a:=view._animation(f,view.manifests[i])
		pair.append({"fighter":f.definition.id,"x":f.x,"facing":f.facing,"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"clip":a.get("key",""),"sprite":a.get("index",-1),"height":f.height,"vy":f.vy,"hp":f.stats.hp,"energy":f.stats.energy,"invulnerable":f.combat.invulnerable})
	trace.append({"movie_frame":frame,"section":section(frame),"action":action_id(frame),"inputs":last_inputs.duplicate(true),"pair":pair,"events":sim.events.duplicate(true),"state_hash":sim.state_hash(),"boxes":view.show_boxes})

func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"fighter":fighter_id,"source":"原主游戏训练；节间仅设站位/朝向/临界训练资源，节内真实双方InputFrame，不摆受击/倒地/起身状态，不改轨迹或伤害。","trace":trace}))
