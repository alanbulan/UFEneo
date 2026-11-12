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
				check(not form_id.is_empty() and FileAccess.file_exists("res://content/fighters/%s/definition.json" % form_id), "%s 形态定义存在" % key)
	for key in listed:
		# 多形态表里的选项必须与选人界面一一对应；单形态变身表沿用旧规则不在此列。
		var base := str(key).get_slice("/", 0)
		if not registry.has(base) or not registry[base].has("choices"): continue
		check(registry[base].choices.any(func(raw): return str(raw.get("id","")) == str(key).get_slice("/",1)), "%s 已登记在战斗表" % key)
	print("FORM_SELECTION_CONSISTENCY " + ("PASS" if failures.is_empty() else str(failures)))
	quit(0 if failures.is_empty() else 1)
