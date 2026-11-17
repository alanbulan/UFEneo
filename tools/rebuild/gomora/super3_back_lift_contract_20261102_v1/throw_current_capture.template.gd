extends RefCounted
## 显式可选的空中接触起相保留。无配置时旧投完全走旧路径；只读整数招式/受方框。
const HoldPoints = preload("res://core/combat/throw_hold_points.gd")
const REVISION := 1

static func integer(v: Variant, low: int, high: int) -> bool:
	return (v is int or v is float) and is_finite(float(v)) and v == int(v) and int(v) >= low and int(v) <= high

static func valid_move(move: Dictionary) -> bool:
	if not move.has("throw_current_capture"):
		for frame in move.get("frames",[]):
			if str(frame.get("target",{}).get("mode","")) == "capture_current": return false
		return true
	var data: Variant = move.throw_current_capture
	if not data is Dictionary or str(move.get("kind","")) != "throw" or move.get("throw_target_air",false) != true: return false
	if not data.get("target_ids",null) is Array or data.target_ids.is_empty(): return false
	if not data.get("states",null) is Array or data.states.is_empty(): return false
	for values in [data.target_ids,data.states]:
		var seen: Dictionary = {}
		for value in values:
			if not value is String or value.is_empty() or seen.has(value): return false
			seen[value] = true
	if not integer(data.get("body_hurtbox_index",null),0,63): return false
	if not integer(data.get("first_tick",null),0,move.frames.size()-2) or not integer(data.get("entry_tick",null),1,move.frames.size()-1): return false
	if int(data.entry_tick) <= int(data.first_tick) or int(data.entry_tick)-int(data.first_tick) > 4: return false
	var bounds: Variant = data.get("max_entry_root_delta",null)
	if not bounds is Array or bounds.size() != 2: return false
	for n in bounds:
		if not integer(n,0,24): return false
	for i in range(move.frames.size()):
		var mode: String = str(move.frames[i].get("target",{}).get("mode",""))
		if (mode == "capture_current") != (i >= int(data.first_tick) and i < int(data.entry_tick)): return false
		if not move.frames[i].hitboxes.is_empty() and (i < int(data.first_tick) or i >= int(data.entry_tick)): return false
	var entry: Dictionary = move.frames[int(data.entry_tick)].get("target",{})
	return str(entry.get("mode","")) == "hold" and entry.has("hold_point_overrides") and HoldPoints.valid(entry.hold_point_overrides)

static func box(f: UfeFighter, local: Array) -> Rect2i:
	return Rect2i(f.x+int(local[0]) if f.facing>0 else f.x-int(local[0])-int(local[2]),f.height+int(local[1]),int(local[2]),int(local[3]))

static func eligible(a: UfeFighter, b: UfeFighter, move: Dictionary) -> bool:
	if not move.has("throw_current_capture"): return true
	if not valid_move(move): return false
	var data: Dictionary = move.throw_current_capture
	if b.definition.id not in data.target_ids or b.state not in data.states or b.height <= 0: return false
	if a.move_tick < int(data.first_tick) or a.move_tick >= int(data.entry_tick): return false
	var hurt: Array = b.frame().hurtboxes
	if int(data.body_hurtbox_index) >= hurt.size(): return false
	var contact := false
	for hit in a.frame().hitboxes:
		if box(a,hit).intersects(box(b,hurt[int(data.body_hurtbox_index)])): contact = true
	if not contact: return false
	# 接触已真实成立后，另查首承重相离当前根的有限距离；不移动根、不改waist或扩框。
	var next: Dictionary = move.frames[int(data.entry_tick)].target
	var poses: Array = b.definition.state_frames.get(str(next.pose),[])
	var index: int = int(next.get("sprite",0))
	if index < 0 or index >= poses.size(): return false
	var point: Array = HoldPoints.point(b,next,poses[index])
	if point.is_empty(): return false
	var offset: Array = next.get("root",[0,0])
	var desired_x: int = a.x+a.facing*(int(next.grip[0])+int(offset[0])-int(next.get("facing",-1))*int(point[0]))
	var desired_height: int = a.height+int(next.grip[1])+int(offset[1])-int(point[1])
	return absi(b.x-desired_x) <= int(data.max_entry_root_delta[0]) and absi(b.height-desired_height) <= int(data.max_entry_root_delta[1])

static func remember(b: UfeFighter, move: Dictionary) -> void:
	b.motion.erase("throw_current_capture")
	if not move.has("throw_current_capture"): return
	b.motion.throw_current_capture = {"active":true,"animation":b.animation_key(),"frame":b.frame().duplicate(true),
		"x":b.x,"height":b.height,"facing":b.facing,"vx":b.vx,"vy":b.vy,"state":b.state,
		"state_tick":b.state_tick,"jump_kind":str(b.motion.get("jump_kind","vertical"))}

static func preserve(b: UfeFighter, target: Dictionary) -> bool:
	if str(target.get("mode","")) != "capture_current":
		if b.motion.has("throw_current_capture"): b.motion.throw_current_capture.active = false
		return false
	var current: Dictionary = b.motion.get("throw_current_capture",{})
	if current.is_empty(): return false
	current.active = true
	b.x = int(current.x); b.height = int(current.height); b.facing = int(current.facing)
	return true
