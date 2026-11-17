class_name UfePixelHudAirReview
extends UfePhase3ZettonAirReview
func _init() -> void: profile="phase4_hud_air_safe_area"
func section(_frame: int) -> int: return 23
func length_frames() -> int: return 360
func boxes(_frame: int) -> bool: return false
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	return super.sample(frame+23*240,sim)
