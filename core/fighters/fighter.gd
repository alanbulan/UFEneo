class_name UfeFighter
extends RefCounted
const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")
# 追击许可只属于尚未被中断的可行动链；自然收招清move不清此窗口。
const CHASE_ACTIONABLE_STATES := ["idle","walk","dash","backstep","dodge","crouch","crouch_start","crouch_rise","guard","crouch_guard","air","charge","takeoff","turn","crouch_turn","charge_start","charge_stop","attack","air_attack","land"]
var definition: UfeFighterDefinition
var base_definition: UfeFighterDefinition
var battle_form: Dictionary = {}
# 多形态选择表的根；battle_form 切到某个子形态后仍从这里继续切换。
var battle_form_choices: Dictionary = {}
var form_id: String = ""
var transformed_this_round: bool = false
var x: int = 0
var height: int = 0
var vx: int = 0
var vy: int = 0
var facing: int = 1
var state: String = "idle"
var state_tick: int = 0
var move_id: String = ""
var move_tick: int = 0
var stats := UfeFighterStats.new()
var combat := UfeFighterCombat.new()
var motion := UfeFighterMotion.new()
var resolver := UfeCommandResolver.new()

func _init(data: UfeFighterDefinition, start_x: int) -> void:
	definition = data
	base_definition = data
	x = start_x
	stats.hp = data.max_health

func enter(id: String, duration: int = 0) -> void:
	# 仅让本次受击后的原crouch→crouch_guard携带恢复姿态；不改变逻辑状态时序。
	if not (state=="crouch" and id=="crouch_guard"):motion.hit_crouch_guard_resume = false
	if id!="thrown":motion.clear_throw_current_capture()
	state = id
	if not chase_allowed(): motion.chase_window = 0
	state_tick = 0
	motion.duration = duration

func chase_allowed() -> bool:
	return state in CHASE_ACTIONABLE_STATES

func has_hit_crouch_guard_resume() -> bool:
	return motion.hit_crouch_guard_resume and height==0 and move_id.is_empty() and state in ["crouch","crouch_guard"] and not definition.state_frames.get("crouch_guard",[]).is_empty()

func frame() -> Dictionary:
	var original := _unmapped_frame()
	if not has_hit_crouch_guard_resume():return original
	# 只同步既有低防保持的图与受击轮廓，保留原状态events/cancel/位移等语义。
	var hold: Dictionary=definition.state_frames.crouch_guard[-1]
	var result: Dictionary=original.duplicate(true)
	result.sprite=hold.sprite
	result.hurtboxes=hold.hurtboxes.duplicate(true)
	return result

func _unmapped_frame() -> Dictionary:
	if CurrentCapture.active(self):return motion.throw_current_capture.frame
	if state == "captured" and motion.has_capture_victim():
		var captured: Dictionary = motion.capture_victim
		var poses: Array = definition.state_frames.get(str(captured.animation),[])
		if not poses.is_empty(): return poses[clampi(int(captured.frame),0,poses.size()-1)]
	if state == "form_entry":
		var entry: Array = battle_form.get("entry_frames", [])
		if not entry.is_empty(): return entry[mini(state_tick, entry.size()-1)]
	if move_id.is_empty():
		if state == "crush_charge":
			var bracing: Array = definition.state_frames.get("idle", [])
			if not bracing.is_empty():
				return bracing[0]
		var spec := _pose_spec(false)
		var key := str(spec.key)
		if state=="thrown" and definition.state_frames.has(key):
			var poses: Array=definition.state_frames[key]
			return poses[clampi(motion.pose_sprite,0,poses.size()-1)]
		if state=="walk":
			if definition.state_frames.has(key):
				var stride: Array=definition.state_frames[key]
				return stride[state_tick%stride.size()]
		elif state == "air":
			var air_key := motion.jump_kind+"_air"
			if definition.state_frames.has(air_key):
				var poses: Array = definition.state_frames[air_key]
				return poses[clampi(definition.jump_speed-vy,0,poses.size()-1)]
		elif key!=state and definition.state_frames.has(key):
			var reaction: Array = definition.state_frames[key]
			var age := state_tick
			if state=="launch": age = 18-vy if vy>=0 else -vy-1
			elif state=="hit":
				@warning_ignore("integer_division") # 受击帧按硬直tick比例取整。
				age = state_tick*reaction.size()/maxi(1,motion.duration)
			return reaction[clampi(age,0,reaction.size()-1)]
		if definition.state_frames.has(state):
			var posture: Array = definition.state_frames[state]
			var age := state_tick
			if state in ["blockstun","crouch_blockstun","guardbreak"]:
				@warning_ignore("integer_division") # 硬直帧按tick比例取整。
				age = state_tick*posture.size()/maxi(1,motion.duration)
			return posture[age%posture.size() if state in ["idle","crouch","stun","charge"] else mini(age,posture.size()-1)]
		return {"sprite": 0, "hitboxes": [], "hurtboxes": [[-18, 0, 36, 128]], "cancel": [], "events": [], "dx": 0, "dy": 0}
	var frames: Array = definition.moves[move_id].frames
	return frames[clampi(move_tick, 0, frames.size() - 1)]

func visual_pose() -> Dictionary:
	var spec := _pose_spec(true)
	var current_frame := frame()
	return {
		"key": str(spec.key),
		"tick": int(spec.tick),
		"move_sprite": int(current_frame.get("sprite", 0)),
		"state_tick": state_tick,
		"move_tick": move_tick,
	}

func animation_key() -> String:
	return str(visual_pose().key)

func _pose_spec(allow_crouch_resume: bool) -> Dictionary:
	if allow_crouch_resume and has_hit_crouch_guard_resume():
		return {"key": "crouch_guard", "tick": state_tick}
	if CurrentCapture.active(self):
		return {"key": str(motion.throw_current_capture.animation), "tick": state_tick}
	if state == "captured" and motion.has_capture_victim():
		return {"key": str(motion.capture_victim.animation), "tick": state_tick}
	if state == "transform":
		return {"key": str(battle_form.get("transform_animation", "transformation")), "tick": move_tick if not move_id.is_empty() else state_tick}
	if state == "form_entry":
		return {"key": str(battle_form.get("entry_animation", "form_entry")), "tick": state_tick}
	if not move_id.is_empty():
		return {"key": "crush" if move_id.begins_with("crush_charge") else move_id, "tick": move_tick}
	if state == "crush_charge":
		return {"key": "crush", "tick": 0}
	if state=="thrown":
		return {"key": motion.pose if not motion.pose.is_empty() else "grabbed", "tick": state_tick}
	if state=="hit":
		return {"key": motion.hit_pose if not motion.hit_pose.is_empty() else "hit_high", "tick": state_tick}
	if state=="launch":
		return {"key": "launch_rise" if vy>=0 else "launch_fall", "tick": state_tick}
	if state == "walk":
		return {"key": "walk_forward" if resolver.previous_x * facing > 0 else "walk_back", "tick": state_tick}
	if state == "takeoff" and motion.jump_kind == "chase":
		return {"key": "chase_takeoff", "tick": state_tick}
	if state == "air":
		var air_key := "flip_forward" if motion.jump_kind == "diagonal" else "flip_back" if motion.jump_kind == "backward" else "chase_takeoff" if motion.jump_kind == "chase" else "vertical_jump"
		@warning_ignore("integer_division") # 空中动画相位按垂直速度取整。
		var air_tick := clampi((16-vy-2)/8,0,3)*8 if air_key == "flip_back" else clampi((16-vy-2)/8,0,3)*3 if air_key == "flip_forward" else 16-vy
		return {"key": air_key, "tick": air_tick}
	return {"key": state, "tick": state_tick}

func clear_move() -> void:
	motion.hit_crouch_guard_resume = false
	motion.crush_chargeable = false
	motion.crush_stamina_paid = 0
	motion.crush_fire = 0
	move_id = ""
	move_tick = 0
	combat.connected = false
	combat.confirmed = false
	combat.blocked = false
	combat.clear_hit_groups()

func clear_input_buffer() -> void:
	UfeInputBuffer.clear(combat)

## 最近两条指令。相同指令只刷新计时；第三条挤掉最旧的一条。
func remember_command(move_id_to_keep: String, ticks: int) -> void:
	UfeInputBuffer.remember(combat, move_id_to_keep, ticks)

func snapshot() -> Array:
	var result: Array = [definition.id, x, height, vx, vy, facing, state, state_tick, move_id, move_tick,
		stats.to_dict(), combat.to_dict(), motion.to_dict(), resolver.snapshot()]
	# 未变身角色保留既有状态序列，便于逐tick基线比较。
	if transformed_this_round or not form_id.is_empty():
		result.append([base_definition.id, form_id, transformed_this_round])
	return result
