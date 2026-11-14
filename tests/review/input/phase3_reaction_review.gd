class_name UfePhase3ReactionReview
extends UfeReviewDriver
@warning_ignore_start("integer_division")
## 只有分组开局设训练站位/资源；组内用双方真实输入驱动。
const ACTIONS := ["turn","crouch_turn","guard","crouch_guard","blockstun","crouch_blockstun","guardbreak","stun","hit_high","hit_mid","hit_crouch","hit_air","launch_rise","launch_fall","bounce","down","wake","roll_forward","roll_back","air_tech","wake_low","wake_mid","guard_counter","burst","charge_start","charge","charge_stop","full_chain"]
const NAMES := ["站立转身","蹲姿转身","站防 U","蹲防 S+U","站防硬直","蹲防硬直","破防（训练低体力）","破绽眩晕（训练临界眩晕）","空中来拳命中头部","站立中段受击","蹲姿受击","空中受击","击飞上升","击飞下落","砸地弹地","倒地","起身","前滚起身","后滚起身","空中受身 U","起身下段 J","起身中段 K","防御反击 D+K / 1格","爆气 U+H / 2格","蓄能起 H","蓄能循环 H","蓄能收 松H","被升击 → 砸地弹地 → 倒地 → 前滚起身"]
var p2 := UfeInputFrame.make()
var chain_stage: int = 0
var current_sim: UfeMatchDirector
var target_player: int = 0
var complete_chain: bool = false
func actions() -> Array: return ACTIONS
func names() -> Array: return NAMES
func section_length() -> int: return 210
func _init() -> void: profile="phase3_reaction"
func section(frame: int) -> int: return mini(frame/section_length(),actions().size()-1)
func length_frames() -> int: return (actions().size()+1)*section_length()
func boxes(_frame: int) -> bool: return true
func label(frame: int) -> String: return names()[section(frame)]+" · F1判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	current_sim=sim
	chain_stage=0
	var id: String=actions()[section(review_frame)]
	sim.fighters[0].x=470
	sim.fighters[1].x=535
	if id in ["turn","crouch_turn"]: sim.fighters[1-target_player].x=400 if target_player==0 else 600
	if id=="guardbreak": sim.fighters[target_player].stats.stamina=1
	if id=="stun": sim.fighters[target_player].stats.stun=sim.rules.stun_threshold-1
	if id=="guard_counter": sim.fighters[target_player].stats.energy=1000
	if id=="burst": sim.fighters[target_player].stats.energy=2000
func second_sample(_frame: int) -> UfeInputFrame: return p2
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var target_input:=target_sample(frame,sim)
	if target_player==0: return target_input
	var attacker_input:=p2
	p2=target_input
	return attacker_input
func target_sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var id: String=actions()[section(frame)]
	var age:=frame-section(frame)*section_length()
	var f:=sim.fighters[target_player]
	var b:=sim.fighters[1-target_player]
	p2=UfeInputFrame.make()
	if id in ["walk_forward","walk_back"]:
		var direction:=f.facing*(1 if id=="walk_forward" else -1) if age>=25 and age<225 else 0
		p2=UfeInputFrame.make(direction)
		return UfeInputFrame.make(direction)
	if id in ["turn","crouch_turn"]: return UfeInputFrame.make(0,-1 if id=="crouch_turn" else 0)
	if id in ["charge_start","charge","charge_stop"]: return UfeInputFrame.make(0,0,UfeInputFrame.CHARGE if age>=25 and age<150 else 0)
	if id in ["guard","crouch_guard","blockstun","crouch_blockstun","guardbreak","guard_counter"]:
		if age==(0 if id=="guardbreak" else 30) and id not in ["guard","crouch_guard"]: p2=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		if id=="guard_counter" and f.state in ["blockstun","crouch_blockstun"] and chain_stage==0:
			chain_stage=1
			return UfeInputFrame.make(f.facing,0,UfeInputFrame.HEAVY)
		return UfeInputFrame.make(0,-1 if id in ["crouch_guard","crouch_blockstun"] else 0,UfeInputFrame.GUARD if age<160 else 0)
	if id=="hit_high":
		if age==20: p2=UfeInputFrame.make(0,1)
		# 杰顿现有独立跳跃手刀/较低跳弧，提早出掌使实际掌端命中初代头部。
		if age==(54 if target_player==0 else 45): p2=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		return UfeInputFrame.make()
	if id in ["hit_mid","hit_crouch","hit_air","stun","burst"]:
		if id=="hit_mid" and target_player==1:
			# 重处理后的初代重拳命中高度已在头部区；改用真实低拳展示中段受击。
			p2=UfeInputFrame.make(0,-1,UfeInputFrame.LIGHT if age==30 else 0)
			return UfeInputFrame.make()
		# 杰顿正式重手刀比旧占位慢、落点更低；先出手再起跳，仍用真实命中触发空中受击。
		if age==(0 if id=="stun" else 20 if id=="hit_air" else 30): p2=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		if id=="burst" and f.state=="hit" and chain_stage==0:
			chain_stage=1
			return UfeInputFrame.make(0,0,UfeInputFrame.GUARD|UfeInputFrame.CHARGE)
		var jump_age:=24 if target_player==1 else 30
		return UfeInputFrame.make(0,-1 if id=="hit_crouch" else 1 if id=="hit_air" and age==jump_age else 0)
	if id in ["down","wake","roll_forward","roll_back","wake_low","wake_mid"]:
		if age==30: p2=UfeInputFrame.make(0,-1,UfeInputFrame.HEAVY)
		if f.state=="wake":
			if id in ["roll_forward","roll_back"]: return UfeInputFrame.make(f.facing if id=="roll_forward" else -f.facing, 0, UfeInputFrame.DODGE)
			if id in ["wake_low","wake_mid"] and chain_stage==0:
				chain_stage=1
				return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if id=="wake_low" else UfeInputFrame.HEAVY)
		return UfeInputFrame.make()
	# 攻击方使用自己的已接入招式，组内只送真实输入。
	if age==25:
		chain_stage=1
		p2=UfeInputFrame.make(b.facing,0,UfeInputFrame.HEAVY)
	if id in ["bounce","full_chain"]:
		if chain_stage==1 and b.combat.confirmed and int(b.motion.chase_window)>0 and int(b.motion.chase_window)<=21:
			chain_stage=2
			p2=UfeInputFrame.make(b.facing,1)
		elif chain_stage==2 and b.state=="air" and b.height>35:
			chain_stage=3
			p2=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if complete_chain else UfeInputFrame.HEAVY)
		elif complete_chain and chain_stage==3 and b.move_id=="chase_light1" and b.combat.confirmed:
			chain_stage=4
			p2=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		elif complete_chain and chain_stage==4 and b.move_id=="chase_light2" and b.combat.confirmed:
			chain_stage=5
			p2=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		if id=="full_chain" and f.state=="wake": return UfeInputFrame.make(-f.facing if complete_chain else f.facing, 0, UfeInputFrame.DODGE)
	if id=="air_tech" and f.state=="launch" and f.vy<0: return UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
	return UfeInputFrame.make()
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var f:=sim.fighters[target_player]
	var b:=sim.fighters[1-target_player]
	var a:=view._animation(f,view.manifests[target_player])
	trace.append({"movie_frame":frame,"section":section(frame),"action":actions()[section(frame)],"inputs":last_inputs.duplicate(true),"boxes":view.show_boxes,"state":f.state,"state_tick":f.state_tick,"clip":f.animation_key(),"move":f.move_id,"move_tick":f.move_tick,"height":f.height,"vy":f.vy,"x":f.x,"facing":f.facing,"sprite_index":a.get("index",-1),"texture":a.get("texture",""),"hp":f.stats.hp,"energy":f.stats.energy,"stamina":f.stats.stamina,"p2_move":b.move_id,"p2_height":b.height,"p2_hp":b.stats.hp,"attacker_state":b.state,"chain_stage":chain_stage,"events":sim.events.duplicate(true)})
func save_file(path: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"target_player":target_player,"source":"主游戏训练InputFrame；分组开局设站位；破防/眩晕使用临界资源、防反/爆气使用规定能量；组内不摆状态、不改轨迹，攻击方使用自己已接入招式。","trace":trace},"\t"))
@warning_ignore_restore("integer_division")
