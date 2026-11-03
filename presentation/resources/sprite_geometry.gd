class_name UfeSpriteGeometry
extends RefCounted
## Atlas pixels and authored coordinates are different units for dense atlases.
## Empty result rejects malformed metadata; legacy manifests use native size.
static func from_manifest(manifest: Dictionary, texture_size: Vector2) -> Dictionary:
	if not texture_size.is_finite() or texture_size.x <= 0 or texture_size.y <= 0:
		return {}
	var display := texture_size
	if manifest.has("display_size"):
		var pair = manifest.display_size
		if not _pair(pair):
			return {}
		display = Vector2(pair[0], pair[1])
		var divisor = manifest.get("texture_divisor", 1)
		if not _number(divisor) or not is_finite(float(divisor)) or float(divisor) < 1 or floorf(float(divisor)) != float(divisor):
			return {}
		if display != texture_size * float(divisor):
			return {}
	elif manifest.has("texture_divisor") and manifest.texture_divisor != 1:
		return {}
	var result := {"display_size": display, "texture_to_display": display / texture_size}
	if manifest.has("ground_origin"):
		var point = manifest.ground_origin
		if not _pair(point):
			return {}
		var ground := Vector2(point[0], point[1])
		if ground.x < 0 or ground.y < 0 or ground.x > display.x or ground.y > display.y:
			return {}
		result["ground_origin"] = ground
	return result

static func _pair(value: Variant) -> bool:
	return value is Array and value.size() == 2 and _number(value[0]) and _number(value[1]) \
		and is_finite(float(value[0])) and is_finite(float(value[1]))

static func _number(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT]
