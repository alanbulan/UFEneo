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
	var training:=UfeTrainingOverlay.new();root.add_child(training)
	sim._start(sim.fighters[0],"ranged_forward");training.update_match(sim)
	require(training.info[0].text.contains("八分光轮") and training.info[0].text.contains("起手%d"%int(sim.fighters[0].definition.moves.ranged_forward.startup)),"训练应显示当前招式完整帧数据")
	sim.fighters[0].clear_move();sim.fighters[0].enter("idle");training.update_match(sim)
	require(training.info[0].text.contains("待机") and training.info[0].text.contains("上一招 八分光轮"),"结束后应保留上一招，状态使用中文名称")
	var feedback:=UfeCombatFeedback.new();root.add_child(feedback)
	sim.events=[{"kind":"hit","player":0,"x":500,"height":80,"feedback":{"spark":"impact_light","block_spark":"impact_guard","flash":2}}]
	feedback.sync(sim,320,0)
	require(feedback.advance_flash()[1]==2,"首次呈现应闪白")
	feedback.sync(sim,320,0)
	require(feedback.advance_flash()[1]==1,"同一模拟tick不能重新触发事件")
	for i in range(20):
		feedback.sync(sim,320,0)
		require(feedback.advance_flash()[1]==0,"冻结模拟与KO期间也必须结束闪白")
	require(feedback.particles.is_empty(),"KO后命中火花也应播完，不能卡在失败动画上")
	var view:=UfeSideView.new();view.ending_tick=12
	var f:=sim.fighters[1];f.state="defeat";f.move_id="light1"
	var manifest: Dictionary=UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")
	var clip:=view._animation(f,manifest)
	require(not clip.is_empty() and clip.key=="defeat","结束演出必须强制使用败方失败动画")
	view.free()
	print("页面目录筛选、虚拟网格、招式分页及真实呈现帧闪白逻辑验证完成")
	quit()
