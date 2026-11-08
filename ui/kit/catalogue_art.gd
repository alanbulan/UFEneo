class_name PixelCatalogueArt
extends Control
## 所有条目共用原生像素比例和脚底根点，不按各自透明画布撑满。
## 待机动画播放的是真帧：assets/.../catalogue/anim-strip.png 是一条水平
## 排列的多帧条，每帧都是独立的像素画面。没有帧的条目退回静态单张，不做
## 位移冒充动画。
const SHARED_EXTENT := Vector2(640, 256)
## 每个姿态停留多少毫秒。
const FRAME_MS := 300
var sprite := Sprite2D.new()
var scroll := ScrollContainer.new()
var canvas := Control.new()
var missing := Label.new()
var native_root := Vector2.ZERO
var pixel_scale := 1
var painted_bounds := Rect2i()
var frame_count := 1
var frame_index := 0
var frame_elapsed := 0

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	clip_contents = true
	custom_minimum_size = Vector2(320, 208)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(scroll)
	canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scroll.add_child(canvas)
	sprite.centered = false
	canvas.add_child(sprite)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	missing.text = "像素形象整理中"
	center.add_child(missing)
	resized.connect(_layout_sprite)
	_layout_sprite()

func set_display(data: Dictionary) -> void:
	var strip := str(data.get("strip", ""))
	var still := str(data.get("image", ""))
	frame_count = 1
	if not strip.is_empty() and ResourceLoader.exists(strip):
		sprite.texture = load(strip)
		frame_count = maxi(1, int(data.get("frames", 1)))
	elif not still.is_empty() and ResourceLoader.exists(still):
		sprite.texture = load(still)
	else:
		sprite.texture = null
	sprite.hframes = frame_count
	sprite.frame = 0
	frame_index = 0
	frame_elapsed = 0
	var point: Array = data.get("native_root", [0, 0])
	native_root = Vector2(float(point[0]), float(point[1]))
	painted_bounds = _first_frame_bounds()
	missing.visible = sprite.texture == null
	scroll.scroll_horizontal = 0
	scroll.scroll_vertical = 0
	_layout_sprite()
	set_process(frame_count > 1)

func _first_frame_bounds() -> Rect2i:
	"""只看第 0 帧的可见范围：整条 strip 所有帧共用同一画布与根点。"""
	if sprite.texture == null: return Rect2i()
	var image := sprite.texture.get_image()
	if image == null: return Rect2i()
	if frame_count <= 1: return image.get_used_rect()
	var slice_width := int(float(image.get_width()) / float(frame_count))
	return image.get_region(Rect2i(0, 0, slice_width, image.get_height())).get_used_rect()

func _process(delta: float) -> void:
	if frame_count <= 1 or not is_visible_in_tree(): return
	frame_elapsed += int(delta * 1000.0)
	if frame_elapsed < FRAME_MS: return
	frame_elapsed %= FRAME_MS
	frame_index = (frame_index + 1) % frame_count
	sprite.frame = frame_index

func _layout_sprite() -> void:
	if not is_inside_tree(): return
	pixel_scale = maxi(1, mini(floori(size.x / SHARED_EXTENT.x), floori(size.y / SHARED_EXTENT.y)))
	sprite.scale = Vector2.ONE * pixel_scale
	# 大轮廓扩大滚动内容，不缩人物，也不让Sprite越过自己的详情区。
	var padding := 4 * pixel_scale
	var painted_size := Vector2(painted_bounds.size) * pixel_scale
	var available := size
	var vertical := painted_size.y + 2 * padding > available.y
	if vertical: available.x -= scroll.get_v_scroll_bar().get_combined_minimum_size().x
	var horizontal := painted_size.x + 2 * padding > available.x
	if horizontal: available.y -= scroll.get_h_scroll_bar().get_combined_minimum_size().y
	if not vertical and painted_size.y + 2 * padding > available.y:
		vertical = true
		available.x -= scroll.get_v_scroll_bar().get_combined_minimum_size().x
	var extent := Vector2(maxf(available.x, painted_size.x + 2 * padding) if horizontal else available.x,
		maxf(available.y, painted_size.y + 2 * padding) if vertical else available.y)
	canvas.custom_minimum_size = extent
	var display_root := Vector2(roundf(extent.x / 2.0), roundf(extent.y - padding))
	# 只平移完整人物以容纳非对称长尾，保留原生比例和近脚地面线。
	if painted_bounds.size.x > 0:
		var left := padding - (float(painted_bounds.position.x) - native_root.x) * pixel_scale
		var right := extent.x - padding - (float(painted_bounds.end.x) - native_root.x) * pixel_scale
		display_root.x = clampf(display_root.x, left, right)
	sprite.position = display_root - native_root * pixel_scale

func display_evidence() -> Dictionary:
	return {"native_root": [native_root.x, native_root.y], "pixel_scale": pixel_scale, "display_root": [sprite.position.x + native_root.x * pixel_scale, sprite.position.y + native_root.y * pixel_scale], "texture": sprite.texture.resource_path if sprite.texture != null else "", "frames": frame_count, "size": [size.x, size.y], "content_size": [canvas.size.x, canvas.size.y], "scroll": [scroll.scroll_horizontal, scroll.scroll_vertical], "clips_to_detail": clip_contents and scroll.clip_contents}
