class_name UfeCaptureView
extends RefCounted
## 仅从捕获关系和当前本人帧读取特效；不改变模拟或隐藏被捕获人物。
var config: Dictionary = {}
var last_tick: int = -1
var last_match: UfeMatchDirector

func setup() -> void:
	var path := "res://content/presentation/capture_effects.json"
	if FileAccess.file_exists(path): config = UfeContentDatabase.read_json(path)

func binding(actor: UfeFighter, move: String) -> Dictionary:
	return config.get(actor.definition.id,{}).get(move,{})

func render_offset(view: UfeSideView,index: int) -> Vector2:
	var f := view.simulation.fighters[index]
	if not f.motion.has("capture_victim"):return Vector2.ZERO
	var actor := view.simulation.fighters[int(f.motion.capture_victim.owner)]
	var relation:Dictionary=actor.motion.get("capture",{})
	if str(relation.get("phase",""))!="shrink":return Vector2.ZERO
	var duration:=int(actor.definition.moves[actor.move_id].capture.stages[1].ticks)
	var remaining:=maxi(0,duration-1-int(relation.phase_age))
	return Vector2(0,-int(f.frame().get("capture_center_start",0))*remaining/maxi(1,duration-1))

func attachments_for(view: UfeSideView, index: int) -> Array:
	var result: Array=[]
	var f := view.simulation.fighters[index]
	var owner := index
	if f.motion.has("capture_victim"): owner=int(f.motion.capture_victim.owner)
	var actor := view.simulation.fighters[owner]
	var relation: Dictionary=actor.motion.get("capture",{})
	if relation.is_empty():return result
	var spec: Dictionary=binding(actor,str(relation.move)).get("phases",{}).get(str(relation.phase),{})
	if spec.is_empty():return result
	var subject := owner if str(spec.subject)=="owner" else int(relation.victim)
	if subject!=index:return result
	var age := int(relation.phase_age)-int(spec.get("start_age",0))
	if age<0 or int(relation.phase_age)>=int(spec.get("end_age",1000000)):return result
	var effect := str(spec.effect)
	if not view.projectile_clips.has(effect):return result
	var anchor: Array=spec.get("anchor",f.frame().get("capture_effect_anchor",[0,0]))
	anchor=anchor.duplicate()
	anchor[1]=int(anchor[1])-int(render_offset(view,index).y)
	result.append({"effect":effect,"sprite":UfeEffectTimeline.phase(view.projectile_clips[effect],age,false),
		"anchor":anchor,"facing":actor.facing,"z_index":1 if bool(spec.get("behind_fighter",false)) else 3})
	return result

func sync_events(view: UfeSideView) -> void:
	var sim := view.simulation
	if not is_same(sim,last_match):last_tick=-1;last_match=sim
	if sim.tick==last_tick:return
	last_tick=sim.tick
	for event in sim.events:
		if str(event.kind)!="capture_fail":continue
		var owner := int(event.player)
		var actor := sim.fighters[owner]
		var data := binding(actor,str(event.move))
		if data.is_empty() or str(event.reason)=="guard":continue # 普通防御已由真实block反馈点出专属消散。
		var point: Array=[]
		var guarded := false
		for contact in sim.events:
			if bool(contact.get("capture_intercepted",false)) and int(contact.player)==1-owner:
				point=[int(contact.x),int(contact.height)];guarded=true;break
		if point.is_empty():
			var token := int(actor.motion.get("capture",{}).get("token",-1))
			for p in view.feedback.projectile_observations+sim.projectiles:
				if bool(p.get("capture",false)) and int(p.source_owner)==owner and int(p.get("capture_token",-2))==token:
					point=[int(p.x),int(p.height)];break
		if not point.is_empty():view.feedback.spawn(str(data.guard_dissolve if guarded else data.miss_dissolve),int(point[0]),int(point[1]),[1,1,1,1],actor.facing)
