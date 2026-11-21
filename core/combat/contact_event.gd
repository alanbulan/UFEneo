class_name UfeContactEvent
extends RefCounted

const REQUIRED_FIELDS: Array[String] = ["kind", "player", "move", "projectile", "x", "height", "feedback"]


static func make(kind: String, player: int, move_id: String, projectile: bool, point: Vector2i, feedback: Dictionary) -> Dictionary:
	return {
		"kind": kind,
		"player": player,
		"move": move_id,
		"projectile": projectile,
		"x": point.x,
		"height": point.y,
		"feedback": feedback.duplicate(true),
	}


static func matches_contract(event: Dictionary) -> bool:
	for field in REQUIRED_FIELDS:
		if not event.has(field):
			return false
	return (
		event["kind"] is String
		and event["player"] is int
		and event["move"] is String
		and event["projectile"] is bool
		and event["x"] is int
		and event["height"] is int
		and event["feedback"] is Dictionary
	)
