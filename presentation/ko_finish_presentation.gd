class_name UfeKoFinishPresentation
extends RefCounted
## 终局只读播放：绝不调用step、输入解析、发射、命中或伤害结算。
## scene只是既有整帧/特效/声音消费者的数据载体，不送回模拟、录制或回放验证。
const HOLD_TICKS := 6
const SLOW_DIVISOR := 3
const SLOW_STEPS := 18
const REPLAY_ENDING_TICKS := 90
const HoldPoints = preload("res://core/combat/throw_hold_points.gd")
var source: UfeMatchDirector
var scene: UfeMatchDirector
var real_age: int = 0
var slow_age: int = 0
var effect_steps: int = 0
var active: bool = false
var move_done: Array = [false,false]
var projectile_rows: Array = []

func reset() -> void:
	source=null;scene=null;real_age=0;slow_age=0;effect_steps=0;active=false
	move_done=[false,false]
	projectile_rows.clear()

func sample(value: UfeMatchDirector, frozen: bool) -> UfeMatchDirector:
	effect_steps=0 if frozen else 1
	if not is_same(source,value):
		reset()
		source=value
		effect_steps=0 if frozen else 1
	if scene==null:
		if not value.finished or value.remaining<=0 or value.terminal_view.is_empty():return value
		_begin()
		effect_steps=0
		return scene
	if frozen:
		effect_steps=0
		return scene
	if not active:
		scene.events.clear()
		scene.tick+=1
		return scene
	real_age+=1
	effect_steps=0
	if real_age>HOLD_TICKS+SLOW_STEPS*SLOW_DIVISOR:
		_ceremony()
		effect_steps=1
	elif real_age>HOLD_TICKS and (real_age-HOLD_TICKS)%SLOW_DIVISOR==0:
		_advance_pose()
		effect_steps=1
	return scene

func can_pause_replay(value: UfeMatchDirector, ending_tick: int) -> bool:
	if not value.finished:return true
	if value.remaining>0 and not value.terminal_view.is_empty():
		if not is_same(source,value) or scene==null or active:return false
	return ending_tick>=REPLAY_ENDING_TICKS

static func fighter_copy(record: Dictionary) -> UfeFighter:
	var row: Array=record.snapshot
	var f:=UfeFighter.new(record.definition,int(row[1]))
	f.base_definition=record.base_definition
	f.battle_form=record.battle_form.duplicate(true)
	f.form_id=str(record.form_id)
	f.transformed_this_round=bool(record.transformed_this_round)
	f.height=int(row[2]);f.vx=int(row[3]);f.vy=int(row[4]);f.facing=int(row[5])
	f.state=str(row[6]);f.state_tick=int(row[7]);f.move_id=str(row[8]);f.move_tick=int(row[9])
	f.stats=row[10].duplicate(true);f.combat=row[11].duplicate(true);f.motion=row[12].duplicate(true)
	var input: Array=row[13]
	f.resolver.previous=int(input[0]);f.resolver.age=int(input[1])
	f.resolver.history=input[2].duplicate(true);f.resolver.press_ticks=input[3].duplicate(true)
	f.resolver.tap_direction=int(input[4]);f.resolver.tap_tick=int(input[5]);f.resolver.previous_x=int(input[6])
	return f

static func fighter_record(f: UfeFighter) -> Dictionary:
	return {"definition":f.definition,"base_definition":f.base_definition,"battle_form":f.battle_form.duplicate(true),
		"form_id":f.form_id,"transformed_this_round":f.transformed_this_round,"snapshot":f.snapshot().duplicate(true)}

func _begin() -> void:
	var data: Dictionary=source.terminal_view
	var records: Array=data.fighters
	scene=UfeMatchDirector.new(records[0].definition,records[1].definition,source.rules,source.states)
	scene.fighters=[fighter_copy(records[0]),fighter_copy(records[1])]
	scene.tick=int(data.tick);scene.remaining=int(data.remaining);scene.hitstop=0
	scene.finished=false;scene.winner=source.winner
	scene.content_fingerprint=source.content_fingerprint
	scene.events=data.events.duplicate(true)
	scene.projectiles=data.projectiles.duplicate(true)
	for p in scene.projectiles:
		var budget:=SLOW_STEPS if bool(p.get("beam",false)) else mini(SLOW_STEPS,maxi(1,int(p.life)))
		p.end_alpha=1000
		projectile_rows.append({"projectile":p,"budget":budget,"detached_at":-1})
	active=true

func _advance_pose() -> void:
	slow_age+=1
	scene.tick+=1
	scene.events.clear()
	for i in range(scene.fighters.size()):
		var f:=scene.fighters[i]
		f.state_tick+=1
		var paired:=f.state in ["thrown","captured"] or scene.fighters[1-i].state=="thrown" and int(scene.fighters[1-i].combat.thrower)==i
		if not paired and (f.height>0 or f.vy!=0):
			f.x+=f.vx;f.height+=f.vy;f.vy-=1
			if f.height<=0:
				f.height=0;f.vx=0;f.vy=0
				if int(f.stats.hp)<=0 and f.state in ["launch","bounce","hit"]:f.enter("down",35)
		if not f.move_id.is_empty() and not bool(move_done[i]):
			var frame:=f.frame()
			# 只读本招已有整相和位移；不执行shots、伤害、取消、变身或新攻击。
			if frame.has("velocity"):f.vx=int(frame.velocity[0])*f.facing;f.vy=int(frame.velocity[1])
			if frame.has("teleport"):f.x=clampi(scene.fighters[1-i].x+f.facing*int(frame.teleport),28,1252)
			f.x+=int(frame.get("dx",0))*f.facing
			f.height=maxi(0,f.height+int(frame.get("dy",0)))
			for event in frame.get("events",[]):
				if str(event.kind)=="sound":scene.events.append({"kind":"sound","id":event.id,"player":i})
			var frames: Array=f.definition.moves[f.move_id].frames
			if f.move_tick+1<frames.size():f.move_tick+=1
			else:move_done[i]=true
		f.x=clampi(f.x,28,1252)
	for i in range(scene.fighters.size()):
		_sync_throw(i)
		_sync_capture(i)
	_advance_projectiles()

func _sync_throw(index: int) -> void:
	var b:=scene.fighters[index]
	if b.state!="thrown":return
	var owner:=int(b.combat.thrower)
	if owner<0 or owner>=scene.fighters.size():return
	var a:=scene.fighters[owner]
	var frame:=a.frame()
	if a.move_id.is_empty() or not frame.has("target"):return
	var target: Dictionary=frame.target
	if frame.has("throw_height"):
		var fraction: Array=frame.throw_height
		@warning_ignore("integer_division")
		a.height=int(a.motion.throw_origin_height)*int(fraction[0])/maxi(1,int(fraction[1]))
	b.motion.pose=str(target.pose)
	# 两个几何查询均只读本人现有整相和抓点，不调用投技sync/伤害。
	b.motion.pose_sprite=UfeThrowResolver.victim_sprite(a,b,target)
	b.facing=a.facing*int(target.get("facing",-1))
	var offset: Array=target.get("root",[0,0])
	match str(target.get("mode","root")):
		"hold":
			var pose:=b.frame()
			var point: Array=HoldPoints.point(b,target,pose) if target.has("hold_point_overrides") else pose.get("grab_points",{}).get(str(target.get("grab_point","waist")),[])
			if point.size()!=2:return
			var grip: Array=target.grip
			b.x=a.x+a.facing*int(grip[0])-b.facing*int(point[0])+a.facing*int(offset[0])
			b.height=maxi(0,a.height+int(grip[1])-int(point[1])+int(offset[1]))
		"release":
			if not bool(b.motion.get("throw_released",false)):
				b.motion.throw_released=true;b.motion.release_x=(b.x-a.x)*a.facing;b.motion.release_height=b.height
				b.motion.release_goal_x=UfeThrowResolver.landing_offset(a,b,int(offset[0]))
			var progress: Array=target.progress
			var at:=int(progress[0]);var duration:=maxi(1,int(progress[1]))
			@warning_ignore("integer_division")
			b.x=a.x+a.facing*(int(b.motion.release_x)+(int(b.motion.release_goal_x)-int(b.motion.release_x))*at/duration)
			@warning_ignore("integer_division")
			b.height=maxi(0,int(b.motion.release_height)*(duration-at)/duration+int(offset[1])*at/duration)
		_:
			b.x=a.x+a.facing*int(offset[0])
			b.height=maxi(0,int(offset[1])+(0 if bool(target.get("ground",false)) else a.height))
	_pair_inside(a,b)

func _sync_capture(owner: int) -> void:
	var actor:=scene.fighters[owner]
	var relation: Dictionary=actor.motion.get("capture",{})
	var victim:=int(relation.get("victim",-1))
	if victim<0 or victim>=scene.fighters.size() or actor.move_id.is_empty():return
	var stages: Array=actor.definition.moves[actor.move_id].get("capture",{}).get("stages",[])
	var phase_index:=int(relation.get("phase_index",-1))
	if phase_index<0 or phase_index>=stages.size():return
	var target:=scene.fighters[victim]
	relation.phase_age=int(relation.phase_age)+1
	if int(relation.phase_age)>=int(stages[phase_index].ticks):
		phase_index+=1
		if phase_index>=stages.size():
			target.motion.erase("capture_victim")
			target.enter("down" if int(target.stats.hp)<=0 else "idle",35)
			target.height=0;target.vx=0;target.vy=0
			actor.motion.erase("capture")
			return
		relation.phase_index=phase_index;relation.phase=str(stages[phase_index].id);relation.phase_age=0
	var phase: Dictionary=stages[phase_index]
	var age:=mini(int(relation.phase_age),int(phase.ticks)-1)
	var selected: Variant=phase.victim_frames[age]
	var pose: Dictionary=target.motion.get("capture_victim",{})
	if pose.is_empty():return
	pose.animation=str(selected.animation) if selected is Dictionary else str(phase.victim_animation)
	pose.frame=int(selected.frame) if selected is Dictionary else int(selected)
	target.facing=-actor.facing
	var data: Dictionary=actor.definition.moves[actor.move_id].capture
	var anchor: Array=data.get("hand_anchor_by_frame",{}).get(str(actor.move_tick),data.hand_anchor)
	var hand_x:=actor.x+actor.facing*int(anchor[0]);var hand_height:=actor.height+int(anchor[1])
	match str(relation.phase):
		"enclose":target.x=int(relation.origin_x);target.height=int(relation.origin_height)
		"shrink":
			target.x=int(relation.origin_x)
			@warning_ignore("integer_division")
			target.height=int(relation.origin_height)+int(data.lift_height)*age/maxi(1,int(phase.ticks)-1)
		"return":
			var elapsed:=age+1;var duration:=int(phase.ticks)
			@warning_ignore("integer_division")
			target.x=(int(relation.origin_x)*(duration-elapsed)+hand_x*elapsed)/duration
			@warning_ignore("integer_division")
			target.height=((int(relation.origin_height)+int(data.lift_height))*(duration-elapsed)+hand_height*elapsed)/duration
		"held":target.x=hand_x;target.height=hand_height
		"release":
			if age<int(data.release_ground_tick):target.x=hand_x;target.height=hand_height
			else:
				if not relation.has("release_x"):
					target.x=actor.x+actor.facing*maxi(int(data.release_distance),actor.definition.body_radius+target.definition.body_radius+2)
					_pair_inside(actor,target);relation.release_x=target.x
				target.x=int(relation.release_x);target.height=0

static func _pair_inside(first: UfeFighter, second: UfeFighter) -> void:
	var left:=mini(first.x,second.x);var right:=maxi(first.x,second.x)
	var shift:=28-left if left<28 else 1252-right if right>1252 else 0
	first.x+=shift;second.x+=shift

func _advance_projectiles() -> void:
	for row in projectile_rows:
		var p: Dictionary=row.projectile
		var left:=maxi(0,int(row.budget)-slow_age)
		p.age=int(p.age)+1
		p.life=maxi(1,left) # 移除不冒充模拟自然到期，不产生新的到期/命中事件。
		var fade:=mini(12 if bool(p.get("beam",false)) else 6,int(row.budget))
		@warning_ignore("integer_division")
		p.end_alpha=mini(1000,left*1000/maxi(1,fade))
		if bool(p.get("beam",false)):
			var actor:=scene.fighters[int(p.owner)]
			if not bool(p.get("beam_reflected",false)) and actor.move_id==str(p.move) and actor.frame().has("beam_origin"):
				var anchor: Array=actor.frame().beam_origin
				p.x=actor.x+actor.facing*int(anchor[0]);p.height=actor.height+int(anchor[1])
			else:
				# 离开发射相后只保留最后能量尾迹，按有界短尾消散，不追到收回的手上。
				if int(row.detached_at)<0:row.detached_at=slow_age
				@warning_ignore("integer_division")
				p.end_alpha=mini(int(p.end_alpha),maxi(0,6-(slow_age-int(row.detached_at)))*1000/6)
		elif p.has("integer_path"):
			_advance_returning(p)
		else:
			p.x=int(p.x)+int(p.facing)*int(p.get("speed",0));p.height=int(p.height)+int(p.get("vy",0))
			if int(p.get("ground_height",-1))>=0 and int(p.height)<=int(p.ground_height):p.height=int(p.ground_height)
	scene.projectiles=scene.projectiles.filter(func(p):return int(p.end_alpha)>0)

func _advance_returning(p: Dictionary) -> void:
	var path: Array=p.integer_path
	if int(p.age)<=path.size() and not bool(p.get("forced_return",false)):
		var point: Array=path[maxi(0,int(p.age)-1)]
		p.x=int(p.origin_x)+int(p.facing)*int(point[0]);p.height=maxi(0,int(p.origin_height)+int(point[1]))
	else:
		if int(p.get("return_age",0))==0:p.return_x=int(p.x);p.return_height=int(p.height)
		p.return_age=int(p.get("return_age",0))+1
		var actor:=scene.fighters[int(p.owner)]
		var anchor: Array=p.get("return_anchor_by_tick",{}).get(str(actor.move_tick),actor.frame().get("weapon_return_anchor",p.get("return_anchor",[42,100])))
		var duration:=maxi(1,int(p.get("return_ticks",6)));var left:=maxi(0,duration-int(p.return_age))
		@warning_ignore("integer_division")
		p.x=(int(p.return_x)*left+(actor.x+actor.facing*int(anchor[0]))*(duration-left))/duration
		@warning_ignore("integer_division")
		p.height=(int(p.return_height)*left+(actor.height+int(anchor[1]))*(duration-left))/duration
		if left==0 and actor.move_tick>=int(p.get("return_not_before_tick",0)):p.end_alpha=0
	var points: Array=p.get("trail_points",[])
	points.append([int(p.x),int(p.height)])
	if points.size()>4:points.pop_front()
	p.trail_points=points

func _ceremony() -> void:
	# 已在只读慢放中落地的败方继续保持本人整张倒地相，避免结算从站立失败相再倒一次。
	var grounded: Dictionary={}
	for i in range(scene.fighters.size()):
		var shown:=scene.fighters[i]
		var landed: bool=shown.state=="down"
		if shown.state=="thrown":
			var holder:=int(shown.combat.thrower)
			if holder>=0 and holder<scene.fighters.size():
				var target: Dictionary=scene.fighters[holder].frame().get("target",{})
				var progress: Array=target.get("progress",[])
				# 仅显式落地且释放轨迹已走完；不把仍在承重/空中的受方持成倒地。
				landed=bool(target.get("ground",false)) and str(target.get("mode",""))=="release" and progress.size()==2 and int(progress[1])>0 and int(progress[0])>=int(progress[1])
		if i!=source.winner and int(shown.stats.hp)<=0 and landed and shown.height==0 and shown.move_id.is_empty():
			grounded[i]={"fighter":shown.definition.id,"key":shown.animation_key(),"sprite":int(shown.frame().sprite),"x":shown.x,"facing":shown.facing}
	active=false
	scene.events.clear()
	scene.projectiles.clear()
	scene.fighters=[fighter_copy(fighter_record(source.fighters[0])),fighter_copy(fighter_record(source.fighters[1]))]
	for i in grounded:
		var result:=scene.fighters[i]
		var pose: Dictionary=grounded[i]
		if result.state=="defeat" and result.definition.id==str(pose.fighter):
			result.motion.ko_grounded_pose={"key":pose.key,"sprite":pose.sprite}
			# 保留可见副本刚落地的位置/朝向，不回退到末击前的根点。
			result.x=int(pose.x);result.height=0;result.vx=0;result.vy=0;result.facing=int(pose.facing)
	scene.finished=true;scene.winner=source.winner;scene.tick+=1
	projectile_rows.clear()
