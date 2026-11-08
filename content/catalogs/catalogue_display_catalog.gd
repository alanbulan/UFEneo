class_name UfeCatalogueDisplayCatalog
extends RefCounted
## 图鉴的静态展示映射；不参与可玩名册或战斗定义。
const PATH := "res://content/roster/catalogue_display.json"
## 每页 10 条：640×360 主界面里左侧列表刚好装得下，不需要滚动条。
const PAGE_SIZE := 10
var roster := UfeRosterCatalog.new()
var display: Dictionary = {}
var supplemental: Array = []
var links: Dictionary = {}
var aliases: Dictionary = {}
var _canonical_rows: Array = []
var _search_names: Dictionary = {}
var _last_query := ""
var _last_kind := ""
var _last_rows: Array = []
var _has_query := false

func _init() -> void:
	var data: Dictionary = UfeContentDatabase.read_json(PATH)
	display = data.get("entries", {})
	supplemental = data.get("supplemental_entries", [])
	links = data.get("form_links", {})
	aliases = data.get("aliases", {})

func canonical_id(id: String) -> String:
	var original := id
	var visited: Dictionary = {}
	while aliases.has(id):
		if visited.has(id):
			push_error("图鉴别名循环：" + original)
			return original
		visited[id] = true
		var target := str(aliases[id])
		if target == id or target.is_empty(): break
		id = target
	return id

func _display_row(row: Dictionary) -> Dictionary:
	var entry: Dictionary = display.get(str(row.get("id", "")), {})
	var name := str(entry.get("display_name", ""))
	# 旧 display_name 里可能已经拼过 " · 形态"，和三项结构重复时以结构字段为准。
	# 图鉴可以用 display_form 覆盖形态：初代本体就是 C 型，画面上不再单列 C 型条目。
	var form_text := UfeDisplayText.text(str(entry.get("display_form", row.get("form", "")))).strip_edges()
	# 旧数据里间隔符有时带空格有时不带，两种都要剥掉，否则名字里会叠两个形态。
	if not form_text.is_empty():
		for separator in [" · ", "·"]:
			var suffix: String = str(separator) + form_text
			if name.ends_with(suffix):
				name = name.substr(0, name.length() - suffix.length()).strip_edges()
				break
	var result := row.duplicate(true)
	result.name = UfeDisplayText.text(name if not name.is_empty() else str(row.get("name", "")))
	# 三项结构：称号 / 主体名称 / 形态。列表和标题都要能分开取用，形态不能丢进名字里。
	result.title = UfeDisplayText.text(str(row.get("title", "")))
	result.form = form_text
	result.display_name = str(result.name) if str(result.form).is_empty() else str(result.name) + " · " + str(result.form)
	return result

func row_for(id: String) -> Dictionary:
	id = canonical_id(id)
	if roster.by_id.has(id):
		var row: Dictionary = roster.by_id[id].duplicate(true)
		if display.has(id) and display[id].has("base_character"): row.base_character = str(display[id].base_character)
		if display.has(id) and display[id].has("series_ids_override"): row.series_ids = display[id].series_ids_override.duplicate()
		else:
			var reviewed_path := "res://content/fighters/%s/profile.json" % id
			if FileAccess.file_exists(reviewed_path):
				var reviewed: Dictionary = UfeContentDatabase.read_json(reviewed_path)
				if str(reviewed.get("id", "")) == id and reviewed.get("catalogue_facts_reviewed", false) == true and reviewed.get("reviewed_series_ids", null) is Array:
					row.series_ids = reviewed.reviewed_series_ids.duplicate()
		return _display_row(row)
	for row in supplemental:
		if str(row.id) == id: return _display_row(row)
	return {}

func display_for(id: String) -> Dictionary:
	return display.get(canonical_id(id), {})

func _redundant_forms() -> Dictionary:
	"""形态与本体是同一形象时，它只是重复条目，列表里保留本体。
	两种判定：条目在展示表里显式登记 duplicate_of；或定稿图与本体完全相同。
	例：初代奥特曼本体与 C 型外观、杰斯提斯本体与标准型。
	本体 id 不能被替代：别名链与旧 id 定位都以本体为终点。"""
	var redundant: Dictionary = {}
	# 重画后同一形象的形态会拿到新图，SHA 不再相同，只能靠登记关系判定。
	for id in display.keys():
		var target := str(display[id].get("duplicate_of", "")).strip_edges()
		if not target.is_empty() and str(id) != target and display.has(target):
			redundant[str(id)] = target
	for base in links.keys():
		var base_image := str(display.get(str(base), {}).get("image_sha256", ""))
		if base_image.is_empty(): continue
		for item in links[base]:
			var form := str(item.get("id", ""))
			if form != str(base) and str(display.get(form, {}).get("image_sha256", "")) == base_image:
				redundant[form] = str(base)
	return redundant

func _matching_rows(query: String, kind: String) -> Array:
	query = UfeDisplayText.text(query).strip_edges().to_lower()
	if _has_query and query == _last_query and kind == _last_kind: return _last_rows
	if _canonical_rows.is_empty():
		var seen: Dictionary = {}
		var redundant := _redundant_forms()
		var originals: Array = []
		originals.append_array(roster.entries); originals.append_array(supplemental)
		for original in originals:
			var id := canonical_id(str(original.id))
			if redundant.has(id): continue
			var search := UfeDisplayText.text(str(original.get("name", "")) + " " + str(original.get("search_text", "")) + " " + str(original.id)).to_lower()
			_search_names[id] = str(_search_names.get(id, "")) + " " + search
			if seen.has(id): continue
			var row := row_for(id)
			if row.is_empty(): continue
			_canonical_rows.append(row); seen[id] = true
			_search_names[id] += " " + str(row.name).to_lower()
	var found: Array = []
	for row in _canonical_rows:
		if not kind.is_empty() and str(row.kind) != kind: continue
		var matches := true
		for term in query.split(" ", false):
			if not str(_search_names[row.id]).contains(term): matches = false; break
		if matches: found.append(row)
	_last_query = query; _last_kind = kind; _last_rows = found; _has_query = true
	return found

func query_page(query: String, kind: String, page: int) -> Dictionary:
	var matches := _matching_rows(query, kind)
	var total := matches.size()
	var pages := maxi(1, ceili(total / float(PAGE_SIZE)))
	var current := clampi(page, 0, pages - 1)
	var offset := current * PAGE_SIZE
	var rows: Array = []
	for i in range(offset, mini(offset + PAGE_SIZE, total)): rows.append(matches[i])
	return {"rows": rows, "total": total, "page": current, "pages": pages}

func page_for_id(id: String, query: String, kind: String) -> int:
	id = canonical_id(id)
	var matches := _matching_rows(query, kind)
	for i in range(matches.size()):
		if str(matches[i].id) == id: return floori(i / float(PAGE_SIZE))
	return -1

func detail_for(id: String) -> Dictionary:
	id = canonical_id(id)
	var result: Dictionary = roster.detail_for(id) if roster.by_id.has(id) else row_for(id)
	return result.duplicate(true)

func forms_for(id: String) -> Array:
	id = canonical_id(id)
	var found: Array = []
	var seen: Dictionary = {}
	var mapped := display_for(id)
	if mapped.has("relations_override"):
		for relation in mapped.relations_override:
			var target := canonical_id(str(relation.id))
			if target == id or seen.has(target) or row_for(target).is_empty(): continue
			found.append({"id": target, "name": str(_form_label(target)), "relation": str(relation.relation)})
			seen[target] = true
		return found
	var base := str(row_for(id).get("base_character", ""))
	if not base.is_empty() and base != id:
		found.append({"id": base, "name": str(row_for(base).get("name", base)), "relation": "本体"})
		seen[base] = true
	for item in links.get(id, []):
		var child := canonical_id(str(item.id))
		if child == id or seen.has(child) or row_for(child).is_empty(): continue
		found.append({"id": child, "name": str(_form_label(child)), "relation": "形态"})
		seen[child] = true
	if not base.is_empty() and base != id and not row_for(base).is_empty():
		for item in links.get(base, []):
			var child := canonical_id(str(item.id))
			if child == id or seen.has(child) or row_for(child).is_empty(): continue
			found.append({"id": child, "name": str(_form_label(child)), "relation": "形态"})
			seen[child] = true
	return found

func _form_label(id: String) -> String:
	"""形态链接只显示形态名；没有形态时退回主体名，避免重复整串名字。"""
	var row := row_for(id)
	var form := str(row.get("form", "")).strip_edges()
	return form if not form.is_empty() else str(row.get("name", id))

func profile_for(id: String) -> Dictionary:
	id = canonical_id(id)
	var mapped := display_for(id)
	var path := str(mapped.get("profile", ""))
	if not path.is_empty() and FileAccess.file_exists(path):
		return _with_identity_title(id, UfeContentDatabase.read_json(path))
	if mapped.has("profile_inline"): return _with_identity_title(id, mapped.profile_inline)
	var reviewed_path := "res://content/fighters/%s/profile.json" % id
	if FileAccess.file_exists(reviewed_path):
		var reviewed: Dictionary = UfeContentDatabase.read_json(reviewed_path)
		if str(reviewed.get("id", "")) == id and reviewed.get("catalogue_facts_reviewed", false) == true:
			return _with_identity_title(id, reviewed)
	var detail := detail_for(id)
	var texts: Array[String] = []
	var sources: Array = []
	for note in detail.get("research_notes", []):
		if str(note.get("text", "")).is_empty(): continue
		texts.append(str(note.get("heading", "资料")) + "\n" + str(note.text).left(1000))
		sources.append({"url": str(note.get("revision_url", "")), "license": "CC BY-SA 4.0" if str(note.get("revision_url", "")).contains("wikipedia.org/") else "按原来源条款"})
		if texts.size() >= 3: break
	return _with_identity_title(id, {"name": str(detail.get("name", id)), "text": "\n\n".join(texts) if not texts.is_empty() else "角色详细资料正在整理。", "sources": sources})

func _with_identity_title(id: String, data: Dictionary) -> Dictionary:
	var result := UfeDisplayText.profile(data.duplicate(true))
	var identity := UfeFighterDisplay.identity_entry(id)
	for key in ["title", "title_status", "title_source_url", "title_source_excerpt", "title_note"]:
		if identity.has(key): result[key] = UfeDisplayText.text(str(identity[key]))
	# 只投影明确过时的称号占位；来源原件和身高/体重等未知事实保持。
	if identity.has("title") and str(result.get("text", "")).contains("称号：未知。"):
		var replacement := "称号：" + str(identity.title) + "。"
		if str(identity.get("title_status", "")).contains("classification"):
			replacement = "身份分类：" + str(identity.title) + "；独立称号尚未核实。"
		result.text = str(result.text).replace("称号：未知。", replacement)
	return result

func title_source_lines(profile: Dictionary) -> String:
	var status := str(profile.get("title_status", ""))
	var url := str(profile.get("title_source_url", ""))
	if status.is_empty() and url.is_empty(): return ""
	var label := "资料称号"
	if status.contains("classification"):
		label = "身份分类"
	elif status.contains("inherited") or status.contains("inherits"):
		label = "同族称呼沿用" if status.contains("species") else "本体称号沿用"
	elif status == "sourced_form_alias":
		label = "形态别称"
	elif status == "sourced_form_description":
		label = "形态名称"
	elif status.contains("self_nickname"):
		label = "本人自称"
	elif status.contains("nickname"):
		label = "民间昵称"
	elif status.contains("group_membership"):
		label = "所属群体"
	elif status.contains("machine_designation"):
		label = "机型编号"
	elif status.contains("role"):
		label = "身份职务"
	elif status.begins_with("official_") or status.contains("_official_summary"):
		label = "官方资料称号"
	elif status.contains("encyclopedia") or status.contains("wiki") or status.contains("nonofficial"):
		label = "百科称号"
	elif status.contains("fan_title"):
		label = "民间资料称号"
	var text := "\n称号性质：" + label
	if not url.is_empty(): text += "\n称号来源：" + url
	if status.contains("special_title_unconfirmed") or status.contains("species_classification_only"):
		text += "\n独立称号尚未核实。"
	return text

func title_for(id: String) -> String:
	id = canonical_id(id)
	var identity := UfeFighterDisplay.identity_entry(id)
	if identity.has("title") and not str(identity.title).is_empty(): return UfeDisplayText.text(str(identity.title))
	# 名册已把称号与名字拆开，登记过的称号直接采用，不再从名称里猜。
	var structured := UfeDisplayText.text(str(row_for(id).get("title", ""))).strip_edges()
	if not structured.is_empty(): return structured
	# 仅本人定义优先；借同一张图片不自动继承另一个身份或形态的称号。
	for candidate in [id]:
		if not FileAccess.file_exists("res://content/fighters/%s/definition.json" % candidate): continue
		var path := "res://content/fighters/%s/profile.json" % candidate
		if not FileAccess.file_exists(path): continue
		var runtime: Dictionary = UfeContentDatabase.read_json(path)
		var title := str(runtime.get("title", "")).strip_edges()
		if not title.is_empty(): return UfeDisplayText.text(title)
	var recorded := str(profile_for(id).get("title", "")).strip_edges()
	var row := row_for(id)
	# 来源已登记的完整别名如“杀手超兽 巴拉巴”，可把类别称号与姓名分开。
	if recorded.is_empty() or recorded.contains("静态档案") or recorded in ["怪兽", "宇宙人", "怪兽／宇宙人"]:
		var name := str(row.get("name", ""))
		for alias in detail_for(id).get("aliases", []):
			var full := UfeDisplayText.text(str(alias))
			if name.is_empty() or not full.ends_with(name): continue
			var prefix := full.trim_suffix(name).strip_edges()
			if prefix.is_empty() or prefix.length() > 12: continue
			for ending in ["怪兽", "超兽", "宇宙人", "怪人", "机器人", "恐龙", "生命体"]:
				if prefix.ends_with(ending): return prefix
	if not recorded.is_empty() and not recorded.contains("静态档案"): return UfeDisplayText.text(recorded)
	match str(row.get("kind", "")):
		"hero": return "奥特战士"
		"dark_ultra": return "黑暗巨人"
		"form": return "形态"
		"kaiju": return "宇宙人" if str(row.get("name", "")).contains("星人") else "怪兽"
	return ""

func source_lines(profile: Dictionary) -> String:
	var text := ""
	if profile.has("source_url") and not str(profile.source_url).is_empty():
		text += "\n来源：" + str(profile.get("source_label", "资料来源")) + "\n" + str(profile.source_url)
		var license := str(profile.get("license", ""))
		if license.is_empty(): license = "CC BY-SA 4.0" if str(profile.source_url).contains("wikipedia.org/") else "按原来源条款"
		text += "\n许可：" + license
	for source in profile.get("sources", []):
		if source is Dictionary and not str(source.get("url", "")).is_empty():
			text += "\n来源：" + str(source.url) + "\n许可：" + str(source.get("license", "按原来源条款"))
	return text
