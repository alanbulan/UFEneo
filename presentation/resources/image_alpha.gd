class_name UfeImageAlpha
extends RefCounted
## Inspect the decoded pixels. Merely having RGBA or transparent padding is insufficient.
static func accepts_region(source: Image, region: Rect2i) -> bool:
	if source == null or source.is_empty() or region.size.x <= 0 or region.size.y <= 0:
		return false
	if not Rect2i(Vector2i.ZERO, source.get_size()).encloses(region):
		return false
	return accepts(source.get_region(region))

static func accepts(source: Image) -> bool:
	if source == null or source.is_empty():
		return false
	var image := source.duplicate() as Image
	image.convert(Image.FORMAT_RGBA8)
	var width := image.get_width()
	var height := image.get_height()
	var pixels := image.get_data()
	var corners := [0, width - 1, (height - 1) * width, width * height - 1]
	for point in corners:
		if pixels[point * 4 + 3] != 0:
			return false
	var clear := 0
	var visible := 0
	var left := width
	var right := -1
	var top := height
	var bottom := -1
	for point in range(width * height):
		var alpha := pixels[point * 4 + 3]
		if alpha == 0:
			clear += 1
		if alpha >= 128:
			visible += 1
			var x := point % width
			@warning_ignore("integer_division") # 线性像素索引转换为整数行坐标。
			var y := point / width
			left = mini(left, x)
			right = maxi(right, x)
			top = mini(top, y)
			bottom = maxi(bottom, y)
	if clear < width * height * 0.05 or visible < width * height * 0.01:
		return false
	var bounds_corners := [top * width + left, top * width + right, bottom * width + left, bottom * width + right]
	for point in bounds_corners:
		if pixels[point * 4 + 3] < 200:
			return true
	for channel in range(3):
		var low := 255
		var high := 0
		for point in bounds_corners:
			low = mini(low, pixels[point * 4 + channel])
			high = maxi(high, pixels[point * 4 + channel])
		if high - low >= 6:
			return true
	return false

static func candidate(state: Dictionary) -> Image:
	var path := str(state.get("preview_path", ""))
	if not path.begins_with("art/shared/legacy/concepts/") or ".." in path.split("/") or "rejected" in path.split("/"):
		return null
	var local := ProjectSettings.globalize_path("res://" + path)
	if not FileAccess.file_exists(local) or FileAccess.get_sha256(local) != str(state.get("sha256", "")):
		return null
	var image := Image.load_from_file(local)
	return image if accepts(image) else null
