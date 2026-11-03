class_name UfeContactSoundLibrary
extends RefCounted
## Shared offline WAV assets. Combat events only select an already loaded sound.
const ROOT := "res://assets/audio/shared/contact/v001/"
static var cache: Dictionary = {}
static var loads := 0

static func prepare(kinds: Array) -> void:
	for kind in kinds:
		if not cache.has(kind):
			var sound := load(ROOT + str(kind).to_lower() + "/sound.wav") as AudioStreamWAV
			if sound == null:
				push_error("接触音效缺失：" + str(kind))
				continue
			cache[kind] = sound
			loads += 1

static func for_kind(kind: String) -> AudioStreamWAV:
	return cache.get(kind, cache.get("LIGHT"))
