class_name UfePhase3SuperReview
extends UfePhase3SpecialReview
## 主游戏真实输入；仅在每组开局设置训练能量、距离。
var feedback_only: bool=false
func _init() -> void:profile="phase3_supers"
func section(frame: int) -> int:return mini(frame/240,4 if feedback_only else 11)
func length_frames() -> int:return 1200 if feedback_only else 2880
func matchup() -> Array:return ["ultraman","zetton"]
func wants_intro() -> bool:return false
func label(frame: int) -> String:
	var part:=section(frame)
	if feedback_only:return ["轻击连打·火花/停顿/闪白","重击·扩散/停顿/震动","站防·防御火花","扫腿倒地·尘土/震动","升击落地·尘土"][part]
	return ("初代" if part<6 else "杰顿")+" · "+str((part%6)/2+1)+"级必杀 · "+("命中" if part%2==0 else "防御削血")
func prepare_match(sim: UfeMatchDirector) -> void:
	var part:=section(review_frame)
	active_player=0 if feedback_only or part<6 else 1
	var gap:=75 if feedback_only else 220
	sim.fighters[0].x=500
	sim.fighters[1].x=500+gap
	for f in sim.fighters:f.stats.energy=0
	if not feedback_only:sim.fighters[active_player].stats.energy=((part%6)/2+1)*1000
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var part:=section(frame)
	var age:=frame%240
	var a:=UfeInputFrame.make()
	var b:=UfeInputFrame.make()
	if not feedback_only:
		if age==30:a=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT|UfeInputFrame.HEAVY if part==2 else UfeInputFrame.SPECIAL)
		if part%2==1:b=UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
	else:
		match part:
			0:
				if age in [30,44,58]:a=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
			1:
				if age==30:a=UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
			2:
				if age in [30,55]:a=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
				b=UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
			3:
				if age>=28 and age<=30:a=UfeInputFrame.make(0,-1,UfeInputFrame.HEAVY if age==30 else 0)
			4:
				if age==30:a=UfeInputFrame.make(1,0,UfeInputFrame.HEAVY)
	passive=b if active_player==0 else a
	return a if active_player==0 else b
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair:=[]
	for i in range(2):
		var f:=sim.fighters[i]
		var anim:=view._animation(f,view.manifests[i])
		pair.append({"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"move":f.move_id,"move_tick":f.move_tick,"clip":anim.get("key",""),"sprite":anim.get("index",-1),"hp":f.stats.hp,"energy":f.stats.energy,"flash":int(view.feedback.flash[i])})
	trace.append({"movie_frame":frame,"section":section(frame),"label":label(frame),"tick":sim.tick,"remaining":sim.remaining,"hitstop":sim.hitstop,"pair":pair,"events":sim.events.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"inputs":last_inputs.duplicate(true),"shake":[view.feedback.shake.x,view.feedback.shake.y]})
