extends SceneTree
## 图鉴待机动画与试听声回归。
## 判据：
## 1. 有 strip 的条目按帧播放，逐帧推进并按帧数循环；
## 2. 没有 strip 的条目退回单张静态图，帧数为 1（不做位移冒充动画）；
## 3. 有本人声音的角色用角色音频，其余条目退回像素界面提示音。
## 输出 CATALOGUE_ANIMATION_JSON_BEGIN/END 之间的 JSON；任一条不合格退出码为 1。

const CATALOGUE_PATH := "res://content/roster/catalogue_display.json"
const JSON_BEGIN := "CATALOGUE_ANIMATION_JSON_BEGIN"
const JSON_END := "CATALOGUE_ANIMATION_JSON_END"
const STEP_SECONDS := 0.35

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var started := Time.get_ticks_msec()
	var failures: Array = []
	var checks := {"strip_frames": 0, "frame_cycle": 0, "static_fallback": 0, "character_sound": 0, "fallback_sound": 0}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(CATALOGUE_PATH))
	if not (parsed is Dictionary) or not (parsed.get("entries") is Dictionary):
		_finish(failures, checks, started, "图鉴数据不可读")
		return
	var entries: Dictionary = parsed.entries

	var animated := ""
	var still := ""
	for key in entries.keys():
		var entry = entries[key]
		if not (entry is Dictionary): continue
		if animated.is_empty() and not str(entry.get("strip", "")).is_empty() and ResourceLoader.exists(str(entry.strip)):
			animated = str(key)
		if still.is_empty() and str(entry.get("strip", "")).is_empty() and not str(entry.get("image", "")).is_empty():
			still = str(key)
		if not animated.is_empty() and not still.is_empty(): break

	var art := PixelCatalogueArt.new()
	root.add_child(art)
	art.size = Vector2(320, 208)

	if animated.is_empty():
		failures.append({"check": "strip", "reason": "no_animated_entry"})
	else:
		art.set_display(entries[animated])
		art.set_process(false)
		if art.sprite.texture == null:
			failures.append({"check": "strip", "id": animated, "reason": "texture_missing"})
		elif art.frame_count < 2:
			failures.append({"check": "strip", "id": animated, "reason": "frame_count_lt_2"})
		else:
			checks.strip_frames += 1
			var seen: Array = []
			for index in art.frame_count:
				seen.append(art.sprite.frame)
				art._process(STEP_SECONDS)
			if seen == range(art.frame_count):
				checks.frame_cycle += 1
			else:
				failures.append({"check": "frames", "id": animated, "got": seen, "want": range(art.frame_count)})
			# 转满一圈必须回到第 0 帧，不能越界。
			if art.sprite.frame != 0:
				failures.append({"check": "loop", "id": animated, "frame": art.sprite.frame})

	if still.is_empty():
		failures.append({"check": "still", "reason": "no_static_entry"})
	else:
		art.set_display(entries[still])
		art.set_process(false)
		if art.sprite.texture == null:
			failures.append({"check": "still", "id": still, "reason": "texture_missing"})
		elif art.frame_count != 1:
			failures.append({"check": "still", "id": still, "reason": "frame_count_should_be_1", "got": art.frame_count})
		else:
			checks.static_fallback += 1
	root.remove_child(art)
	art.free()

	for id in ["gomora", "ultraman"]:
		var picked: Dictionary = PixelCatalogueSound.for_entry(id)
		if bool(picked.own_voice) and str(picked.path).contains("/characters/"):
			checks.character_sound += 1
		else:
			failures.append({"check": "sound", "id": id, "reason": "character_sound_missing", "path": str(picked.path)})
	for id in ["wiki_300673598b96f6", "zetton"]:
		var picked: Dictionary = PixelCatalogueSound.for_entry(id)
		if str(picked.path) == PixelCatalogueSound.PICK_SOUND and not bool(picked.own_voice):
			checks.fallback_sound += 1
		else:
			failures.append({"check": "sound", "id": id, "reason": "fallback_sound_missing", "path": str(picked.path)})

	_finish(failures, checks, started, "")

func _finish(failures: Array, checks: Dictionary, started: int, error: String) -> void:
	var result := {
		"check": "catalogue_animation",
		"error": error,
		"checks": checks,
		"passed": failures.is_empty(),
		"failures": failures,
		"elapsed_ms": Time.get_ticks_msec() - started,
	}
	print(JSON_BEGIN)
	print(JSON.stringify(result, "  ", true))
	print(JSON_END)
	print("CATALOGUE_ANIMATION %s failures=%d" % ["PASS" if failures.is_empty() else "FAIL", failures.size()])
	quit(0 if failures.is_empty() else 1)
