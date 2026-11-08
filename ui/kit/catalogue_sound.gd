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
static var cache: Dictionary = {}

static func for_entry(catalogue_id: String, base_character: String = "") -> Dictionary:
	var base := base_character if not base_character.is_empty() else catalogue_id
	var key := base
	if cache.has(key): return cache[key]
	var picked := {"path": PICK_SOUND, "volume_db": PICK_VOLUME_DB, "own_voice": false}
	for tail in VOICE_CANDIDATES:
		var candidate := "res://assets/audio/characters/%s/%s" % [base, tail]
		if ResourceLoader.exists(candidate):
			picked = {"path": candidate, "volume_db": VOICE_VOLUME_DB, "own_voice": true}
			break
	cache[key] = picked
	return picked
