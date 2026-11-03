class_name UfeBattleStageCatalog
extends RefCounted
## 正式舞台名册；世界尺寸/碰撞保持由模拟核决定。
const PATH: String="res://content/stages/catalog.json"
static var cached: Dictionary={}

static func data() -> Dictionary:
	if cached.is_empty() and FileAccess.file_exists(PATH):
		cached=UfeContentDatabase.read_json(PATH)
	return cached

static func entries() -> Array:
	return data().get("stages",[])

static func get_stage(id: String) -> Dictionary:
	for item in entries():
		if str(item.id)==id:return item
	return entries()[0] if not entries().is_empty() else {}

static func default_id() -> String:
	return str(data().get("default","coastal-sunset"))

static func valid_id(id: String) -> String:
	for item in entries():
		if str(item.id)==id:return id
	return default_id()
