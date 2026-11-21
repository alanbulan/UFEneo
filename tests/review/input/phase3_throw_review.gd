class_name UfePhase3ThrowReview
extends UfeReviewDriver
@warning_ignore_start("integer_division")
## 两个攻击方向；只设置训练组的开局距离，组内通过真实InputFrame执行。
const ACTIONS := ["throw_forward","throw_back","air_throw","dash_throw","tech_simultaneous","tech_tick3"]
const NAMES := ["前投","后投","空中擒摔","冲刺擒抱","同时投·拆投","被抓后第3tick拆投"]
var active_player: int=0
var passive := UfeInputFrame.make()
var capture_age: int=0
const FIGHTER_ACTIONS := ["throw_forward","throw_back","air_throw","dash_throw","motion_41236"]
var fighter_audit: bool=false
var throw_sent: bool=false
var alpha_bottom_offsets: Dictionary={}
func _init() -> void: profile="phase3_throws"
func section(frame: int) -> int:return mini(frame/180,FIGHTER_ACTIONS.size()*2-1 if fighter_audit else 11)
func length_frames() -> int:return FIGHTER_ACTIONS.size()*360 if fighter_audit else 2160
func action_at(frame: int) -> String:return str(FIGHTER_ACTIONS[section(frame)%FIGHTER_ACTIONS.size()] if fighter_audit else ACTIONS[section(frame)%6])
func boxes(_frame: int) -> bool:return true
func label(frame: int) -> String:
	if fighter_audit:return action_at(frame)+(" · 向右" if section(frame)<FIGHTER_ACTIONS.size() else " · 向左")+" · F1抓点/判定框"
	return ("初代 → 杰顿 · " if section(frame)<6 else "杰顿 → 初代 · ")+NAMES[section(frame)%6]+" · F1抓点/判定框"
func prepare_match(sim: UfeMatchDirector) -> void:
	active_player=0 if fighter_audit else section(review_frame)/6
	capture_age=0
	throw_sent=false
	passive=UfeInputFrame.make()
	var action: String=action_at(review_frame)
	if fighter_audit:
		var direction:=1 if section(review_frame)<FIGHTER_ACTIONS.size() else -1
		var gap:=110 if action=="dash_throw" else 52
		sim.fighters[0].x=640-direction*(gap/2)
		sim.fighters[1].x=sim.fighters[0].x+direction*gap
		sim.fighters[0].facing=direction
		sim.fighters[1].facing=-direction
	else:
		sim.fighters[0].x=500
		sim.fighters[1].x=610 if action=="dash_throw" else 552
func second_sample(_frame: int) -> UfeInputFrame:return passive
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var action: String=action_at(frame)
	var age:=frame%180
	var f:=sim.fighters[active_player]
	var b:=sim.fighters[1-active_player]
	var first:=UfeInputFrame.make()
	var second:=UfeInputFrame.make()
	if action=="air_throw":
		if age==20:
			first=UfeInputFrame.make(0,1,UfeInputFrame.JUMP);second=UfeInputFrame.make(0,1,UfeInputFrame.JUMP)
		if (age==25 and not fighter_audit) or (fighter_audit and not throw_sent and age>20 and f.state=="air" and b.state=="air"):
			first=UfeInputFrame.make(0,0,UfeInputFrame.THROW)
			throw_sent=true
	elif action=="motion_41236":
		if age==30:first=direction_skill_input(action,f.facing)
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
		if data.has("target") and data.target.get("mode","")=="hold":
			var offset:=UfeThrowResolver.RootOffsets.offset(sim.fighters[1-i],data.target)
			if offset.size()==2:entry.grip_world=[f.x+f.facing*(int(data.target.grip[0])+int(offset[0])),f.height+int(data.target.grip[1])+int(offset[1])]
		if f.state=="thrown" and f.combat.thrower>=0:
			var target: Dictionary=sim.fighters[f.combat.thrower].frame().get("target",{})
			if str(target.get("mode",""))=="hold":
				var p: Array=UfeThrowResolver.HoldPoints.point(f,target,data) if target.has("hold_point_overrides") else data.get("grab_points",{}).get(str(target.get("grab_point","waist")),[])
				if p.size()==2:entry.grab_world=[f.x+f.facing*int(p[0]),f.height+int(p[1])]
		var hurt_boxes: Array=data.get("hurtboxes",[])
		if not hurt_boxes.is_empty():
			var bottom:=int(hurt_boxes[0][1])
			for box in hurt_boxes:bottom=mini(bottom,int(box[1]))
			entry.body_bottom=f.height+bottom
			entry.hurtbox_bottom=f.height+bottom
		var pixels:=pixel_bottom(a)
		if not pixels.is_empty():
			entry.pixel_bottom=f.height+int(pixels.offset)
			entry.alpha_bounds=pixels.bounds
			entry.texture=a.texture
			entry.rect=a.rect
			entry.anchor=a.anchor
		if data.has("target"):entry.target=data.target.duplicate(true)
		pair.append(entry)
	trace.append({"movie_frame":frame,"section":section(frame),"action":action_at(frame),"player":active_player,"inputs":last_inputs.duplicate(true),"tick":sim.tick,"state_hash":sim.state_hash(),"pair":pair,"events":sim.events.duplicate(true),"boxes":view.show_boxes,"camera_x":view.camera_x,"camera_y":view.camera_y})
func pixel_bottom(animation: Dictionary) -> Dictionary:
	var path:=str(animation.get("texture",""))
	var rect: Array=animation.get("rect",[])
	var anchor: Array=animation.get("anchor",[])
	if path.is_empty() or rect.size()!=4 or anchor.size()!=2:return {}
	var key:="%s:%s:%s" % [path,rect,anchor]
	if not alpha_bottom_offsets.has(key):
		var texture:=load(path) as Texture2D
		var image: Image=texture.get_image() if texture!=null else null
		if image==null:return {}
		if image.is_compressed():image.decompress()
		var region:=Rect2i(int(rect[0]),int(rect[1]),int(rect[2]),int(rect[3]))
		var used:=image.get_region(region).get_used_rect()
		if not used.has_area():return {}
		alpha_bottom_offsets[key]={"offset":int(anchor[1])-used.end.y,"bounds":[used.position.x,used.position.y,used.size.x,used.size.y]}
	return alpha_bottom_offsets[key]
func save_file(path: String) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"profile":profile,"input_source":"主游戏训练真实InputFrame；每组只设开局距离，组内不改状态/坐标/高度；双方抓点与实际帧、拆投事件均来自同一模拟。","clearance_units":"原生像素；向上为正，0为地面；hurtbox_bottom为受击框底缘，pixel_bottom为实际显示图集Alpha下边界，不夹取负值。body_bottom仅保留为受击框旧字段。","trace":trace},"\t"))
@warning_ignore_restore("integer_division")
