extends SceneTree
var failures: Array[String] = []
var checks := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:failures.append(label)
func inside(outer: Rect2, inner: Rect2) -> bool:
	return outer.grow(0.002).encloses(inner)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	await check_window_fit()
	root.size=Vector2i(640,360)
	for safe in [Rect2(16,62,608,262),Rect2(16,170,608,140),Rect2(20,80,500,190)]:
		for bounds in [Rect2(200,100,200,204),Rect2(-200,-300,1100,610),Rect2(20,270,580,60),Rect2(300,-700,90,1004)]:
			for shake in [Vector2.ZERO,Vector2(30,-30),Vector2(-50,50)]:
				var fit := UfeBattleFraming.fit(bounds,1,shake,safe)
				var limit := minf(safe.size.x/maxf(1.0,bounds.size.x),safe.size.y/maxf(1.0,bounds.size.y))
				var expected_zoom := 1.0
				if limit<=0.5:expected_zoom=0.5 if limit>=0.5-0.00001 else 1.0/3.0
				check(is_equal_approx(float(fit.zoom),expected_zoom),"镜头只用1、1/2或1/3 "+str(bounds))
				if limit<=0.5 and limit>=1.0/3.0 and shake==Vector2.ZERO:
					check(inside(safe,fit.bounds),"允许缩放档内的极端轮廓收进安全区 "+str(bounds))
	# 临时面板即使把平移区压到1px，也不能成为世界缩放预算。
	var permanent_safe:=Rect2(16,62,608,262)
	for height in [120,80,1]:
		var temporary_safe:=Rect2(16,200,608,height)
		var fit:=UfeBattleFraming.fit(Rect2(200,100,200,204),1,Vector2.ZERO,temporary_safe,true,permanent_safe)
		check(is_equal_approx(float(fit.zoom),1.0),"临时安全区不决定缩放 "+str(height))
		check(fit.bounds.position.y>=temporary_safe.position.y,"临时覆盖层仍通过平移避让 "+str(height))
	var hud:=UfeBattleHUD.new();root.add_child(hud)
	var training:=UfeTrainingOverlay.new();root.add_child(training)
	training.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	training.offset_top=56;training.offset_bottom=56;training.hide()
	hud.framing_top_overlays.append(training)
	var sim:=UfeContentDatabase.match_for("gomora","ultraman-jack")
	var twin:=UfeContentDatabase.match_for("gomora","ultraman-jack")
	var view:=UfeSideView.new();view.bind_match(sim);root.add_child(view)
	view.framing_safe_provider=hud.battle_safe_rect
	view.framing_zoom_safe_provider=hud.battle_zoom_rect
	hud.update_match(sim,"",0,false)
	check(hud.battle_safe_rect().size.y>100,"首次容器排版前不能把世界压成一个像素")
	view.update_view()
	check(view.camera_zoom>0.1,"首次取景不因未排版意外缩小")
	for frame in range(4):await process_frame
	for facing in [-1,1]:
		for state in ["idle","down","air"]:
			for f in sim.fighters:
				f.facing=facing;f.enter(state)
				sim.fighters[0].height=260 if state=="air" else 0
			var before:=sim.state_hash()
			view.update_view()
			check(sim.state_hash()==before,"取景不得修改状态 "+state)
			if state=="air":
				check(is_equal_approx(view.camera_zoom,1.0),"跳跃保持整数缩放 1 "+state)
			else:
				check(inside(hud.battle_safe_rect(),view.framed_bounds),"正式哥莫拉长尾/杰克整帧双向 "+state)
	# 普通跳跃不竖直追镜头：起跳后取景与缩放沿用地面值，落地恢复。
	# 训练信息显示时可用区只有一百多像素高，跳跃顶点也不允许瞬间落进 1/2。
	for f in sim.fighters:f.height=0;f.enter("idle")
	view.update_view()
	var ground_y:=view.position.y
	sim.fighters[0].enter("air");sim.fighters[0].height=136
	view.update_view()
	check(is_equal_approx(view.camera_zoom,1.0),"跳跃不改变缩放")
	# 只有头顶恰好出画时按像素平移，不再整场追着跳跃上下走。
	check(absf(view.position.y-ground_y)<=4.0,"跳跃不竖直追镜头")
	# 被击飞更高时只平移不让头出画，仍然不缩放。
	sim.fighters[0].height=260
	view.update_view()
	check(is_equal_approx(view.camera_zoom,1.0),"被击飞高度也不落进 1/2")
	# Alpha取景必须兼容附件默认centered、偏心Alpha、镜像、旋转及缩放。
	var image:=Image.create(32,24,false,Image.FORMAT_RGBA8)
	image.fill(Color.TRANSPARENT)
	image.fill_rect(Rect2i(3,5,19,12),Color.WHITE)
	var weapon:=Sprite2D.new();weapon.texture=ImageTexture.create_from_image(image)
	weapon.position=Vector2(750,-90);weapon.offset=Vector2(4,-8);weapon.rotation=0.4;weapon.scale=Vector2(1.2,0.8)
	view.add_child(weapon)
	for flip in [false,true]:
		weapon.flip_h=flip
		var alpha_pos:=Vector2(10 if flip else 3,5)
		var expected: Rect2=weapon.transform*Rect2(weapon.get_rect().position+alpha_pos,Vector2(19,12))
		check(view._sprite_bounds(weapon).is_equal_approx(expected),"持握实体Alpha使用真实局部transform")
		view.framing_entities.assign([weapon]);view._update_camera_framing()
		check(is_equal_approx(view.camera_zoom,1.0) or view.camera_zoom<=0.5,"持握实体不使用非整数缩放")
	weapon.queue_free();view.framing_entities.clear()
	# 任一侧变身提示、训练信息与字号增高必须改变可用区，不隐藏HUD。
	for hints in [[false,false],[true,false],[false,true],[true,true]]:
		for i in range(2):hud.transform_hints[i].visible=hints[i]
		var safe:=hud.battle_safe_rect()
		check(safe.end.y <= hud.size.y-8-hud.bottom_bar.get_combined_minimum_size().y,"提示变化当帧预测下栏")
		for frame in range(3):await process_frame
		view.update_view()
		check(is_equal_approx(view.camera_zoom,1.0) or view.camera_zoom<=0.5,"提示排版后仍是整数缩放 "+str(hints))
	# 落地后照常避让训练信息；跳跃中头不进安全区是上面的显式例外。
	for f in sim.fighters:f.height=0;f.enter("idle")
	training.show();training.update_match(sim)
	for frame in range(4):await process_frame
	view.update_view()
	check(hud.battle_safe_rect().position.y>=training.get_global_rect().end.y,"避让训练信息实际底部")
	# 训练信息占据上缘；高度只剩一百多像素时人物本身已放不下，此时只保证上缘对齐且不缩小。
	check(absf(view.framed_bounds.position.y-hud.battle_safe_rect().position.y)<=2.0 and is_equal_approx(view.camera_zoom,1.0),"训练信息显示上缘对齐且不缩小")
	# 上一组强制显示了双方形态提示。先同步真实HUD并完成排版，再比较覆盖层显隐。
	var saved_transform_hints: Array[bool]=[]
	for hint in hud.transform_hints:saved_transform_hints.append(hint.visible)
	var forced_zoom_safe:=hud.battle_zoom_rect()
	hud.update_match(sim,"",0,true)
	for frame in range(3):await process_frame
	view.update_view()
	# 状态/反馈换行使训练面板变高；主游戏F1/F2显隐组合只改变平移区。
	var zoom_safe:=hud.battle_zoom_rect()
	var zoom_before:=view.camera_zoom
	var state_before:=sim.state_hash()
	var layout_diagnostics: Array[Dictionary]=[{"stage":"baseline","forced_hints":saved_transform_hints,"forced_zoom_safe":str(forced_zoom_safe),"hints":[hud.transform_hints[0].visible,hud.transform_hints[1].visible],"zoom_safe":str(zoom_safe)}]
	training.custom_minimum_size.y=176
	for flags in [[true,false,false],[true,true,false],[true,false,true],[true,true,true],[false,false,false],[true,false,false]]:
		view.show_boxes=flags[1]
		hud.debug_visible=flags[1]
		if hud.commands.visible!=bool(flags[2]):hud.show_commands(sim.fighters[0].definition,sim.fighters)
		training.visible=bool(flags[0]) and not bool(flags[1]) and not bool(flags[2])
		hud.update_match(sim,"F1/F2取景回归",0,bool(flags[0]))
		for frame in range(3):await process_frame
		view.update_view();view._refresh_layout_framing()
		layout_diagnostics.append({"stage":"toggle","flags":flags,"safe":str(hud.battle_safe_rect()),"zoom_safe":str(hud.battle_zoom_rect()),"cached_zoom_safe":str(view.framing_zoom_safe_rect),"bounds":str(view.framed_bounds),"zoom":view.camera_zoom})
		check(hud.battle_zoom_rect().is_equal_approx(zoom_safe),"F1/F2/训练显隐不改变常驻HUD缩放预算 "+str(flags))
		check(is_equal_approx(view.camera_zoom,zoom_before),"高训练信息与F1/F2切换保持同一缩放 "+str(flags))
		check(sim.state_hash()==state_before,"覆盖层显隐不修改模拟 "+str(flags))
		if training.visible:
			check(hud.battle_safe_rect().position.y>=training.get_global_rect().end.y,"高训练信息仍避让实际底部")
			check(view.framed_bounds.position.y>=hud.battle_safe_rect().position.y-2.0,"高训练信息不能压到人物头部")
		else:check(hud.battle_safe_rect().is_equal_approx(zoom_safe),"隐藏训练信息恢复常驻HUD平移区")
	training.hide();training.custom_minimum_size.y=0
	view.show_boxes=false;hud.debug_visible=false;hud.close_overlays()
	# 恢复上一组常驻HUD夹具，避免update_match的真实提示显隐污染后续95px上栏用例。
	for i in range(saved_transform_hints.size()):hud.transform_hints[i].visible=saved_transform_hints[i]
	hud.top_bar.custom_minimum_size.y=95
	check(hud.battle_safe_rect().position.y>=103,"上栏布局当帧预测")
	for frame in range(3):await process_frame
	view._refresh_layout_framing()
	layout_diagnostics.append({"stage":"layout_refresh","hints":[hud.transform_hints[0].visible,hud.transform_hints[1].visible],"safe":str(hud.battle_safe_rect()),"zoom_safe":str(hud.battle_zoom_rect()),"cached_safe":str(view.framing_safe_rect),"bounds":str(view.framed_bounds),"zoom":view.camera_zoom})
	check(absf(view.framed_bounds.position.y-hud.battle_safe_rect().position.y)<=2.0 and is_equal_approx(view.camera_zoom,1.0),"绘制前布局刷新")
	sim.finished=true;sim.winner=0;hud.update_match(sim,"",0,false)
	check(hud.battle_safe_rect().size.y>100,"结算当帧不得读取reparent残留arena高度")
	view.update_view()
	check(view.camera_zoom>0.1,"结算当帧不因延迟排版变成极小世界")
	for frame in range(3):await process_frame
	view.update_view()
	check(hud.battle_safe_rect().position.y>=hud.word_center.get_global_rect().end.y,"结算顶部避让")
	# 正式手持岩石附件必须在本帧刷新后参与取景；刀光/远程弹束不追逐。
	var rock_sim:=UfeContentDatabase.match_for("red_king","gomora")
	view.bind_match(rock_sim)
	for move in ["special","special2","special3","ranged_forward","motion_214","pulse","low_pulse"]:
		rock_sim.fighters[0].stats.energy=3000
		rock_sim._start(rock_sim.fighters[0],move)
		var seen:=false
		for tick in range(rock_sim.fighters[0].definition.moves[move].frames.size()):
			rock_sim.fighters[0].move_tick=tick
			var before:=rock_sim.state_hash()
			view.update_view()
			check(before==rock_sim.state_hash(),"手持岩石只读 "+move+str(tick))
			if not view.framing_entities.is_empty():
				seen=true
				for entity in view.framing_entities:
					check(inside(view.framing_safe_rect,view.transform*view._sprite_bounds(entity)),"正式实体Alpha不得进入HUD "+move+str(tick))
		check(seen,"正式岩石附件必须命中 "+move)
	check(not UfeBattleFraming.is_held_entity({"effect":"arc_sword_upper_edge"},{}),"刀光不冒充实体武器")
	check(not UfeBattleFraming.is_held_entity({"effect":"seven_slugger"},{}),"未持握飞行实体不拉远镜头")
	# 同输入双模拟：仅一侧有HUD、镜头、附件读取，逐tick hash保持一致。
	sim=UfeContentDatabase.match_for("gomora","ultraman-jack");view.bind_match(sim)
	for tick in range(120):
		var inputs: Array=[UfeInputFrame.make(1 if tick<20 else 0,-1 if tick==20 else 0),UfeInputFrame.make()]
		sim.step(inputs);twin.step(inputs)
		var packed: Array=[inputs[0].pack(),inputs[1].pack()]
		hud.update_match(sim,"",0,false);view.update_view();view._refresh_layout_framing()
		check(sim.state_hash()==twin.state_hash(),"模拟hash不变 tick"+str(tick))
		check(packed==[inputs[0].pack(),inputs[1].pack()],"输入不变 tick"+str(tick))
	var idle_sim:=UfeContentDatabase.match_for("zoffy","ultraman-king")
	view.bind_match(idle_sim)
	var idle_manifests:=view.manifests.duplicate(true)
	for facing in [-1,1]:
		for fighter in idle_sim.fighters:
			fighter.facing=facing
			fighter.enter("idle")
		view.manifests=idle_manifests.duplicate(true)
		view.update_view()
		var idle_bounds:=view.fighters.map(func(sprite): return view._sprite_bounds(sprite))
		view.manifests=[{},{}]
		view.update_view()
		for player in range(2):
			check(view._sprite_bounds(view.fighters[player]).is_equal_approx(idle_bounds[player]),"新待机静态回退保留本人根点与轮廓 "+str(player)+":"+str(facing))
	print(JSON.stringify({"test":"battle_framing","checks":checks,"failures":failures,"final_hash":sim.state_hash(),"layout_diagnostics":layout_diagnostics}))
	view.queue_free();hud.queue_free();training.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)

func check_window_fit() -> void:
	# 主游戏重建对局只重建显示容器，不重设系统窗口；两种输出仍渲染640×360。
	for output_size in [Vector2i(1280,720),Vector2i(1920,1080)]:
		root.size=output_size
		var inherited_size:=root.size
		for rebuild in range(2):
			var center:=CenterContainer.new();root.add_child(center)
			center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
			var holder:=Control.new();center.add_child(holder)
			var image:=SubViewportContainer.new();image.stretch=true;image.stretch_shrink=1
			holder.add_child(image)
			var viewport:=SubViewport.new();viewport.size=Vector2i(640,360)
			image.add_child(viewport)
			UfeWindowFitter.fit(Vector2(inherited_size),image,holder)
			for frame in range(3):await process_frame
			var label:="输出%s 重建%d"%[output_size,rebuild]
			var factor:=float(output_size.x)/640.0
			check(viewport.size==Vector2i(640,360),label+"继承窗口而非放大内部渲染尺寸")
			check(image.size.is_equal_approx(Vector2(640,360)),label+"原生显示容器保持640×360")
			check(image.scale.is_equal_approx(Vector2.ONE*factor),label+"外层为2倍或3倍")
			check(holder.size.is_equal_approx(Vector2(output_size)),label+"缩放后尺寸参与窗口居中布局")
			check(root.size==inherited_size,label+"不覆盖用户窗口尺寸")
			center.queue_free()
			await process_frame
