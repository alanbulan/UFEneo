extends SceneTree
## 图鉴静态图回归：逐条验证 catalogue_display.json 的 image 能被 Godot 载入。
## 判据：.import 存在、load() 得到 Texture2D、尺寸等于 native_canvas、native_root 在纹理内。
## 输出 CATALOGUE_ASSETS_JSON_BEGIN/END 之间的 JSON；任一条不合格退出码为 1。

const CATALOGUE_PATH := "res://content/roster/catalogue_display.json"
const JSON_BEGIN := "CATALOGUE_ASSETS_JSON_BEGIN"
const JSON_END := "CATALOGUE_ASSETS_JSON_END"

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var started := Time.get_ticks_msec()
	var failures: Array = []
	var reasons: Dictionary = {}
	var seen_images: Dictionary = {}
	var counts := {"image_present": 0, "import_present": 0, "texture_loaded": 0, "pixels_loaded": 0, "canvas_matches": 0, "root_in_bounds": 0, "alpha_present": 0, "height_matches": 0, "grounded": 0}
	var total := 0
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(CATALOGUE_PATH))
	if not (parsed is Dictionary) or not (parsed.get("entries") is Dictionary):
		var broken := {
			"check": "catalogue_assets",
			"catalogue": CATALOGUE_PATH,
			"error": "图鉴数据不是含 entries 的对象",
			"total_entries": 0,
			"passed": 0,
			"failed": 0,
			"failures": [],
			"elapsed_ms": Time.get_ticks_msec() - started,
		}
		print(JSON_BEGIN)
		print(JSON.stringify(broken, "  ", true))
		print(JSON_END)
		printerr("CATALOGUE_ASSETS FAIL " + str(broken.error))
		quit(1)
		return
	var entries: Dictionary = parsed.entries
	var ids: Array = entries.keys()
	ids.sort()
	total = ids.size()
	for id_value in ids:
		var id := str(id_value)
		var entry = entries[id_value]
		if not (entry is Dictionary):
			_add_failure(failures, reasons, id, "", ["entry_not_object"])
			continue
		var image := str(entry.get("image", ""))
		seen_images[image] = true
		var failure_reasons: Array[String] = []
		if image.is_empty() or not image.begins_with("res://"):
			failure_reasons.append("image_path_missing_or_invalid")
		else:
			counts.image_present += 1
			if not FileAccess.file_exists(image + ".import"):
				failure_reasons.append("import_missing")
			else:
				counts.import_present += 1
			var texture = ResourceLoader.load(image, "Texture2D", ResourceLoader.CACHE_MODE_IGNORE)
			var root_point = entry.get("native_root", [])
			if not (root_point is Array) or root_point.size() < 2:
				root_point = [0.0, 0.0]
			if not (texture is Texture2D):
				failure_reasons.append("load_failed")
			else:
				counts.texture_loaded += 1
				var width := int(texture.get_width())
				var height := int(texture.get_height())
				var image_data = texture.get_image()
				if image_data == null:
					failure_reasons.append("image_pixels_unavailable")
				else:
					counts.pixels_loaded += 1
					var used: Rect2i = image_data.get_used_rect()
					if used.size.x <= 0 or used.size.y <= 0:
						failure_reasons.append("alpha_empty")
					else:
						counts.alpha_present += 1
						# 实际站高必须与声明的设定身高换算值一致：只验可载入会
						# 漏掉「人物被缩成十几个像素仍能加载」这类损坏。
						var declared := int(entry.get("visible_height_including_ornaments", 0))
						if declared > 0 and absi(used.size.y - declared) > 2:
							failure_reasons.append("height_mismatch:%d!=%d" % [used.size.y, declared])
						else:
							counts.height_matches += 1
						# 脚底要踩在根点地面线上，不能悬空或穿出画布。
						var ground_gap: int = int(float(root_point[1])) - used.end.y
						if ground_gap < -2 or ground_gap > 4:
							failure_reasons.append("ground_gap:%d" % ground_gap)
						else:
							counts.grounded += 1
				var canvas = entry.get("native_canvas", [])
				if not (canvas is Array) or canvas.size() < 2:
					failure_reasons.append("native_canvas_invalid")
				else:
					var expected_width := int(canvas[0])
					var expected_height := int(canvas[1])
					if width != expected_width or height != expected_height:
						failure_reasons.append("canvas_mismatch:%dx%d!=%dx%d" % [width, height, expected_width, expected_height])
					else:
						counts.canvas_matches += 1
				if not (entry.get("native_root") is Array) or entry.native_root.size() < 2:
					failure_reasons.append("native_root_invalid")
				else:
					var root_x := float(root_point[0])
					var root_y := float(root_point[1])
					if root_x < 0.0 or root_x > float(width) or root_y < 0.0 or root_y > float(height):
						failure_reasons.append("root_out_of_bounds:%s,%s outside %dx%d" % [root_x, root_y, width, height])
					else:
						counts.root_in_bounds += 1
		if not failure_reasons.is_empty():
			_add_failure(failures, reasons, id, image, failure_reasons)
	var result := {
		"check": "catalogue_assets",
		"catalogue": CATALOGUE_PATH,
		"total_entries": total,
		"unique_images": seen_images.size(),
		"passed": total - failures.size(),
		"failed": failures.size(),
		"checks": counts,
		"failure_reasons": reasons,
		"failures": failures,
		"elapsed_ms": Time.get_ticks_msec() - started,
	}
	print(JSON_BEGIN)
	print(JSON.stringify(result, "  ", true))
	print(JSON_END)
	print("CATALOGUE_ASSETS %s total=%d failed=%d elapsed_ms=%d" % ["PASS" if failures.is_empty() else "FAIL", total, failures.size(), int(result.elapsed_ms)])
	quit(0 if failures.is_empty() else 1)

func _add_failure(failures: Array, reasons: Dictionary, id: String, image: String, failure_reasons: Array[String]) -> void:
	for reason in failure_reasons:
		var key := reason.split(":")[0]
		reasons[key] = int(reasons.get(key, 0)) + 1
	failures.append({"id": id, "image": image, "reasons": failure_reasons})
