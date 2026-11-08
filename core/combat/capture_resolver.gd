class_name UfeCaptureResolver
extends RefCounted
## 只有声明capture的招式建立关系；所有位置、分支和逐相时钟均进入motion快照。
const PHASES := ["enclose","shrink","return","held","release"]

static func integer(value: Variant, low: int, high: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value == int(value) and int(value) >= low and int(value) <= high

static func valid_move(move: Dictionary) -> bool:
	if not move.get("capture",null) is Dictionary or str(move.get("kind","")) != "projectile": return false
	var data: Dictionary = move.capture
	var count: int = move.get("frames",[]).size()
	for key in ["flight_tick","success_tick","success_end_tick","miss_recovery_tick"]:
		if not integer(data.get(key,null),1,count): return false
	if not integer(data.get("flight_max_ticks",null),1,30): return false
	if not integer(data.get("lift_height",null),0,512) or not integer(data.get("release_distance",null),1,500): return false
	var anchor: Variant = data.get("hand_anchor",null)
	if not anchor is Array or anchor.size() != 2 or not integer(anchor[0],-512,512) or not integer(anchor[1],0,512): return false
	if data.has("hand_anchor_by_frame"):
		var anchors: Variant = data.hand_anchor_by_frame
		if not anchors is Dictionary or anchors.is_empty(): return false
		for key in anchors:
			if not key is String or not key.is_valid_int() or str(int(key)) != key or not integer(int(key),0,count-1): return false
			var point: Variant = anchors[key]
			if not point is Array or point.size() != 2 or not integer(point[0],-512,512) or not integer(point[1],0,512): return false
	var stages: Variant = data.get("stages",null)
	if not stages is Array or stages.size() != PHASES.size(): return false
	var duration := 0
	for index in range(PHASES.size()):
		var phase: Variant = stages[index]
		if not phase is Dictionary or str(phase.get("id","")) != PHASES[index]: return false
		if not integer(phase.get("ticks",null),1,120): return false
		if not phase.get("victim_animation",null) is String or str(phase.victim_animation).is_empty(): return false
		var frames: Variant = phase.get("victim_frames",null)
		if not frames is Array or frames.size() != int(phase.ticks): return false
		for frame in frames:
			if frame is Dictionary:
				if not frame.get("animation",null) is String or str(frame.animation).is_empty() or not integer(frame.get("frame",null),0,1023): return false
			elif not integer(frame,0,1023): return false
		duration += int(phase.ticks)
	if not integer(data.get("release_ground_tick",null),0,int(stages[4].ticks)-1): return false
	if int(data.flight_tick) >= int(data.success_tick): return false
	if int(data.success_tick)+duration > int(data.success_end_tick): return false
	if int(data.success_end_tick) > int(data.miss_recovery_tick) or int(data.miss_recovery_tick) >= count: return false
	# 等待帧会真实停留，不能重复发射、位移、取消或触发事件。
	var wait: Dictionary = move.frames[int(data.flight_tick)]
	if int(wait.dx) != 0 or int(wait.dy) != 0 or not wait.events.is_empty() or not wait.get("shots",[]).is_empty() or wait.has("velocity") or wait.has("teleport"): return false
	var shots := 0
	for index in range(count):
		var frame: Dictionary = move.frames[index]
		if not frame.hitboxes.is_empty() or not frame.cancel.is_empty(): return false
		for shot in frame.get("shots",[]):
			if not shot.get("capture",false) is bool or not bool(shot.get("capture",false)) or index != int(data.flight_tick)-1: return false
			if not integer(shot.get("life",null),1,int(data.flight_max_ticks)) or bool(shot.get("beam",false)) or shot.has("integer_path"): return false
			shots += 1
	return shots == 1 and move.get("projectile",{}).is_empty()

static func locked(f: UfeFighter) -> bool:
	return f.state in ["capturing","captured"]

static func can_start(f: UfeFighter, move: Dictionary) -> bool:
	return f.height == 0 and not f.motion.has("capture_victim") and not f.motion.has("capture") and valid_move(move)

static func begin(sim: UfeMatchDirector, owner: int) -> void:
	var actor := sim.fighters[owner]
	actor.motion.capture = {"move":actor.move_id,"token":sim.tick,"phase":"startup","phase_index":-1,"phase_age":0,
		"flight_age":0,"victim":-1,"settled":false}
	actor.motion.chase_window = 0
	actor.motion.jump_buffer = 0
	actor.vx = 0; actor.vy = 0
	actor.enter("capturing")
	sim.events.append({"kind":"capture_start","player":owner,"move":actor.move_id,"stamina_cost":int(actor.definition.moves[actor.move_id].stamina_cost),"energy_cost":int(actor.definition.moves[actor.move_id].energy_cost)})

static func projectile_valid(sim: UfeMatchDirector, p: Dictionary) -> bool:
	var owner := int(p.get("source_owner",-1))
	if owner < 0 or owner >= sim.fighters.size() or int(p.owner) != owner: return false
	var actor := sim.fighters[owner]
	var relation: Dictionary = actor.motion.get("capture",{})
	return not relation.is_empty() and actor.state == "capturing" and actor.move_id == str(p.move) and int(relation.token) == int(p.get("capture_token",-1)) and str(relation.phase) == "flight" and int(actor.stats.hp) > 0

static func clear_shots(sim: UfeMatchDirector, owner: int, token: int) -> void:
	for p in sim.projectiles:
		if bool(p.get("capture",false)) and int(p.get("source_owner",-1)) == owner and int(p.get("capture_token",-1)) == token: p.life = 0

static func receiver_supported(target: UfeFighter, data: Dictionary) -> bool:
	# 资源合同是静态条件；不要把跳跃、无敌或防御提前当成不能出招。
	for phase in data.stages:
		for frame in phase.victim_frames:
			var animation := str(frame.animation) if frame is Dictionary else str(phase.victim_animation)
			var index := int(frame.frame) if frame is Dictionary else int(frame)
			var poses: Array = target.definition.state_frames.get(animation,[])
			if index >= poses.size(): return false
	return true

static func eligible(target: UfeFighter, data: Dictionary) -> bool:
	if target.height != 0 or target.motion.has("capture") or target.motion.has("capture_victim") or UfeHitResolver.invulnerable(target): return false
	if target.state in ["down","thrown","captured","capturing","defeat","victory","timeout","air","air_attack","takeoff","launch","bounce"]: return false
	return int(target.stats.hp) > 0 and receiver_supported(target,data)

static func contact(sim: UfeMatchDirector, owner: int, move: Dictionary, defending: bool, token: int) -> String:
	var actor := sim.fighters[owner]
	var target := sim.fighters[1-owner]
	var relation: Dictionary = actor.motion.get("capture",{})
	if relation.is_empty() or str(relation.phase) != "flight" or int(relation.token) != token or actor.move_id != str(move.id) or actor.state != "capturing": return "ignored"
	if not eligible(target,move.capture):
		fail(sim,owner,"invalid_target")
		return "ignored"
	if UfeHitResolver.is_blocked(target,move,defending):
		UfeHitResolver.apply(actor,target,move,true,sim.rules)
		fail(sim,owner,"guard")
		return "block"
	actor.combat.connected = true; actor.combat.confirmed = true
	relation.victim = 1-owner
	relation.origin_x = target.x; relation.origin_height = target.height
	relation.phase = PHASES[0]; relation.phase_index = 0; relation.phase_age = 0
	actor.move_tick = int(move.capture.success_tick)
	target.clear_move(); target.vx = 0; target.vy = 0
	target.combat.buffer = ""; target.combat.buffer_ticks = 0; target.motion.jump_buffer = 0
	target.motion.capture_victim = {"owner":owner,"token":token,"animation":"","frame":0}
	target.enter("captured")
	clear_shots(sim,owner,token)
	sync_victim(sim,owner)
	sim.events.append({"kind":"capture_begin","player":owner,"victim":1-owner,"move":actor.move_id,"x":target.x,"height":target.height})
	return "capture"

static func fail(sim: UfeMatchDirector, owner: int, reason: String) -> void:
	var actor := sim.fighters[owner]
	var relation: Dictionary = actor.motion.get("capture",{})
	if relation.is_empty() or str(relation.phase) in ["failed","recovery"]: return
	if int(relation.victim) >= 0:
		abort(sim,owner,reason)
		return
	clear_shots(sim,owner,int(relation.token))
	relation.phase = "failed"; relation.phase_age = 0
	actor.move_tick = int(actor.definition.moves[actor.move_id].capture.miss_recovery_tick)
	sim.events.append({"kind":"capture_fail","player":owner,"move":str(relation.move),"reason":reason})

static func settle(sim: UfeMatchDirector, owner: int) -> void:
	var actor := sim.fighters[owner]
	var relation: Dictionary = actor.motion.capture
	if bool(relation.settled): return
	var target := sim.fighters[int(relation.victim)]
	var move: Dictionary = actor.definition.moves[actor.move_id]
	relation.settled = true
	target.stats.hp = maxi(0,int(target.stats.hp)-int(move.damage))
	actor.combat.combo = int(actor.combat.combo)+1; actor.combat.combo_ticks = 90
	sim.events.append({"kind":"capture_impact","player":owner,"victim":int(relation.victim),"move":actor.move_id,"damage":int(move.damage),"x":target.x,"height":target.height})

static func after_move_tick(sim: UfeMatchDirector, owner: int, input: UfeInputFrame) -> bool:
	var actor := sim.fighters[owner]
	if not actor.motion.has("capture"): return false
	var relation: Dictionary = actor.motion.capture
	var move: Dictionary = actor.definition.moves[actor.move_id]
	var data: Dictionary = move.capture
	var phase := str(relation.phase)
	if phase == "startup":
		if actor.move_tick >= int(data.flight_tick):
			relation.phase = "flight"; actor.move_tick = int(data.flight_tick)
	elif phase == "flight":
		relation.flight_age = int(relation.flight_age)+1
		actor.move_tick = int(data.flight_tick)
		if int(relation.flight_age) >= int(data.flight_max_ticks): fail(sim,owner,"timeout")
	elif phase in PHASES:
		var index := int(relation.phase_index)
		relation.phase_age = int(relation.phase_age)+1
		if int(relation.phase_age) >= int(data.stages[index].ticks):
			if phase == "held": settle(sim,owner)
			if phase == "release":
				release_victim(sim,owner)
				sim.events.append({"kind":"capture_release","player":owner,"victim":int(relation.victim),"move":actor.move_id})
				relation.phase = "recovery"; relation.victim = -1
			else:
				relation.phase_index = index+1; relation.phase = PHASES[index+1]; relation.phase_age = 0
				sim.events.append({"kind":"capture_phase","player":owner,"victim":int(relation.victim),"move":actor.move_id,"phase":str(relation.phase)})
		if str(relation.phase) == "recovery" and actor.move_tick >= int(data.success_end_tick): finish_owner(actor,input)
	elif phase == "recovery":
		if actor.move_tick >= int(data.success_end_tick): finish_owner(actor,input)
	elif phase == "failed":
		if actor.move_tick >= move.frames.size(): finish_owner(actor,input)
	if actor.motion.has("capture"): sync_victim(sim,owner)
	return true

static func finish_owner(actor: UfeFighter, input: UfeInputFrame) -> void:
	actor.motion.erase("capture")
	actor.clear_move(); actor.combat.buffer = ""; actor.combat.buffer_ticks = 0
	actor.enter("crouch" if input.y < 0 else "idle")

static func safe_position(actor: UfeFighter, target: UfeFighter, authored: int) -> void:
	var distance := maxi(authored,actor.definition.body_radius+target.definition.body_radius+2)
	for a in actor.definition.state_frames.get("idle",[actor.frame()]):
		for b in target.definition.state_frames.get("idle",[target.frame()]):
			distance = maxi(distance,UfeThrowResolver.separated_distance(a,1,b,-1,1))
	# 成对平移保留安全间距；不单独夹住目标造成躯体重叠。
	target.x = actor.x+actor.facing*distance
	var left := mini(actor.x,target.x); var right := maxi(actor.x,target.x)
	var shift := 28-left if left < 28 else 1252-right if right > 1252 else 0
	actor.x += shift; target.x += shift
	target.height = 0; target.vx = 0; target.vy = 0

static func sync_victim(sim: UfeMatchDirector, owner: int) -> void:
	var actor := sim.fighters[owner]
	var relation: Dictionary = actor.motion.get("capture",{})
	if relation.is_empty() or int(relation.victim) < 0 or str(relation.phase) not in PHASES: return
	var target := sim.fighters[int(relation.victim)]
	var data: Dictionary = actor.definition.moves[actor.move_id].capture
	var phase: Dictionary = data.stages[int(relation.phase_index)]
	var age := mini(int(relation.phase_age),int(phase.ticks)-1)
	var pose: Dictionary = target.motion.capture_victim
	var selected: Variant = phase.victim_frames[age]
	pose.animation = str(selected.animation) if selected is Dictionary else str(phase.victim_animation)
	pose.frame = int(selected.frame) if selected is Dictionary else int(selected)
	target.facing = -actor.facing
	var anchor: Array = data.get("hand_anchor_by_frame",{}).get(str(actor.move_tick),data.hand_anchor)
	var hand_x := actor.x+actor.facing*int(anchor[0])
	var hand_height := actor.height+int(anchor[1])
	match str(relation.phase):
		"enclose":
			target.x = int(relation.origin_x); target.height = int(relation.origin_height)
		"shrink":
			target.x = int(relation.origin_x)
			@warning_ignore("integer_division") # 逐tick整数像素插值，确定性模拟要求取整。
			target.height = int(relation.origin_height)+int(data.lift_height)*age/maxi(1,int(phase.ticks)-1)
		"return":
			var elapsed := age+1; var duration := int(phase.ticks)
			@warning_ignore("integer_division") # 整数像素线性插值，按帧取整。
			target.x = (int(relation.origin_x)*(duration-elapsed)+hand_x*elapsed)/duration
			@warning_ignore("integer_division") # 整数像素线性插值，按帧取整。
			target.height = ((int(relation.origin_height)+int(data.lift_height))*(duration-elapsed)+hand_height*elapsed)/duration
		"held":
			target.x = hand_x; target.height = hand_height
		"release":
			if age < int(data.release_ground_tick):
				target.x = hand_x; target.height = hand_height
			else:
				if not relation.has("release_x"):
					safe_position(actor,target,int(data.release_distance)); relation.release_x = target.x
					sim.events.append({"kind":"capture_restore","player":owner,"victim":int(relation.victim),"move":actor.move_id,"x":target.x,"height":0})
				target.x = int(relation.release_x); target.height = 0

static func release_victim(sim: UfeMatchDirector, owner: int) -> void:
	var actor := sim.fighters[owner]
	var relation: Dictionary = actor.motion.get("capture",{})
	var victim := int(relation.get("victim",-1))
	if victim < 0 or victim >= sim.fighters.size(): return
	var target := sim.fighters[victim]
	var pose: Dictionary = target.motion.get("capture_victim",{})
	if pose.is_empty() or int(pose.get("owner",-1)) != owner or int(pose.get("token",-1)) != int(relation.token): return
	if target.state == "captured":
		var move: Dictionary = actor.definition.moves.get(str(relation.move),{})
		safe_position(actor,target,int(move.get("capture",{}).get("release_distance",80)))
		target.enter("idle")
	target.motion.erase("capture_victim")
	target.combat.buffer = ""; target.combat.buffer_ticks = 0; target.motion.jump_buffer = 0

static func abort(sim: UfeMatchDirector, owner: int, reason: String) -> void:
	var actor := sim.fighters[owner]
	var relation: Dictionary = actor.motion.get("capture",{})
	if relation.is_empty(): return
	clear_shots(sim,owner,int(relation.token))
	release_victim(sim,owner)
	actor.motion.erase("capture")
	if actor.state == "capturing":
		actor.clear_move(); actor.enter("air" if actor.height > 0 else "idle")
	actor.combat.buffer = ""; actor.combat.buffer_ticks = 0
	sim.events.append({"kind":"capture_abort","player":owner,"move":str(relation.move),"reason":reason})

static func cleanup(sim: UfeMatchDirector) -> void:
	var changed := false
	for owner in range(sim.fighters.size()):
		var actor := sim.fighters[owner]
		if not actor.motion.has("capture"): continue
		changed = true
		var relation: Dictionary = actor.motion.capture
		var invalid := sim.finished or int(actor.stats.hp) <= 0 or actor.state != "capturing" or actor.move_id != str(relation.move)
		invalid = invalid or not actor.definition.moves.has(str(relation.move))
		if not invalid: invalid = not valid_move(actor.definition.moves[str(relation.move)])
		var victim := int(relation.victim)
		invalid = invalid or victim < -1 or victim >= sim.fighters.size()
		if victim >= 0 and not invalid:
			var target := sim.fighters[victim]
			var pose: Dictionary = target.motion.get("capture_victim",{})
			invalid = int(target.stats.hp) <= 0 or target.state != "captured" or int(pose.get("owner",-1)) != owner or int(pose.get("token",-1)) != int(relation.token)
		if invalid: abort(sim,owner,"interrupted_or_terminal")
	for target in sim.fighters:
		if target.state != "captured" and not target.motion.has("capture_victim"): continue
		var pose: Dictionary = target.motion.get("capture_victim",{})
		var owner := int(pose.get("owner",-1))
		if owner >= 0 and owner < sim.fighters.size() and sim.fighters[owner].motion.has("capture"): continue
		changed = true
		target.motion.erase("capture_victim")
		if target.state == "captured":
			if owner >= 0 and owner < sim.fighters.size(): safe_position(sim.fighters[owner],target,80)
			else:
				target.x = clampi(target.x,28,1252); target.height = 0; target.vx = 0; target.vy = 0
			target.clear_move(); target.enter("idle")
	if changed: sim.projectiles = sim.projectiles.filter(func(p): return int(p.life) > 0)
