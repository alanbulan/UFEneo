class_name UfeActionSoundLibrary
extends RefCounted
static var cache: Dictionary = {}
static var records: Dictionary = {}
static var loads := 0
static var actors: Dictionary = {}

static func prepare() -> void:
	if not cache.is_empty():
		return
	records = JSON.parse_string(FileAccess.get_file_as_string("res://content/presentation/action_sounds.json")).sounds
	var character_data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/presentation/character_sounds.json"))
	records.merge(character_data.sounds)
	actors = character_data.actors
	for id in records:
		var stream := load(str(records[id].path)) as AudioStreamWAV
		if stream == null:
			push_error("动作音效缺失：" + str(id))
			continue
		if records[id].loop:
			stream = stream.duplicate()
			stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
			stream.loop_begin = 0
			stream.loop_end = stream.data.size() / 2
		cache[id] = stream
		loads += 1

static func get_sound(id: String) -> AudioStreamWAV:
	return cache.get(id)
