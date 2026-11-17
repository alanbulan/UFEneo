extends RefCounted
## 可选受方root offset。缺字段/身份沿原默认；不会把非法覆盖静默换成零点。
const REVISION := 1

static func integer(value: Variant) -> bool:
	# JSON数值可能是float；只接受有限且数学上为整数的值，bool不属于数值。
	return (value is int or value is float) and is_finite(float(value)) and value==int(value)

static func valid(table: Variant) -> bool:
	if not table is Dictionary:return false
	# 空表等同没有匹配身份，仍走原root；存在的每个键/点都必须合法。
	for identity in table:
		if not identity is String or identity.strip_edges().is_empty() or identity!=identity.strip_edges():return false
		var point: Variant=table[identity]
		if not point is Array or point.size()!=2:return false
		if not integer(point[0]) or not integer(point[1]):return false
	return true

static func offset(victim: UfeFighter, target: Dictionary) -> Array:
	if not target.has("root_overrides"):return target.get("root",[0,0])
	var table: Variant=target.root_overrides
	if not valid(table):return []
	return table.get(victim.definition.id,target.get("root",[0,0]))

static func used_in(data: Variant) -> bool:
	# 扫描实际参与指纹的模拟数据，含开放可达形态；锁定形态只有id/false。
	if data is Dictionary:
		if data.has("root_overrides"):return true
		for value in data.values():
			if used_in(value):return true
	elif data is Array:
		for value in data:
			if used_in(value):return true
	return false
