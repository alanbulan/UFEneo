class_name UfeZettonCounterReview
extends UfeReviewDriver
## 仅在分组开始设训练站位；两组均通过真实输入触发侧闪手刀。
var passive := UfeInputFrame.make()
func _init() -> void: profile="zetton_counter"
func section(frame: int) -> int:return mini(frame/180,1)
func length_frames() -> int:return 360
func boxes(_frame: int) -> bool:return true
func label(frame: int) -> String:return "杰顿侧闪手刀（中段） → "+("站姿初代：命中头肩" if section(frame)==0 else "蹲姿初代：仍在横切覆盖内")+" · F1判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	sim.fighters[0].x=500
	sim.fighters[1].x=565
func sample(frame: int,_sim: UfeMatchDirector) -> UfeInputFrame:
	var age:=frame%180
	passive=UfeInputFrame.make(0,0,UfeInputFrame.DODGE if age==24 else UfeInputFrame.LIGHT if age==30 else 0)
	return UfeInputFrame.make(0,-1 if section(frame)==1 else 0)
func second_sample(_frame: int) -> UfeInputFrame:return passive
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var f:=sim.fighters[1];var b:=sim.fighters[0];var a:=view._animation(f,view.manifests[1])
	trace.append({"movie_frame":frame,"section":section(frame),"inputs":last_inputs.duplicate(true),"tick":sim.tick,"move":f.move_id,"move_tick":f.move_tick,"state":f.state,"sprite_index":a.get("index",-1),"clip":a.get("key",""),"x":f.x,"target_x":b.x,"target_height":b.height,"target_state":b.state,"target_hp":b.stats.hp,"boxes":view.show_boxes,"events":sim.events.duplicate(true)})
func save_file(path: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练真实InputFrame；只设分组初始站位；目标始终站姿或下蹲，不跳跃、不改模拟状态。","trace":trace},"\t"))
