extends SceneTree
var failures: Array[String]=[]
func check(ok: bool,message: String) -> void:
	if not ok:failures.append(message)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	root.size=Vector2i(640,360)
	var front:=UfeFrontEnd.new();root.add_child(front)
	front.open("title")
	await process_frame
	var covers: Array=front.content.find_children("*","TextureRect",true,false).filter(func(n):return n.texture!=null and n.texture.resource_path=="res://assets/ui/title-cover/ensemble.png")
	check(covers.size()==1,"标题页使用唯一完整群像封面")
	for cover in covers:check(not cover.flip_h and cover.scale==Vector2.ONE,"标题完整群像保持原生朝向")
	for page in ["vs","select"]:
		front.open(page)
		for frame in range(6):await process_frame
		var players: Array=[]
		for node in front.content.find_children("*","TextureRect",true,false):
			if node.has_meta("display_player"):players.append(node)
		check(players.size()==2,page+"必须登记双人显示朝向")
		for player in range(players.size()):
			check(players[player].get_meta("display_player")==player,page+"左右玩家顺序")
			check(players[player].flip_h==(player==1),page+"右侧必须面朝左、左侧必须面朝右")
			check(players[player].scale==Vector2.ONE,page+"镜像不得使用负缩放移动容器")
		if page=="vs":
			var vs: PixelVS=front.content.get_child(1)
			vs.age=1;vs._process(0)
			var right: PixelArt=vs.portraits[1]
			var slot: Control=right.get_parent()
			var factor:=right.size.x/right.texture.get_width()
			var foot:=right.position+right.displayed_foot_anchor()*factor
			check(foot.is_equal_approx(Vector2(slot.size.x/2,slot.size.y)),"VS翻转后脚底仍在容器底部中央")
			var before:=foot
			right.flip_h=false;vs._process(0)
			foot=right.position+right.displayed_foot_anchor()*factor
			check(before.is_equal_approx(foot),"VS镜像前后脚底锚点不能漂移")
			right.face_player(1)
	front.open("archive")
	await process_frame
	var archive_models:=front.content.find_children("*","Sprite2D",true,false).filter(func(n):return n.texture!=null and n.texture.resource_path.contains("model-native"))
	check(archive_models.size()==1 and not archive_models[0].flip_h,"档案单人保持原生朝右")
	front.queue_free();await process_frame
	var hud:=UfeBattleHUD.new();root.add_child(hud);await process_frame
	check(not hud.portraits[0].picture.flip_h and hud.portraits[1].picture.flip_h,"HUD右侧头像朝左")
	var sim:=UfeContentDatabase.match_for()
	sim.finished=true;sim.winner=0
	sim.fighters[0].enter("victory");sim.fighters[1].enter("defeat")
	var view:=UfeSideView.new();view.bind_match(sim);root.add_child(view);view.update_view()
	check(not view.fighters[0].flip_h and view.fighters[1].flip_h,"胜负画面延用对局中的面对面朝向")
	print("UI_FACING "+("PASS" if failures.is_empty() else str(failures)))
	quit(0 if failures.is_empty() else 1)
