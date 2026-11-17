extends RefCounted
@warning_ignore_start("integer_division")
static func read_sealed(path: String) -> Dictionary:
	var cfg: Dictionary=UfeContentDatabase.read_json(path)
	assert(cfg.schema=="ufeneo.hud_framing.v1")
	for r in cfg.bound_resources:assert(FileAccess.get_sha256(r.path)==r.sha256,"冻结资源已变化")
	cfg["contract_sha256"]=FileAccess.get_sha256(path)
	return cfg
static func make_match(cfg: Dictionary,direction: int) -> UfeMatchDirector:
	var sim:=UfeBattleFormCatalog.match_for(str(cfg.fighter),str(cfg.opponent),false)
	assert(sim.tick==0)
	sim.fighters[0].x=640-direction*int(cfg.gap)/2
	sim.fighters[1].x=640+direction*int(cfg.gap)/2
	for i in range(2):
		sim.fighters[i].facing=direction if i==0 else -direction
		sim.fighters[i].stats.energy=int(cfg.get("initial_energy",[3000,3000])[i])
		sim.fighters[i].stats.hp=int(cfg.initial_hp[i])
	return sim
@warning_ignore_restore("integer_division")
