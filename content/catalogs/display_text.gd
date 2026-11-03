class_name UfeDisplayText
extends RefCounted
## 仅转换显示文字；查询身份、资源路径和来源URL保持原值。
static var _data: Dictionary = {}
static var _urls: RegEx

static func text(value: String) -> String:
	if _data.is_empty():
		_data = UfeContentDatabase.read_json("res://content/roster/display_text_zh_cn.json")
		_urls = RegEx.create_from_string("https?://[^\\s<>\\[\\]()]+")
	var strings: Dictionary = _data.get("strings", {})
	if strings.has(value): return str(strings[value])
	var result := ""
	var offset := 0
	for found in _urls.search_all(value):
		result += _terms(value.substr(offset, found.get_start() - offset)) + found.get_string()
		offset = found.get_end()
	result += _terms(value.substr(offset))
	return result

static func _terms(value: String) -> String:
	for pair in _data.get("terms", []): value = value.replace(str(pair[0]), str(pair[1]))
	return value

static func profile(value: Dictionary) -> Dictionary:
	var result := value.duplicate(true)
	for key in ["name", "title", "text", "source_label"]:
		if result.has(key): result[key] = text(str(result[key]))
	return result
