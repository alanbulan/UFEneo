class_name UfeThrowResolver
extends RefCounted
const HoldPoints = preload("res://core/combat/throw_hold_points.gd")
const RootOffsets = preload("res://core/combat/throw_root_offsets.gd")
const ROOT_OVERRIDE_RULE_REVISION = RootOffsets.REVISION
## 全部抓点为角色本地整数坐标(x,离根点高度)，由招式数据与被投姿势数据提供。
static func can_capture(victim: UfeFighter, move: Dictionary) -> bool:
	for frame in move.frames:
		var target: Dictionary=frame.get("target",{})
		if target.has("root_overrides") and not RootOffsets.valid(target.root_overrides):return false
	return HoldPoints.can_capture(victim,move)

static func abort_hold(sim: UfeMatchDirector, owner: int, victim: UfeFighter, reason: String="missing_hold_point") -> void:
	var actor:=sim.fighters[owner]
	# 正常数据已经过捕获前预检；仅防运行中损坏，保留最后有效位置及已付费用。
	sim.events.append({"kind":"throw_hold_abort","player":owner,"move":actor.move_id,"reason":reason})
	actor.clear_move()
	actor.combat.buffer=""
	actor.combat.buffer_ticks=0
	actor.enter("air" if actor.height>0 else "idle")
	victim.combat.thrower=-1
	victim.vx=0
	victim.vy=0
	victim.enter("down",35)

static func tech(sim: UfeMatchDirector, owner: int) -> void:
	var a := sim.fighters[owner]
	var b := sim.fighters[1-owner]
	var captured := b.state=="thrown"
	var origin_a := int(a.motion.get("throw_origin_height",a.height)) if captured else a.height
	var origin_b := int(b.motion.get("throw_origin_height",b.height)) if captured else b.height
	for f in [a,b]:
		f.clear_move()
		f.combat.buffer=""
		f.combat.buffer_ticks=0
		f.combat.thrower=-1
		f.vx=0
		f.height=origin_a if f==a else origin_b
		f.vy=6 if f.height>0 else 0
		f.combat.invulnerable=15
		f.motion.tech_direction=-a.facing if f==a else a.facing
		f.enter("throw_tech",15)
	sim.hitstop=0
	sim.events.append({"kind":"throw_tech","player":owner})

static func input_step(sim: UfeMatchDirector, commands: Array) -> void:
	# 捕获后的第1/2/3个真实tick均可拆，包含命中停顿，不丢掉停顿中的新按键。
	for i in range(2):
		var b := sim.fighters[i]
		if b.state!="thrown":continue
		b.combat.throw_age=int(b.combat.throw_age)+1
		if int(b.combat.throw_age)<=3 and int(commands[i].pressed)&UfeInputFrame.THROW:
			tech(sim,int(b.combat.thrower))
			return

static func begin(sim: UfeMatchDirector, owner: int, move: Dictionary) -> void:
	var a := sim.fighters[owner]
	var b := sim.fighters[1-owner]
	b.combat.thrower=owner
	b.combat.throw_age=0
	b.combat.throw_damage_done=false
	b.motion.throw_move=str(move.id)
	a.motion.throw_origin_height=a.height
	b.motion.throw_origin_height=b.height
	b.motion.throw_released=false
	a.vx=0
	a.vy=0
	b.vx=0
	b.vy=0

static func pose_frame(f: UfeFighter, key: String, sprite: int) -> Dictionary:
	var frames: Array=f.definition.state_frames.get(key,[])
	return frames[clampi(sprite,0,frames.size()-1)] if not frames.is_empty() else {}

static func separated_distance(actor: Dictionary, actor_facing: int, victim: Dictionary, victim_facing: int, side: int) -> int:
	# 只比较同一高度带的实体受击框；空中的角、手臂不扩大地面落点。
	var distance:=0
	for aa in actor.get("hurtboxes",[]):
		for bb in victim.get("hurtboxes",[]):
			if int(aa[1])+int(aa[3])<=int(bb[1]) or int(bb[1])+int(bb[3])<=int(aa[1]):continue
			var al:=int(aa[0]) if actor_facing>0 else -int(aa[0])-int(aa[2])
			var bl:=int(bb[0]) if victim_facing>0 else -int(bb[0])-int(bb[2])
			var required:=al+int(aa[2])-bl+2 if side>0 else bl+int(bb[2])-al+2
			distance=maxi(distance,required)
	return distance

static func unique_postures(frames: Array) -> Array:
	var poses: Array=[]
	var boxes: Array=[]
	for frame in frames:
		var hurt: Array=frame.get("hurtboxes",[])
		if not boxes.has(hurt):
			boxes.append(hurt)
			poses.append(frame)
	return poses

static func landing_offset(a: UfeFighter, b: UfeFighter, authored: int) -> int:
	# 整数帧数据决定落点，不读取纹理或表现层。保留作者落点，只向外补足。
	var side:=1 if authored>=0 else -1
	var distance:=absi(authored)
	var landings: Array=[]
	for frame in a.definition.moves[a.move_id].frames:
		var target: Dictionary=frame.get("target",{})
		if not bool(target.get("impact",false)):continue
		var victim:=pose_frame(b,str(target.pose),int(target.get("sprite",0)))
		var facing:=int(target.get("facing",-1))
		distance=maxi(distance,separated_distance(frame,1,victim,facing,side))
		landings.append(frame)
	# 撞地后的收势、自动转身和整段倒地仍须留出同样的空间。
	# 朝向在此均相对投出时的朝向；受方倒地期间不会自动转身。
	var down_poses:=unique_postures(b.definition.state_frames.get("down",[]))
	for frame in unique_postures(landings):
		for down in down_poses:
			distance=maxi(distance,separated_distance(frame,1,down,-1,side))
	for key in ["idle","turn"]:
		for frame in unique_postures(a.definition.state_frames.get(key,[])):
			for down in down_poses:
				distance=maxi(distance,separated_distance(frame,side,down,-1,side))
	return distance*side

static func same_hold_phase(frame: Dictionary, target: Dictionary) -> bool:
	var other: Dictionary=frame.get("target",{})
	return str(other.get("mode",""))=="hold" and str(other.get("pose",""))==str(target.get("pose","")) and int(other.get("sprite",0))==int(target.get("sprite",0))

static func floor_safe_hold_sprite(a: UfeFighter, b: UfeFighter, target: Dictionary, preferred: int, fallback: int) -> int:
	var poses: Array=b.definition.state_frames.get(str(target.get("pose","")),[])
	var choices: Array=poses[fallback].get("throw_hold_floor_variants",[])
	# 只有角色自身显式登记的姿势参与；没有登记的旧角色逐帧保持原编号。
	if choices.is_empty():return preferred
	var offset: Array=RootOffsets.offset(b,target)
	if offset.is_empty():return preferred # sync在改姿势前拒绝非法覆盖。
	var available:=a.height+int(target.grip[1])+int(offset[1])
	for candidate in [preferred]+choices:
		var index:=int(candidate)
		if index<0 or index>=poses.size():continue
		var pose: Dictionary=poses[index]
		var point: Array=pose.get("grab_points",{}).get(str(target.get("grab_point","waist")),[])
		if target.has("hold_point_overrides"):point=HoldPoints.point(b,target,pose)
		var boxes: Array=pose.get("hurtboxes",[])
		if point.size()!=2 or boxes.is_empty():continue
		var bottom:=int(boxes[0][1])
		for box in boxes:bottom=mini(bottom,int(box[1]))
		if available-int(point[1])+bottom>=0:return index
	# 数据未提供能放下的姿势时保留原相，交资源检查报错，不抬高抓点或改落地轨迹。
	return preferred

static func victim_sprite(a: UfeFighter, b: UfeFighter, target: Dictionary) -> int:
	var fallback:=int(target.get("sprite",0))
	var poses: Array=b.definition.state_frames.get(str(target.get("pose","")),[])
	if str(target.get("mode",""))!="hold" or fallback<0 or fallback>=poses.size():return fallback
	# 角色可给自己的被抓姿势登记细分。默认无此字段，旧角色保持原姿势编号。
	var variants: Array=poses[fallback].get("throw_hold_variants",[])
	var preferred:=fallback
	if not variants.is_empty():
		var frames: Array=a.definition.moves[a.move_id].frames
		var tick:=clampi(a.move_tick,0,frames.size()-1)
		var first:=tick
		var last:=tick
		while first>0 and same_hold_phase(frames[first-1],target):first-=1
		while last+1<frames.size() and same_hold_phase(frames[last+1],target):last+=1
		var index:=mini(variants.size()-1,(tick-first)*variants.size()/(last-first+1))
		preferred=clampi(int(variants[index]),0,poses.size()-1)
	return floor_safe_hold_sprite(a,b,target,preferred,fallback)

static func sync(sim: UfeMatchDirector) -> void:
	for i in range(2):
		var b := sim.fighters[i]
		if b.state!="thrown":continue
		var owner:=int(b.combat.thrower)
		if owner<0:continue
		var a := sim.fighters[owner]
		if a.move_id.is_empty():
			b.combat.thrower=-1
			b.vx=0
			b.vy=0
			b.enter("down",35)
			continue
		var frame := a.frame()
		if not frame.has("target"):continue
		var target: Dictionary=frame.target
		var offset: Array=RootOffsets.offset(b,target)
		if offset.is_empty():
			abort_hold(sim,owner,b,"invalid_root_override")
			continue
		if str(target.get("mode","root"))=="hold" and target.has("hold_point_overrides") and not can_capture(b,a.definition.moves[a.move_id]):
			abort_hold(sim,owner,b)
			continue
		if frame.has("throw_height"):
			var fraction: Array=frame.throw_height
			a.height=int(a.motion.throw_origin_height)*int(fraction[0])/int(fraction[1])
		b.motion.pose=str(target.pose)
		b.motion.pose_sprite=victim_sprite(a,b,target)
		b.facing=a.facing*int(target.get("facing",-1))
		if str(target.get("mode","root"))=="hold":
			var pose:=b.frame()
			var grabbed: Array
			if target.has("hold_point_overrides"):
				grabbed=HoldPoints.point(b,target,pose)
				if grabbed.is_empty():
					abort_hold(sim,owner,b)
					continue
			else:grabbed=pose.grab_points[str(target.get("grab_point","waist"))]
			var grip: Array=target.grip
			b.x=a.x+a.facing*int(grip[0])-b.facing*int(grabbed[0])+a.facing*int(offset[0])
			b.height=a.height+int(grip[1])-int(grabbed[1])+int(offset[1])
		elif str(target.get("mode","root"))=="release":
			if not bool(b.motion.get("throw_released",false)):
				b.motion.throw_released=true
				b.motion.release_x=(b.x-a.x)*a.facing
				b.motion.release_height=b.height
				b.motion.release_goal_x=landing_offset(a,b,int(offset[0]))
			var progress: Array=target.progress
			var numerator:=int(progress[0])
			var denominator:=int(progress[1])
			b.x=a.x+a.facing*(int(b.motion.release_x)+(int(b.motion.release_goal_x)-int(b.motion.release_x))*numerator/denominator)
			b.height=int(b.motion.release_height)*(denominator-numerator)/denominator+int(offset[1])*numerator/denominator
		else:
			b.x=a.x+a.facing*int(offset[0])
			b.height=int(offset[1])+(0 if bool(target.get("ground",false)) else a.height)
		# 靠墙时整体平移配对，不能单独夹住受投者而断开抓点。
		var left:=mini(a.x,b.x)
		var right:=maxi(a.x,b.x)
		var shift:=28-left if left<28 else 1252-right if right>1252 else 0
		a.x+=shift
		b.x+=shift
		if bool(target.get("impact",false)) and not bool(b.combat.get("throw_damage_done",false)):
			var move: Dictionary=a.definition.moves[a.move_id]
			b.combat.throw_damage_done=true
			b.stats.hp=maxi(0,int(b.stats.hp)-int(move.damage))
			a.stats.energy=mini(3000,int(a.stats.energy)+90)
			b.stats.energy=mini(3000,int(b.stats.energy)+40)
			a.combat.combo=int(a.combat.combo)+1
			a.combat.combo_ticks=90
			sim.events.append({"kind":"throw_slam","player":owner,"move":a.move_id,"x":b.x,"height":b.height})
			sim.events.append({"kind":"sound","id":"land","player":i})
			sim.hitstop=maxi(sim.hitstop,4)
