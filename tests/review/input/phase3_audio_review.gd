class_name UfePhase3AudioReview
extends UfePhase3SuperReview
var audio_cursor: int=0
## 单回合：只设置开局能量/站位；此后仅输入，生命值不重置。
func _init() -> void:profile="phase3_audio_round"
func section(_frame: int) -> int:return 0
func length_frames() -> int:return 2100
func wants_intro() -> bool:return true
func label(_frame: int) -> String:return "有声完整回合 · 登场/普通远程/双方三级必杀/胜负"
func prepare_match(sim: UfeMatchDirector) -> void:
	active_player=0
	sim.fighters[0].x=500
	sim.fighters[1].x=720
	for f in sim.fighters:f.stats.energy=3000
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var a:=UfeInputFrame.make()
	var b:=UfeInputFrame.make()
	if frame==105:a=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
	if frame==210:b=UfeInputFrame.make(0,0,UfeInputFrame.RANGED)
	if frame==315:a=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	if frame==520:b=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	if frame>=750:a=command_input("motion_623",posmod(frame-750,75),sim.fighters[0])
	passive=b
	return a
