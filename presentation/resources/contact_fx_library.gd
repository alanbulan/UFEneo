class_name UfeContactFxLibrary
extends RefCounted
## Common contact art is separate from fighter identity, move data and simulation.
# 目录含 .gdignore，编辑器不注册 class_name；显式 preload 才能在本文件内解析依赖。
const SpriteLibrary = preload("res://presentation/resources/sprite_library.gd")
const PATH := "res://content/presentation/contact_effects.json"
const CACHE_LIMIT := 8
static var _catalog: Dictionary = {}
static var _assets: Dictionary = {}
static var _order: Array[String] = []
static var manifest_loads := 0

static func for_kind(kind: String) -> Dictionary:
	if _catalog.is_empty():
		_catalog = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	var choice: Dictionary = _catalog.contacts.get(kind, _catalog.contacts.LIGHT)
	var id := str(choice.effect)
	var result := _asset(id, _catalog.effects[id])
	result["scale"] = float(choice.scale)
	return result

static func for_study(row: Dictionary) -> Dictionary:
	var result := for_asset(row)
	result["scale"] = 1
	return result

static func for_asset(row: Dictionary) -> Dictionary:
	# Shared, bounded atlas storage for contact art and travelling skill effects.
	var result := _asset(str(row.id), row)
	result["scale"] = float(row.get("scale",1))
	return result

static func _asset(id: String, source: Dictionary) -> Dictionary:
	var key := str(source.manifest) + "|" + str(source.review)
	if not _assets.has(key):
		var frames := SpriteLibrary.load_frames(str(source.manifest))
		var review: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(str(source.review)))
		_assets[key] = {"frames": frames, "anchor": Vector2(review.anchor_px[0], review.anchor_px[1])}
		manifest_loads += 1
		while _assets.size() > CACHE_LIMIT:
			_assets.erase(_order.pop_front())
	_order.erase(key)
	_order.append(key)
	var result: Dictionary = _assets[key].duplicate()
	result.merge({"state": str(source.state), "mirror": bool(source.mirror), "id": id})
	return result

static func transform_for(visual: Dictionary, position: Vector2, facing: int) -> Transform2D:
	var scale := float(visual.scale)
	var direction := -1.0 if visual.mirror and facing < 0 else 1.0
	var x := Vector2(scale * direction, 0)
	var y := Vector2(0, scale)
	var anchor: Vector2 = visual.anchor
	return Transform2D(x, y, position.round() - x * anchor.x - y * anchor.y)
