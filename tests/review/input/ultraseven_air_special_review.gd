class_name UfeUltrasevenAirSpecialReview
extends UfeReviewDriver
@warning_ignore_start("integer_division")
## 只在训练开局设置站位/能量；跳跃、空中P和之后的全部运动都由InputFrame驱动。
func _init() -> void:profile="stage4_ultraseven_air_special"
func section(frame: int) -> int:return mini(frame/240,1)
func length_frames() -> int:return 480
func label(frame: int) -> String:return "赛文 · 空中念力头镖 · "+("多段命中 → 接回 → 装回" if section(frame)==0 else "空中P / 武器回收后恢复护架")
func prepare_match(sim: UfeMatchDirector) -> void:
	sim.fighters[0].x=500
	sim.fighters[1].x=680
	sim.fighters[0].stats.energy=1000
func sample(frame: int,_sim: UfeMatchDirector) -> UfeInputFrame:
	var age:=frame%240
	if age==30:return UfeInputFrame.make(0,1)
	if age==36:return UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	return UfeInputFrame.make()
func second_sample(_frame: int) -> UfeInputFrame:return UfeInputFrame.make()
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var f:=sim.fighters[0]
	var a:=view._animation(f,view.manifests[0])
	trace.append({"movie_frame":frame,"tick":sim.tick,"height":f.height,"move":f.move_id,"move_tick":f.move_tick,
		"sprite":a.get("index",-1),"target_hp":sim.fighters[1].stats.hp,"combo":f.combat.combo,"energy":f.stats.energy,
		"inputs":last_inputs.duplicate(true),"projectiles":sim.projectiles.duplicate(true),"events":sim.events.duplicate(true)})
func save_file(path: String) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练真实InputFrame；不修改运动中的状态/高度/伤害", "trace":trace},"\t"))
@warning_ignore_restore("integer_division")
