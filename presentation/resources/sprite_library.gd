class_name UfeSpriteLibrary
extends RefCounted
# 目录含 .gdignore，编辑器不注册 class_name；显式 preload 才能在本文件内解析依赖。
const SpriteGeometry = preload("res://presentation/resources/sprite_geometry.gd")
const ImageAlpha = preload("res://presentation/resources/image_alpha.gd")
const MAX_BUNDLES := 8
static var bundle_cache: Dictionary = {}
static var bundle_order: Array[String] = []
static var texture_bounds: Dictionary = {}
## Curated sprite-gen output only. Absolute frame rectangles and per-frame times.
static func frame_at_tick(frames: SpriteFrames, state: StringName, tick: int) -> int:
	# SpriteFrames stores durations at float precision. A rational 60Hz boundary
	# may otherwise lag one tick (383.333333ms vs stored 383.333344ms).
	return frame_at_msec(frames, state, maxi(0, tick) * (1000.0 / 60.0) + 0.001)

static func frame_at_msec(frames: SpriteFrames, state: StringName, elapsed: float, hold_last := true) -> int:
	if frames == null or not frames.has_animation(state) or frames.get_frame_count(state) == 0:
		return -1
	var total := 0.0
	for index in range(frames.get_frame_count(state)):
		total += frames.get_frame_duration(state, index)
	if total <= 0:
		return -1
	elapsed = maxf(0, elapsed)
	if not frames.get_animation_loop(state) and not hold_last and elapsed >= total:
		return -1
	var cursor := fmod(elapsed, total) if frames.get_animation_loop(state) else minf(elapsed, total)
	for index in range(frames.get_frame_count(state)):
		cursor -= frames.get_frame_duration(state, index)
		if cursor < 0:
			return index
	return frames.get_frame_count(state) - 1

static func load_frames(manifest_path: String) -> SpriteFrames:
	if bundle_cache.has(manifest_path):
		bundle_order.erase(manifest_path)
		bundle_order.append(manifest_path)
		return bundle_cache[manifest_path]
	var manifest = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not manifest is Dictionary or not manifest.has("frame_layout") or not manifest.has("animation"):
		push_error("Sprite manifest requires frame_layout and animation: " + manifest_path)
		return null
	var layout: Dictionary = manifest.frame_layout
	var image_name: String = str(manifest.get("game_input", "sprite-sheet-alpha.png"))
	if image_name.is_absolute_path() or ".." in image_name:
		push_error("Atlas must be relative to its manifest")
		return null
	var atlas: Texture2D = load(manifest_path.get_base_dir().path_join(image_name))
	if atlas == null:
		return null
	var atlas_image := atlas.get_image()
	var audited: Dictionary = {}
	var audit: Dictionary = manifest.get("alpha_audit", {})
	if audit.get("method", "") == "ufe-real-alpha-v1" and str(audit.get("png_sha256", "")) == FileAccess.get_sha256(manifest_path.get_base_dir().path_join(image_name)):
		for record in audit.regions:
			var r: Array = record.rect
			var b: Array = record.bounds
			audited[str(Rect2(r[0],r[1],r[2],r[3]))] = Rect2(b[0],b[1],b[2],b[3])
	var frames := SpriteFrames.new()
	var texture_cache: Dictionary = {}
	frames.remove_animation("default")
	for state in layout.rows:
		var row: Array = layout.rows[state]
		var timing: Dictionary = manifest.animation.rows[state]
		var durations: Array = timing.durations_ms
		if row.is_empty() or row.size() != durations.size():
			push_error("Invalid sprite frame timing: " + str(state))
			return null
		frames.add_animation(state)
		frames.set_animation_speed(state, 1000.0)
		frames.set_animation_loop(state, bool(timing.get("loop", false)))
		for i in range(row.size()):
			var rect: Dictionary = row[i]
			var region := Rect2(float(rect.x), float(rect.y), float(rect.w), float(rect.h))
			if region != Rect2(Rect2i(region)) or region.size.x <= 0 or region.size.y <= 0 or not Rect2(Vector2.ZERO, atlas.get_size()).encloses(region) or float(durations[i]) <= 0:
				push_error("Invalid atlas rectangle or duration")
				return null
			var geometry := SpriteGeometry.from_manifest(manifest, region.size)
			if geometry.is_empty():
				push_error("Invalid sprite display size, density or ground origin: " + manifest_path)
				return null
			var key := str(region)
			if texture_cache.has(key):
				frames.add_frame(state, texture_cache[key], float(durations[i]))
				continue
			if not audited.has(key) and not ImageAlpha.accepts_region(atlas_image, Rect2i(region)):
				push_error("Sprite frame requires real transparency: %s frame %d" % [state, i])
				return null
			var texture := AtlasTexture.new()
			texture.atlas = atlas
			texture.region = region
			texture.set_meta(&"ufe_geometry", geometry)
			texture_bounds[texture.get_instance_id()] = audited[key] if audited.has(key) else Rect2(atlas_image.get_region(Rect2i(region)).get_used_rect())
			texture_cache[key] = texture
			frames.add_frame(state, texture, float(durations[i]))
	bundle_cache[manifest_path] = frames
	bundle_order.append(manifest_path)
	while bundle_order.size() > MAX_BUNDLES:
		var evicted: String = bundle_order.pop_front()
		var old: SpriteFrames = bundle_cache[evicted]
		for state in old.get_animation_names():
			for index in range(old.get_frame_count(state)):
				texture_bounds.erase(old.get_frame_texture(state,index).get_instance_id())
		bundle_cache.erase(evicted)
	return frames

static func bounds_for(texture: Texture2D) -> Rect2:
	var id := texture.get_instance_id()
	return texture_bounds[id] if texture_bounds.has(id) else Rect2(texture.get_image().get_used_rect())
