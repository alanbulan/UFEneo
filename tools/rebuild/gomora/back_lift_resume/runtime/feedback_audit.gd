extends SceneTree
## 实际生产反馈模块的只读呈现审计；不代替主游戏截图或听感验收。
const Factory=preload("res://tools/rebuild/gomora/back_lift_resume/runtime/factory.gd")
class AuditedFeedback extends UfeCombatFeedback:
	var calls: Array=[]
	var audit_tick: int=0
	var event_kinds: Array=[]
	func spawn(id: String,x: int,height: int,tint: Array=[1,1,1,1],facing: int=1) -> void:
		var before: int=particles.size()
		super.spawn(id,x,height,tint,facing)
		calls.append({"id":id,"tick":audit_tick,"events":event_kinds.duplicate(),"x":x,"height":height,"node_created":particles.size()==before+1})
var errors: Array=[]
func _initialize() -> void:call_deferred("run")
func need(ok: bool,label: String) -> void:
	if not ok:errors.append(label)
func canonical(v: Variant) -> String:return JSON.stringify(v,"",true,true)
func clean_events(events: Array) -> Array:
	var clean:=events.duplicate(true)
	for e in clean:
		if e.has("feedback"):
			e.feedback.erase("finish_effect");e.feedback.erase("finish_trigger")
			if str(e.feedback.get("spark",""))=="impact_light":e.feedback.spark="impact_hit"
	return clean
func run() -> void:
	var contract: String="";var baseline: String="";var traces: String="";var out: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contract="):contract=arg.trim_prefix("--contract=")
		elif arg.begins_with("--baseline="):baseline=arg.trim_prefix("--baseline=")
		elif arg.begins_with("--traces="):traces=arg.trim_prefix("--traces=")
		elif arg.begins_with("--output="):out=arg.trim_prefix("--output=")
	var cfg:=Factory.read_sealed(contract);var old:=Factory.read_sealed(baseline)
	var expected_feedback: Dictionary=old.move.feedback.duplicate(true)
	expected_feedback.merge({"spark":"impact_light","finish_effect":"explosion","finish_trigger":"throw_slam"},true)
	need(canonical(cfg.move.feedback)==canonical(expected_feedback),"only authorized three display fields changed")
	var rows: Array=[]
	for owner in [0,1]:
		for kind in ["rear_vertical_hit","rear_vertical_tech1","rear_vertical_tech2","rear_vertical_tech3","rear_vertical_tech4","whiff"]:
			var source: String=traces.path_join("owner%d-%s/search-result.json"%[owner,kind])
			var data: Dictionary=UfeContentDatabase.read_json(source)
			need(data.rows.size()==1,"single tape")
			var row: Dictionary=data.rows[0]
			var sim:=Factory.make_match(cfg,owner,kind);var previous:=Factory.make_match(old,owner,kind)
			need(sim.content_fingerprint!=previous.content_fingerprint,"不同显示合同应有不同内容指纹")
			var fx:=AuditedFeedback.new();root.add_child(fx)
			var old_fx:=AuditedFeedback.new();root.add_child(old_fx)
			var captures: Array=[];var slams: Array=[];var techs: Array=[];var whiffs: Array=[]
			for index in range(row.original_inputs.size()):
				var pair: Array=row.original_inputs[index]
				sim.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
				previous.step([UfeInputFrame.unpack(pair[0]),UfeInputFrame.unpack(pair[1])])
				need(sim.state_hash()==str(row.state_hashes[index]),"new tape hash/%s/%d"%[kind,index])
				for i in [0,1]:need(canonical(sim.fighters[i].snapshot())==canonical(previous.fighters[i].snapshot()),"fighter snapshot/%s/%d"%[kind,index])
				for key in ["tick","remaining","hitstop","finished","projectiles"]:need(canonical(sim.get(key))==canonical(previous.get(key)),"match/%s/%s/%d"%[kind,key,index])
				need(canonical(clean_events(sim.events))==canonical(clean_events(previous.events)),"events except display fields")
				fx.audit_tick=sim.tick;old_fx.audit_tick=previous.tick
				fx.event_kinds=sim.events.map(func(e):return str(e.kind));old_fx.event_kinds=previous.events.map(func(e):return str(e.kind))
				fx.sync(sim,0,0);old_fx.sync(previous,0,0)
				need(fx.flash==old_fx.flash and fx.shake_ticks==old_fx.shake_ticks,"flash/shake counters unchanged")
				# 重复同tick sync不得重复发射，符合主视图可能多次刷新的行为。
				var count:=fx.calls.size();fx.sync(sim,0,0);need(count==fx.calls.size(),"same tick FX dedup")
				for e in sim.events:
					if e.kind=="hit" and e.get("move","")=="special3":captures.append(sim.tick)
					if e.kind=="throw_slam":slams.append(sim.tick)
					if e.kind=="throw_tech":techs.append(sim.tick)
					if e.kind=="throw_whiff":whiffs.append(sim.tick)
				fx.advance_effects(1);old_fx.advance_effects(1);fx.advance_flash(false);old_fx.advance_flash(false)
			var explosions: Array=fx.calls.filter(func(c):return c.id=="explosion")
			need(explosions.size()==slams.size(),"仅每次摔落一次explosion")
			for e in explosions:need(e.tick in slams and "throw_slam" in e.events and e.node_created,"真实摔落生成爆炸节点")
			for tick in captures:
				need(not explosions.any(func(c):return c.tick==tick),"捕获无爆炸")
				var new_impact: Array=fx.calls.filter(func(c):return c.tick==tick and c.id=="impact_light")
				need(new_impact.size()==1 and bool(new_impact[0].node_created),"捕获必须真实生成impact_light局部节点")
			if not techs.is_empty() or not whiffs.is_empty():need(explosions.is_empty(),"拆投/落空无爆炸")
			rows.append({"owner":owner,"case":kind,"source":source,"ticks":row.original_inputs.size(),"capture_ticks":captures,"slam_ticks":slams,"tech_ticks":techs,"whiff_ticks":whiffs,"capture_spark":"impact_light","capture_spark_registered":fx.clips.has("impact_light"),"new_spawn_calls":fx.calls,"old_spawn_calls":old_fx.calls,"old_fingerprint":previous.content_fingerprint,"new_fingerprint":sim.content_fingerprint,"damage":1000-int(sim.fighters[1-owner].stats.hp)})
			fx.free();old_fx.free()
	assert(not FileAccess.file_exists(out));var file:=FileAccess.open(out,FileAccess.WRITE);assert(file!=null)
	file.store_string(JSON.stringify({"errors":errors,"rows":rows,"uses_production_combat_feedback":true,"not_main_visual_evidence":true,"same_gameplay_snapshots_except_display_event_fields":true,"claims_identical_content_hash":false,"installed":false}));file.close()
	quit(0 if errors.is_empty() else 1)
