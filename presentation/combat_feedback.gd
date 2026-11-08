class_name UfeCombatFeedback
extends Node2D
const PROJECTILE_EXPIRY = preload("res://presentation/projectile_expiry.gd")
## 事件每模拟tick消费一次；闪白由真实呈现帧推进，不受KO/暂停/命中停顿影响。
var clips: Dictionary = {}
var particles: Array = []
var flash: Array = [0,0]
var shake_ticks: int = 0
var last_tick: int = -1
var previous: Array = []
var shake := Vector2.ZERO
var projectile_observations:Array=[]

func advance_flash(advance_fx: bool = true) -> Array:
	var flash_snapshot:=flash.duplicate()
	for i in range(2):flash[i]=maxi(0,int(flash[i])-1)
	if advance_fx:advance_effects(1) # 保留既有离线消费者接口；主游戏显式传false。
	return flash_snapshot

func advance_effects(ticks: int) -> void:
	shake_ticks=maxi(0,shake_ticks-maxi(0,ticks))
	for p in particles:p.age=int(p.age)+maxi(0,ticks)

func reset_match() -> void:
	for p in particles:p.node.queue_free()
	particles.clear();projectile_observations.clear();previous.clear()
	flash=[0,0];shake_ticks=0;last_tick=-1;shake=Vector2.ZERO

func _ready() -> void:
	z_index=5
	clips=UfeContentDatabase.read_json("res://content/presentation/impact_effects.json")
	# 旧命中名册优先；角色特效名册提供专属命中与终结的回退查询。
	clips.merge(UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json"),false)

func spawn(id: String, x: int, height: int, tint: Array = [1,1,1,1], facing: int = 1) -> void:
	if not clips.has(id):return
	var s:=Sprite2D.new()
	var clip: Dictionary=clips[id]
	s.scale=UfeEffectGeometry.scale_for(clip)
	s.texture=load(clip.texture)
	s.region_enabled=true
	s.centered=false
	UfeEffectGeometry.apply_anchor(s,clip,clip.rects[0],facing)
	# 新普通火花使用生成的原色；原有专属/防御的材质路径保持。
	if not bool(clip.get("ordinary_melee_only",false)) or bool(clip.get("color_parameter",true)):
		var mat:=ShaderMaterial.new()
		mat.shader=preload("res://presentation/effect_palette.gdshader")
		mat.set_shader_parameter("palette_tint",Color(float(tint[0]),float(tint[1]),float(tint[2]),float(tint[3])))
		s.material=mat
	add_child(s)
	particles.append({"id":id,"node":s,"clip":clip,"age":0,"x":x,"height":height})

func impact_id(sim:UfeMatchDirector,event:Dictionary) -> String:
	var fb:Dictionary=event.feedback
	var fallback:=str(fb.spark)
	var mapping:Dictionary=fb.get("projectile_impacts",{})
	if mapping.is_empty() or not bool(event.get("projectile",false)):
		var selected:=UfeImpactFeedbackPolicy.impact_id(event,fallback)
		return selected if clips.has(selected) else fallback
	var point:=Vector2i(int(event.x),int(event.height))
	var best_distance:float=INF
	var best_effect:String=""
	# 上次观察保留原弹体引用，命中后即使从模拟数组移除，仍能读到真实最终碰撞位置。
	for p in projectile_observations+sim.projectiles:
		if int(p.owner)!=int(event.player) or str(p.move)!=str(event.move) or not mapping.has(str(p.effect)):continue
		if not bool(p.get("connected",false)):continue
		var box:=UfeMatchDirector.projectile_box(p)
		if not box.grow(1).has_point(point):continue
		var distance:float=Vector2(box.get_center()).distance_squared_to(Vector2(point))
		if distance<best_distance:
			best_distance=distance
			best_effect=str(p.effect)
	if not best_effect.is_empty():return str(mapping[best_effect])
	# 出生同tick即接触的弹体没有上一帧引用；只读本tick实际发射帧的显示字段。
	var f:=sim.fighters[int(event.player)]
	var move:Dictionary=f.definition.moves.get(str(event.move),{})
	var shots:Array=[]
	if f.move_id==str(event.move) and not move.get("frames",[]).is_empty():
		shots=move.frames[clampi(f.move_tick-1,0,move.frames.size()-1)].get("shots",[]).duplicate()
	if move.has("projectile"):shots.append(move.projectile)
	for shot in shots:
		var effect:=str(shot.get("effect",""))
		if not mapping.has(effect):continue
		var at:Array=shot.get("spawn",[45,75])
		var x:int=f.x+f.facing*(int(at[0])+int(shot.get("speed",8)))
		var y:int=f.height+int(at[1])+int(shot.get("vy",0))
		var distance:float=Vector2(x,y).distance_squared_to(Vector2(point))
		if distance<best_distance:
			best_distance=distance
			best_effect=effect
	return str(mapping.get(best_effect,fallback))

func finish(sim:UfeMatchDirector,event:Dictionary,fb:Dictionary,trigger:String) -> void:
	if fb.has("finish_effect"):
		if str(fb.get("finish_trigger","hit"))!=trigger:return
		var key:=str(fb.finish_effect)
		if not key.is_empty():spawn(key,int(event.x),int(event.height),[1,1,1,1],sim.fighters[int(event.player)].facing)
	elif trigger=="hit" or int(sim.fighters[1-int(event.player)].stats.hp)==0:
		spawn("explosion",int(event.x),int(event.height) if trigger=="hit" else 40)

func sync(sim: UfeMatchDirector, camera_x: int, camera_y: int) -> void:
	if last_tick!=sim.tick:
		last_tick=sim.tick
		for e in sim.events:
			var kind:=str(e.kind)
			if kind in ["hit","block"] and e.has("feedback"):
				var fb: Dictionary=e.feedback
				var tint:Array=fb.get("block_color",fb.get("color",[1,1,1,1])) if kind=="block" else fb.get("color",[1,1,1,1])
				spawn(str(fb.block_spark) if kind=="block" else impact_id(sim,e),int(e.x),int(e.height),tint,int(e.get("effect_facing",sim.fighters[int(e.player)].facing)))
				if kind=="hit":
					flash[1-int(e.player)]=clampi(int(fb.get("flash",2)),1,2)
					shake_ticks=maxi(shake_ticks,int(fb.get("shake",0)))
					if str(e.get("move",""))=="special3" or int(sim.fighters[1-int(e.player)].stats.hp)==0:
						finish(sim,e,fb,"hit")
			elif kind=="weapon_return" and e.has("effect"):
				spawn(str(e.effect),int(e.x),int(e.height),[1,1,1,1],int(e.get("effect_facing",1)))
			elif kind=="throw_slam":
				spawn("dust",int(e.x),0)
				shake_ticks=4
				var move:Dictionary=sim.fighters[int(e.player)].definition.moves.get(str(e.get("move","")),{})
				var fb:Dictionary=move.get("feedback",{})
				if not str(fb.get("slam_spark","")).is_empty():spawn(str(fb.slam_spark),int(e.x),int(e.height),fb.get("color",[1,1,1,1]),sim.fighters[int(e.player)].facing)
				if fb.has("finish_effect") or int(sim.fighters[1-int(e.player)].stats.hp)==0:finish(sim,e,fb,"throw_slam")
			elif kind in ["projectile_block","projectile_absorb","projectile_reflect"]:
				var f:=sim.fighters[int(e.player)]
				spawn(str(e.get("guard_effect","impact_guard")),int(e.get("x",f.x+f.facing*35)),int(e.get("height",f.height+80)),[1,1,1,1],int(e.get("effect_facing",1)))
		for i in range(2):
			var f:=sim.fighters[i]
			if previous.size()==2:
				var old: Dictionary=previous[i]
				if (int(old.height)>0 and f.height==0) or (f.state=="down" and old.state!="down"):
					spawn("dust",f.x,0)
					if f.state in ["down","bounce"]:shake_ticks=maxi(shake_ticks,3)
		previous=[]
		for f in sim.fighters:previous.append({"height":f.height,"state":f.state})
		for expired in PROJECTILE_EXPIRY.collect(projectile_observations,sim.projectiles,clips,sim.finished):
			spawn(str(expired.id),int(expired.x),int(expired.height),[1,1,1,1],int(expired.facing))
		projectile_observations=sim.projectiles.duplicate()
	for p in particles:
		var clip: Dictionary=p.clip
		if int(p.age)>=UfeEffectTimeline.length(clip):
			p.node.queue_free()
			continue
		var index:=UfeEffectTimeline.phase(clip,int(p.age),false)
		var r: Array=clip.rects[index]
		p.node.region_rect=Rect2(r[0],r[1],r[2],r[3])
		UfeEffectGeometry.apply_anchor(p.node,clip,r,-1 if p.node.flip_h else 1)
		p.node.position=Vector2(int(p.x)-camera_x+320,304-int(p.height)+camera_y)
	particles=particles.filter(func(p):return int(p.age)<UfeEffectTimeline.length(p.clip))
	shake=Vector2((2 if shake_ticks%2==0 else -2),1 if shake_ticks%2==0 else -1) if shake_ticks>0 else Vector2.ZERO
