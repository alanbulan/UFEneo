class_name UfeReturningProjectile
extends RefCounted
## 数据给出逐tick整数折线；回程每tick追向实际掌点，包含在projectiles的回放哈希中。
static func blocks_move(sim: UfeMatchDirector, owner: UfeFighter, move_id: String) -> bool:
	var index := sim.fighters.find(owner)
	for p in sim.projectiles:
		if int(p.owner)==index and int(p.life)>0 and move_id in p.get("locked_moves",[]):return true
	return false

# 仅显式声明的返航物启用；未声明的旧弹体不新增任何字段或事件。
static func clear_explicit(sim: UfeMatchDirector, p: Dictionary, reason: String) -> void:
	if int(p.life)<=0:return
	p.life=0
	var event: Dictionary={"kind":"weapon_clear","player":int(p.owner),"move":str(p.move),"reason":reason,"x":int(p.x),"height":int(p.height)}
	if p.has("weapon_id"):event.weapon_id=str(p.weapon_id)
	sim.events.append(event)

static func cleanup_explicit(sim: UfeMatchDirector) -> void:
	var changed: bool=false
	for p in sim.projectiles:
		if str(p.get("owner_interrupt_policy",""))!="clear" or int(p.life)<=0:continue
		var owner_index: int=int(p.owner)
		var reason: String=""
		if sim.finished:reason="round_end"
		elif owner_index<0 or owner_index>=sim.fighters.size():reason="owner_removed"
		else:
			var owner: UfeFighter=sim.fighters[owner_index]
			if owner.move_id!=str(p.move):reason="owner_move_cleared"
			elif owner.state in ["hit","launch","bounce","down","thrown","captured","guardbreak","stun","defeat","victory","timeout","transform","form_entry"]:reason="owner_interrupted"
		if reason.is_empty():continue
		clear_explicit(sim,p,reason)
		changed=true
	if changed:sim.projectiles=sim.projectiles.filter(func(p):return int(p.life)>0)

static func initialize(p: Dictionary) -> void:
	p.origin_x=int(p.x)
	p.origin_height=int(p.height)
	p.hits=0
	p.last_hit_age=-999
	p.return_age=0
	p.trail_points=[]

static func advance(sim: UfeMatchDirector, p: Dictionary) -> void:
	p.age=int(p.age)+1
	var path: Array=p.integer_path
	if int(p.age)<=path.size() and not bool(p.get("forced_return",false)):
		var offset: Array=path[int(p.age)-1]
		p.x=int(p.origin_x)+int(p.facing)*int(offset[0])
		p.height=maxi(0,int(p.origin_height)+int(offset[1]))
	else:
		if int(p.return_age)==0:
			p.return_x=int(p.x)
			p.return_height=int(p.height)
		p.return_age=int(p.return_age)+1
		var owner:=sim.fighters[int(p.owner)]
		var duration:=int(p.get("return_ticks",6))
		# 回程瞄准预告的接镖姿势；最终tick再核实当帧实际掌点，避免操控手下摆造成尾段折角。
		var anchor: Array=p.get("return_anchor",[42,100])
		if p.has("return_anchor_by_tick"):
			var mapped: Variant=p.return_anchor_by_tick.get(str(owner.move_tick),null)
			if not mapped is Array or mapped.size()!=2:
				clear_explicit(sim,p,"missing_current_return_anchor")
				return
			anchor=mapped
		elif int(p.return_age)>=duration:anchor=owner.frame().get("weapon_return_anchor",anchor)
		var left:=maxi(0,duration-int(p.return_age))
		# 两个分量都使用整数除法；没有浮点、系统时间、随机数或渲染依赖。
		p.x=(int(p.return_x)*left+(owner.x+owner.facing*int(anchor[0]))*(duration-left))/duration
		p.height=(int(p.return_height)*left+(owner.height+int(anchor[1]))*(duration-left))/duration
		# 显式最早接回相之前，保留同一实体在当帧腕点；回程/等待始终无伤。
		# 旧数据无此字段，结束tick、字典及事件保持原样。
		if left==0 and (not p.has("return_not_before_tick") or owner.move_tick>=int(p.return_not_before_tick)):
			p.life=0
			var event: Dictionary={"kind":"weapon_return","player":int(p.owner),"move":str(p.move),"x":int(p.x),"height":int(p.height)}
			if p.has("weapon_id"):event.weapon_id=str(p.weapon_id)
			if p.has("return_effect"):
				event.effect=str(p.return_effect)
				event.effect_facing=owner.facing
			if p.has("return_sound"):event.sound=str(p.return_sound)
			sim.events.append(event)
	p.trail_points.append([int(p.x),int(p.height)])
	if p.trail_points.size()>4:p.trail_points.pop_front()
	p.life=int(p.life)-1 if int(p.life)>0 else 0

static func can_contact(p: Dictionary) -> bool:
	return int(p.return_age)==0 and not bool(p.get("forced_return",false)) and int(p.hits)<int(p.get("max_hits",3)) and int(p.age)-int(p.last_hit_age)>=int(p.get("hit_interval",4))

static func contact(p: Dictionary) -> void:
	p.hits=int(p.hits)+1
	p.last_hit_age=int(p.age)
