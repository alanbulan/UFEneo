class_name UfePhase3ThrowReview
extends UfeReviewDriver
## 两个攻击方向；只设置训练组的开局距离，组内通过真实InputFrame执行。
const ACTIONS := ["throw_forward","throw_back","air_throw","dash_throw","tech_simultaneous","tech_tick3"]
const NAMES := ["前投","后投","空中擒摔","冲刺擒抱","同时投·拆投","被抓后第3tick拆投"]
var active_player: int=0
var passive := UfeInputFrame.make()
var capture_age: int=0
func _init() -> void: profile="phase3_throws"
func section(frame: int) -> int:return mini(frame/180,11)
func length_frames() -> int:return 2160
func boxes(_frame: int) -> bool:return true
func label(frame: int) -> String:return ("初代 → 杰顿 · " if section(frame)<6 else "杰顿 → 初代 · ")+NAMES[section(frame)%6]+" · F1抓点/判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	active_player=section(review_frame)/6
	capture_age=0
	var action: String=ACTIONS[section(review_frame)%6]
	sim.fighters[0].x=500
	sim.fighters[1].x=610 if action=="dash_throw" else 552
func second_sample(_frame: int) -> UfeInputFrame:return passive
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var action: String=ACTIONS[section(frame)%6]
	var age:=frame%180
	var f:=sim.fighters[active_player]
	var b:=sim.fighters[1-active_player]
	var first:=UfeInputFrame.make()
	var second:=UfeInputFrame.make()
	if action=="air_throw":
		if age==20:
			first=UfeInputFrame.make(0,1);second=UfeInputFrame.make(0,1)
		if age==25:first=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
	elif action=="dash_throw":
		if age in [20,21,24,25]:first=UfeInputFrame.make(f.facing)
		if age==29:first=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
	else:
		if age==30:
			first=UfeInputFrame.make(-f.facing if action=="throw_back" else 0,0,UfeInputFrame.THROW)
			if action=="tech_simultaneous":second=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
		if action=="tech_tick3" and b.state=="thrown":
			capture_age+=1
			if capture_age==3:second=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
	passive=second if active_player==0 else first
	return first if active_player==0 else second
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	var pair:=[]
	for i in range(2):
		var f:=sim.fighters[i]
		var a:=view._animation(f,view.manifests[i])
		var data:=f.frame()
		var entry:={"player":i,"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"state_tick":f.state_tick,"move":f.move_id,"move_tick":f.move_tick,"clip":a.get("key",""),"sprite":a.get("index",-1),"hp":f.stats.hp}
		if data.has("target") and data.target.get("mode","")=="hold":entry.grip_world=[f.x+f.facing*int(data.target.grip[0]),f.height+int(data.target.grip[1])]
		if f.state=="thrown" and data.has("grab_points"):
			var p: Array=data.grab_points.waist
			entry.grab_world=[f.x+f.facing*int(p[0]),f.height+int(p[1])]
		pair.append(entry)
	trace.append({"movie_frame":frame,"section":section(frame),"action":ACTIONS[section(frame)%6],"player":active_player,"inputs":last_inputs.duplicate(true),"tick":sim.tick,"pair":pair,"events":sim.events.duplicate(true),"boxes":view.show_boxes,"camera_x":view.camera_x,"camera_y":view.camera_y})
func save_file(path: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练真实InputFrame；每组只设开局距离，组内不改状态/坐标/高度；双方抓点与实际帧、拆投事件均来自同一模拟。","trace":trace},"\t"))
