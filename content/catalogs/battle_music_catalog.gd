class_name UfeBattleMusicCatalog
extends RefCounted
## 曲目归属只采用台账列出的来源；同一原曲变奏在曲名中明确。
const PATH: String="res://content/audio/battle_music.json"
static var cached: Dictionary={}

static func data() -> Dictionary:
	if cached.is_empty() and FileAccess.file_exists(PATH):cached=UfeContentDatabase.read_json(PATH)
	return cached

static func tracks() -> Array:
	return data().get("tracks",[])

static func track(id: String) -> Dictionary:
	for item in tracks():
		if str(item.id)==id:return item
	return {}

static func options() -> Array:
	var values: Array=[{"id":"auto","name":"自动 · 按出场人物"},{"id":"random","name":"随机曲目"},{"id":"off","name":"关闭BGM"}]
	for item in tracks():
		if bool(item.get("selectable",true)):values.append({"id":str(item.id),"name":str(item.name)})
	return values

static func valid_choice(id: String) -> String:
	return id if id in ["auto","random","off"] or not track(id).is_empty() else "auto"

static func owner_id(id: String,form_id: String="") -> String:
	if id in ["super-taro","super_taro"] or form_id in ["super-taro","super_taro"]:return "ultraman-taro"
	return id.get_slice("__",0)

static func for_fighter(id: String,form_id: String="") -> String:
	var fighters: Dictionary=data().get("fighters",{})
	return str(fighters.get(owner_id(id,form_id),data().get("fallback","battle_1")))

static func association(id: String,form_id: String="") -> String:
	var owner:=owner_id(id,form_id)
	var fighters: Dictionary=data().get("fighters",{})
	if not fighters.has(owner):return "通用回退"
	return "气氛配乐" if for_fighter(id,form_id)=="monster-pressure" else "本人作品配乐"
