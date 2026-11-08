class_name PixelCatalogueArt
extends Control
## 图鉴形象：固定 384×256 原生画布，按整数倍缩放居中显示。
## 待机动画播放 anim-strip.png 的真帧；没有帧的条目退回静态单张。
## 人物最高 248、最宽 376，都在画布内，所以永远不需要滚动条——之前用
## ScrollContainer 会在大轮廓时冒出滚动条，直接去掉。
const CANVAS := Vector2(384, 256)
## 每个姿态停留多少毫秒。
const FRAME_MS := 300
var sprite := Sprite2D.new()
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
	custom_minimum_size = Vector2(384, 256)
	# 固定 384×256，不再拉伸：拉伸只会让画布四周多出空白，看不出大小差别。
	size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)
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
	# 画布能放下几倍就放大几倍，放不下就保持 1 倍；始终不滚动。
	pixel_scale = maxi(1, mini(floori(size.x / CANVAS.x), floori(size.y / CANVAS.y)))
	sprite.scale = Vector2.ONE * pixel_scale
	# 画布居中；根点就是画布里的脚底位置，不再做非对称平移。
	sprite.position = (size - CANVAS * pixel_scale) / 2.0

func display_evidence() -> Dictionary:
	return {"native_root": [native_root.x, native_root.y], "pixel_scale": pixel_scale, "display_root": [sprite.position.x + native_root.x * pixel_scale, sprite.position.y + native_root.y * pixel_scale], "texture": sprite.texture.resource_path if sprite.texture != null else "", "frames": frame_count, "size": [size.x, size.y], "scroll": [0, 0], "clips_to_detail": clip_contents}
