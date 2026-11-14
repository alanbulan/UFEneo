class_name UfeHitResolver
extends RefCounted
const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")
const PUSHBACK_BOUNDARY_REVISION := 2
const THROW_TARGET_RULE_REVISION := 1
const PROJECTILE_DIRECTION_RULE_REVISION := 2
const PROJECTILE_MOVE_ISOLATION_RULE_REVISION := 1
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
	# 免费形态切换是主动换装，不是必杀演出：不给无敌，避免靠按E白嫖闪避。
	var free_switch := f.state == "transform" and bool(f.battle_form.get("free_switch", false))
	return (not free_switch and f.state in ["transform", "form_entry"]) or f.state == "captured" \
		or int(f.combat.invulnerable)>0 or bool(f.frame().get("invulnerable",false))

static func is_blocked(target: UfeFighter, move: Dictionary, defending: bool) -> bool:
	var crouching := target.state in ["crouch","crouch_start","crouch_guard","crouch_blockstun","crouch_turn"]
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

static func apply(a: UfeFighter, b: UfeFighter, move: Dictionary, defending: bool, rules: UfeRuleSet, projectile_facing: int = 0) -> String:
	# 非零来向只由真实离手弹体接触传入；它的去重由弹体自身负责。
	# 旧弹可能在下一次同名招式起手时到达，不能消耗射手当前招式的接触/发射许可。
	# 命中confirmed仍沿既有规则写入，不扩大或收窄命中取消。
	if projectile_facing==0:a.combat.connected = true
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
	var crouching := b.state in ["crouch","crouch_start","crouch_guard","crouch_blockstun","crouch_turn"]
	var airborne := b.height>0
	var blocked := is_blocked(b,move,defending)
	var impact_facing := projectile_facing if projectile_facing!=0 else a.facing
	if blocked:
		# confirmed 仍只表示打中，追击跳和命中取消沿用它。被防另记 blocked，取消窗口两边都认。
		a.combat.blocked = true
		b.clear_move()
		b.enter("crouch_blockstun" if crouching else "blockstun", int(move.blockstun))
		UfeStaminaRules.spend(b, UfeStaminaRules.block_cost(int(move.damage)))
		var chip := _scaled_damage(a, int(move.get("chip_damage", 0)))
		b.stats.hp=maxi(0,int(b.stats.hp)-chip)
		if b.stats.stamina == 0: b.enter("guardbreak", 35)
		var block_speed := UfeFeelRules.block_push(int(move.get("pushback", 0)))
		if block_speed > 0:
			b.motion.push_vx = slide(b, a, impact_facing * block_speed)
		return "block"
	a.combat.confirmed = true
	var impact_height := 0
	@warning_ignore("integer_division") # 命中框半高取整，结果为整数像素。
	for box in a.frame().hitboxes: impact_height=maxi(impact_height,a.height-b.height+int(box[1])+int(box[3])/2)
	if str(move.kind)=="projectile": impact_height=int(move.get("projectile",{}).get("spawn",[0,75])[1])+a.height-b.height
	b.motion.hit_pose = "hit_air" if airborne else "hit_crouch" if crouching else "hit_high" if impact_height>=100 else "hit_mid"
	# 素材为朝右、从右侧受击；记录攻击来向，防止背面受击仍向攻击者倾倒。
	# 弹体离手后可与射手朝向分离；0保留近战原有来向判定。
	b.facing = -projectile_facing if projectile_facing!=0 else (1 if a.x>=b.x else -1)
	b.clear_move()
	b.stats.hp = maxi(0, int(b.stats.hp) - _scaled_damage(a, int(move.damage) * int(a.combat.power)))
	# 眩晕免疫期内不再累积，避免连续命中把对手永久锁在眩晕里。
	if int(b.stats.get("stun_immune",0)) <= 0:
		b.stats.stun = mini(rules.stun_threshold, int(b.stats.stun) + int(move.stun))
	# 减速只改受方移动速度，不改招式时序；未过期的减速取更强档并延长到较长剩余。
	if move.has("chill"):
		var chill: Dictionary = move.chill
		var chilled := int(b.stats.get("chill_ticks", 0)) > 0
		b.stats.chill_ticks = maxi(int(b.stats.get("chill_ticks", 0)), int(chill.ticks))
		b.stats.chill_percent = mini(int(b.stats.get("chill_percent", 100)), int(chill.speed_percent)) if chilled else int(chill.speed_percent)
	a.stats.energy = mini(3000, int(a.stats.energy) + 90)
	b.stats.energy = mini(3000, int(b.stats.energy) + 40)
	a.combat.combo = int(a.combat.combo) + 1
	a.combat.combo_ticks = 90
	var hit_speed := int(move.get("pushback", 0))
	if hit_speed > 0:
		b.motion.push_vx = slide(b, a, impact_facing * hit_speed)
	b.enter("hit", int(move.hitstun))
	if bool(move.launch):
		b.vy = 18
		b.vx = impact_facing * 2
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
			b.vx=impact_facing*2
			b.vy=mini(b.vy,-6)
			b.enter("launch")
		else: b.enter("down", 35)
	elif int(b.stats.stun) >= rules.stun_threshold:
		b.enter("stun", 60)
		b.stats.stun = 0
		b.stats.stun_immune = 60 + int(rules.stun_immunity)
	return "hit"

## 本 tick 走一步，并把衰减后的速度交还调用方。贴墙时走不完的像素转给另一方。
static func slide(body: UfeFighter, other: UfeFighter, velocity: int) -> int:
	if velocity == 0:
		return 0
	var proposed := body.x + velocity
	var clamped := clampi(proposed, 28, 1252)
	var leftover := proposed - clamped
	body.x = clamped
	if leftover != 0 and other != null:
		other.x = clampi(other.x - leftover, 28, 1252)
	if absi(velocity) <= 1:
		return 0
	return velocity - signi(velocity)

static func _scaled_damage(attacker: UfeFighter, amount: int) -> int:
	if amount <= 0:
		return 0
	@warning_ignore("integer_division") # 连段补正取整，结果为整数伤害。
	var scaled := amount * UfeFeelRules.scale_percent(int(attacker.combat.combo) + 1) / 100
	return maxi(1, scaled)
