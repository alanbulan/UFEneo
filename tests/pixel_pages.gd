extends SceneTree
func _initialize() -> void:call_deferred("run")
func require(value: bool,message: String) -> void:
	if not value:push_error(message);quit(1)
func run() -> void:
	var model:=UfeRosterModel.new()
	var plan: Dictionary=UfeContentDatabase.read_json("res://content/roster/selection.json")
	require(model.entries==plan.entries,"网格必须只消费正式名单")
	var ids:={};var names:={}
	for entry in model.entries:
		require(not ids.has(entry.id) and not names.has(entry.name),"选人身份/名字不能重复")
		ids[entry.id]=true;names[entry.name]=true
		require(not entry.forms.is_empty(),"每个身份必须声明可选形态")
		require(not entry.id in ["wiki_4bb5f20de07217","wiki_d0ac335d746e26","kei_fukuide"],"别名与剧情对象不能成为格子")
	for cat in ["ultra","kaiju","alien"]:
		model.filter(cat)
		require(not model.filtered.is_empty(),"三个分类必须独立可用")
		for entry in model.filtered:require(entry.selection_category==cat,"筛选分类错误")
	model.filter("all","showa","ultraman")
	for entry in model.filtered:require(entry.era=="showa" and "ultraman" in entry.series_ids,"年代作品交集错误")
	model.filter()
	var grid:=RosterGrid.new();root.add_child(grid);grid.size=Vector2(600,170);grid.bind(model)
	await process_frame
	require(grid.loaded_cells<=70,"列表只能创建可见行")
	grid.reveal(model.filtered.size()-1)
	await process_frame
	require(grid.first_row>0 and grid.loaded_cells<=70,"底部滚动应保持虚拟化")
	require(grid.selected_ids==["ultraman","zetton"],"公共滚动不能改变玩家选择")
	var sim:=UfeContentDatabase.match_for()
	var counts:={}
	for entry in sim.fighters[0].definition.command_table:
		var cat:=UfeCommandPages.category(entry);counts[cat]=int(counts.get(cat,0))+1
	for i in range(8):require(counts.has(i),"招式表分类不能为空 "+str(i))
	require(sim.fighters[0].definition.moves.ranged_forward.display_name=="八分光轮","初代6I不能显示模板名")
	require(sim.fighters[1].definition.moves.pulse.display_name=="脸部小火球","杰顿5I必须显示自己的招式名")
	var commands:=UfeCommandPages.new();root.add_child(commands);commands.set_fighter(sim.fighters[1].definition)
	require(commands.entries.any(func(e):return e.move=="special2") and commands.entries.any(func(e):return e.move=="special3"),"按能量选择的三档必杀必须分别展示实际数据")
	commands.show_page(7)
	var special_rows:=commands.rows.rows.get_children()
	var displayed_costs: Array=[]
	for row in special_rows:
		displayed_costs.append(row.get_child(1).get_child(1).text)
	for id in ["special","special2","special3"]:
		require(displayed_costs.has(UfeCommandPages.move_costs(sim.fighters[1].definition.moves[id])),"各必杀行应显示自身实际能量和体力费用 "+id)
	require(UfeCommandPages.move_costs({"energy_cost":1500,"stamina_cost":37})=="能量 1500点 · 体力 37","非整格费用不能四舍五入")
	require(UfeCommandPages.move_costs({})=="能量 0 · 体力 0","缺省费用为零")
	require(UfeCommandPages.move_title({"move":"air_throw","display_name":"空投"},{},false)=="待制作：空投","缺资源不能把任意招式误称半圈投技")
	var original_moves:=JSON.stringify(sim.fighters[1].definition.moves)
	commands.clips.erase("special2");commands.show_page(7)
	var unavailable_found:=false
	for row in commands.rows.rows.get_children():
		if row.get_child(1).get_child(0).text=="待制作："+str(sim.fighters[1].definition.moves.special2.display_name):
			unavailable_found=true
			require(row.get_child(1).get_child(1).text=="费用待实装核验" and row.get_child(2).text=="—","缺资源不宣称就绪费用与帧数")
	require(unavailable_found,"缺资源行保留本人招名")
	require(JSON.stringify(sim.fighters[1].definition.moves)==original_moves,"查看招式费用不修改模拟数据")
	commands.set_match_fighters(sim.fighters)
	require(commands.match_choices.visible and commands.match_buttons.size()==2,"对局招式表提供双方当前角色快捷入口")
	var before_hash:=sim.state_hash()
	commands.match_buttons[1].pressed.emit()
	require(commands.fighter_data.id==sim.fighters[1].definition.id and commands.title.text.contains("2P当前"),"2P按钮直达当前对手招式")
	commands.match_buttons[0].pressed.emit()
	require(commands.fighter_data.id==sim.fighters[0].definition.id and commands.title.text.contains("1P当前"),"1P按钮回到当前本人")
	require(sim.state_hash()==before_hash,"切换双方招式表不能改变战斗状态")
	var forms_sim:=UfeBattleFormCatalog.match_for("ex_gomora","ultraman-taro")
	forms_sim.fighters[1].form_id="super-taro"
	commands.set_match_fighters(forms_sim.fighters)
	require(commands.fighter_choice.fighter_id=="ex_gomora","EX当前身份不能回退为本体")
	commands.select_match_player(1)
	require(commands.fighter_choice.fighter_id==UfeFighterDisplay.resolved_id("ultraman-taro","super-taro"),"2P保留当前超级泰罗显示身份")
	commands.cycle_fighter(1)
	require(not commands.title.text.contains("P当前"),"自由翻名册不能误标当前玩家")
	commands.select_match_player(1)
	require(commands.fighter_data.id=="ultraman-taro","翻名册后仍可回到2P")
	commands.set_match_fighters(sim.fighters)
	commands.select_match_player(1)
	require(commands.fighter_data.id=="zetton","新对局重新绑定，不能残留旧玩家或形态")
	commands.set_match_fighters([])
	require(not commands.match_choices.visible,"非对局招式表隐藏当前玩家按钮")
	var commands_hud:=UfeBattleHUD.new();root.add_child(commands_hud)
	commands_hud.show_commands(sim.fighters[0].definition,sim.fighters)
	require(commands_hud.commands.visible and commands_hud.commands.match_choices.visible,"HUD对局入口绑定双方")
	commands_hud.commands.select_match_player(1)
	commands_hud.show_commands(sim.fighters[0].definition,sim.fighters)
	require(not commands_hud.commands.visible,"再次F2关闭招式表")
	commands_hud.show_commands(forms_sim.fighters[0].definition,forms_sim.fighters)
	require(commands_hud.commands.visible and commands_hud.commands.fighter_data.id=="ex_gomora","重新打开使用新对局当前定义")
	commands_hud.close_overlays();commands_hud.queue_free()
	var training:=UfeTrainingOverlay.new();root.add_child(training)
	sim._start(sim.fighters[0],"ranged_forward");training.update_match(sim)
	require(training.info[0].text.contains("八分光轮") and training.info[0].text.contains("起手%d"%int(sim.fighters[0].definition.moves.ranged_forward.startup)),"训练应显示当前招式完整帧数据")
	sim.fighters[0].clear_move();sim.fighters[0].enter("idle");training.update_match(sim)
	require(training.info[0].text.contains("待机") and training.info[0].text.contains("上一招 八分光轮"),"结束后应保留上一招，状态使用中文名称")
	var feedback:=UfeCombatFeedback.new();root.add_child(feedback)
	sim.events=[{"kind":"hit","player":0,"x":500,"height":80,"feedback":{"spark":"impact_light","block_spark":"impact_guard","flash":2}}]
	feedback.sync(sim,320,0)
	require(feedback.advance_flash()[1]==2,"首次呈现应闪白")
	for i in range(4):
		require(feedback.advance_flash()[1]==2,"同一模拟tick的呈现帧不能缩短闪白")
	sim.events=[]
	sim.tick+=1
	feedback.sync(sim,320,0)
	require(feedback.advance_flash()[1]==1,"闪白按模拟tick减少")
	sim.tick+=1
	feedback.sync(sim,320,0)
	require(feedback.advance_flash()[1]==0,"两tick后闪白结束")
	require(feedback.particles.is_empty(),"KO后命中火花也应播完，不能卡在失败动画上")
	var view:=UfeSideView.new();view.ending_tick=12
	var f:=sim.fighters[1];f.state="defeat";f.move_id="light1"
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")
	var clip:=view._animation(f,manifest)
	require(not clip.is_empty() and clip.key=="defeat","结束演出必须强制使用败方失败动画")
	view.free()
	print("页面目录筛选、虚拟网格、招式分页及真实呈现帧闪白逻辑验证完成")
	quit()
