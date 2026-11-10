class_name UfeFighter
extends RefCounted
const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")
# 追击许可只属于尚未被中断的可行动链；自然收招清move不清此窗口。
const CHASE_ACTIONABLE_STATES := ["idle","walk","dash","backstep","dodge","crouch","crouch_start","crouch_rise","guard","crouch_guard","air","charge","takeoff","turn","crouch_turn","charge_start","charge_stop","attack","air_attack","land"]
var definition: UfeFighterDefinition
var base_definition: UfeFighterDefinition
var battle_form: Dictionary = {}
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
var stats: Dictionary = {"hp": 1000, "energy": 0, "stamina": 1000, "stun": 0, "stun_immune": 0,
	"chill_ticks": 0, "chill_percent": 100}
var combat: Dictionary = {"buffer": "", "buffer_ticks": 0, "connected": false, "confirmed": false,
	"combo": 0, "combo_ticks": 0, "bounced": false, "invulnerable": 0, "thrower": -1, "throw_age": 0, "power": 1}
var motion: Dictionary = {"jump_kind": "vertical", "direction": 1, "duration": 0, "chase_window": 0, "land_window": 0, "bounce_followup":false}
var resolver := UfeCommandResolver.new()

func _init(data: UfeFighterDefinition, start_x: int) -> void:
	definition = data
	base_definition = data
	x = start_x
	stats.hp = data.max_health

func enter(id: String, duration: int = 0) -> void:
	# 仅让本次受击后的原crouch→crouch_guard携带恢复姿态；不改变逻辑状态时序。
	if not (state=="crouch" and id=="crouch_guard"):motion.erase("hit_crouch_guard_resume")
	if id!="thrown":motion.erase("throw_current_capture")
	state = id
	if not chase_allowed(): motion.chase_window = 0
	state_tick = 0
	motion.duration = duration

func chase_allowed() -> bool:
	return state in CHASE_ACTIONABLE_STATES

func has_hit_crouch_guard_resume() -> bool:
	return bool(motion.get("hit_crouch_guard_resume",false)) and height==0 and move_id.is_empty() and state in ["crouch","crouch_guard"] and not definition.state_frames.get("crouch_guard",[]).is_empty()

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
	if state == "captured" and motion.has("capture_victim"):
		var captured: Dictionary = motion.capture_victim
		var poses: Array = definition.state_frames.get(str(captured.animation),[])
		if not poses.is_empty(): return poses[clampi(int(captured.frame),0,poses.size()-1)]
	if state == "form_entry":
		var entry: Array = battle_form.get("entry_frames", [])
		if not entry.is_empty(): return entry[mini(state_tick, entry.size()-1)]
	if move_id.is_empty():
		var key := _unmapped_animation_key()
		if state=="thrown" and definition.state_frames.has(key):
			var poses: Array=definition.state_frames[key]
			return poses[clampi(int(motion.get("pose_sprite",0)),0,poses.size()-1)]
		if state=="takeoff" and motion.jump_kind=="chase":key="chase_takeoff"
		if state=="walk":
			var walk_key: String="walk_forward" if resolver.previous_x*facing>0 else "walk_back"
			if definition.state_frames.has(walk_key):
				var stride: Array=definition.state_frames[walk_key]
				return stride[state_tick%stride.size()]
		if key!=state and definition.state_frames.has(key):
			var reaction: Array = definition.state_frames[key]
			var age := state_tick
			if state=="launch": age = 18-vy if vy>=0 else -vy-1
			elif state=="hit":
				@warning_ignore("integer_division") # 受击帧按硬直tick比例取整。
				age = state_tick*reaction.size()/maxi(1,int(motion.duration))
			return reaction[clampi(age,0,reaction.size()-1)]
		var air_key := str(motion.jump_kind)+"_air"
		if state == "air" and definition.state_frames.has(air_key):
			var poses: Array = definition.state_frames[air_key]
			return poses[clampi(definition.jump_speed-vy,0,poses.size()-1)]
		if definition.state_frames.has(state):
			var posture: Array = definition.state_frames[state]
			var age := state_tick
			if state in ["blockstun","crouch_blockstun","guardbreak"]:
				@warning_ignore("integer_division") # 硬直帧按tick比例取整。
				age = state_tick*posture.size()/maxi(1,int(motion.duration))
			return posture[age%posture.size() if state in ["idle","crouch","stun","charge"] else mini(age,posture.size()-1)]
		return {"sprite": 0, "hitboxes": [], "hurtboxes": [[-18, 0, 36, 128]], "cancel": [], "events": [], "dx": 0, "dy": 0}
	var frames: Array = definition.moves[move_id].frames
	return frames[clampi(move_tick, 0, frames.size() - 1)]

func animation_key() -> String:
	if has_hit_crouch_guard_resume():return "crouch_guard"
	return _unmapped_animation_key()

func _unmapped_animation_key() -> String:
	if CurrentCapture.active(self):return str(motion.throw_current_capture.animation)
	if state == "captured" and motion.has("capture_victim"): return str(motion.capture_victim.animation)
	if state == "transform": return str(battle_form.get("transform_animation", "transformation"))
	if state == "form_entry": return str(battle_form.get("entry_animation", "form_entry"))
	if not move_id.is_empty(): return move_id
	if state=="thrown":return str(motion.get("pose","grabbed"))
	if state=="hit": return str(motion.get("hit_pose","hit_high"))
	if state=="launch": return "launch_rise" if vy>=0 else "launch_fall"
	return state

func clear_move() -> void:
	motion.erase("hit_crouch_guard_resume")
	move_id = ""
	move_tick = 0
	combat.connected = false
	combat.confirmed = false
	combat.erase("hit_groups")

func snapshot() -> Array:
	var result: Array = [definition.id, x, height, vx, vy, facing, state, state_tick, move_id, move_tick,
		stats, combat, motion, resolver.snapshot()]
	# 未变身角色保留既有状态序列，便于逐tick基线比较。
	if transformed_this_round or not form_id.is_empty():
		result.append([base_definition.id, form_id, transformed_this_round])
	return result
