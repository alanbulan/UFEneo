class_name UfeMoveData
extends RefCounted
const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")
const HoldPoints = preload("res://core/combat/throw_hold_points.gd")
const RootOffsets = preload("res://core/combat/throw_root_offsets.gd")
## 每个 tick 均显式包含图片索引、位移、框、取消窗口和事件。
static func validate(move: Dictionary) -> bool:
	if not move.get("frames",null) is Array or move.frames.is_empty():
		return false
	if not CurrentCapture.valid_move(move):return false
	if move.has("throw_target_air"):
		if not move.throw_target_air is bool or str(move.get("kind",""))!="throw":return false
	if move.has("air_only"):
		if not move.air_only is bool:return false
		if move.air_only and (not move.get("air_allowed",false) is bool or not bool(move.get("air_allowed",false))):return false
	if move.has("stamina_regen") and not valid_stamina_regen(move.stamina_regen):return false
	for frame in move.frames:
		for key in ["sprite", "dx", "dy", "hitboxes", "hurtboxes", "cancel", "events"]:
			if not frame.has(key): return false
		for box in frame.hitboxes + frame.hurtboxes:
			if box.size() != 4 or int(box[2]) <= 0 or int(box[3]) <= 0: return false
		var target: Dictionary=frame.get("target",{})
		if target.has("root_overrides") and not RootOffsets.valid(target.root_overrides):return false
		if str(target.get("mode",""))=="hold" and target.has("hold_point_overrides") and not HoldPoints.valid(target.hold_point_overrides):return false
		if frame.has("melee_guard"):
			if not frame.melee_guard is String or frame.melee_guard!="block" or not valid_guard_box(frame.get("guard_box",null)):return false
		for key in ["guard_effect","guard_sound"]:
			if frame.has(key) and (not frame[key] is String or str(frame[key]).is_empty()):return false
		if frame.has("guard_respects_unblockable") and not frame.guard_respects_unblockable is bool:return false
		var weapon_ids: Dictionary={}
		for shot in frame.get("shots",[]):
			if not shot is Dictionary or not valid_projectile(shot,move.frames.size()):return false
			if shot.has("weapon_id"):
				if weapon_ids.has(str(shot.weapon_id)):return false
				weapon_ids[str(shot.weapon_id)]=true
			if bool(shot.get("capture",false)) and not move.has("capture"):return false
		for shot in frame.get("shots",[]):
			if shot.has("pair_trail_peer_id") and not weapon_ids.has(str(shot.pair_trail_peer_id)):return false
	if not valid_projectile(move.get("projectile",{}),move.frames.size()):return false
	if bool(move.get("projectile",{}).get("capture",false)) and not move.has("capture"):return false
	if move.has("capture") and not UfeCaptureResolver.valid_move(move):return false
	return UfeMeleeHitGroups.validate(move)

static func valid_stamina_regen(value: Variant) -> bool:
	if not (value is int or value is float):return false
	return is_finite(float(value)) and value==int(value) and int(value)>=0 and int(value)<=4

static func valid_guard_box(box: Variant) -> bool:
	if not box is Array or box.size()!=4:return false
	for value in box:
		if not (value is int or value is float) or not is_finite(float(value)) or value!=int(value):return false
	return int(box[2])>0 and int(box[3])>0

static func valid_projectile(shot: Dictionary, frame_count: int) -> bool:
	if shot.has("capture") and not shot.capture is bool:return false
	if shot.has("clip_below_ground"):
		if not shot.clip_below_ground is bool:return false
		if shot.clip_below_ground and not bool(shot.get("beam",false)):return false
	if shot.has("frame_hitboxes"):
		if not shot.frame_hitboxes is Array or shot.frame_hitboxes.is_empty():return false
		for phase in shot.frame_hitboxes:
			if not phase is Array:return false
			for box in phase:
				if not valid_guard_box(box):return false
	if shot.has("expire_below_height"):
		var height: Variant=shot.expire_below_height
		if not (height is int or height is float) or not is_finite(float(height)) or height!=int(height) or int(height)<0:return false
	return valid_follow_origin(shot,frame_count) and valid_explicit_returning_weapon(shot,frame_count)

static func valid_follow_origin(shot: Dictionary, frame_count: int) -> bool:
	if not shot.has("origin_by_frame"):return true
	if not bool(shot.get("beam",false)) or not shot.origin_by_frame is Dictionary or shot.origin_by_frame.is_empty():return false
	for key in shot.origin_by_frame:
		if not key is String or not key.is_valid_int() or str(int(key))!=key or int(key)<0 or int(key)>=frame_count:return false
		var point:Variant=shot.origin_by_frame[key]
		if not point is Array or point.size()!=2:return false
		for coordinate in point:
			if not (coordinate is int or coordinate is float) or not is_finite(float(coordinate)) or coordinate!=int(coordinate):return false
	return true

static func explicit_weapon_integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==int(value)

static func explicit_weapon_point(point: Variant, positive_height: bool=false) -> bool:
	if not point is Array or point.size()!=2:return false
	for coordinate in point:
		if not explicit_weapon_integer(coordinate):return false
	return not positive_height or int(point[1])>=0

static func valid_explicit_returning_weapon(shot: Dictionary, frame_count: int) -> bool:
	var enabled: bool=false
	for field in ["weapon_id","return_anchor_by_tick","owner_interrupt_policy","return_effect","return_sound","pair_trail_effect","pair_trail_peer_id","return_not_before_tick"]:
		if shot.has(field):enabled=true
	if not enabled:return true # 旧招式验证和默认字段保持。
	var identity: Variant=shot.get("weapon_id",null)
	if not identity is String or identity.strip_edges().is_empty() or identity!=identity.strip_edges():return false
	if str(shot.get("owner_interrupt_policy",""))!="clear" or not shot.get("owner_interrupt_policy",null) is String:return false
	if bool(shot.get("beam",false)) or bool(shot.get("capture",false)):return false
	var path: Variant=shot.get("integer_path",null)
	if not path is Array or path.is_empty() or path.size()>frame_count:return false
	for point in path:
		if not explicit_weapon_point(point):return false
	if int(path[0][0])!=0 or int(path[0][1])!=0:return false
	var duration: Variant=shot.get("return_ticks",null)
	if not explicit_weapon_integer(duration) or int(duration)<=0 or int(duration)>frame_count:return false
	# 可选最早接回相；仅显式返航武器启用，等待期间仍跟随当前腕点。
	if shot.has("return_not_before_tick"):
		var catch_tick: Variant=shot.return_not_before_tick
		if not explicit_weapon_integer(catch_tick) or int(catch_tick)<0 or int(catch_tick)>=frame_count:return false
	var life: Variant=shot.get("life",null)
	if not explicit_weapon_integer(life) or int(life)<path.size()+int(duration):return false
	if not explicit_weapon_point(shot.get("spawn",null),true) or not explicit_weapon_point(shot.get("return_anchor",null),true):return false
	var anchors: Variant=shot.get("return_anchor_by_tick",null)
	if not anchors is Dictionary or anchors.is_empty():return false
	for key in anchors:
		if not key is String or not key.is_valid_int() or str(int(key))!=key or int(key)<0 or int(key)>=frame_count:return false
		if not explicit_weapon_point(anchors[key],true):return false
	for field in ["return_effect","return_sound","pair_trail_effect","pair_trail_peer_id"]:
		if shot.has(field) and (not shot[field] is String or str(shot[field]).strip_edges().is_empty()):return false
	if shot.has("pair_trail_effect")!=shot.has("pair_trail_peer_id"):return false
	if shot.has("pair_trail_peer_id") and str(shot.pair_trail_peer_id)==str(identity):return false
	for field in ["max_hits","hit_interval"]:
		if shot.has(field) and (not explicit_weapon_integer(shot[field]) or int(shot[field])<=0):return false
	if shot.has("locked_moves"):
		if not shot.locked_moves is Array or shot.locked_moves.is_empty():return false
		var seen: Dictionary={}
		for move_id in shot.locked_moves:
			if not move_id is String or move_id.is_empty() or seen.has(move_id):return false
			seen[move_id]=true
	if shot.has("hit_overrides"):
		if not shot.hit_overrides is Dictionary:return false
		for field in shot.hit_overrides:
			var value: Variant=shot.hit_overrides[field]
			if field=="knockdown":
				if not value is bool:return false
			elif field in ["damage","chip_damage","pushback","stun"]:
				if not explicit_weapon_integer(value) or (field!="pushback" and int(value)<0):return false
			else:return false
	return true
