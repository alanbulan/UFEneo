extends SceneTree
## 选人界面形态开关与战斗切换表必须一致：只在一处实装会出现“能选出却切不了”或反之。
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		printerr("FAIL " + label)

func run() -> void:
	var selection: Dictionary = UfeContentDatabase.read_json("res://content/roster/selection.json")
	var registry: Dictionary = UfeBattleFormCatalog.registry()
	var listed: Dictionary = {}
	for row in selection.entries:
		for form in row.get("forms", []):
			if str(form.get("id", "")) == "default": continue
			listed[str(row.id) + "/" + str(form.id)] = bool(form.get("implemented", false))
	for base in registry:
		var source: Dictionary = registry[base]
		for raw in source.get("choices", []):
			var key := str(base) + "/" + str(raw.get("id", ""))
			if not listed.has(key): continue
			var runtime := bool(raw.get("enabled", false)) and bool(raw.get("implemented", true))
			check(runtime == bool(listed[key]), "%s 选人/战斗形态开关一致" % key)
			if runtime:
				var form_id := str(raw.get("target", ""))
				var definition_path := "res://content/fighters/%s/definition.json" % form_id
				check(not form_id.is_empty() and FileAccess.file_exists(definition_path), "%s 形态定义存在" % key)
				if FileAccess.file_exists(definition_path):
					var definition: Dictionary = UfeContentDatabase.read_json(definition_path)
					var model := str(definition.get("presentation", {}).get("model", ""))
					# 运行时必须指向动作整图；图鉴静态图放进 presentation 会让动作帧与rects对不上。
					check(bool(definition.get("playable", false)) and FileAccess.file_exists(model) and not model.contains("/catalogue/"), "%s 运行时模型为可玩动作整图" % key)
				# 切换动作读目标形态清单里的片段，缺片段会让人物隐形；时长必须与共用时间轴一致。
				var timeline: Dictionary = UfeContentDatabase.read_json(str(raw.get("transform", "")))
				var manifest: Dictionary = UfeContentDatabase.read_json("res://assets/fighters/%s/animations/manifest.json" % form_id)
				var animation := str(raw.get("transform_animation", source.get("transform_animation", "")))
				var clip: Dictionary = manifest.get("clips", {}).get(animation, {})
				var ticks := 0
				for value in clip.get("ticks", []): ticks += int(value)
				check(not clip.is_empty() and ticks == timeline.get("frames", []).size(), "%s 切换动画时长与时间轴一致" % key)
	for key in listed:
		# 多形态表里的选项必须与选人界面一一对应；单形态变身表沿用旧规则不在此列。
		var base := str(key).get_slice("/", 0)
		if not registry.has(base) or not registry[base].has("choices"): continue
		check(registry[base].choices.any(func(raw): return str(raw.get("id","")) == str(key).get_slice("/",1)), "%s 已登记在战斗表" % key)
	print("FORM_SELECTION_CONSISTENCY " + ("PASS" if failures.is_empty() else str(failures)))
	quit(0 if failures.is_empty() else 1)
