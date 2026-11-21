class_name UfeMatchDirector
extends RefCounted
const ContactEvent = preload("res://core/combat/contact_event.gd")
const MOVE_START_RULE_REVISION := UfeMatchFingerprint.MOVE_START_RULE_REVISION
const CHASE_INTERRUPT_RULE_REVISION := UfeMatchFingerprint.CHASE_INTERRUPT_RULE_REVISION
const CROUCH_GUARD_RESUME_RULE_REVISION := UfeMatchFingerprint.CROUCH_GUARD_RESUME_RULE_REVISION
const HIT_CROUCH_GUARD_RESUME_RULE_REVISION := UfeMatchFingerprint.HIT_CROUCH_GUARD_RESUME_RULE_REVISION
var rules: UfeRuleSet
var fighters: Array[UfeFighter] = []
var states: Dictionary
var tick: int = 0
var remaining: int = 5400
var hitstop: int = 0
var finished: bool = false
var winner: int = -1
var events: Array = []
var projectiles: Array = []
var content_fingerprint: String
# 终局清理前只读副本；不加入内容指纹、输入、事件或state_hash。
var terminal_view: Dictionary = {}

func _init(first: UfeFighterDefinition, second: UfeFighterDefinition, rule: UfeRuleSet, registry: Dictionary, battle_forms: Dictionary = {}, start_forms: Dictionary = {}) -> void:
	rules = rule
	states = registry.duplicate()
	_ensure_transform_states()
	remaining = rules.round_ticks
	fighters = [UfeFighter.new(first, 470), UfeFighter.new(second, 750)]
	fighters[1].facing = -1
	var start_data: Array = []
	for i in range(2):
		var start: UfeFighterDefinition = start_forms.get(i)
		if start != null and start.id != fighters[i].definition.id:
			# 选人界面选定的出场形态：定义即出场定义，基础ID留在base_definition供回放/名册复原。
			fighters[i].definition = start
			fighters[i].form_id = start.id
		start_data.append([fighters[i].form_id, fighters[i].definition.simulation_data()])
	var form_rules: Array = []
	for f in fighters:
		f.battle_form = battle_forms.get(f.base_definition.id, {})
		var choices: Variant = f.battle_form.get("choices", {})
		f.battle_form_choices = choices if choices is Dictionary else {}
		form_rules.append(UfeBattleTransform.simulation_data(f.battle_form))
	content_fingerprint = _content_fingerprint(first, second, rule, form_rules, start_data)

func _ensure_transform_states() -> void:
	for required in ["transform", "form_entry", "capturing", "captured"]:
		assert(states.has(required), "缺少必要战斗状态定义：%s" % required)

func _content_fingerprint(first: UfeFighterDefinition, second: UfeFighterDefinition, rule: UfeRuleSet, form_rules: Array, start_data: Array) -> String:
	return UfeMatchFingerprint.compute(first, second, rule, form_rules, start_data)

func command_state(f: UfeFighter) -> String:
	return UfeInputBuffer.command_state(f)

func step(inputs: Array) -> void:
	# Tick contract: cleanup/input → hitstop → actor advance → contact collection → resolution → terminal.
	events.clear()
	UfeCaptureResolver.cleanup(self)
	UfeReturningProjectile.cleanup_explicit(self)
	if finished: return
	tick += 1
	var commands := UfeInputBuffer.resolve_step_commands(fighters, inputs)
	UfeThrowResolver.input_step(self, commands)
	if hitstop > 0:
		hitstop -= 1
		return
	var cinematic_owner: int = -1
	var freeze_opponent: bool = false
	for i in range(2):
		if bool(fighters[i].frame().get("pause_clock", false)):
			cinematic_owner = i
			freeze_opponent = bool(fighters[i].frame().get("freeze_opponent", false))
	if cinematic_owner < 0: remaining -= 1
	for i in range(2):
		if freeze_opponent and i != cinematic_owner: continue
		_advance(i, inputs[i], commands[i])
	_separate()
	# 自然结束/取消/落地清招必须在本tick弹体推进与接触形成前清除显式武器。
	UfeReturningProjectile.cleanup_explicit(self)
	var contacts: Array = []
	for i in range(2):
		var f := fighters[i]
		if f.move_id.is_empty(): continue
		if not freeze_opponent: UfeProjectileResolver.emit_pose(self, i)
		var move: Dictionary = f.definition.moves[f.move_id]
		var frame := f.frame()
		if str(move.kind) == "projectile" and not frame.hitboxes.is_empty() and not f.combat.connected:
			UfeProjectileResolver.spawn(self, i, move.get("projectile", {}), f.move_id)
			f.combat.connected = true
		elif UfeHitResolver.can_hit(f, fighters[1 - i]):
			var contact: Dictionary = {"owner": i, "move": UfeMeleeHitGroups.contact_move(f, move), "projectile": false, "point": UfeHitResolver.contact_point(f, fighters[1 - i])}
			if frame.has("hit_group"): contact.hit_group = int(frame.hit_group)
			if UfeFrameGuard.melee_point(f, fighters[1 - i], contact.move) != null: contact.guard_frame = fighters[1 - i].frame().duplicate(true)
			contacts.append(contact)
	if not freeze_opponent: UfeProjectileResolver.advance(self, contacts)
	_resolve_contacts(contacts, inputs)
	UfeThrowResolver.sync(self)
	if remaining > 0 and (fighters[0].stats.hp <= 0 or fighters[1].stats.hp <= 0):
		_capture_terminal_view()
	UfeCaptureResolver.cleanup(self)
	UfeReturningProjectile.cleanup_explicit(self)
	if remaining <= 0 or fighters[0].stats.hp <= 0 or fighters[1].stats.hp <= 0:
		finished = true
		UfeCaptureResolver.cleanup(self)
		winner = -1 if fighters[0].stats.hp == fighters[1].stats.hp else (0 if fighters[0].stats.hp > fighters[1].stats.hp else 1)
		for i in range(2):
			UfeBattleTransform.round_end(fighters[i])
			fighters[i].clear_move()
			fighters[i].enter("timeout" if remaining <= 0 else "victory" if i == winner else "defeat")
		UfeReturningProjectile.cleanup_explicit(self)

## Contact-resolution phase. Candidate collection is complete; emitted events describe committed results.
func _resolve_contacts(contacts: Array, inputs: Array) -> void:
	if contacts.size() == 2 and str(contacts[0].move.kind) == "throw" and str(contacts[1].move.kind) == "throw":
		UfeThrowResolver.tech(self, int(contacts[0].owner))
		return
	for contact in contacts:
		var index := int(contact.owner)
		var a := fighters[index]
		var b := fighters[1 - index]
		var input: UfeInputFrame = inputs[1 - index]
		var guardable := b.height == 0 and b.move_id.is_empty() and UfeStateRules.is_guardable_state(b.state)
		var projectile_facing := int(contact.facing) if bool(contact.projectile) else 0
		var facing_attack := projectile_facing * b.facing < 0 if projectile_facing != 0 else (a.x - b.x) * b.facing >= 0
		var defending := guardable and facing_attack and (input.held(UfeInputFrame.GUARD) or input.x * b.facing < 0)
		var old_power := a.combat.power
		var feedback: Dictionary = contact.move.get("feedback", {"spark": "impact_heavy", "block_spark": "impact_guard", "hitstop": 6, "blockstop": 3, "shake": 0, "flash": 2}).duplicate(true)
		if not bool(contact.projectile):
			feedback.spark = a.frame().get("impact_effect", feedback.spark)
			feedback.block_spark = a.frame().get("block_effect", feedback.block_spark)
		if contact.projectile: a.combat.power = int(contact.power)
		var result: String
		if bool(contact.get("capture", false)):
			result = UfeCaptureResolver.contact(self, index, contact.move, defending, int(contact.capture_token))
		elif contact.has("guard_frame"):
			UfeFrameGuard.block_melee(a, b, contact.move)
			a.combat.blocked = true
			var guard_speed := UfeFeelRules.block_push(int(contact.move.get("pushback", 0)))
			if guard_speed > 0:
				b.motion.push_vx = UfeHitResolver.slide(b, a, a.facing * guard_speed)
			result = "block"
			feedback.block_spark = contact.guard_frame.get("guard_effect", feedback.block_spark)
			feedback.block_color = [1, 1, 1, 1]
		else:
			result = UfeHitResolver.apply(a, b, contact.move, defending, rules, projectile_facing)
		a.combat.power = old_power
		if result in ["capture", "ignored"]: continue
		if contact.has("hit_group"): UfeMeleeHitGroups.record(a, int(contact.hit_group), str(contact.move.id), result)
		if str(contact.move.kind) == "throw" and result == "hit":
			UfeThrowResolver.begin(self, index, contact.move)
		var point: Vector2i = contact.get("point", Vector2i(b.x, b.height + 80))
		var event: Dictionary = ContactEvent.make(result, index, str(contact.move.id), bool(contact.projectile), point, feedback)
		if contact.has("weapon_id"): event.weapon_id = str(contact.weapon_id)
		if contact.has("guard_frame"):
			event.guarded_by = 1 - index
			UfeFrameGuard.decorate(event, contact.guard_frame, point, b.facing)
		events.append(event)
		hitstop = maxi(hitstop, int(feedback.get("blockstop", 3) if result == "block" else feedback.get("hitstop", 6)))

func _advance(index: int, input: UfeInputFrame, command: Dictionary) -> void:
	var f := fighters[index]
	var other := fighters[1 - index]
	var stamina_regen: int = -1
	var previous_state := f.state
	var land_allowed := f.motion.land_window > 0
	command.jump = bool(command.jump) or f.motion.jump_buffer > 0
	f.motion.jump_buffer = maxi(0, f.motion.jump_buffer - 1)
	f.state_tick += 1
	f.motion.chase_window = maxi(0, f.motion.chase_window - 1)
	f.motion.land_window = maxi(0, f.motion.land_window - 1)
	f.combat.invulnerable = maxi(0, f.combat.invulnerable - 1)
	f.stats.stun_immune = maxi(0, f.stats.stun_immune - 1)
	f.stats.chill_ticks = maxi(0, f.stats.chill_ticks - 1)
	if f.state in ["transform", "form_entry"]:
		states[f.state].step(f, input, command)
		return
	if command.jump and f.chase_allowed() and f.motion.chase_window > 0 and f.combat.confirmed:
		f.clear_move()
		f.vy = 18
		f.vx = f.facing * 4
		f.motion.jump_kind = "chase"
		f.enter("takeoff", 3)
		f.motion.chase_window = 0
	f.combat.combo_ticks = maxi(0, f.combat.combo_ticks - 1)
	if f.combat.combo_ticks == 0:
		f.combat.combo = 0
		other.combat.bounced = false
	if f.state in ["thrown", "captured"]:
		return
	var paired_throw := other.state == "thrown" and other.combat.thrower == index
	if not paired_throw and (f.height > 0 or f.vy != 0):
		f.x += f.vx
		f.height += f.vy
		f.vy -= 1
		if f.height <= 0:
			f.height = 0
			f.vy = 0
			f.vx = 0
			var finish_landing: bool = not f.move_id.is_empty() and bool(f.definition.moves[f.move_id].get("finish_on_landing", false))
			if not finish_landing: f.clear_move()
			if finish_landing:
				pass # 物理照常落地；完成本招接回/装回，不改变高度或冻结模拟。
			elif f.state == "bounce":
				f.vy = f.motion.bounce_velocity
				f.enter("launch")
			elif f.state == "launch":
				f.enter("down", 35)
			else:
				f.enter("land", 4)
				f.motion.land_window = 2 if f.motion.bounce_followup else 0
				f.motion.bounce_followup = false
				land_allowed = f.motion.land_window > 0
				if land_allowed:
					if int(command.pressed) & UfeInputFrame.HEAVY and input.y < 0: f.remember_command("sweep", UfeCommandResolver.INPUT_BUFFER_TICKS)
					elif int(command.pressed) & UfeInputFrame.CRUSH and input.x == 0 and input.y == 0: f.remember_command("crush", UfeCommandResolver.INPUT_BUFFER_TICKS)
	UfeInputBuffer.release(f, land_allowed, _start)
	if f.state == "transform": return
	var skip_state_step := false
	if f.state == "crush_charge" and f.move_id.is_empty():
		states["crush_charge"].step(f, input, command)
		var fired := f.motion.crush_fire
		if fired > 0:
			f.motion.crush_fire = 0
			_start(f, "crush" if fired <= 1 else "crush_charge_%d" % fired)
		elif f.state == "crush_charge":
			skip_state_step = true
	if not f.move_id.is_empty() and _convert_held_crush(f, input):
		skip_state_step = true
	elif not f.move_id.is_empty():
		# 在推进和末tick清招前捕获；不声明的旧招继续使用原状态恢复。
		if f.definition.moves[f.move_id].has("stamina_regen"):
			stamina_regen = int(f.definition.moves[f.move_id].stamina_regen)
		var frame := f.frame()
		if frame.has("velocity"):
			f.vx = int(frame.velocity[0]) * f.facing
			f.vy = int(frame.velocity[1])
		if frame.has("teleport"):
			f.x = UfeStateRules.clamp_stage_x(other.x + f.facing * int(frame.teleport))
			f.facing = 1 if f.x <= other.x else -1
			events.append({"kind": "teleport", "player": index, "x": f.x})
		UfeProjectileResolver.emit(self, index)
		f.x += int(frame.dx) * f.facing
		f.height = maxi(0, f.height + int(frame.dy))
		for event in frame.events:
			events.append({"kind": event.kind, "id": event.id, "player": index})
		# 自身回复：只在招式声明的帧结算一次，整数、无随机；不清对手状态。
		var heal: Dictionary = f.definition.moves[f.move_id].get("self_heal", {})
		if not heal.is_empty() and f.move_tick == int(heal.get("frame", 0)):
			var amount := maxi(0, int(heal.get("amount", 0)))
			var healed := mini(int(f.definition.max_health), f.stats.hp + amount) - f.stats.hp
			f.stats.hp += healed
			if bool(heal.get("cleanse", false)):
				f.stats.stun = 0
				f.stats.stun_immune = maxi(f.stats.stun_immune, 10)
			events.append({"kind": "self_heal", "player": index, "move": f.move_id,
				"amount": healed, "cleanse": bool(heal.get("cleanse", false))})
		f.move_tick += 1
		UfeBattleTransform.after_move_tick(f)
		var capture_handled := UfeCaptureResolver.after_move_tick(self, index, input)
		# 只对显式声明的抓取招式启用落空收势；既有招式沿原逐tick路径。
		var whiff_branch := -1 if capture_handled else int(f.definition.moves[f.move_id].get("whiff_branch_tick", -1))
		if not capture_handled and f.move_tick == whiff_branch and not f.combat.connected:
			var recovery := int(f.definition.moves[f.move_id].get("whiff_recovery_tick", f.move_tick))
			f.move_tick = clampi(recovery, f.move_tick, f.definition.moves[f.move_id].frames.size())
			events.append({"kind": "throw_whiff", "player": index, "move": f.move_id})
		if not capture_handled and f.move_tick >= f.definition.moves[f.move_id].frames.size():
			f.clear_move()
			f.enter("air" if f.height > 0 else "crouch" if input.y < 0 else "idle")
	elif not skip_state_step:
		if command.jump and f.chase_allowed() and f.motion.chase_window > 0:
			f.clear_move()
			f.vy = 18
			f.vx = f.facing * 4
			f.motion.jump_kind = "chase"
			f.enter("takeoff", 3)
			f.motion.chase_window = 0
		else:
			states[f.state].step(f, input, command)
		if f.state == "takeoff": f.motion.jump_buffer = 0
		if f.state in ["idle", "walk", "crouch", "guard", "crouch_guard"]:
			var desired := 1 if f.x <= other.x else -1
			if f.facing != desired:
				f.facing = desired
				f.enter("crouch_turn" if f.state in ["crouch", "crouch_guard"] else "turn", 6)
	if f.state == "charge": f.stats.energy = mini(3000, f.stats.energy + 20)
	UfeStaminaRules.advance(f, previous_state, stamina_regen)
	f.stats.stun = maxi(0, f.stats.stun - 1)
	if f.state not in ["thrown", "captured"]:
		var push := f.motion.push_vx
		if push != 0:
			f.motion.push_vx = UfeHitResolver.slide(f, other, push)
	f.x = UfeStateRules.clamp_stage_x(f.x)

func _start(f: UfeFighter, id: String) -> void:
	if UfeBattleTransform.is_command(id):
		if f.height == 0 and UfeBattleTransform.can_transform(f, id):
			UfeBattleTransform.begin(f, id)
			events.append({"kind": "transform", "player": fighters.find(f), "form": f.battle_form.id})
		return # E 是独立形态键；启动条件失效时不回退为 P 必杀。
	if id == "special" and f.height > 0: return
	if UfeReturningProjectile.blocks_move(self, f, id): return
	if id == "special":
		@warning_ignore("integer_division") # 千点能量为一格，整数取档。
		var level := clampi(f.stats.energy / 1000, 1, 3)
		if level > 1 and f.definition.moves.has("special%d" % level): id = "special%d" % level
		if level == 3 and f.form_id == "super-taro": id = "super_special3"
	if not f.definition.moves.has(id): return
	var move: Dictionary = f.definition.moves[id]
	# 输入缓存可能跨过落地；空中限定按真正启动时的高度重验，先于任何扣费。
	if bool(move.get("air_only", false)) and f.height <= 0: return
	if move.has("capture"):
		if not UfeCaptureResolver.can_start(f, move): return
		var player := fighters.find(f)
		if not UfeCaptureResolver.receiver_supported(fighters[1 - player], move.capture):
			f.clear_input_buffer()
			events.append({"kind": "move_denied", "player": player, "move": id, "reason": "capture_receiver"})
			return
	# 显式派生不能借残留输入缓存，在来源动作已结束的idle中独立启动。
	if move.has("followup_from") and f.move_id not in move.followup_from: return
	if id == "air_special" and (f.height <= 0 or not bool(move.get("air_allowed", false))): return
	var cost := int(move.energy_cost)
	var power := 1 # 各级必杀伤害、消耗独立写在各角色数据中，不再乘能量格数。
	if f.stats.energy < cost:
		events.append({"kind": "move_denied", "player": fighters.find(f), "move": id, "reason": "energy", "required": cost, "available": f.stats.energy})
		return
	var stamina_cost := maxi(0, int(move.stamina_cost))
	if f.stats.stamina < stamina_cost:
		f.clear_input_buffer()
		events.append({"kind": "move_denied", "player": fighters.find(f), "move": id, "reason": "stamina", "required": stamina_cost, "available": f.stats.stamina})
		return
	f.stats.energy -= cost
	UfeStaminaRules.spend(f, stamina_cost)
	var from_state := f.state
	# 主动攻击结束侧闪来源的无敌；招式自己逐帧声明的特殊无敌照常读取。
	if f.state == "dodge": f.combat.invulnerable = 0
	f.clear_move()
	f.combat.power = power
	f.combat.absorbed = 0
	f.clear_input_buffer()
	# 自己出招就停下受击滑步，避免防反和取消被自己的推退带出距离。
	f.motion.push_vx = 0
	f.move_id = id
	f.move_tick = 0
	f.enter("air_attack" if f.height > 0 else "attack")
	if id == "crush" and f.height == 0 and from_state in ["idle", "walk", "turn", "charge", "charge_start", "charge_stop"]:
		f.motion.crush_chargeable = true
		f.motion.crush_hold = 0
		f.motion.crush_tier = 1
		f.motion.crush_stamina_paid = stamina_cost
	if move.has("capture"): UfeCaptureResolver.begin(self, fighters.find(f))
	if id == "burst":
		f.combat.invulnerable = 18
		f.vx = 0
		f.vy = 0
		f.enter("burst")

func _convert_held_crush(f: UfeFighter, input: UfeInputFrame) -> bool:
	if f.move_id != "crush" or not f.motion.crush_chargeable:
		return false
	if not input.held(UfeInputFrame.CRUSH) or input.y < 0 or f.height > 0:
		f.motion.crush_chargeable = false
		return false
	var hold := f.motion.crush_hold + 1
	f.motion.crush_hold = hold
	f.motion.crush_tier = 1
	if hold < UfeFeelRules.CRUSH_TAP_TICKS:
		return false
	if not f.frame().get("hitboxes", []).is_empty():
		f.motion.crush_chargeable = false
		return false
	var paid := f.motion.crush_stamina_paid
	f.stats.stamina = mini(UfeStaminaRules.MAXIMUM, f.stats.stamina + paid)
	f.combat.stamina_delay = 0
	f.clear_move()
	f.motion.crush_hold = hold
	f.motion.crush_tier = 1
	f.enter("crush_charge")
	return true

func _separate() -> void:
	var a := fighters[0]
	var b := fighters[1]
	if a.state in ["thrown", "captured"] or b.state in ["thrown", "captured"] or absi(a.height - b.height) > 120: return
	var gap := a.definition.body_radius + b.definition.body_radius
	var direction := 1 if a.x <= b.x else -1
	var overlap := gap - absi(a.x - b.x)
	# 可选逐帧躯干推挤框；没有该数据的角色保留原来的半径算法。
	if a.frame().has("pushbox") or b.frame().has("pushbox"):
		var first := _push_edges(a)
		var second := _push_edges(b)
		overlap = int(first[1]) - int(second[0]) if direction > 0 else int(second[1]) - int(first[0])
	if overlap > 0:
		@warning_ignore("integer_division") # 重叠整数像素对半分，余数归前一方。
		a.x = UfeStateRules.clamp_stage_x(a.x - direction * ((overlap + 1) / 2))
		@warning_ignore("integer_division") # 重叠整数像素对半分。
		b.x = UfeStateRules.clamp_stage_x(b.x + direction * (overlap / 2))

static func _push_edges(f: UfeFighter) -> Array:
	if not f.frame().has("pushbox"):
		return [f.x - f.definition.body_radius, f.x + f.definition.body_radius]
	var box: Array = f.frame().pushbox
	var first := f.x + f.facing * int(box[0])
	var second := first + f.facing * int(box[2])
	return [mini(first, second), maxi(first, second)]

func _capture_terminal_view() -> void:
	if not terminal_view.is_empty(): return
	terminal_view = {"tick": tick, "remaining": remaining, "events": events.duplicate(true),
		"projectiles": projectiles.duplicate(true), "projectile_refs": projectiles.duplicate(), "fighters": []}
	for f in fighters:
		terminal_view.fighters.append({"definition": f.definition, "base_definition": f.base_definition,
			"battle_form": f.battle_form.duplicate(true), "form_id": f.form_id,
			"transformed_this_round": f.transformed_this_round, "snapshot": f.snapshot().duplicate(true)})

func state_hash() -> String:
	return UfeMatchFingerprint.state_hash(tick, remaining, hitstop, finished, winner, projectiles, fighters)


static func projectile_box(p: Dictionary) -> Rect2i:
	var b: Array = p.box
	return Rect2i(int(p.x) + int(b[0]) if int(p.facing) > 0 else int(p.x) - int(b[0]) - int(b[2]), int(p.height) + int(b[1]), int(b[2]), int(b[3]))
