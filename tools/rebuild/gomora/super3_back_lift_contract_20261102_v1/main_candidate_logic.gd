extends SceneTree
## 纯逻辑夹具：直接摆状态只用于负向边界，不冒充主游戏真实输入/画面证据。
const Current = preload("res://core/combat/throw_current_capture.gd")
var errors: Array = []
var observations: Array = []
func _initialize() -> void:call_deferred("run")
func check(ok: bool, message: String) -> void:
	observations.append({"case":message,"passed":ok})
	if not ok:errors.append(message);push_error(message)
func fixture() -> UfeMatchDirector:
	var sim := UfeBattleFormCatalog.match_for("gomora","zetton",false)
	var a := sim.fighters[0]
	var b := sim.fighters[1]
	a.move_id="special3";a.move_tick=16;a.enter("attack")
	b.x=a.x-49;b.height=30;b.facing=-1;b.motion.jump_kind="vertical";b.enter("air")
	return sim
func run() -> void:
	var output := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--back-lift-logic-output="):output=arg.trim_prefix("--back-lift-logic-output=")
	if output.is_empty() or FileAccess.file_exists(output):push_error("新增逻辑输出路径必需");quit(2);return
	var sim := fixture()
	var a := sim.fighters[0]
	var b := sim.fighters[1]
	var move: Dictionary=a.definition.moves.special3
	check(UfeMoveData.validate(move),"当前显式候选MoveData合法")
	check(move.damage==490 and move.energy_cost==3000 and move.stamina_cost==50,"费用和唯一伤害数值")
	var impact_ticks: Array=[]
	for tick in range(move.frames.size()):
		if move.frames[tick].get("target",{}).get("impact",false):impact_ticks.append(tick)
	check(impact_ticks==[52],"仅raw52声明impact")
	check(Current.eligible(a,b,move),"有限上背/真实中躯干/首承重近邻正向逻辑夹具")
	var original_x: int=b.x
	var original_height: int=b.height
	var original_facing: int=b.facing
	var original_frame: Dictionary=b.frame().duplicate(true)
	var result: String=UfeHitResolver.apply(a,b,move,false,sim.rules)
	UfeThrowResolver.begin(sim,0,move)
	UfeThrowResolver.sync(sim)
	check(result=="hit" and b.state=="thrown","捕获建立既有thrown关系")
	for tick in range(16,20):
		a.move_tick=tick;UfeThrowResolver.sync(sim)
		check(b.x==original_x and b.height==original_height and b.facing==original_facing and b.frame()==original_frame,"起相保留当前完整相/位置/朝向 tick"+str(tick))
	a.move_tick=20;UfeThrowResolver.sync(sim)
	check(not b.motion.throw_current_capture.active and b.animation_key()=="gomora_back_lift_receiver","raw20退出只读当前相，改读本人专属受方完整相")
	check(absi(b.x-original_x)<=14 and absi(b.height-original_height)<=14,"首承重根变化仍在显式有限邻域")
	for kind in ["ground","wrong_state","far_x","far_height","head_only","feet_only","outside_window","invulnerable"]:
		var probe := fixture()
		var own := probe.fighters[0]
		var victim := probe.fighters[1]
		match kind:
			"ground":victim.height=0;victim.enter("idle")
			"wrong_state":victim.enter("launch")
			"far_x":victim.x+=30
			"far_height":victim.height+=30
			"head_only":own.definition.moves.special3.frames[16].hitboxes=[[0,190,8,8]]
			"feet_only":own.definition.moves.special3.frames[16].hitboxes=[[-40,30,8,8]]
			"outside_window":own.move_tick=15
			"invulnerable":victim.combat.invulnerable=1
		check(not UfeHitResolver.can_hit(own,victim),"负向拒绝 "+kind)
	var unsupported := UfeBattleFormCatalog.match_for("gomora","ultraseven",false)
	unsupported.fighters[0].move_id="special3";unsupported.fighters[0].move_tick=16
	unsupported.fighters[1].height=30;unsupported.fighters[1].enter("air")
	check(not UfeThrowResolver.can_capture(unsupported.fighters[1],unsupported.fighters[0].definition.moves.special3),"未装专属受方目标预检拒绝，不能当全名册开放")
	for field in ["target_ids","states","body_hurtbox_index","first_tick","entry_tick","max_entry_root_delta"]:
		var bad: Dictionary=move.duplicate(true)
		bad.throw_current_capture.erase(field)
		check(not UfeMoveData.validate(bad),"缺字段拒绝 "+field)
	for bounds in [[25,14],[-1,14],[14.5,14],[],"14"]:
		var bad: Dictionary=move.duplicate(true);bad.throw_current_capture.max_entry_root_delta=bounds
		check(not UfeMoveData.validate(bad),"越界/错误邻域拒绝 "+str(bounds))
	var missing: Dictionary=move.duplicate(true);missing.erase("throw_current_capture")
	check(not UfeMoveData.validate(missing),"没有显式参数的capture_current阶段不得启用")
	var legacy: Dictionary=UfeContentDatabase.fighter("gomora",false).moves.throw_forward
	check(UfeMoveData.validate(legacy),"无参数旧默认仍合法")
	check(not legacy.has("throw_current_capture"),"旧默认未被注入新配置")
	var file := FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify({"errors":errors,"observations":observations,"logic_fixtures_only":true,"visual_acceptance":false,"main_input_acceptance":false,"generated_videos":0}))
	file.close();quit(0 if errors.is_empty() else 1)
