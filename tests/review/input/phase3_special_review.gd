class_name UfePhase3SpecialReview
extends UfeReviewDriver
## 每组只设置开局训练参数，动作、命中、KO均使用真实InputFrame。
const MOVES := ["motion_236","motion_623","motion_214","motion_22"]
const S_LABELS := ["初代·切割光线","初代·奥特攻击光线","初代·拘束之环","初代·奥特屏障反射","杰顿·连射火球","杰顿·吸收反击","杰顿·瞬移手刀","杰顿·护盾外推","杰顿护盾挡火球·同角色陪练","双方手动挑衅","时间到演出·训练剩余1秒","完整回合·初代胜利/杰顿失败","完整回合·杰顿胜利/初代失败"]
const S_STARTS := [0,240,480,720,960,1200,1440,1680,1920,2160,2340,2520,3480,4500]
var passive := UfeInputFrame.make()
var active_player: int=0
func _init() -> void:profile="phase3_specials"
func section(frame: int) -> int:
	for i in range(13):
		if frame<S_STARTS[i+1]:return i
	return 12
func length_frames() -> int:return 4500
func boxes(_frame: int) -> bool:return true
func label(frame: int) -> String:return S_LABELS[section(frame)]+" · F1红攻/蓝受/黄盾"
func matchup() -> Array:return ["zetton","zetton"] if section(review_frame)==8 else ["ultraman","zetton"]
func wants_intro() -> bool:return section(review_frame) in [11,12]
func prepare_match(sim: UfeMatchDirector) -> void:
	var part:=section(review_frame)
	active_player=1 if part in [4,5,6,7,12] else 0
	var gap:=80 if part==7 else 100 if part==12 else 220
	sim.fighters[0].x=500
	sim.fighters[1].x=500+gap
	for f in sim.fighters:f.stats.energy=1000
	if part==10:sim.remaining=60
	if part in [11,12]:
		sim.fighters[0].stats.energy=0
		sim.fighters[1].stats.energy=0
func command_input(id: String, age: int, f: UfeFighter) -> UfeInputFrame:
	var dirs: Array=[2,3,6] if id=="motion_236" else [6,2,3] if id=="motion_623" else [2,1,4] if id=="motion_214" else [2,5,2]
	if age<0 or age>5:return UfeInputFrame.make()
	var d: int=int(dirs[age/2])
	var x:= -1 if d in [1,4,7] else 1 if d in [3,6,9] else 0
	var y:= -1 if d in [1,2,3] else 1 if d in [7,8,9] else 0
	var bit: int=UfeInputFrame.LIGHT if id=="motion_236" else UfeInputFrame.HEAVY if id=="motion_623" else UfeInputFrame.RANGED if id=="motion_214" else UfeInputFrame.CRUSH
	return UfeInputFrame.make(x*f.facing,y,bit if age==5 else 0)
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var part:=section(frame)
	var age: int=frame-int(S_STARTS[part])
	var first:=UfeInputFrame.make()
	var second:=UfeInputFrame.make()
	if part<8:
		var move: String=MOVES[part%4]
		first=command_input(move,age-30,sim.fighters[active_player])
		if part in [3,5] and age==(34 if part==5 else 24):second=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
	elif part==8:
		first=command_input("motion_22",age-30,sim.fighters[0])
		if age==24:second=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
	elif part==9:
		if age==30:
			first=UfeInputFrame.make(0,0,UfeInputFrame.GUARD|UfeInputFrame.THROW)
			second=first
	elif part in [11,12]:
		first=command_input("motion_623" if active_player==0 else "motion_236",posmod(age-100,64),sim.fighters[active_player]) if age>=100 else UfeInputFrame.make()
	passive=second if active_player==0 else first
	return first if active_player==0 else second
func second_sample(_frame: int) -> UfeInputFrame:return passive
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair:=[]
	for i in range(2):
		var f:=sim.fighters[i]
		var a:=view._animation(f,view.manifests[i])
		pair.append({"player":i,"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"move":f.move_id,"move_tick":f.move_tick,"clip":a.get("key",""),"sprite":a.get("index",-1),"hp":f.stats.hp,"invulnerable":UfeHitResolver.invulnerable(f),"conceal":f.frame().get("conceal",false)})
	trace.append({"movie_frame":frame,"section":section(frame),"label":S_LABELS[section(frame)],"inputs":last_inputs.duplicate(true),"tick":sim.tick,"pair":pair,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"finished":sim.finished,"winner":sim.winner,"intro_tick":view.intro_tick,"ending_tick":view.ending_tick})
