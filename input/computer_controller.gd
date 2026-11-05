class_name UfeComputerController
extends RefCounted
## 只观察模拟并产出设备同款输入。随机状态、反应记忆和指令队列全部属于input层。
const LEVELS={"easy":{"delay":22,"guard":30,"combo":40,"recover":35,"counter":20,"burst":10},"normal":{"delay":12,"guard":65,"combo":75,"recover":65,"counter":45,"burst":20},"hard":{"delay":6,"guard":90,"combo":95,"recover":90,"counter":70,"burst":35}}
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
var recovery_age: int=-1
var recovery_decided: bool=false
var recovery_allowed: bool=false
var counter_age: int=-1
var counter_state: String=""
var counter_decided: bool=false
var counter_allowed: bool=false
var burst_decided: bool=false
var burst_allowed: bool=false
var burst_next_tick: int=0

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
	var escape:=burst_input(f,sim.tick)
	if escape!=null:return escape
	var counter:=guard_counter_input(f)
	if counter!=null:return counter
	if f.state in ["blockstun","crouch_blockstun"] and f.move_id.is_empty():
		# 等待/放弃防反时不能让旧指令或普通攻击策略绕过概率与反应窗。
		queue.clear()
		return emit(0,-1 if f.state=="crouch_blockstun" else 0,UfeInputFrame.GUARD)
	# 受身使用已有GUARD规则，不直接改状态或无敌。每次击飞只掷一次，
	# 上升期及难度反应窗内不提前输入；hitstop中保持已作出的选择。
	if f.state=="launch":
		queue.clear()
		if f.state_tick<recovery_age:recovery_decided=false;recovery_allowed=false
		recovery_age=f.state_tick
		if f.vy>=0 or f.state_tick<maxi(13,int(LEVELS[difficulty].delay)):return emit()
		if not recovery_decided:
			recovery_decided=true
			recovery_allowed=roll()<int(LEVELS[difficulty].recover)
			if recovery_allowed:note("air_recovery")
		return emit(0,0,UfeInputFrame.GUARD if recovery_allowed else 0)
	recovery_age=-1;recovery_decided=false;recovery_allowed=false
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

func guard_counter_input(f: UfeFighter) -> UfeInputFrame:
	# 仅在真实格挡硬直内反击，不把普通站防当作已经挡住攻击。
	if f.state not in ["blockstun","crouch_blockstun"] or not f.move_id.is_empty():
		counter_age=-1;counter_state="";counter_decided=false;counter_allowed=false
		return null
	if f.state!=counter_state or f.state_tick<counter_age:
		counter_decided=false;counter_allowed=false
	counter_state=f.state;counter_age=f.state_tick
	if f.state_tick<maxi(3,int(LEVELS[difficulty].delay)/2):return null
	if not counter_decided:
		counter_decided=true
		var move: Dictionary=f.definition.moves.get("guard_counter",{})
		# 以本人现装指令和费用为准，不能给缺动作或不支持蹲防反击者补造能力。
		var available:=f.definition.command_table.any(func(entry):return str(entry.move)=="guard_counter" and (f.state in entry.states or "*" in entry.states) and int(entry.buttons)==UfeInputFrame.HEAVY and entry.directions.any(func(d):return int(d) in [0,6]) and entry.motion.is_empty() and int(f.stats.energy)>=int(entry.get("min_energy",0)))
		if move.is_empty() or not available or int(f.stats.energy)<int(move.get("energy_cost",1000)):return null
		counter_allowed=roll()<int(LEVELS[difficulty].counter)
		if counter_allowed:note("guard_counter")
	if not counter_allowed:return null
	queue.clear()
	return emit(f.facing,0,UfeInputFrame.GUARD|UfeInputFrame.HEAVY)

func burst_input(f: UfeFighter, tick: int) -> UfeInputFrame:
	# 保守使用昂贵脱离：格挡另有一格防反；连续受击不逐段重掷。
	if f.state not in ["hit","launch"]:
		burst_decided=false;burst_allowed=false
		return null
	# 释放旧键后也重新核免费窗口，顶点转下降时放弃付费和弦。
	if f.state=="launch" and f.vy<0 and f.state_tick>=13:
		burst_allowed=false
		return null
	if burst_decided:
		return emit(0,0,UfeInputFrame.GUARD|UfeInputFrame.CHARGE) if burst_allowed else null
	if tick<burst_next_tick or f.state_tick<int(LEVELS[difficulty].delay):return null
	if int(f.stats.hp)*2>f.base_definition.max_health or int(f.stats.hp)<=0:return null
	var move: Dictionary=f.definition.moves.get("burst",{})
	var mask:=UfeInputFrame.GUARD|UfeInputFrame.CHARGE
	var available:=f.definition.command_table.any(func(entry):return str(entry.move)=="burst" and (f.state in entry.states or "*" in entry.states) and int(entry.buttons)==mask and entry.directions.any(func(d):return int(d) in [0,5]) and entry.motion.is_empty() and int(f.stats.energy)>=int(entry.get("min_energy",0)))
	if move.is_empty() or not available or int(f.stats.energy)<int(move.get("energy_cost",2000)):return null
	burst_decided=true;burst_next_tick=tick+300
	burst_allowed=roll()<int(LEVELS[difficulty].burst)
	if not burst_allowed:return null
	note("burst");queue.clear()
	# 先释放旧按键一tick，再同时按GUARD+CHARGE，满足真实和弦边沿窗口。
	return emit()
