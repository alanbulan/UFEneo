extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,what: String) -> void:
	if not ok and what not in failures:failures.append(what);printerr(what)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var driver:=UfeGateBPatchReview.new()
	var view:=UfeSideView.new()
	var manifests:=[UfeContentDatabase.read_json("res://assets/fighters/ultraman/animations/manifest.json"),UfeContentDatabase.read_json("res://assets/fighters/zetton/animations/manifest.json")]
	var sim:=UfeContentDatabase.match_for();var twin:=UfeContentDatabase.match_for();var results:={};var trace:=[]
	for frame in range(driver.length_frames()):
		driver.review_frame=frame
		var section:=driver.section(frame);var key:=str(section)
		if section!=driver.last_section:
			sim=UfeContentDatabase.match_for();twin=UfeContentDatabase.match_for();driver.prepare_match(sim);driver.prepare_match(twin);driver.last_section=section
			results[key]={"hits":[],"slams":0,"tech":false,"sprites":[],"grip_error":0}
		var inputs:=[driver.sample(frame,sim),driver.second_sample(frame)]
		sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"指令投/三级KO回放确定性")
		var owner:=driver.active_player;var a:=sim.fighters[owner];var b:=sim.fighters[1-owner]
		var pair:=[]
		for i in range(2):
			var f:=sim.fighters[i];var anim:=view._animation(f,manifests[i])
			check(f.height>=0,"受投根点不能入地："+key+"/"+str(frame))
			pair.append({"fighter":f.definition.id,"x":f.x,"height":f.height,"facing":f.facing,"state":f.state,"move":f.move_id,"clip":anim.get("key",""),"sprite":anim.get("index",0),"hp":f.stats.hp,"data":f.frame().duplicate(true)})
		if a.move_id=="motion_41236":
			var index:=int(a.frame().sprite)
			if index not in results[key].sprites:results[key].sprites.append(index)
		if b.state=="thrown" and a.frame().get("target",{}).get("mode","")=="hold":
			var grip: Array=a.frame().target.grip;var grab: Array=b.frame().grab_points.waist
			var error:=absi(a.x+a.facing*int(grip[0])-b.x-b.facing*int(grab[0]))+absi(a.height+int(grip[1])-b.height-int(grab[1]))
			results[key].grip_error=maxi(results[key].grip_error,error)
			check(error==0,"双向抓点必须完全重合："+key)
		for e in sim.events:
			if e.kind=="hit":results[key].hits.append(e.move)
			if e.kind=="throw_slam":results[key].slams+=1
			if e.kind=="throw_tech":results[key].tech=true
		trace.append({"movie_frame":frame,"section":section,"player":owner,"pair":pair,"events":sim.events.duplicate(true)})
		if frame%180==179:
			if section<2:
				check(results[key].hits==["motion_41236"] and results[key].slams==1,"站防仍被指令投捕获且只结算一次伤害："+key)
				check(b.stats.hp==1000-int(a.definition.moves.motion_41236.damage),"指令投伤害："+key)
				check(results[key].sprites.size()==8,"独立八格完整播放："+key)
			elif section<4:check(results[key].tech and b.stats.hp==1000,"第3tick可拆且不扣血："+key)
			elif section<6:check(results[key].hits.is_empty() and b.stats.hp==1000,"起跳避开地面指令投："+key)
			else:check(sim.finished and sim.winner==owner and results[key].hits==["special3"],"三级必杀真实KO："+key)
	for f in sim.fighters:
		var m: Dictionary=f.definition.moves.motion_41236
		check(m.kind=="throw" and m.unblockable and m.damage>f.definition.moves.throw_forward.damage,"指令投不可防，伤害高于普通投")
		check(UfeMoveData.validate(m) and m.frames.size()==40,"指令投完整帧数据")
	view.free()
	FileAccess.open("res://reports/gate-b-patch-evidence.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"results":results,"trace":trace},"\t"))
	await ui_geometry()
	print("GATE_B_PATCH "+JSON.stringify({"failures":failures,"results":results}))
	quit(0 if failures.is_empty() else 1)

func ui_geometry() -> void:
	root.size=Vector2i(640,360)
	var front:=UfeFrontEnd.new();root.add_child(front)
	var checked:=[]
	for page in ["title","select","vs","archive","settings","commands"]:
		front.open(page)
		for tick in range(8):await process_frame
		check_buttons(front,page,checked)
		if page=="vs":
			var vs:=front.content.get_child(1) as PixelVS
			check(vs!=null and vs.heights==[144,166],"VS按定稿实际身高显示，不缩小杰顿")
	front.queue_free()
	await process_frame
	var hud:=UfeBattleHUD.new();root.add_child(hud)
	await process_frame
	hud.update_match(UfeContentDatabase.match_for(),"",0,true)
	for panel in [hud.menu,hud.settings,hud.home,hud.selection,hud.commands]:
		hud.close_overlays();panel.show()
		if panel==hud.selection:hud.show_selection(["ultraman","zetton"])
		if panel==hud.commands:
			hud.commands.set_fighter(UfeContentDatabase.fighter("zetton"))
			hud.commands.show_page(5)
		for tick in range(8):await process_frame
		check_buttons(hud,"battle/"+panel.name,checked)
	FileAccess.open("res://reports/ui-text-bounds.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"buttons":checked},"\t"))
	hud.queue_free()

func check_buttons(parent: Node,page: String,checked: Array) -> void:
	for node in parent.find_children("*","Button",true,false):
		if not node.is_visible_in_tree():continue
		check(node is PixelButton or node is PixelChoice,"正式按钮必须使用组件："+node.name)
		if not node is PixelButton and not node is PixelChoice:continue
		var caption: Label=node.caption
		for error in PixelTextBounds.violations(node,caption):check(false,page+" "+error)
		checked.append({"page":page,"text":caption.text,"button_size":[node.size.x,node.size.y],"text_rect":[caption.position.x,caption.position.y,caption.size.x,caption.size.y]})
