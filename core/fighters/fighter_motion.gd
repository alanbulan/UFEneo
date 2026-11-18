class_name UfeFighterMotion
extends RefCounted
## 参战角色的强类型移动、受击姿态、蓄力与投/捕获状态。

var jump_kind: String = "vertical"
var jump_x: int = 0
var jump_buffer: int = 0
var direction: int = 1
var duration: int = 0
var chase_window: int = 0
var land_window: int = 0
var bounce_followup: bool = false
var bounce_velocity: int = 11
var dodge_tired: bool = false
var tech_direction: int = 0
var push_vx: int = 0
var crush_chargeable: bool = false
var crush_hold: int = 0
var crush_tier: int = 1
var crush_fire: int = 0
var crush_stamina_paid: int = 0
var hit_pose: String = ""
var hit_crouch_guard_resume: bool = false
var pose: String = ""
var pose_sprite: int = 0
var ko_grounded_pose: Dictionary = {}
var throw_move: String = ""
var throw_origin_height: int = 0
var throw_released: bool = false
var release_x: int = 0
var release_height: int = 0
var release_goal_x: int = 0
var throw_current_capture: Dictionary = {}
var capture: Dictionary = {}
var capture_victim: Dictionary = {}


func has_capture() -> bool:
	return not capture.is_empty()


func clear_capture() -> void:
	capture = {}


func has_capture_victim() -> bool:
	return not capture_victim.is_empty()


func clear_capture_victim() -> void:
	capture_victim = {}


func has_throw_current_capture() -> bool:
	return not throw_current_capture.is_empty()


func clear_throw_current_capture() -> void:
	throw_current_capture = {}


func has_ko_grounded_pose() -> bool:
	return not ko_grounded_pose.is_empty()


func clear_ko_grounded_pose() -> void:
	ko_grounded_pose = {}


func duplicate_state() -> UfeFighterMotion:
	var copy := UfeFighterMotion.new()
	copy.jump_kind = jump_kind
	copy.jump_x = jump_x
	copy.jump_buffer = jump_buffer
	copy.direction = direction
	copy.duration = duration
	copy.chase_window = chase_window
	copy.land_window = land_window
	copy.bounce_followup = bounce_followup
	copy.bounce_velocity = bounce_velocity
	copy.dodge_tired = dodge_tired
	copy.tech_direction = tech_direction
	copy.push_vx = push_vx
	copy.crush_chargeable = crush_chargeable
	copy.crush_hold = crush_hold
	copy.crush_tier = crush_tier
	copy.crush_fire = crush_fire
	copy.crush_stamina_paid = crush_stamina_paid
	copy.hit_pose = hit_pose
	copy.hit_crouch_guard_resume = hit_crouch_guard_resume
	copy.pose = pose
	copy.pose_sprite = pose_sprite
	copy.ko_grounded_pose = ko_grounded_pose.duplicate(true)
	copy.throw_move = throw_move
	copy.throw_origin_height = throw_origin_height
	copy.throw_released = throw_released
	copy.release_x = release_x
	copy.release_height = release_height
	copy.release_goal_x = release_goal_x
	copy.throw_current_capture = throw_current_capture.duplicate(true)
	copy.capture = capture.duplicate(true)
	copy.capture_victim = capture_victim.duplicate(true)
	return copy


static func from_dict(d: Dictionary) -> UfeFighterMotion:
	var result := UfeFighterMotion.new()
	result.jump_kind = str(d.get("jump_kind", "vertical"))
	result.jump_x = int(d.get("jump_x", 0))
	result.jump_buffer = int(d.get("jump_buffer", 0))
	result.direction = int(d.get("direction", 1))
	result.duration = int(d.get("duration", 0))
	result.chase_window = int(d.get("chase_window", 0))
	result.land_window = int(d.get("land_window", 0))
	result.bounce_followup = bool(d.get("bounce_followup", false))
	result.bounce_velocity = int(d.get("bounce_velocity", 11))
	result.dodge_tired = bool(d.get("dodge_tired", false))
	result.tech_direction = int(d.get("tech_direction", 0))
	result.push_vx = int(d.get("push_vx", 0))
	result.crush_chargeable = bool(d.get("crush_chargeable", false))
	result.crush_hold = int(d.get("crush_hold", 0))
	result.crush_tier = int(d.get("crush_tier", 1))
	result.crush_fire = int(d.get("crush_fire", 0))
	result.crush_stamina_paid = int(d.get("crush_stamina_paid", 0))
	result.hit_pose = str(d.get("hit_pose", ""))
	result.hit_crouch_guard_resume = bool(d.get("hit_crouch_guard_resume", false))
	result.pose = str(d.get("pose", ""))
	result.pose_sprite = int(d.get("pose_sprite", 0))
	result.ko_grounded_pose = _dup_dict(d.get("ko_grounded_pose", {}))
	result.throw_move = str(d.get("throw_move", ""))
	result.throw_origin_height = int(d.get("throw_origin_height", 0))
	result.throw_released = bool(d.get("throw_released", false))
	result.release_x = int(d.get("release_x", 0))
	result.release_height = int(d.get("release_height", 0))
	result.release_goal_x = int(d.get("release_goal_x", 0))
	result.throw_current_capture = _dup_dict(d.get("throw_current_capture", {}))
	result.capture = _dup_dict(d.get("capture", {}))
	result.capture_victim = _dup_dict(d.get("capture_victim", {}))
	return result


static func _dup_dict(raw: Variant) -> Dictionary:
	return (raw as Dictionary).duplicate(true) if raw is Dictionary else {}


func to_dict() -> Dictionary:
	var result: Dictionary = {
		"jump_kind": jump_kind,
		"jump_x": jump_x,
		"jump_buffer": jump_buffer,
		"direction": direction,
		"duration": duration,
		"chase_window": chase_window,
		"land_window": land_window,
		"bounce_followup": bounce_followup,
		"bounce_velocity": bounce_velocity,
		"dodge_tired": dodge_tired,
		"tech_direction": tech_direction,
		"push_vx": push_vx,
		"crush_chargeable": crush_chargeable,
		"crush_hold": crush_hold,
		"crush_tier": crush_tier,
		"crush_fire": crush_fire,
		"crush_stamina_paid": crush_stamina_paid,
		"hit_pose": hit_pose,
		"pose": pose,
		"pose_sprite": pose_sprite,
		"throw_move": throw_move,
		"throw_origin_height": throw_origin_height,
		"throw_released": throw_released,
		"release_x": release_x,
		"release_height": release_height,
		"release_goal_x": release_goal_x,
	}
	if hit_crouch_guard_resume:
		result["hit_crouch_guard_resume"] = true
	if not ko_grounded_pose.is_empty():
		result["ko_grounded_pose"] = ko_grounded_pose.duplicate(true)
	if not throw_current_capture.is_empty():
		result["throw_current_capture"] = throw_current_capture.duplicate(true)
	if not capture.is_empty():
		result["capture"] = capture.duplicate(true)
	if not capture_victim.is_empty():
		result["capture_victim"] = capture_victim.duplicate(true)
	return result
