class_name UfeRosterCatalog
extends RefCounted
## Lightweight shared index; full research is loaded only on selection.
const PATH := "res://content/roster/index.json"
const KIND_NAMES := {"hero": "英雄 / 战友", "kaiju": "怪兽 / 宇宙人 / 机甲", "dark_ultra": "黑暗巨人 / 敌役", "form": "形态 / 外观", "story": "剧情人物"}
const ERA_NAMES := {"showa": "昭和", "overseas": "海外", "heisei": "平成", "newgen": "新生代", "alternate": "独立世界观"}
var entries: Array[Dictionary] = []
var series: Array[Dictionary] = []
var by_id: Dictionary = {}
var errors: Array[String] = []
const MAX_PAGE_SIZE := 48
const QUERY_CACHE_LIMIT := 8
const DETAIL_CACHE_LIMIT := 16
static var _shared: Dictionary = {}
static var _queries: Dictionary = {}
static var _query_order: Array[String] = []
static var _details: Dictionary = {}
static var _detail_order: Array[String] = []
static var index_reads := 0
static var detail_reads := 0
static var query_scans := 0
static var related_scans := 0
var _store: Dictionary = {}
var _cache_prefix := ""

func _init(path: String = PATH) -> void:
	_cache_prefix = path + ":"
	if path == PATH and not _shared.is_empty():
		_store = _shared
	else:
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		index_reads += 1
		if not parsed is Dictionary or parsed.get("schema") != 1:
			errors.append("角色目录格式错误")
			return
		_store = {"entries": [], "series": parsed.get("series", []), "by_id": {}, "positions": {}, "work_names": {}, "era": {}, "kind": {}, "work": {}, "forms": {}, "errors": []}
		for work in _store.series:
			_store.work_names[work.id] = work.name
		for row in parsed.get("entries", []):
			if not row is Dictionary or _store.by_id.has(row.get("id", "")):
				_store.errors.append("角色记录重复或无效")
				continue
			_store.positions[row.id] = _store.entries.size()
			_store.entries.append(row)
			_store.by_id[row.id] = row
			_bucket("era", row.era, row.id)
			_bucket("kind", row.kind, row.id)
			for sid in row.get("series_ids", []):
				_bucket("work", sid, row.id)
				if not _store.work_names.has(sid):
					_store.errors.append("未知作品: " + str(sid))
			if not str(row.get("base_character", "")).is_empty():
				_bucket("forms", row.base_character, row.id)
			if not KIND_NAMES.has(row.get("kind")):
				_store.errors.append("未知角色种类")
			if row.get("playable", false) and str(row.get("fighter_resource", "")).is_empty():
				_store.errors.append("可玩角色缺少已验收资源")
		for row in _store.entries:
			if not str(row.get("base_character", "")).is_empty() and not _store.by_id.has(row.base_character):
				_store.errors.append("形态缺少所属角色")
		_store["all_ids"] = _store.by_id.keys()
		if path == PATH:
			_shared = _store
	entries.assign(_store.entries)
	series.assign(_store.series)
	by_id = _store.by_id
	errors.assign(_store.errors)

func _bucket(group: String, key: String, id: String) -> void:
	if not _store[group].has(key):
		_store[group][key] = []
	_store[group][key].append(id)

func _matching_ids(query: String, era: String, kind: String, work: String) -> Array:
	var terms := query.strip_edges().to_lower().split(" ", false)
	var key := _cache_prefix + JSON.stringify([terms, era, kind, work])
	if _queries.has(key):
		_query_order.erase(key)
		_query_order.append(key)
		return _queries[key]
	var candidates: Array = _store.all_ids
	for pair in [["era", era], ["kind", kind], ["work", work]]:
		if not str(pair[1]).is_empty():
			var bucket: Array = _store[pair[0]].get(pair[1], [])
			if bucket.size() < candidates.size():
				candidates = bucket
	var ids: Array = []
	query_scans += 1
	for id in candidates:
		var row: Dictionary = by_id[id]
		if not era.is_empty() and row.era != era:
			continue
		if not kind.is_empty() and row.kind != kind:
			continue
		if not work.is_empty() and work not in row.series_ids:
			continue
		var matches := true
		for term in terms:
			if not str(row.get("search_text", "")).contains(term):
				matches = false
				break
		if matches:
			ids.append(id)
	_remember_query(key, ids)
	return ids

func _remember_query(key: String, ids: Array) -> void:
	_queries[key] = ids
	_query_order.append(key)
	while _query_order.size() > QUERY_CACHE_LIMIT:
		_queries.erase(_query_order.pop_front())

func _page(ids: Array, page: int, requested_size: int) -> Dictionary:
	var count := clampi(requested_size, 1, MAX_PAGE_SIZE)
	var pages := maxi(1, ceili(ids.size() / float(count)))
	var current := clampi(page, 0, pages - 1)
	var rows: Array[Dictionary] = []
	for i in range(current * count, mini(ids.size(), (current + 1) * count)):
		rows.append(by_id[ids[i]])
	return {"rows": rows, "total": ids.size(), "page": current, "pages": pages, "page_size": count}

func query_page(query: String = "", era: String = "", kind: String = "", work: String = "", page: int = 0, page_size: int = 24) -> Dictionary:
	return _page(_matching_ids(query, era, kind, work), page, page_size)

func page_for_id(id: String, query: String, era: String, kind: String, work: String, page_size: int = 24) -> int:
	var index := _matching_ids(query, era, kind, work).find(id)
	return floori(index / float(clampi(page_size, 1, MAX_PAGE_SIZE))) if index >= 0 else -1

func detail_for(id: String) -> Dictionary:
	if not by_id.has(id):
		return {}
	var key := _cache_prefix + id
	if _details.has(key):
		_detail_order.erase(key)
		_detail_order.append(key)
		return _details[key]
	var path := str(by_id[id].get("detail_path", ""))
	if not path.begins_with("content/roster/details/") or ".." in path.split("/"):
		errors.append("角色详细资料路径无效: " + id)
		return by_id[id]
	var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://" + path))
	detail_reads += 1
	if not parsed is Dictionary or parsed.get("id") != id:
		errors.append("角色详细资料不匹配: " + id)
		return by_id[id]
	_details[key] = parsed
	_detail_order.append(key)
	while _detail_order.size() > DETAIL_CACHE_LIMIT:
		_details.erase(_detail_order.pop_front())
	return parsed

func forms_for(id: String) -> Array[Dictionary]:
	var found: Array[Dictionary] = []
	for child in _store.forms.get(id, []):
		found.append(by_id[child])
	return found

func forms_page(id: String, page: int = 0, page_size: int = 8) -> Dictionary:
	return _page(_store.forms.get(id, []), page, page_size)

func related_page(row: Dictionary, page: int = 0, page_size: int = 8) -> Dictionary:
	var key := _cache_prefix + "related:" + JSON.stringify([row.id, row.series_ids])
	if _queries.has(key):
		_query_order.erase(key)
		_query_order.append(key)
		return _page(_queries[key], page, page_size)
	related_scans += 1
	var related_ids: Dictionary = {}
	for sid in row.series_ids:
		for id in _store.work.get(sid, []):
			if id != row.id:
				related_ids[id] = true
	var ids: Array = related_ids.keys()
	ids.sort_custom(func(a: String, b: String): return _store.positions[a] < _store.positions[b])
	_remember_query(key, ids)
	return _page(ids, page, page_size)

func search(query: String = "", era: String = "", kind: String = "", series_id: String = "") -> Array[Dictionary]:
	# Research compatibility. UI must use query_page so result rows stay bounded.
	var found: Array[Dictionary] = []
	for id in _matching_ids(query, era, kind, series_id):
		found.append(by_id[id])
	return found

func work_names(row: Dictionary, limit: int = 0) -> String:
	var names: Array[String] = []
	for work in series:
		if work.id in row.series_ids:
			names.append(work.name)
	if limit > 0 and names.size() > limit:
		return " / ".join(names.slice(0, limit)) + " 等%d部作品" % names.size()
	return " / ".join(names)

func related(row: Dictionary, limit: int = 12) -> Array[Dictionary]:
	return related_page(row, 0, limit).rows

func statistics() -> Dictionary:
	return {"index_reads": index_reads, "detail_reads": detail_reads, "query_scans": query_scans, "related_scans": related_scans, "cached_details": _details.size(), "cached_queries": _queries.size()}

func research(row: Dictionary) -> String:
	row = detail_for(str(row.id))
	var notes: Array = row.get("research_notes", [])
	var result := ""
	var count := 0
	for note in notes:
		if str(note.get("text", "")).is_empty():
			continue
		result += "【" + str(note.heading) + "】\n" + str(note.text).left(1400) + "\n\n"
		count += 1
		if count >= 3:
			break
	if not result.is_empty():
		return result + "资料来自维基百科，适用知识共享署名相同方式共享 4.0。固定修订与作者记录见研究文档。"
	if not notes.is_empty():
		var appearances: Array[String] = []
		for note in notes:
			if str(note.heading) not in appearances:
				appearances.append(str(note.heading))
			if appearances.size() >= 8:
				break
		return "【出场资料】\n" + "\n".join(appearances) + "\n\n已收录维基命名条目。角色技能与详细剧情尚待核对，未换算为游戏招式或数值。"
	return "【研究进度】\n" + work_names(row) + "\n\n角色技能、形态与剧情资料正在整理。维基原文与固定修订可通过右侧入口查看。"

func work_research(row: Dictionary) -> String:
	row = detail_for(str(row.id))
	var documents: Array = row.get("wikipedia", [])
	if documents.is_empty():
		return "维基百科资料待补充；技能、形态与剧情不按猜测填写。"
	var text := "维基百科研究摘录（技能数据尚待设计验收）\n"
	var sources: Array[Dictionary] = []
	for document in documents.slice(0, 3):
		var path := "res://" + str(document.file)
		if not FileAccess.file_exists(path):
			continue
		var source = JSON.parse_string(FileAccess.get_file_as_string(path))
		if source is Dictionary and source.get("language", "") == "zh":
			sources.append(source)
	# Show a small selection; complete revision-linked text stays in the research document.
	var used := 0
	var shown: Array[String] = []
	for tag in ["skills", "forms", "story", "characters"]:
		var found := false
		for source in sources:
			for section in source.get("sections", []):
				var key := str(source.id) + "/" + str(section.heading)
				if tag in section.categories and not str(section.text).is_empty() and key not in shown:
					text += "\n" + str(source.get("display_title", source.title)) + " / " + str(section.heading) + "\n" + str(section.text).left(1200) + "\n"
					shown.append(key)
					used += 1
					found = true
					break
			if found:
				break
	return text + ("\n完整章节见研究文档。\n摘录适用知识共享署名相同方式共享 4.0，作者与固定修订见文档。" if used > 0 else "中文正文章节待补充。")
