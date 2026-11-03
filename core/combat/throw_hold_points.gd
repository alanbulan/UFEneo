extends RefCounted
## 显式投技覆盖只读招式及受方整数数据；不猜身份、姿势或旧waist。
static func integer(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==int(value)

static func point_valid(value: Variant) -> bool:
	return value is Array and value.size()==2 and integer(value[0]) and integer(value[1]) and int(value[1])>=0

static func valid(table: Variant) -> bool:
	if not table is Dictionary or table.is_empty():return false
	for id in table:
		if not id is String or id.is_empty() or not table[id] is Dictionary or table[id].is_empty():return false
		for key in table[id]:
			if not key is String or key.is_empty() or not table[id][key] is Dictionary or table[id][key].is_empty():return false
			for sprite in table[id][key]:
				if not sprite is String or not sprite.is_valid_int() or str(int(sprite))!=sprite or int(sprite)<0:return false
				if not point_valid(table[id][key][sprite]):return false
	return true

static func point(b: UfeFighter, target: Dictionary, pose: Dictionary) -> Array:
	var table: Variant=target.get("hold_point_overrides",null)
	if not valid(table):return []
	var poses: Array=b.definition.state_frames.get(str(target.get("pose","")),[])
	if not poses.has(pose):return []
	var sprite: Variant=pose.get("sprite",null)
	if not integer(sprite) or int(sprite)<0:return []
	# state_frames的索引可能重复或重排，键必须取实际帧sprite。
	return table.get(b.definition.id,{}).get(str(target.get("pose","")),{}).get(str(int(sprite)),[])

static func can_capture(b: UfeFighter, move: Dictionary) -> bool:
	for frame in move.frames:
		var target: Dictionary=frame.get("target",{})
		if str(target.get("mode",""))!="hold" or not target.has("hold_point_overrides"):continue
		if not valid(target.hold_point_overrides):return false
		var key: Variant=target.get("pose",null)
		var fallback: Variant=target.get("sprite",0)
		if not key is String or not integer(fallback):return false
		var poses: Array=b.definition.state_frames.get(key,[])
		if int(fallback)<0 or int(fallback)>=poses.size():return false
		var pose: Dictionary=poses[int(fallback)]
		var variants: Variant=pose.get("throw_hold_variants",[])
		var floor_variants: Variant=pose.get("throw_hold_floor_variants",[])
		if not variants is Array or not floor_variants is Array:return false
		# 整段及所有可选分支先查齐，不能先抓中再发现后相缺点。
		for index in [fallback]+variants+floor_variants:
			if not integer(index) or int(index)<0 or int(index)>=poses.size():return false
			if point(b,target,poses[int(index)]).is_empty():return false
	return true
