class_name UfeUltrasevenBodyReview
extends UfeUltrasevenFourthReview
@warning_ignore_start("integer_division")
## 本轮补齐取证，组内仅发送玩家同类InputFrame，不摆状态或改轨迹。
const BODY_LABELS := ["赛文前投杰顿：前投4连续向前", "赛文前投初代：前投4连续向前", "杰顿前投赛文", "杰顿空投赛文", "杰顿冲刺擒抱赛文", "赛文新蓄能完整循环", "击飞下落 → 倒地 → 起身", "击飞下落 → 倒地 → 前滚起身", "击飞下落 → 倒地 → 后滚起身", "击飞下落 → 倒地 → 起身下段", "击飞下落 → 倒地 → 起身中段", "赛文战败完整演出"]
var wake_sent := false
func _init() -> void:profile="stage4_ultraseven_body_fix"
func section(frame: int) -> int:return mini(frame/360,11)
func length_frames() -> int:return 4320
func matchup() -> Array:return ["ultraseven","ultraman"] if section(review_frame)==1 else ["ultraseven","zetton"]
func wants_intro() -> bool:return section(review_frame)==11
func ready_action(_part: int) -> bool:return true
func label(frame: int) -> String:return BODY_LABELS[section(frame)]+" · F1判定/抓点"
func prepare_match(sim: UfeMatchDirector) -> void:
	var part:=section(review_frame)
	active_player=1 if part in [2,3,4] else 0
	capture_age=0;wake_sent=false
	throw_input.active_player=active_player;throw_input.capture_age=0
	sim.fighters[0].x=500
	sim.fighters[1].x=610 if part==4 else 552
	if part==11:sim.fighters[0].stats.hp=45
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var part:=section(frame);var age:=frame%360
	passive=UfeInputFrame.make()
	if part<=4:
		var action_index:=2 if part==3 else 3 if part==4 else 0
		var first:=throw_input.sample(action_index*180+mini(age,179),sim)
		passive=throw_input.second_sample(frame)
		return first
	if part==5:return UfeInputFrame.make(0,0,UfeInputFrame.CHARGE if age>=30 and age<270 else 0)
	if part==11:
		if age in [100,160]:passive=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		return UfeInputFrame.make()
	var hero:=sim.fighters[0];var foe:=sim.fighters[1]
	if age==30:passive=UfeInputFrame.make(foe.facing,0,UfeInputFrame.HEAVY)
	# 击飞后陪练真实走近，使起身攻击能在正常掌/足端范围内命中。
	if age>65 and foe.state in ["idle","walk"] and absi(foe.x-hero.x)>54:
		passive=UfeInputFrame.make(1 if hero.x>foe.x else -1)
	if hero.state=="wake":
		if part in [7,8]:return UfeInputFrame.make(hero.facing if part==7 else -hero.facing)
		if part in [9,10] and not wake_sent:
			wake_sent=true
			return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if part==9 else UfeInputFrame.HEAVY)
	return UfeInputFrame.make()
@warning_ignore_restore("integer_division")
