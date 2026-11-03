class_name UfeStageArtLibrary
extends RefCounted
## One static environment package, shared across rematches. No per-frame IO.
const MANIFEST := "res://assets/stages/city/neo-night/v001/manifest.json"
static var _cached: Dictionary = {}

static func package() -> Dictionary:
	if not _cached.is_empty(): return _cached
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	assert(data.get("kind") == "ufe-layered-stage")
	var textures := {}
	for key in data.layers:
		textures[key] = load(str(data.layers[key].texture)) as Texture2D
		assert(textures[key] != null)
	textures.sky = load(str(data.sky.texture)) as Texture2D
	assert(textures.sky != null and textures.size() <= int(data.texture_limit))
	_cached = {"data": data, "textures": textures}
	return _cached

static func point(value: Array) -> Vector2:
	return Vector2(float(value[0]), float(value[1]))

static func tint(value: Array) -> Color:
	return Color(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
