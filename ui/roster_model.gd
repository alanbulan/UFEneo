class_name UfeRosterModel
extends RefCounted
var catalog: Dictionary
var entries: Array=[]
var filtered: Array=[]
func _init() -> void:
	catalog=UfeContentDatabase.read_json("res://content/roster/catalog.json")
	entries=UfeContentDatabase.read_json("res://content/roster/selection.json").entries
	filter()
func filter(category: String="all", era: String="all", series: String="all") -> void:
	filtered=entries.filter(func(e):return (category=="all" or str(e.selection_category)==category) and (era=="all" or str(e.era)==era) and (series=="all" or series in e.series_ids))
func index_of(id: String) -> int:
	for i in range(filtered.size()):
		if filtered[i].id==id:return i
	return -1
static func implemented(id: String) -> bool:
	var path:="res://content/fighters/%s/definition.json"%id
	if not FileAccess.file_exists(path):return false
	var data: Dictionary=UfeContentDatabase.read_json(path)
	# 与核心加载器一致：最早实装角色未写该字段，准备中的角色显式为false。
	return bool(data.get("playable",true)) or bool(data.get("pilot_playable",false))
