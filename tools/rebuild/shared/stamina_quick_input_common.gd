extends RefCounted
## 真实物理键事件，经正式InputRouter取得InputFrame；不直接指定招式。
static var held_keys: Array = []
static var definitions: Dictionary = {}
static var state_registry: Dictionary = {}
const X := [0,-1,0,1,-1,0,1,-1,0,1]
const Y := [0,-1,-1,-1,0,0,0,1,1,1]

static func physical_key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode=code;event.physical_keycode=code;event.pressed=pressed
	event.ctrl_pressed=Input.is_key_pressed(KEY_CTRL)
	event.alt_pressed=Input.is_key_pressed(KEY_ALT)
	event.shift_pressed=Input.is_key_pressed(KEY_SHIFT)
	event.meta_pressed=Input.is_key_pressed(KEY_META)
	Input.parse_input_event(event)

static func set_keys(keys: Array) -> void:
	for code in held_keys:
		if not keys.has(code):physical_key(int(code),false)
	for code in keys:
		if not held_keys.has(code):physical_key(int(code),true)
	held_keys=keys.duplicate()
	Input.flush_buffered_events()

static func release_all() -> void:
	set_keys([])

static func keys_for(player: int, direction: int, facing: int, buttons: int) -> Array:
	var result: Array=[]
	var horizontal := int(X[direction])*facing
	var vertical := int(Y[direction])
	if horizontal!=0:result.append(UfeInputRouter.KEYS[player][0 if horizontal<0 else 1])
	if vertical!=0:result.append(UfeInputRouter.KEYS[player][2 if vertical>0 else 3])
	for index in range(4,UfeInputRouter.ACTIONS.size()):
		if buttons & (1 << (index-4)):
			var code: int=int(UfeInputRouter.KEYS[player][index])
			if not result.has(code):result.append(code)
	return result

static func pair(player: int, direction: int, facing: int, buttons: int) -> Array:
	set_keys(keys_for(player,direction,facing,buttons))
	return [UfeInputRouter.poll(0),UfeInputRouter.poll(1)]

static func fixture(identity: String, facing: int=1, player: int=0, stamina: int=1000, energy: int=3000, half_health: bool=false) -> UfeMatchDirector:
	var other := "zetton" if identity!="zetton" else "ultraseven"
	for id in [identity,other]:
		if not definitions.has(id):definitions[id]=UfeBattleFormCatalog.prepare(id,true)
	if state_registry.is_empty():state_registry=UfeContentDatabase.states()
	var first: Dictionary=definitions[identity if player==0 else other]
	var second: Dictionary=definitions[other if player==0 else identity]
	var forms: Dictionary={}
	forms[first.definition.id]=first.form;forms[second.definition.id]=second.form
	var sim := UfeMatchDirector.new(first.definition,second.definition,load("res://content/rules/neo.tres"),state_registry,forms)
	var actor := sim.fighters[player]
	actor.x=470 if facing>0 else 880
	sim.fighters[1-player].x=880 if facing>0 else 470
	actor.facing=facing;sim.fighters[1-player].facing=-facing
	actor.stats.stamina=stamina;actor.stats.energy=energy
	if half_health:actor.stats.hp=actor.definition.max_health/2
	return sim

static func observation(sim: UfeMatchDirector, inputs: Array, before: String) -> Dictionary:
	var pair: Array=[]
	for actor in sim.fighters:
		pair.append({"fighter":actor.definition.id,"state":actor.state,"state_tick":actor.state_tick,"move":actor.move_id,"move_tick":actor.move_tick,"x":actor.x,"height":actor.height,"facing":actor.facing,"stats":actor.stats.duplicate(true),"buffer":str(actor.combat.buffer),"delay":int(actor.combat.get("stamina_delay",0)),"invulnerable":int(actor.combat.invulnerable)})
	return {"inputs":[inputs[0].pack(),inputs[1].pack()],"pre_hash":before,"post_hash":sim.state_hash(),"events":sim.events.duplicate(true),"pair":pair}

static func default_configuration() -> void:
	release_all()
	UfeInputRouter.configure_values({"key_bindings":{},"joy_bindings":{}})
