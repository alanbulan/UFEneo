class_name UfeIdentityCatalog
extends RefCounted
## 身份显示别名与称号目录查询（纯内容数据层，不涉及主题/字体/材质等 UI 资源）。

static var _cache: Dictionary = {}


static func clear_cache() -> void:
	_cache.clear()


static func data() -> Dictionary:
	if _cache.is_empty():
		var parsed: Variant = UfeContentDatabase.read_json("res://content/roster/identity_display.json")
		if parsed is Dictionary:
			_cache = parsed
	return _cache


static func identity_id(id: String) -> String:
	var table := data()
	var aliases: Dictionary = table.get("aliases", {})
	var visited: Dictionary = {}
	while aliases.has(id) and not visited.has(id):
		visited[id] = true
		id = str(aliases[id])
	return id


static func identity_entry(id: String) -> Dictionary:
	var table := data()
	var canonical := identity_id(id)
	return Dictionary(table.get("entries", {}).get(canonical, {}))


static func resolved_id(id: String, form_id: String = "") -> String:
	if form_id.is_empty() or form_id == "default":
		return identity_id(id)
	if not identity_entry(form_id).is_empty():
		return identity_id(form_id)
	var combined := id + "__" + form_id
	return combined if not identity_entry(combined).is_empty() else identity_id(id)
