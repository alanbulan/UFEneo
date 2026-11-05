class_name UfeMatchDirector
extends RefCounted
const MOVE_START_RULE_REVISION := 2
const CHASE_INTERRUPT_RULE_REVISION := 1
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

func _init(first: UfeFighterDefinition, second: UfeFighterDefinition, rule: UfeRuleSet, registry: Dictionary, battle_forms: Dictionary = {}) -> void:
	rules = rule
	states = registry.duplicate()
	states["transform"] = preload("res://core/states/transform.gd").new()
	states["form_entry"] = preload("res://core/states/form_entry.gd").new()
	states["capturing"] = preload("res://core/states/capturing.gd").new()
	states["captured"] = preload("res://core/states/captured.gd").new()
	remaining = rules.round_ticks
	fighters = [UfeFighter.new(first, 470), UfeFighter.new(second, 750)]
	fighters[1].facing = -1
	var form_rules: Array = []
	for f in fighters:
		f.battle_form = battle_forms.get(f.definition.id, {})
		form_rules.append(UfeBattleTransform.simulation_data(f.battle_form))
	var fingerprint_data: Array = [6, 60, rule.simulation_data(), first.simulation_data(), second.simulation_data(), form_rules, ["round_end_identity", 1], ["move_start_conditions", MOVE_START_RULE_REVISION], ["hit_pushback_bounds", UfeHitResolver.PUSHBACK_BOUNDARY_REVISION], ["throw_target_air", UfeHitResolver.THROW_TARGET_RULE_REVISION], ["chase_interrupt", CHASE_INTERRUPT_RULE_REVISION], ["projectile_contact_direction", UfeHitResolver.PROJECTILE_DIRECTION_RULE_REVISION]]
	if UfeThrowResolver.RootOffsets.used_in(fingerprint_data):
		fingerprint_data.append(["throw_root_overrides", UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION])
	if UfeThrowResolver.CurrentCapture.used_in(fingerprint_data):
		fingerprint_data.append(["throw_current_capture", UfeThrowResolver.CurrentCapture.REVISION])
	content_fingerprint = JSON.stringify(fingerprint_data, "", true).sha256_text()

func command_state(f: UfeFighter) -> String:
	if not f.move_id.is_empty(): return f.move_id
	if f.state in ["crouch_start","crouch_rise"]: return "crouch"
	if f.state=="crouch_guard": return "guard"
	if f.state=="crouch_blockstun": return "blockstun"
	if f.height > 0 and f.state in ["air", "takeoff"]:
		return ("diagonal" if f.motion.jump_kind == "backward" else str(f.motion.jump_kind)) + "_air"
	return f.state

func step(inputs: Array) -> void:
	events.clear()
	UfeCaptureResolver.cleanup(self)
	UfeReturningProjectile.cleanup_explicit(self)
	if finished: return
	tick += 1
	var commands: Array = []
	for i in range(2):
		var f := fighters[i]
		var context := command_state(f)
		if f.state in ["idle", "walk"] and inputs[i].y < 0: context = "crouch"
		var fallback := ""
		if f.height == 0 and f.state not in ["transform","form_entry","captured","thrown","intro","victory","defeat","timeout","takeoff"]:
			fallback = "crouch" if inputs[i].y < 0 else "idle"
		var command := f.resolver.resolve(inputs[i], f.facing, context, f.definition.command_table, int(f.stats.energy), UfeBattleTransform.can_transform(f), fallback)
		if UfeCaptureResolver.locked(f):
			command.move = ""; command.jump = false
		if context == "land" and int(f.motion.land_window)<=0: command.move = ""
		commands.append(command)
		if bool(command.get("consume_jump", false)): f.motion.jump_buffer = 0
		if command.jump:
			f.motion.jump_buffer = 7
			f.motion.jump_x = inputs[i].x
		if not str(command.move).is_empty():
			f.combat.buffer = command.move
			f.combat.buffer_ticks = UfeCommandResolver.INPUT_BUFFER_TICKS
	UfeThrowResolver.input_step(self,commands)
	if hitstop > 0:
		hitstop -= 1
		return
	var cinematic_owner: int=-1
	var freeze_opponent: bool=false
	for i in range(2):
		if bool(fighters[i].frame().get("pause_clock",false)):
			cinematic_owner=i
			freeze_opponent=bool(fighters[i].frame().get("freeze_opponent",false))
	if cinematic_owner<0:remaining -= 1
	for i in range(2):
		if freeze_opponent and i!=cinematic_owner:continue
		_advance(i, inputs[i], commands[i])
	_separate()
	# 自然结束/取消/落地清招必须在本tick弹体推进与接触形成前清除显式武器。
	UfeReturningProjectile.cleanup_explicit(self)
	var contacts: Array = []
	for i in range(2):
		var f := fighters[i]
		if f.move_id.is_empty(): continue
		var move: Dictionary = f.definition.moves[f.move_id]
		var frame := f.frame()
		if str(move.kind) == "projectile" and not frame.hitboxes.is_empty() and not f.combat.connected:
			UfeProjectileResolver.spawn(self,i,move.get("projectile",{}),f.move_id)
			f.combat.connected = true
		elif UfeHitResolver.can_hit(f, fighters[1-i]):
			var contact: Dictionary={"owner": i, "move": UfeMeleeHitGroups.contact_move(f,move), "projectile": false,"point":UfeHitResolver.contact_point(f,fighters[1-i])}
			if frame.has("hit_group"):contact.hit_group=int(frame.hit_group)
			if UfeFrameGuard.melee_point(f,fighters[1-i],contact.move)!=null:contact.guard_frame=fighters[1-i].frame().duplicate(true)
			contacts.append(contact)
	if not freeze_opponent:UfeProjectileResolver.advance(self,contacts)
	if contacts.size() == 2 and str(contacts[0].move.kind) == "throw" and str(contacts[1].move.kind) == "throw":
		UfeThrowResolver.tech(self,int(contacts[0].owner))
	else:
		for contact in contacts:
			var index := int(contact.owner)
			var a := fighters[index]
			var b := fighters[1-index]
			var input: UfeInputFrame = inputs[1-index]
			var guardable := b.height==0 and b.move_id.is_empty() and b.state in ["idle","walk","crouch","crouch_start","crouch_rise","guard","crouch_guard","blockstun","crouch_blockstun"]
			var projectile_facing := int(contact.facing) if bool(contact.projectile) else 0
			var facing_attack := projectile_facing*b.facing<0 if projectile_facing!=0 else (a.x-b.x)*b.facing>=0
			var defending := guardable and facing_attack and (input.held(UfeInputFrame.GUARD) or input.x * b.facing < 0)
			var old_power := int(a.combat.power)
			var feedback: Dictionary=contact.move.get("feedback",{"spark":"impact_heavy","block_spark":"impact_guard","hitstop":6,"blockstop":3,"shake":0,"flash":2}).duplicate(true)
			if not bool(contact.projectile):
				feedback.spark=a.frame().get("impact_effect",feedback.spark)
				feedback.block_spark=a.frame().get("block_effect",feedback.block_spark)
			if contact.projectile: a.combat.power = int(contact.power)
			var result: String
			if bool(contact.get("capture",false)):
				result=UfeCaptureResolver.contact(self,index,contact.move,defending,int(contact.capture_token))
			elif contact.has("guard_frame"):
				UfeFrameGuard.block_melee(a,b,contact.move)
				result="block"
				feedback.block_spark=contact.guard_frame.get("guard_effect",feedback.block_spark)
				feedback.block_color=[1,1,1,1]
			else:result=UfeHitResolver.apply(a, b, contact.move, defending, rules, projectile_facing)
			a.combat.power = old_power
			if result in ["capture","ignored"]:continue
			if contact.has("hit_group"):UfeMeleeHitGroups.record(a,int(contact.hit_group),str(contact.move.id),result)
			if str(contact.move.kind) == "throw" and result == "hit":
				UfeThrowResolver.begin(self,index,contact.move)
			var point: Vector2i=contact.get("point",Vector2i(b.x,b.height+80))
			var event: Dictionary={"kind": result, "player": index, "move":contact.move.id,"projectile":contact.projectile,"x":point.x,"height":point.y,"feedback":feedback}
			if contact.has("weapon_id"):event.weapon_id=str(contact.weapon_id)
			if contact.has("guard_frame"):
				event.guarded_by=1-index
				UfeFrameGuard.decorate(event,contact.guard_frame,point,b.facing)
			events.append(event)
			hitstop = maxi(hitstop,int(feedback.get("blockstop",3) if result=="block" else feedback.get("hitstop",6)))
	UfeThrowResolver.sync(self)
	if remaining>0 and (int(fighters[0].stats.hp)<=0 or int(fighters[1].stats.hp)<=0):
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
			fighters[i].enter("timeout" if remaining<=0 else "victory" if i == winner else "defeat")
		UfeReturningProjectile.cleanup_explicit(self)

func _advance(index: int, input: UfeInputFrame, command: Dictionary) -> void:
	var f := fighters[index]
	var other := fighters[1-index]
	var stamina_regen: int = -1
	var previous_state := f.state
	var land_allowed := int(f.motion.land_window)>0
	command.jump = bool(command.jump) or int(f.motion.get("jump_buffer", 0)) > 0
	f.motion.jump_buffer = maxi(0,int(f.motion.get("jump_buffer", 0))-1)
	f.state_tick += 1
	for key in ["chase_window", "land_window"]:
		f.motion[key] = maxi(0, int(f.motion[key]) - 1)
	f.combat.invulnerable = maxi(0, int(f.combat.invulnerable) - 1)
	if f.state in ["transform", "form_entry"]:
		states[f.state].step(f, input, command)
		return
	if command.jump and f.chase_allowed() and int(f.motion.chase_window) > 0 and f.combat.confirmed:
		f.clear_move()
		f.vy = 18
		f.vx = f.facing * 4
		f.motion.jump_kind = "chase"
		f.enter("takeoff", 3)
		f.motion.chase_window = 0
	f.combat.combo_ticks = maxi(0, int(f.combat.combo_ticks) - 1)
	if f.combat.combo_ticks == 0:
		f.combat.combo = 0
		other.combat.bounced = false
	if f.state in ["thrown","captured"]:
		return
	var paired_throw := other.state=="thrown" and int(other.combat.thrower)==index
	if not paired_throw and (f.height > 0 or f.vy != 0):
		f.x += f.vx
		f.height += f.vy
		f.vy -= 1
		if f.height <= 0:
			f.height = 0
			f.vy = 0
			f.vx = 0
			var finish_landing: bool=not f.move_id.is_empty() and bool(f.definition.moves[f.move_id].get("finish_on_landing",false))
			if not finish_landing:f.clear_move()
			if finish_landing:
				pass # 物理照常落地；完成本招接回/装回，不改变高度或冻结模拟。
			elif f.state == "bounce":
				f.vy = int(f.motion.get("bounce_velocity",11))
				f.enter("launch")
			elif f.state == "launch":
				f.enter("down", 35)
			else:
				f.enter("land", 4)
				f.motion.land_window = 2 if bool(f.motion.bounce_followup) else 0
				f.motion.bounce_followup = false
				land_allowed = int(f.motion.land_window)>0
				if land_allowed:
					if int(command.pressed)&UfeInputFrame.HEAVY and input.y<0: f.combat.buffer = "sweep"
					elif int(command.pressed)&UfeInputFrame.CRUSH and input.x==0 and input.y==0: f.combat.buffer = "crush"
	var buffered := str(f.combat.buffer)
	if not buffered.is_empty():
		var cancel: bool = f.move_id.is_empty() or (f.combat.confirmed and buffered in f.frame().cancel)
		var burst := buffered == "burst" and f.state in ["hit", "launch", "blockstun", "crouch_blockstun"]
		var chord_upgrade := buffered == "special" and f.move_tick <= 3 and f.move_id in ["light1", "heavy"]
		var actionable := f.state in ["idle", "walk", "dash", "backstep", "dodge", "crouch", "crouch_start", "crouch_rise", "guard", "crouch_guard", "air", "wake", "charge", "takeoff", "turn", "crouch_turn", "charge_start", "charge_stop"] or (f.state=="land" and land_allowed and buffered in ["sweep","crush"])
		if UfeBattleTransform.is_command(buffered) and f.height == 0 and f.state in ["charge_start","charge_stop","turn","crouch_turn"]: actionable = true
		var guard_counter := buffered == "guard_counter" and f.state in ["blockstun","crouch_blockstun"]
		if (cancel and (actionable or not f.move_id.is_empty())) or burst or chord_upgrade or guard_counter:
			_start(f, buffered)
		f.combat.buffer_ticks = maxi(0, int(f.combat.buffer_ticks) - 1)
		if f.combat.buffer_ticks == 0: f.combat.buffer = ""
	if f.state == "transform": return
	if not f.move_id.is_empty():
		# 在推进和末tick清招前捕获；不声明的旧招继续使用原状态恢复。
		if f.definition.moves[f.move_id].has("stamina_regen"):
			stamina_regen = int(f.definition.moves[f.move_id].stamina_regen)
		var frame := f.frame()
		if frame.has("velocity"):
			f.vx = int(frame.velocity[0])*f.facing
			f.vy = int(frame.velocity[1])
		if frame.has("teleport"):
			f.x=clampi(other.x+f.facing*int(frame.teleport),28,1252)
			f.facing=1 if f.x<=other.x else -1
			events.append({"kind":"teleport","player":index,"x":f.x})
		UfeProjectileResolver.emit(self,index)
		f.x += int(frame.dx) * f.facing
		f.height = maxi(0, f.height + int(frame.dy))
		for event in frame.events:
			events.append({"kind": event.kind, "id": event.id, "player": index})
		f.move_tick += 1
		UfeBattleTransform.after_move_tick(f)
		var capture_handled := UfeCaptureResolver.after_move_tick(self,index,input)
		# 只对显式声明的抓取招式启用落空收势；既有招式沿原逐tick路径。
		var whiff_branch := -1 if capture_handled else int(f.definition.moves[f.move_id].get("whiff_branch_tick", -1))
		if not capture_handled and f.move_tick == whiff_branch and not bool(f.combat.connected):
			var recovery := int(f.definition.moves[f.move_id].get("whiff_recovery_tick", f.move_tick))
			f.move_tick = clampi(recovery, f.move_tick, f.definition.moves[f.move_id].frames.size())
			events.append({"kind":"throw_whiff","player":index,"move":f.move_id})
		if not capture_handled and f.move_tick >= f.definition.moves[f.move_id].frames.size():
			f.clear_move()
			f.enter("air" if f.height > 0 else "crouch" if input.y<0 else "idle")
	else:
		if command.jump and f.chase_allowed() and int(f.motion.chase_window) > 0:
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
				f.enter("crouch_turn" if f.state in ["crouch","crouch_guard"] else "turn", 6)
	if f.state == "charge": f.stats.energy = mini(3000, int(f.stats.energy) + 20)
	UfeStaminaRules.advance(f, previous_state, stamina_regen)
	f.stats.stun = maxi(0, int(f.stats.stun) - 1)
	f.x = clampi(f.x, 28, 1252)

func _start(f: UfeFighter, id: String) -> void:
	if UfeBattleTransform.is_command(id):
		if f.height == 0 and UfeBattleTransform.can_transform(f, id):
			UfeBattleTransform.begin(f, id)
			events.append({"kind":"transform", "player":fighters.find(f), "form":f.battle_form.id})
		else:
			_start(f, "special") # 条件失效时保留同次P输入的普通必杀。
		return
	if id=="special" and f.height>0:return
	if UfeReturningProjectile.blocks_move(self,f,id):return
	if id=="special":
		var level:=clampi(int(f.stats.energy)/1000,1,3)
		if level>1 and f.definition.moves.has("special%d"%level):id="special%d"%level
		if level == 3 and f.form_id == "super-taro": id = "super_special3"
	if not f.definition.moves.has(id): return
	var move: Dictionary = f.definition.moves[id]
	# 输入缓存可能跨过落地；空中限定按真正启动时的高度重验，先于任何扣费。
	if bool(move.get("air_only",false)) and f.height<=0:return
	if move.has("capture"):
		if not UfeCaptureResolver.can_start(f,move):return
		var player := fighters.find(f)
		if not UfeCaptureResolver.receiver_supported(fighters[1-player],move.capture):
			f.combat.buffer = ""; f.combat.buffer_ticks = 0
			events.append({"kind":"move_denied","player":player,"move":id,"reason":"capture_receiver"})
			return
	# 显式派生不能借残留输入缓存，在来源动作已结束的idle中独立启动。
	if move.has("followup_from") and f.move_id not in move.followup_from: return
	if id=="air_special" and (f.height<=0 or not bool(move.get("air_allowed",false))):return
	var cost := int(move.energy_cost)
	var power := 1 # 各级必杀伤害、消耗独立写在各角色数据中，不再乘能量格数。
	if int(f.stats.energy) < cost:
		events.append({"kind":"move_denied","player":fighters.find(f),"move":id,"reason":"energy","required":cost,"available":int(f.stats.energy)})
		return
	f.stats.energy = int(f.stats.energy) - cost
	UfeStaminaRules.spend(f, int(move.stamina_cost))
	# 主动攻击结束侧闪来源的无敌；招式自己逐帧声明的特殊无敌照常读取。
	if f.state=="dodge":f.combat.invulnerable=0
	f.clear_move()
	f.combat.power = power
	f.combat.absorbed = 0
	f.combat.buffer = ""
	f.combat.buffer_ticks = 0
	f.move_id = id
	f.move_tick = 0
	f.enter("air_attack" if f.height > 0 else "attack")
	if move.has("capture"):UfeCaptureResolver.begin(self,fighters.find(f))
	if id == "burst":
		f.combat.invulnerable = 18
		f.vx=0
		f.vy=0
		f.enter("burst")

func _separate() -> void:
	var a := fighters[0]
	var b := fighters[1]
	if a.state in ["thrown","captured"] or b.state in ["thrown","captured"] or absi(a.height-b.height) > 120: return
	var gap := a.definition.body_radius + b.definition.body_radius
	var direction := 1 if a.x <= b.x else -1
	var overlap := gap - absi(a.x-b.x)
	# 可选逐帧躯干推挤框；没有该数据的角色保留原来的半径算法。
	if a.frame().has("pushbox") or b.frame().has("pushbox"):
		var first := _push_edges(a)
		var second := _push_edges(b)
		overlap = int(first[1])-int(second[0]) if direction > 0 else int(second[1])-int(first[0])
	if overlap > 0:
		a.x = clampi(a.x - direction * ((overlap+1)/2), 28, 1252)
		b.x = clampi(b.x + direction * (overlap/2), 28, 1252)

static func _push_edges(f: UfeFighter) -> Array:
	if not f.frame().has("pushbox"):
		return [f.x-f.definition.body_radius, f.x+f.definition.body_radius]
	var box: Array = f.frame().pushbox
	var first := f.x+f.facing*int(box[0])
	var second := first+f.facing*int(box[2])
	return [mini(first,second),maxi(first,second)]

func _capture_terminal_view() -> void:
	if not terminal_view.is_empty():return
	terminal_view={"tick":tick,"remaining":remaining,"events":events.duplicate(true),
		"projectiles":projectiles.duplicate(true),"projectile_refs":projectiles.duplicate(),"fighters":[]}
	for f in fighters:
		terminal_view.fighters.append({"definition":f.definition,"base_definition":f.base_definition,
			"battle_form":f.battle_form.duplicate(true),"form_id":f.form_id,
			"transformed_this_round":f.transformed_this_round,"snapshot":f.snapshot().duplicate(true)})

func state_hash() -> String:
	return JSON.stringify([tick, remaining, hitstop, finished, winner, projectiles,
		fighters[0].snapshot(), fighters[1].snapshot()], "", true).sha256_text()


static func projectile_box(p: Dictionary) -> Rect2i:
	var b: Array = p.box
	return Rect2i(int(p.x)+int(b[0]) if int(p.facing)>0 else int(p.x)-int(b[0])-int(b[2]),int(p.height)+int(b[1]),int(b[2]),int(b[3]))
