class_name UfeProjectileResolver
extends RefCounted
const BEAM_REFLECTION_RULE_REVISION := 1
## 飞行物与护盾/反射/吸收共用一套整数判定，不依赖角色 ID。
static func spawn(sim: UfeMatchDirector, index: int, shot: Dictionary, move_id: String) -> void:
	var f := sim.fighters[index]
	var at: Array = shot.get("spawn",[45,75])
	sim.projectiles.append({"owner":index,"source_owner":index,"x":f.x+f.facing*int(at[0]),"height":f.height+int(at[1]),
		"facing":f.facing,"life":int(shot.get("life",90)),"age":0,"speed":int(shot.get("speed",8)),"vy":int(shot.get("vy",0)),
		"box":shot.get("box",[-12,-10,24,20]),"effect":shot.get("effect","pulse"),"move":move_id,"power":f.combat.power,
		"ground_height":int(shot.get("ground_height",-1)),"color":shot.get("color",[1,1,1,1])})
	var p: Dictionary=sim.projectiles.back()
	if bool(shot.get("capture",false)) and f.motion.has("capture"):
		p.capture=true; p.capture_token=int(f.motion.capture.token)
		p.life=mini(int(p.life),int(f.definition.moves[move_id].capture.flight_max_ticks))
	if bool(f.battle_form.get("enabled",false)) and str(f.battle_form.get("mode",""))=="definition":
		p.source_move=f.definition.moves[move_id].duplicate(true)
	for key in ["beam","length","thickness","anchor","level","frame_boxes","visual_scale","impact_linger","integer_path","return_ticks","return_anchor","locked_moves","max_hits","hit_interval","trail_effect"]:
		if shot.has(key):p[key]=shot[key]
	# 仅显式声明的持续束携带独立逐帧原点；旧招式的飞行物字典逐位不变。
	if shot.has("origin_by_frame"):p.origin_by_frame=shot.origin_by_frame.duplicate(true)
	if shot.has("hit_overrides"):p.hit_overrides=shot.hit_overrides.duplicate(true)
	# 显式逐相多框与像素特效共用age/4时钟；旧弹体不增加任何快照字段。
	if shot.has("frame_hitboxes"):p.frame_hitboxes=shot.frame_hitboxes.duplicate(true)
	if shot.has("clip_below_ground"):p.clip_below_ground=shot.clip_below_ground
	# 图像最低像素相对尾根的整数下缘；不声明的旧弹体不新增快照字段。
	if shot.has("expire_below_height"):p.expire_below_height=int(shot.expire_below_height)
	# 独立返航物协议完全按招式显式声明；不扩充旧字典默认快照。
	for key in ["weapon_id","owner_interrupt_policy","return_effect","return_sound","pair_trail_effect","pair_trail_peer_id","return_not_before_tick"]:
		if shot.has(key):p[key]=shot[key]
	if shot.has("return_anchor_by_tick"):p.return_anchor_by_tick=shot.return_anchor_by_tick.duplicate(true)
	if p.has("integer_path"):UfeReturningProjectile.initialize(p)

static func beam_origin(emitter: UfeFighter, projectile: Dictionary) -> Array:
	if projectile.has("origin_by_frame"):
		return projectile.origin_by_frame.get(str(emitter.move_tick),projectile.anchor)
	return emitter.frame().get("beam_origin",projectile.anchor)

static func world_hitboxes(projectile: Dictionary) -> Array:
	var boxes: Array=[]
	if not projectile.has("frame_hitboxes"):
		boxes.append(UfeMatchDirector.projectile_box(projectile))
	else:
		var phases: Array=projectile.frame_hitboxes
		var phase: Array=phases[(int(projectile.age)/4)%phases.size()]
		for local in phase:
			var x:=int(projectile.x)+int(local[0]) if int(projectile.facing)>0 else int(projectile.x)-int(local[0])-int(local[2])
			boxes.append(Rect2i(x,int(projectile.height)+int(local[1]),int(local[2]),int(local[3])))
	if bool(projectile.get("clip_below_ground",false)):
		var clipped: Array=[]
		for box in boxes:
			var bottom:=maxi(0,box.position.y)
			if box.end.y>bottom:clipped.append(Rect2i(box.position.x,bottom,box.size.x,box.end.y-bottom))
		return clipped
	return boxes

static func contact_point(projectile: Dictionary, target: Rect2i) -> Variant:
	# 判定与F1读取同一组有效世界框；有序取首个实际交集。
	for box in world_hitboxes(projectile):
		if box.intersects(target):return box.intersection(target).get_center()
	return null

static func emit(sim: UfeMatchDirector, index: int) -> void:
	var f := sim.fighters[index]
	var frame := f.frame()
	for shot in frame.get("shots",[]): spawn(sim,index,shot,f.move_id)
	if frame.get("counter_shot",{}).is_empty() or int(f.combat.get("absorbed",0))==0: return
	spawn(sim,index,frame.counter_shot,f.move_id)
	f.combat.absorbed=0
	f.combat.confirmed=true
	sim.events.append({"kind":"absorb_counter","player":index,"move":f.move_id})

static func advance(sim: UfeMatchDirector, contacts: Array) -> void:
	for p in sim.projectiles:
		if bool(p.get("capture",false)) and not UfeCaptureResolver.projectile_valid(sim,p):
			p.life=0
			continue
		var returning: bool=p.has("integer_path")
		if returning:UfeReturningProjectile.advance(sim,p)
		if bool(p.get("beam",false)):
			# 攻击归属可反转，持续发射许可仍属于原发射者。
			var emitter:=sim.fighters[int(p.get("source_owner",p.owner))]
			if emitter.move_id!=str(p.move):
				p.life=0
				continue
			# 反射束保留已登记的屏外缘原点；双反射也不重新粘回人物。
			if not bool(p.get("beam_reflected",false)):
				var anchor: Array=beam_origin(emitter,p)
				p.x=emitter.x+emitter.facing*int(anchor[0])
				p.height=emitter.height+int(anchor[1])
		if not returning:
			p.x=int(p.x)+int(p.facing)*int(p.speed)
			p.height=int(p.height)+int(p.vy)
		if int(p.ground_height)>=0 and int(p.height)<=int(p.ground_height):
			p.height=int(p.ground_height)
			p.vy=0
		if not returning:
			p.life=int(p.life)-1
			p.age=int(p.age)+1
		if p.has("frame_boxes"):p.box=p.frame_boxes[(int(p.age)/4)%p.frame_boxes.size()]
		# 先移动/粘地，再清除越过可见地线的弹体，禁止同tick继续接触。
		if int(p.height)<int(p.get("expire_below_height",0)):p.life=0
		if int(p.life)<=0:
			if bool(p.get("capture",false)):UfeCaptureResolver.fail(sim,int(p.source_owner),"projectile_expired")
			continue
		if returning and not UfeReturningProjectile.can_contact(p):continue
		if bool(p.get("connected",false)):continue # 已命中的余焰/光束只保留画面，不再交互或二次伤害。
		var target_index := 1-int(p.owner)
		var target := sim.fighters[target_index]
		# 被捕获者失去普通交互，不能从受方姿势数据意外继承反射/吸收能力。
		if target.state=="captured":continue
		var frame := target.frame()
		var mode := str(frame.get("projectile_guard",""))
		var guard: Array = frame.get("guard_box",[])
		var front := (int(p.x)-target.x)*target.facing>=-8 and int(p.facing)*target.facing<0
		var guardable:=true
		if bool(frame.get("guard_respects_unblockable",false)):
			var source:=sim.fighters[int(p.get("source_owner",p.owner))]
			var source_move: Dictionary=p.get("source_move",source.definition.moves.get(str(p.move),{}))
			guardable=not bool(source_move.get("unblockable",false))
		var guard_point: Variant=null
		if guardable and not mode.is_empty() and guard.size()==4 and front:
			guard_point=contact_point(p,UfeHitResolver.world_box(target,guard))
		if guard_point!=null:
			var point: Vector2i=guard_point
			if bool(p.get("capture",false)):
				p.life=0
				if mode=="absorb":
					target.combat.absorbed=int(target.combat.get("absorbed",0))+1
					target.combat.confirmed=true
				UfeCaptureResolver.fail(sim,int(p.source_owner),"projectile_"+mode)
				var event_kind := "projectile_reflect" if mode=="reflect" else "projectile_absorb" if mode=="absorb" else "projectile_block"
				sim.events.append(UfeFrameGuard.decorate({"kind":event_kind,"player":target_index,"move":target.move_id,"capture_intercepted":true,"owner_transferred":false},frame,point,target.facing))
				continue
			if returning:
				p.forced_return=true
				var guard_event: Dictionary={"kind":"projectile_block","player":target_index,"move":target.move_id}
				if p.has("weapon_id"):guard_event.weapon_id=str(p.weapon_id)
				sim.events.append(UfeFrameGuard.decorate(guard_event,frame,point,target.facing))
				continue # 实体武器被挡后念力收回，不复制或消灭角色的唯一武器。
			if mode=="reflect":
				p.owner=target_index
				p.facing=target.facing
				p.x=target.x+target.facing*(int(guard[0])+int(guard[2])+2)
				if bool(p.get("beam",false)):p.beam_reflected=true
				sim.events.append(UfeFrameGuard.decorate({"kind":"projectile_reflect","player":target_index,"move":target.move_id},frame,point,target.facing))
			else:
				p.life=0
				if mode=="absorb":
					target.combat.absorbed=int(target.combat.get("absorbed",0))+1
					target.combat.confirmed=true
				sim.events.append(UfeFrameGuard.decorate({"kind":"projectile_absorb" if mode=="absorb" else "projectile_block","player":target_index,"move":target.move_id},frame,point,target.facing))
			continue
		if UfeHitResolver.invulnerable(target) or target.state in ["down","thrown","defeat","timeout"]:continue
		if bool(p.get("capture",false)) and not UfeCaptureResolver.eligible(target,sim.fighters[int(p.source_owner)].definition.moves[str(p.move)].capture):continue
		for hurt in frame.hurtboxes:
			var hit_point: Variant=contact_point(p,UfeHitResolver.world_box(target,hurt))
			if hit_point!=null:
				var source := sim.fighters[int(p.get("source_owner",p.owner))]
				var point: Vector2i=hit_point
				if returning or not bool(p.get("connected",false)):
					var contact_move: Dictionary=p.get("source_move",source.definition.moves.get(str(p.move),{})).duplicate(true)
					# 分拍弹体仅能覆盖命中参数；没有声明时保留全部既有行为。
					for key in ["damage","chip_damage","knockdown","pushback","stun"]:
						if p.get("hit_overrides",{}).has(key):contact_move[key]=p.hit_overrides[key]
					var contact: Dictionary={"owner":int(p.owner),"move":contact_move,"projectile":true,"power":int(p.power),"point":point,"facing":int(p.facing)}
					if p.has("weapon_id"):contact.weapon_id=str(p.weapon_id)
					if bool(p.get("capture",false)):
						contact.capture=true; contact.capture_token=int(p.capture_token)
					contacts.append(contact)
					if returning:UfeReturningProjectile.contact(p)
					else:p.connected=true
				if not returning and not bool(p.get("beam",false)):
					p.life=int(p.get("impact_linger",0))
					p.speed=0
				break
	sim.projectiles=sim.projectiles.filter(func(p):return int(p.life)>0)
