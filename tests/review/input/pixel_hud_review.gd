class_name UfePixelHudReview
extends UfePhase3AudioReview
## 一回合完整真实输入；仅开局配置能量/距离，180–269帧通过主游戏暂停。
func _init() -> void: profile="phase4_pixel_hud"
func boxes(_frame: int) -> bool: return false
func label(_frame: int) -> String: return "像素HUD完整回合"
func length_frames() -> int: return 2400
func prepare_match(sim: UfeMatchDirector) -> void:
	active_player=0
	sim.fighters[0].x=500
	sim.fighters[1].x=575
	for f in sim.fighters: f.stats.energy=3000
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var a:=UfeInputFrame.make()
	var b:=UfeInputFrame.make()
	if frame in [100,114,128]: a=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
	if frame==300: b=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
	if frame==420: a=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	if frame==650: b=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	if frame>=900: a=command_input("motion_623",posmod(frame-900,75),sim.fighters[0])
	passive=b
	return a
