class_name UfeComputerController
extends RefCounted
## 只观察模拟并产出设备同款输入。随机状态、反应记忆和指令队列全部属于input层。
const LEVELS={"easy":{"delay":22,"guard":30,"combo":40},"normal":{"delay":12,"guard":65,"combo":75},"hard":{"delay":6,"guard":90,"combo":95}}
var difficulty: String
var player: int
var seed_value: int
var rng: int
var observations: Array=[]
var queue: Array=[]
var last_tick: int=-1
var cached:=UfeInputFrame.make()
var next_decision: int=0
var last_threat: String=""
var defend: bool=false
var travel_x: int=0
var actions: Dictionary={}
var combo_key: String=""
var complete_combo: bool=false
var observed_move: String=""
var observed_age: int=-1
var threat_serial: int=0
var combo_move: String=""
var combo_age: int=-1

func _init(match_seed: int=20261022,level: String="normal",index: int=1) -> void:
	seed_value=match_seed;difficulty=level if LEVELS.has(level) else "normal";player=index
	rng=(match_seed+index*104729)&0x7fffffff
func roll() -> int:
	rng=(rng*1103515245+12345)&0x7fffffff
	return (rng>>8)%100
func note(action: String) -> void:actions[action]=int(actions.get(action,0))+1
func emit(x: int=0,y: int=0,buttons: int=0) -> UfeInputFrame:return UfeInputFrame.make(x,y,buttons)
func tap(buttons: int,x: int=0,y: int=0) -> UfeInputFrame:
	# 释放键也进入输入流，保证每次按下都有边沿，连段不靠直接设置move_id。
	queue.append([0,0,0])
	return emit(x,y,buttons)
func motion_input(motion: Array,button: int) -> void:
	for i in range(motion.size()):
		var d:=int(motion[i]);var x: int=-1 if d in [1,4,7] else 1 if d in [3,6,9] else 0
		var y: int=-1 if d<=3 else 1 if d>=7 else 0
		queue.append([x,y,button if i==motion.size()-1 else 0])
	queue.append([0,0,0])
func sample(sim: UfeMatchDirector) -> UfeInputFrame:
	if sim.tick==last_tick:return cached
	last_tick=sim.tick
	var other:=sim.fighters[1-player]
	var attack: Dictionary=other.definition.moves.get(other.move_id,{})
	var incoming:=sim.projectiles.any(func(p):return int(p.owner)!=player)
	if other.move_id!=observed_move or other.move_tick<observed_age:threat_serial+=1
	observed_move=other.move_id;observed_age=other.move_tick
	observations.append({"x":other.x,"height":other.height,"move":other.move_id,"move_start":threat_serial,"level":attack.get("level","mid"),"threat":not attack.is_empty() or incoming})
	var delay: int=LEVELS[difficulty].delay
	if observations.size()<=delay:cached=emit();return cached
	var seen: Dictionary=observations.pop_front()
	cached=decide(sim,seen)
	return cached
func decide(sim: UfeMatchDirector,seen: Dictionary) -> UfeInputFrame:
	var f:=sim.fighters[player]
	var direction:=signi(int(seen.x)-f.x)
	if direction==0:direction=f.facing
	var gap:=absi(int(seen.x)-f.x)
	if sim.finished:return emit()
	# 延迟后的威胁每次只掷一次防御概率，不能逐tick反复抽签变成必防。
	var threat:="%s:%d"%[seen.move,int(seen.move_start)] if seen.threat else ""
	if threat!=last_threat:
		last_threat=threat;defend=bool(seen.threat) and roll()<int(LEVELS[difficulty].guard)
	var can_guard:=f.height==0 and f.move_id.is_empty() and f.state in ["idle","walk","crouch","crouch_start","crouch_rise","guard","crouch_guard","blockstun","crouch_blockstun"]
	if defend and can_guard and (gap<240 or not sim.projectiles.is_empty()):
		queue.clear();note("crouch_guard" if seen.level=="low" else "stand_guard")
		return emit(-f.facing,-1 if seen.level=="low" else 0,UfeInputFrame.GUARD)
	if not queue.is_empty():
		var q: Array=queue.pop_front();return emit(int(q[0])*f.facing,int(q[1]),int(q[2]))
	if f.state=="wake":note("wake_counter");return tap(UfeInputFrame.LIGHT if roll()<50 else UfeInputFrame.HEAVY)
	if f.state in ["down","hit","launch","bounce","thrown","stun","guardbreak"]:return emit()
	if not f.move_id.is_empty():
		if f.move_id!=combo_move or f.move_tick<combo_age:complete_combo=roll()<int(LEVELS[difficulty].combo)
		combo_move=f.move_id;combo_age=f.move_tick
		if f.combat.confirmed and complete_combo:
			if f.move_id=="launcher" and int(f.motion.chase_window)>0:note("chase");return tap(UfeInputFrame.JUMP,f.facing,1)
			var cancels: Array=f.frame().cancel
			if "light2" in cancels or "light3" in cancels or "chase_light2" in cancels:note("combo");return tap(UfeInputFrame.LIGHT)
			if "chase_end" in cancels:note("air_end");return tap(UfeInputFrame.HEAVY)
		return emit()
	combo_move="";combo_age=-1
	if f.height>0:
		if gap<150 and absi(f.height-int(seen.height))<90:
			note("air_attack");return tap(UfeInputFrame.LIGHT if f.motion.jump_kind=="chase" else UfeInputFrame.HEAVY)
		return emit(direction)
	if f.state=="land" and int(f.motion.land_window)>0:note("bounce_followup");return tap(UfeInputFrame.HEAVY,0,-1)
	if f.state in ["charge_start","charge"] and gap>230 and int(f.stats.energy)<1100:return emit(0,0,UfeInputFrame.CHARGE)
	if sim.tick<next_decision:return emit(travel_x)
	travel_x=0
	next_decision=sim.tick+maxi(4,int(LEVELS[difficulty].delay)/2)
	if UfeBattleTransform.can_transform(f) and f.state in UfeBattleFormCatalog.GROUND_STATES and roll()<35:
		motion_input([2,5,2],UfeInputFrame.SPECIAL)
		note("transform")
		var transform_input: Array=queue.pop_front()
		return emit(int(transform_input[0])*f.facing,int(transform_input[1]),int(transform_input[2]))
	if int(seen.height)>35 and gap<180:note("anti_air");return tap(UfeInputFrame.HEAVY,f.facing)
	if int(f.stats.energy)>=1000 and gap<460 and roll()<45:note("super");return tap(UfeInputFrame.SPECIAL)
	if gap<82 and roll()<30:note("throw");return tap(UfeInputFrame.THROW)
	if gap>260 and int(f.stats.energy)<1000 and roll()<35:note("charge");next_decision=sim.tick+42;return emit(0,0,UfeInputFrame.CHARGE)
	if gap<330 and roll()<22:
		var specials: Array=[[ [2,3,6],UfeInputFrame.LIGHT ],[ [6,2,3],UfeInputFrame.HEAVY ],[ [2,1,4],UfeInputFrame.RANGED ],[ [2,5,2],UfeInputFrame.CRUSH ]]
		var chosen: Array=specials[roll()%specials.size()]
		motion_input(chosen[0],chosen[1]);note("special")
		var q: Array=queue.pop_front();return emit(int(q[0])*f.facing,int(q[1]),int(q[2]))
	if gap<=95:
		if roll()<12:note("retreat");next_decision=sim.tick+12;travel_x=-direction;return emit(travel_x)
		note("attack")
		var choice:=roll()
		return tap(UfeInputFrame.LIGHT if choice<45 else UfeInputFrame.HEAVY if choice<85 else UfeInputFrame.CRUSH,0,-1 if choice>=85 else 0)
	if gap<430 and roll()<18:note("projectile");return tap(UfeInputFrame.RANGED)
	note("approach");travel_x=direction;return emit(travel_x)
