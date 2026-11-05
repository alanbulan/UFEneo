class_name UfeHitResolver
extends RefCounted
const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")
const PUSHBACK_BOUNDARY_REVISION := 1
const THROW_TARGET_RULE_REVISION := 1
static func world_box(f: UfeFighter, box: Array) -> Rect2i:
	return Rect2i(f.x + int(box[0]) if f.facing > 0 else f.x - int(box[0]) - int(box[2]),
		f.height + int(box[1]), int(box[2]), int(box[3]))

static func can_hit(attacker: UfeFighter, target: UfeFighter) -> bool:
	if UfeMeleeHitGroups.spent(attacker) or invulnerable(target) or target.state in ["down", "thrown", "defeat", "timeout"]:
		return false
	if not attacker.move_id.is_empty() and str(attacker.definition.moves[attacker.move_id].kind)=="throw":
		var throw_move: Dictionary=attacker.definition.moves[attacker.move_id]
		var air_throw: bool=bool(throw_move.get("throw_target_air",attacker.move_id=="air_throw"))
		if air_throw!=(target.height>0):return false
		if not UfeThrowResolver.can_capture(target,throw_move):return false
		if not CurrentCapture.eligible(attacker,target,throw_move):return false
	if not attacker.move_id.is_empty():
		var move: Dictionary=attacker.definition.moves[attacker.move_id]
		if move.has("hit_groups"):move=UfeMeleeHitGroups.contact_move(attacker,move)
		if UfeFrameGuard.melee_point(attacker,target,move)!=null:return true
	for hit in attacker.frame().hitboxes:
		for hurt in target.frame().hurtboxes:
			if world_box(attacker, hit).intersects(world_box(target, hurt)):
				return true
	return false

static func invulnerable(f: UfeFighter) -> bool:
	return f.state in ["transform", "form_entry", "captured"] or int(f.combat.invulnerable)>0 or bool(f.frame().get("invulnerable",false))

static func is_blocked(target: UfeFighter, move: Dictionary, defending: bool) -> bool:
	var crouching := target.state in ["crouch","crouch_start","crouch_guard","crouch_blockstun"]
	return defending and not bool(move.unblockable) and (str(move.level) != "low" or crouching) and (str(move.level) != "overhead" or not crouching)

static func contact_point(a: UfeFighter,b: UfeFighter) -> Vector2i:
	if not a.move_id.is_empty():
		var move: Dictionary=a.definition.moves[a.move_id]
		if move.has("hit_groups"):move=UfeMeleeHitGroups.contact_move(a,move)
		var screen: Variant=UfeFrameGuard.melee_point(a,b,move)
		if screen!=null:return screen
	for hit in a.frame().hitboxes:
		for hurt in b.frame().hurtboxes:
			var area:=world_box(a,hit).intersection(world_box(b,hurt))
			if area.has_area():return area.get_center()
	return Vector2i(b.x,b.height+60)

static func apply(a: UfeFighter, b: UfeFighter, move: Dictionary, defending: bool, rules: UfeRuleSet) -> String:
	a.combat.connected = true
	# 破防被真实命中/投中终止也属于结束，不能绕过自然收势的最低恢复，
	# 否则持续远程可让受方永远以0体再次破防。
	if b.state=="guardbreak":UfeStaminaRules.finish_guard_break(b)
	if str(move.kind)=="throw":
		CurrentCapture.remember(b,move)
		a.combat.confirmed=true
		b.clear_move()
		b.facing=-a.facing
		b.enter("thrown")
		return "hit" # 抓中不扣血；拆投窗口结束后，在落地冲击帧结算一次伤害。
	var crouching := b.state in ["crouch","crouch_start","crouch_guard","crouch_blockstun"]
	var airborne := b.height>0
	var blocked := is_blocked(b,move,defending)
	if blocked:
		b.clear_move()
		b.enter("crouch_blockstun" if crouching else "blockstun", int(move.blockstun))
		UfeStaminaRules.spend(b, int(move.damage))
		b.stats.hp=maxi(0,int(b.stats.hp)-int(move.get("chip_damage",0)))
		if b.stats.stamina == 0: b.enter("guardbreak", 35)
		return "block"
	a.combat.confirmed = true
	var impact_height := 0
	for box in a.frame().hitboxes: impact_height=maxi(impact_height,a.height-b.height+int(box[1])+int(box[3])/2)
	if str(move.kind)=="projectile": impact_height=int(move.get("projectile",{}).get("spawn",[0,75])[1])+a.height-b.height
	b.motion.hit_pose = "hit_air" if airborne else "hit_crouch" if crouching else "hit_high" if impact_height>=100 else "hit_mid"
	# 素材为朝右、从右侧受击；记录攻击来向，防止背面受击仍向攻击者倾倒。
	b.facing = 1 if a.x>=b.x else -1
	b.clear_move()
	b.stats.hp = maxi(0, int(b.stats.hp) - int(move.damage) * int(a.combat.power))
	b.stats.stun = mini(rules.stun_threshold, int(b.stats.stun) + int(move.stun))
	a.stats.energy = mini(3000, int(a.stats.energy) + 90)
	b.stats.energy = mini(3000, int(b.stats.energy) + 40)
	a.combat.combo = int(a.combat.combo) + 1
	a.combat.combo_ticks = 90
	b.x = clampi(b.x + a.facing * int(move.pushback), 28, 1252)
	b.enter("hit", int(move.hitstun))
	if bool(move.launch):
		b.vy = 18
		b.vx = a.facing * 2
		b.enter("launch")
		# 同tick互击的后结算不能给已受击的攻击者重新授予追击。
		if a.chase_allowed(): a.motion.chase_window = 24
	elif bool(move.bounce) and b.height > 0 and not b.combat.bounced:
		b.vy = -18
		b.combat.bounced = true
		b.motion.bounce_velocity = int(move.get("bounce_velocity",11))
		b.enter("bounce")
		a.motion.bounce_followup = true
	elif bool(move.knockdown):
		if airborne:
			b.vx=a.facing*2
			b.vy=mini(b.vy,-6)
			b.enter("launch")
		else: b.enter("down", 35)
	elif int(b.stats.stun) >= rules.stun_threshold:
		b.enter("stun", 60)
		b.stats.stun = 0
	return "hit"
