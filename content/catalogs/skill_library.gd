class_name UfeSkillLibrary
extends RefCounted
## Research only. Simulation reads MoveData, never this production catalog.
const PATH := "res://content/combat/skill_library.json"
const MAX_PAGE_SIZE := 48
static var _by_character: Dictionary = {}
static var _loaded := false
static var source_reads := 0

static func _ensure_loaded() -> void:
	if not _loaded:
		var data = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		source_reads += 1
		if data is Dictionary:
			for skill in data.get("skills", []):
				if not _by_character.has(skill.character_id):
					_by_character[skill.character_id] = []
				_by_character[skill.character_id].append(skill)
		_loaded = true

static func query_page(id: String, page: int = 0, page_size: int = 8) -> Dictionary:
	_ensure_loaded()
	var skills: Array = _by_character.get(id, [])
	var count := clampi(page_size, 1, MAX_PAGE_SIZE)
	var pages := maxi(1, ceili(skills.size() / float(count)))
	var current := clampi(page, 0, pages - 1)
	var rows: Array[Dictionary] = []
	for i in range(current * count, mini(skills.size(), (current + 1) * count)):
		rows.append(skills[i])
	return {"rows": rows, "total": skills.size(), "page": current, "pages": pages, "page_size": count}

static func for_character(id: String) -> Array[Dictionary]:
	# Research compatibility. UI uses query_page to keep formatting bounded.
	_ensure_loaded()
	var found: Array[Dictionary] = []
	found.assign(_by_character.get(id, []))
	return found
