class_name PixelCatalogueSound
extends RefCounted
## 图鉴试听选声。
## 优先用角色本人的登场声（怪兽咆哮、奥特战士叫喊）——这些音频已在
## content/audio 里逐项核过归属；没有本人声音的条目统一用像素界面提示音，
## 不拿别的角色声音顶替。

const PICK_SOUND := "res://assets/audio/production/v1/catalogue_pick.wav"
const PICK_VOLUME_DB := -6.0
const VOICE_VOLUME_DB := -9.0
## 按优先级排列：先登场咆哮，再威吓咆哮，最后奥特战士的叫喊。
const VOICE_CANDIDATES: Array[String] = [
	"roars-v3/intro.wav",
	"roar_threat.wav",
	"c-type/preview-v001/call-1/sound.wav",
]
const RUNTIME_PATH := "res://content/audio/runtime.json"
const SOURCES_PATH := "res://content/audio/sources.json"
# 亚刻的 intro 是合体前卢提昂对白，不是亚刻本人登场声；
# 欧米伽的 intro 当前是光线释放喊声，不拿技能声冒充试听。
const NON_SELF_INTRO := ["ultraman-arc", "ultraman-omega"]
static var cache: Dictionary = {}
static var runtime_data: Dictionary = {}
static var installed_records: Dictionary = {}

static func _read_runtime() -> void:
	if not runtime_data.is_empty() or not FileAccess.file_exists(RUNTIME_PATH):
		return
	var parsed = UfeContentDatabase.read_json(RUNTIME_PATH)
	if parsed is Dictionary:
		runtime_data = parsed

static func _record_status(sound_id: String) -> String:
	if installed_records.is_empty() and FileAccess.file_exists(SOURCES_PATH):
		var parsed = UfeContentDatabase.read_json(SOURCES_PATH)
		if parsed is Dictionary and parsed.get("records") is Array:
			for record in parsed.records:
				if record is Dictionary:
					installed_records[str(record.get("id", ""))] = str(record.get("runtime_status", "installed"))
	var status := str(installed_records.get(sound_id, ""))
	return status if status == "installed" or status == "installed_pending_user_listening" else ""

static func _runtime_intro(base: String) -> String:
	_read_runtime()
	if base.is_empty() or NON_SELF_INTRO.has(base):
		return ""
	var voices: Dictionary = runtime_data.get("voices", {})
	var voice: Dictionary = voices.get(base, {})
	var sound_id := str(voice.get("intro", ""))
	if sound_id.is_empty() or not _record_status(sound_id).begins_with("installed"):
		return ""
	var sounds: Dictionary = runtime_data.get("sounds", {})
	var sound: Dictionary = sounds.get(sound_id, {})
	var path := str(sound.get("path", ""))
	# 只有当台账与资源都齐全时才认作本人声；没有 intro 不拿 victory/attack 顶替。
	if path.is_empty() or not path.begins_with("res://") or not ResourceLoader.exists(path):
		return ""
	return path

static func for_entry(catalogue_id: String, base_character: String = "") -> Dictionary:
	var base := base_character if not base_character.is_empty() else catalogue_id
	var key := catalogue_id + "|" + base
	if cache.has(key): return cache[key]
	var picked := {"path": PICK_SOUND, "volume_db": PICK_VOLUME_DB, "own_voice": false}
	for tail in VOICE_CANDIDATES:
		var candidate := "res://assets/audio/characters/%s/%s" % [base, tail]
		if ResourceLoader.exists(candidate):
			picked = {"path": candidate, "volume_db": VOICE_VOLUME_DB, "own_voice": true}
			break
	if not bool(picked.own_voice):
		var runtime_intro := _runtime_intro(base)
		if not runtime_intro.is_empty():
			picked = {"path": runtime_intro, "volume_db": VOICE_VOLUME_DB, "own_voice": true}
	cache[key] = picked
	return picked
