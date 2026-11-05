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
	root.size=Vector2i(640,360)
	for safe in [Rect2(16,62,608,262),Rect2(16,170,608,140),Rect2(20,80,500,190)]:
		for bounds in [Rect2(200,100,200,204),Rect2(-200,-300,1100,610),Rect2(20,270,580,60),Rect2(300,-700,90,1004)]:
			for shake in [Vector2.ZERO,Vector2(30,-30),Vector2(-50,50)]:
				var fit := UfeBattleFraming.fit(bounds,1,shake,safe)
				check(inside(safe,fit.bounds),"动态边界/高跳/长尾/倒地/震屏 "+str(bounds))
	var hud:=UfeBattleHUD.new();root.add_child(hud)
	var training:=UfeTrainingOverlay.new();root.add_child(training)
	training.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	training.offset_top=56;training.offset_bottom=56;training.hide()
	hud.framing_top_overlays.append(training)
	var sim:=UfeContentDatabase.match_for("gomora","ultraman-jack")
	var twin:=UfeContentDatabase.match_for("gomora","ultraman-jack")
	var view:=UfeSideView.new();view.bind_match(sim);root.add_child(view)
	view.framing_safe_provider=hud.battle_safe_rect
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
			check(inside(hud.battle_safe_rect(),view.framed_bounds),"正式哥莫拉长尾/杰克整帧双向 "+state)
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
		check(inside(hud.battle_safe_rect(),view.framed_bounds),"持握实体共同取景")
	weapon.queue_free();view.framing_entities.clear()
	# 任一侧变身提示、训练信息与字号增高必须改变可用区，不隐藏HUD。
	for hints in [[false,false],[true,false],[false,true],[true,true]]:
		for i in range(2):hud.transform_hints[i].visible=hints[i]
		var safe:=hud.battle_safe_rect()
		check(safe.end.y <= hud.size.y-8-hud.bottom_bar.get_combined_minimum_size().y,"提示变化当帧预测下栏")
		for frame in range(3):await process_frame
		view.update_view()
		check(inside(hud.battle_safe_rect(),view.framed_bounds),"提示排版后共同取景 "+str(hints))
	training.show();training.update_match(sim)
	for frame in range(4):await process_frame
	view.update_view()
	check(hud.battle_safe_rect().position.y>=training.get_global_rect().end.y,"避让训练信息实际底部")
	check(inside(hud.battle_safe_rect(),view.framed_bounds),"训练信息显示仍完整")
	training.hide()
	hud.top_bar.custom_minimum_size.y=95
	check(hud.battle_safe_rect().position.y>=103,"上栏布局当帧预测")
	for frame in range(3):await process_frame
	view._refresh_layout_framing()
	check(inside(hud.battle_safe_rect(),view.framed_bounds),"绘制前布局刷新")
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
	print(JSON.stringify({"test":"battle_framing","checks":checks,"failures":failures,"final_hash":sim.state_hash()}))
	view.queue_free();hud.queue_free();training.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)
