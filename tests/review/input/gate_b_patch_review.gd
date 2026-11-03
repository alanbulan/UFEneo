class_name UfeGateBPatchReview
extends UfePhase3ThrowReview
## 分组训练，仅设置每组的开局距离/能量/生命；之后均为正式输入。
func _init() -> void:profile="gate_b_patch"
func section(frame: int) -> int:return mini(frame/180,7)
func length_frames() -> int:return 1440
func boxes(_frame: int) -> bool:return true
func label(frame: int) -> String:
	var part:=section(frame)
	return ("初代 → 杰顿" if part%2==0 else "杰顿 → 初代")+" · "+["41236× 对站防·不可防","41236× 第3tick拆投","41236× 起跳避开","三级必杀KO·爆炸"][part/2]
func prepare_match(sim: UfeMatchDirector) -> void:
	active_player=section(review_frame)%2
	capture_age=0
	sim.fighters[0].x=500
	sim.fighters[1].x=720 if section(review_frame)>=6 else 552
	if section(review_frame)>=6:
		sim.fighters[active_player].stats.energy=3000
		sim.fighters[1-active_player].stats.hp=180
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var age:=frame%180
	var part:=section(frame)
	var a:=UfeInputFrame.make();var b:=UfeInputFrame.make()
	var facing:=sim.fighters[active_player].facing
	if part<6:
		if age>=26 and age<=30:
			var dirs: Array=[[-1,0],[-1,-1],[0,-1],[1,-1],[1,0]]
			var dir: Array=dirs[age-26]
			a=UfeInputFrame.make(int(dir[0])*facing,int(dir[1]),UfeInputFrame.THROW if age==30 else 0)
		if part<2:b=UfeInputFrame.make(0,0,UfeInputFrame.GUARD)
		elif part<4 and sim.fighters[1-active_player].state=="thrown":
			capture_age+=1
			if capture_age==3:b=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		elif part>=4 and age==29:b=UfeInputFrame.make(0,1)
	elif age==30:a=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	passive=b if active_player==0 else a
	return a if active_player==0 else b
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair:=[]
	for i in range(2):
		var f:=sim.fighters[i];var anim:=view._animation(f,view.manifests[i])
		pair.append({"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"move":f.move_id,"move_tick":f.move_tick,"clip":anim.get("key",""),"sprite":anim.get("index",-1),"hp":f.stats.hp,"data":f.frame().duplicate(true)})
	var effects:=[]
	for p in view.feedback.particles:effects.append({"texture":p.clip.texture,"age":p.age,"scale":[p.node.scale.x,p.node.scale.y]})
	trace.append({"movie_frame":frame,"section":section(frame),"label":label(frame),"player":active_player,"tick":sim.tick,"pair":pair,"events":sim.events.duplicate(true),"effects":effects,"inputs":last_inputs.duplicate(true)})
func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练InputFrame；分组设置距离/必杀能量与KO测试生命，组内不改坐标、姿势、判定或胜负。","trace":trace},"\t"))
