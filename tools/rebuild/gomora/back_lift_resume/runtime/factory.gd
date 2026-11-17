extends RefCounted
## 只在新建对局前装配候选；不写数据库、正式三级或已运行模拟。
static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary=UfeContentDatabase.read_json(path)
	assert(str(cfg.schema)=="ufeneo.gomora.back-lift-main-candidate.v1")
	assert(bool(cfg.root_runtime_ready) and not bool(cfg.installed) and str(cfg.opponent)=="ultraman")
	assert(not cfg.bound_resources.is_empty())
	for resource in cfg.bound_resources:
		assert(FileAccess.get_sha256(str(resource.path))==str(resource.sha256),"候选资源SHA已变")
	assert(str(cfg.move.id)=="special3" and str(cfg.move.kind)=="throw" and UfeMoveData.validate(cfg.move))
	var impacts: Array=[]
	for tick in range(cfg.move.frames.size()):
		if bool(cfg.move.frames[tick].get("target",{}).get("impact",false)):impacts.append(tick)
	assert(impacts.size()==1,"候选必须只声明一个落地impact")
	cfg._impact_tick=int(impacts[0])
	cfg._contract_sha256=FileAccess.get_sha256(path)
	return cfg

static func make_match(cfg: Dictionary,owner: int,kind: String) -> UfeMatchDirector:
	assert(owner in [0,1])
	var actor:=UfeContentDatabase.fighter("gomora",false)
	var victim:=UfeContentDatabase.fighter("ultraseven" if kind=="unsupported" else str(cfg.opponent),false)
	actor.moves=actor.moves.duplicate(true)
	actor.moves.special3=cfg.move.duplicate(true)
	victim.state_frames=victim.state_frames.duplicate(true)
	if kind!="unsupported":
		for pose in cfg.receiver_states:victim.state_frames[pose]=cfg.receiver_states[pose].duplicate(true)
	var sim:=UfeMatchDirector.new(actor if owner==0 else victim,victim if owner==0 else actor,load("res://content/rules/neo.tres"),UfeContentDatabase.states(),{})
	return sim
