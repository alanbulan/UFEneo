extends RefCounted
## 显式可选的空中接触起相保留。无配置时旧投完全走旧路径；只读整数招式/受方框。
const HoldPoints = preload("res://core/combat/throw_hold_points.gd")
const RootOffsets = preload("res://core/combat/throw_root_offsets.gd")
const REVISION := 1

static func integer(v: Variant, low: int, high: int) -> bool:
	return (v is int or v is float) and is_finite(float(v)) and v == int(v) and int(v) >= low and int(v) <= high

static func valid_move(move: Dictionary) -> bool:
	var frames: Variant=move.get("frames",null)
	if not frames is Array or frames.is_empty():return false
	for frame in frames:
		if not frame is Dictionary:return false
		var target: Variant=frame.get("target",{})
		if not target is Dictionary:return false
		if move.has("throw_current_capture"):
			if not frame.get("hitboxes",null) is Array:return false
			for hit in frame.hitboxes:
				if not hit is Array or hit.size()!=4:return false
				for coordinate in hit:
					if not RootOffsets.integer(coordinate):return false
	if not move.has("throw_current_capture"):
		for frame in move.get("frames",[]):
			if str(frame.get("target",{}).get("mode","")) == "capture_current": return false
		return true
	var data: Variant = move.throw_current_capture
	if not data is Dictionary or str(move.get("kind","")) != "throw" or not move.get("throw_target_air",null) is bool or move.throw_target_air != true: return false
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
		if i>=int(data.first_tick) and i<=int(data.entry_tick):
			# v1只接地面静止攻击方，不能在保相期移动背部而扩大入口误差。
			for axis in ["dx","dy"]:
				if not integer(move.frames[i].get(axis,null),0,0):return false
			if move.frames[i].has("throw_height"):return false
		var mode: String = str(move.frames[i].get("target",{}).get("mode",""))
		if (mode == "capture_current") != (i >= int(data.first_tick) and i < int(data.entry_tick)): return false
		if not move.frames[i].hitboxes.is_empty() and (i < int(data.first_tick) or i >= int(data.entry_tick)): return false
	var entry: Dictionary = move.frames[int(data.entry_tick)].get("target",{})
	if str(entry.get("mode",""))!="hold" or not HoldPoints.valid(entry.get("hold_point_overrides",null)):return false
	if not entry.get("pose",null) is String or str(entry.pose).is_empty():return false
	if not integer(entry.get("sprite",0),0,2147483647) or not integer(entry.get("facing",-1),-1,1) or int(entry.get("facing",-1))==0:return false
	for key in ["grip","root"]:
		var point: Variant=entry.get(key,[0,0] if key=="root" else null)
		if not point is Array or point.size()!=2:return false
		for coordinate in point:
			if not RootOffsets.integer(coordinate):return false
	return not entry.has("root_overrides") or RootOffsets.valid(entry.root_overrides)

static func box(f: UfeFighter, local: Array) -> Rect2i:
	return Rect2i(f.x+int(local[0]) if f.facing>0 else f.x-int(local[0])-int(local[2]),f.height+int(local[1]),int(local[2]),int(local[3]))

static func eligible(a: UfeFighter, b: UfeFighter, move: Dictionary) -> bool:
	if not move.has("throw_current_capture"): return true
	if not valid_move(move): return false
	var data: Dictionary = move.throw_current_capture
	if a.height!=0 or a.vy!=0:return false
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
	# v1仅接受固定承重相；否则floor-safe/variants可能改变实际入口根点。
	var pose: Dictionary=poses[index]
	for key in ["throw_hold_variants","throw_hold_floor_variants"]:
		var variants: Variant=pose.get(key,[])
		if not variants is Array or not variants.is_empty():return false
	var point: Array = HoldPoints.point(b,next,pose)
	if point.is_empty(): return false
	var offset: Array = RootOffsets.offset(b,next)
	if offset.is_empty(): return false
	var desired_x: int = a.x+a.facing*(int(next.grip[0])+int(offset[0])-int(next.get("facing",-1))*int(point[0]))
	var desired_height: int = a.height+int(next.grip[1])+int(offset[1])-int(point[1])
	return absi(b.x-desired_x) <= int(data.max_entry_root_delta[0]) and absi(b.height-desired_height) <= int(data.max_entry_root_delta[1])

static func remember(b: UfeFighter, move: Dictionary) -> void:
	b.motion.erase("throw_current_capture")
	if not move.has("throw_current_capture"): return
	b.motion.throw_current_capture = {"active":true,"animation":b.animation_key(),"frame":b.frame().duplicate(true),
		"x":b.x,"height":b.height,"facing":b.facing,"vx":b.vx,"vy":b.vy,"state":b.state,
		"state_tick":b.state_tick,"move_id":b.move_id,"move_tick":b.move_tick,
		"motion":b.motion.duplicate(true)}

static func preserve(b: UfeFighter, target: Dictionary) -> bool:
	if str(target.get("mode","")) != "capture_current":
		b.motion.erase("throw_current_capture")
		return false
	var current: Dictionary = b.motion.get("throw_current_capture",{})
	if current.is_empty(): return false
	current.active = true
	b.x = int(current.x); b.height = int(current.height); b.facing = int(current.facing)
	return true

static func active(b: UfeFighter) -> bool:
	return b.state=="thrown" and bool(b.motion.get("throw_current_capture",{}).get("active",false))

static func visual_fighter(b: UfeFighter) -> UfeFighter:
	# 表现只读副本重用原动画解析，避免另写一套跳跃相位算法。
	var saved: Dictionary=b.motion.throw_current_capture
	var view:=UfeFighter.new(b.definition,int(saved.x))
	view.height=int(saved.height);view.facing=int(saved.facing)
	view.vx=int(saved.vx);view.vy=int(saved.vy)
	view.state=str(saved.state);view.state_tick=int(saved.state_tick)
	view.move_id=str(saved.move_id);view.move_tick=int(saved.move_tick)
	view.motion=saved.motion.duplicate(true)
	view.battle_form=b.battle_form
	return view

static func used_in(data: Variant) -> bool:
	if data is Dictionary:
		if data.has("throw_current_capture"):return true
		for value in data.values():
			if used_in(value):return true
	elif data is Array:
		for value in data:
			if used_in(value):return true
	return false
