class_name UfeProjectileHistory
extends RefCounted
## 以Dictionary身份追踪，只在模拟tick变化时采样；不向模拟弹体写字段。
var records:Array=[]
var match_ref:UfeMatchDirector
var last_tick:int=-1
const SAMPLE_TICKS:int=2
const POINT_LIMIT:int=4

func clear() -> void:
	records.clear()
	match_ref=null
	last_tick=-1

func sync(sim:UfeMatchDirector) -> void:
	if not is_same(match_ref,sim) or sim.tick<last_tick:
		clear()
		match_ref=sim
	if last_tick==sim.tick:return
	last_tick=sim.tick
	# 停止采样死亡或已命中的余焰，避免消失后残留或跨回合串尾。
	records=records.filter(func(r):return sim.projectiles.any(func(p):return is_same(p,r.projectile)) and not sim.finished)
	for p in sim.projectiles:
		if sim.finished or bool(p.get("beam",false)) or p.has("trail_points") or str(p.get("trail_effect","" )).is_empty():continue
		var row:Dictionary={}
		for r in records:
			if is_same(r.projectile,p):row=r;break
		if row.is_empty():
			row={"projectile":p,"points":[],"sample_tick":sim.tick-SAMPLE_TICKS,"owner":p.owner,"facing":p.facing}
			records.append(row)
		if row.owner!=p.owner or row.facing!=p.facing:
			row.points.clear()
			row.owner=p.owner
			row.facing=p.facing
		if bool(p.get("connected",false)):
			row.points.clear()
			continue
		if sim.tick-int(row.sample_tick)>=SAMPLE_TICKS:
			row.points.push_front([int(p.x),int(p.height)])
			row.sample_tick=sim.tick
			if row.points.size()>POINT_LIMIT+1:row.points.resize(POINT_LIMIT+1)

func points_for(projectile:Dictionary) -> Array:
	for r in records:
		if is_same(r.projectile,projectile):return r.points.slice(1,POINT_LIMIT+1)
	return []
