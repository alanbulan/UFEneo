class_name UfeInputBuffer
extends RefCounted
## 输入上下文映射、指令缓冲队列与取消释放管线。


static func command_state(f: UfeFighter) -> String:
	if not f.move_id.is_empty(): return f.move_id
	if f.state in ["crouch_start", "crouch_rise"]: return "crouch"
	if f.state == "crouch_guard": return "guard"
	if f.state == "crouch_blockstun": return "blockstun"
	if f.height > 0 and f.state in ["air", "takeoff"]:
		return ("diagonal" if f.motion.jump_kind == "backward" else f.motion.jump_kind) + "_air"
	return f.state


static func clear(combat: UfeFighterCombat) -> void:
	combat.buffer = ""
	combat.buffer_ticks = 0
	combat.buffer_next = ""
	combat.buffer_next_ticks = 0


## 最近两条指令。相同指令只刷新计时；第三条挤掉最旧的一条。
static func remember(combat: UfeFighterCombat, move_id_to_keep: String, ticks: int) -> void:
	if move_id_to_keep.is_empty():
		return
	if combat.buffer.is_empty() or combat.buffer == move_id_to_keep:
		combat.buffer = move_id_to_keep
		combat.buffer_ticks = ticks
	elif combat.buffer_next.is_empty() or combat.buffer_next == move_id_to_keep:
		combat.buffer_next = move_id_to_keep
		combat.buffer_next_ticks = ticks
	else:
		combat.buffer = combat.buffer_next
		combat.buffer_ticks = combat.buffer_next_ticks
		combat.buffer_next = move_id_to_keep
		combat.buffer_next_ticks = ticks


static func resolve_step_commands(fighters: Array[UfeFighter], inputs: Array) -> Array:
	var commands: Array = []
	for i in range(2):
		var f := fighters[i]
		var input: UfeInputFrame = inputs[i]
		var context := command_state(f)
		if f.state in ["idle", "walk"] and input.y < 0:
			context = "crouch"
		var fallback := ""
		if f.height == 0 and f.state not in ["transform", "form_entry", "captured", "thrown", "intro", "victory", "defeat", "timeout", "takeoff"]:
			fallback = "crouch" if input.y < 0 else "idle"
		var command := f.resolver.resolve(
			input,
			f.facing,
			context,
			f.definition.command_table,
			f.stats.energy,
			UfeBattleTransform.can_transform(f, ""),
			fallback
		)
		if UfeCaptureResolver.locked(f):
			command.move = ""
			command.jump = false
		if context == "land" and f.motion.land_window <= 0:
			command.move = ""
		commands.append(command)
		if bool(command.jump):
			f.motion.jump_buffer = 7
			f.motion.jump_x = input.x
		if not str(command.move).is_empty():
			f.remember_command(str(command.move), UfeCommandResolver.INPUT_BUFFER_TICKS)
	return commands


static func release(f: UfeFighter, land_allowed: bool, start_move: Callable) -> void:
	var primary := f.combat.buffer
	var next_move := f.combat.buffer_next
	var choice := ""
	var keep := ""
	var keep_ticks := 0
	# 先出更早按下的那条，后一条留着等取消，避免连按被后键盖掉。
	if not primary.is_empty() and ready(f, primary, land_allowed):
		choice = primary
		keep = next_move
		keep_ticks = f.combat.buffer_next_ticks
	elif not next_move.is_empty() and ready(f, next_move, land_allowed):
		choice = next_move
	if not choice.is_empty():
		var before_move := f.move_id
		var before_state := f.state
		start_move.call(f, choice)
		if f.move_id != before_move or f.state != before_state:
			if not keep.is_empty() and keep != f.move_id:
				f.combat.buffer = keep
				f.combat.buffer_ticks = maxi(0, keep_ticks - 1)
				if f.combat.buffer_ticks == 0:
					f.combat.buffer = ""
			return
	_decay_primary(f.combat)
	_decay_next(f.combat)


static func _decay_primary(combat: UfeFighterCombat) -> void:
	if combat.buffer.is_empty():
		return
	combat.buffer_ticks = maxi(0, combat.buffer_ticks - 1)
	if combat.buffer_ticks == 0:
		combat.buffer = ""


static func _decay_next(combat: UfeFighterCombat) -> void:
	if combat.buffer_next.is_empty():
		return
	combat.buffer_next_ticks = maxi(0, combat.buffer_next_ticks - 1)
	if combat.buffer_next_ticks == 0:
		combat.buffer_next = ""


static func ready(f: UfeFighter, buffered: String, land_allowed: bool) -> bool:
	var contact := f.combat.confirmed or f.combat.blocked
	var listed: bool = f.frame().get("cancel", []).has(buffered)
	var routed := contact and UfeFeelRules.allows_route(f.move_id, buffered) and f.definition.moves.has(buffered)
	var cancel := f.move_id.is_empty() or (contact and (listed or routed))
	var burst := buffered == "burst" and f.state in ["hit", "launch", "blockstun", "crouch_blockstun"]
	var actionable := f.state in [
		"idle", "walk", "dash", "backstep", "dodge",
		"crouch", "crouch_start", "crouch_rise", "guard", "crouch_guard",
		"air", "wake", "charge", "takeoff", "turn", "crouch_turn", "charge_start", "charge_stop",
	] or (f.state == "land" and land_allowed and buffered in ["sweep", "crush"])
	if UfeBattleTransform.is_command(buffered) and f.height == 0 and f.state in ["charge_start", "charge_stop", "turn", "crouch_turn"]:
		actionable = true
	var guard_counter := buffered == "guard_counter" and f.state in ["blockstun", "crouch_blockstun"]
	return (cancel and (actionable or not f.move_id.is_empty())) or burst or guard_counter
