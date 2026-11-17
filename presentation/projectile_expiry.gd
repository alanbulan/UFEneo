class_name UfeProjectileExpiry
extends RefCounted
## 到期演出只读取显式绑定和已移除弹体的末态，不向模拟添加字段。

static func eligible(projectile: Dictionary, binding: Dictionary, finished: bool) -> bool:
	var ticks := int(binding.get("expiry_ticks", 0))
	return not finished and ticks > 0 and int(projectile.get("age", 0)) >= ticks and int(projectile.get("life", 1)) <= 0 and not bool(projectile.get("connected", false))

static func collect(previous: Array, current: Array, bindings: Dictionary, finished: bool) -> Array:
	var result: Array = []
	for projectile in previous:
		var binding: Dictionary = bindings.get(str(projectile.get("effect", "")), {})
		var effect := str(binding.get("expiry_effect", ""))
		if effect.is_empty() or not eligible(projectile, binding, finished): continue
		if current.any(func(p): return is_same(p, projectile)): continue
		result.append({"id": effect, "x": int(projectile.x), "height": int(projectile.height), "facing": int(projectile.facing)})
	return result
