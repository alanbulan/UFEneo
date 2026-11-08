class_name UfeGateBReview
extends RefCounted
## 审片仅导航和代按玩家一；玩家二始终经过正式困难电脑控制器。
var app: Node
var original_settings: Dictionary={}
var trace: Array=[]
var ended_at: int=-1
var pressed_before: int=0
const OUT="res://reports/review/2026-10-22-gate-b/"
func key(code: int) -> void:
	for pressed in [true,false]:
		var event:=InputEventKey.new();event.keycode=code as Key;event.physical_keycode=code as Key;event.pressed=pressed;app.get_viewport().push_input(event)
func click_button(text: String) -> void:
	for node in app.viewport.find_children("*","Button",true,false):
		if node.is_visible_in_tree() and node.text==text:
			var point: Vector2=app.image.get_global_rect().position+node.get_global_rect().get_center()*app.image.stretch_shrink
			var move:=InputEventMouseMotion.new();move.position=point;move.global_position=point;app.get_viewport().push_input(move)
			for pressed in [true,false]:
				var event:=InputEventMouseButton.new();event.position=point;event.global_position=point;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;app.get_viewport().push_input(event)
			return
func drive(frame: int,root: Node) -> void:
	app=root
	match frame:
		0:original_settings=UfePlayerSettings.values().duplicate()
		45:click_button("设置")
		85:
			for choice in app.front.find_children("*","OptionButton",true,false):
				if choice.item_count==3:choice.select(2);choice.item_selected.emit(2)
		125:click_button("返回")
		160:click_button("对战电脑")
		230:key(KEY_J)
		260:key(KEY_KP_1)
		5375:
			var file:=FileAccess.open(OUT+"match-evidence.json",FileAccess.WRITE)
			file.store_string(JSON.stringify({"match_seed":app.match_seed,"difficulty":app.ai_difficulty,"p2_input_source":"UfeComputerController.sample","p1_input_source":"审片脚本代按，未改模拟","ended_at_frame":ended_at,"winner":app.simulation.winner,"finished":app.simulation.finished,"ai_actions":app.computers[1].actions,"frames":trace},"\t"))
			app.recorder.save_file(OUT+"match-replay.json")
		5380:UfePlayerSettings.apply(original_settings)
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	return player_input(frame,sim)
static func player_input(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var f:=sim.fighters[0];var b:=sim.fighters[1]
	var gap:=absi(b.x-f.x)
	if f.state=="thrown" or b.move_id in ["throw_forward","throw_back","dash_throw"]:return UfeInputFrame.make(0,0,UfeInputFrame.THROW if sim.tick%2==0 else 0)
	# 前半局有攻防交换，后半局追击/必杀。只使用普通输入，不调整生命、计时或电脑行为。
	if frame<4000:
		var move: Dictionary=b.definition.moves.get(b.move_id,{})
		if not move.is_empty() or not sim.projectiles.is_empty():return UfeInputFrame.make(0,-1 if move.get("level","")=="low" else 0,UfeInputFrame.GUARD)
		if frame%600<110 and gap>190:return UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
		if frame%600>300 and frame%600<360 and gap<110 and sim.tick%28==0:return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		return UfeInputFrame.make(-f.facing if gap<110 and frame%600<300 else f.facing if gap>220 else 0,0,UfeInputFrame.GUARD)
	if not f.move_id.is_empty():
		if f.combat.confirmed and int(f.motion.chase_window)>0:return UfeInputFrame.make(f.facing,1,UfeInputFrame.JUMP)
		if f.combat.confirmed and sim.tick%2==0:
			return UfeInputFrame.make(0,0,UfeInputFrame.HEAVY if "chase_end" in f.frame().cancel else UfeInputFrame.LIGHT)
		return UfeInputFrame.make()
	if int(f.stats.energy)>=1000 and sim.tick%2==0:return UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	if f.height>0:return UfeInputFrame.make(f.facing,0,UfeInputFrame.LIGHT if sim.tick%6==0 else 0)
	if gap>90:return UfeInputFrame.make(f.facing,0,UfeInputFrame.RANGED if sim.tick%75==0 else 0)
	if sim.tick%20==0:return UfeInputFrame.make(0,-1,UfeInputFrame.HEAVY)
	if sim.tick%20==10:return UfeInputFrame.make(f.facing,0,UfeInputFrame.HEAVY)
	return UfeInputFrame.make()
func observe(frame: int,sim: UfeMatchDirector) -> void:
	if sim.finished and ended_at<0:ended_at=frame
	if frame%30==0 or not sim.events.is_empty():trace.append({"frame":frame,"page":app.front.page if app.front.visible else "battle","tick":sim.tick,"hp":[sim.fighters[0].stats.hp,sim.fighters[1].stats.hp],"energy":[sim.fighters[0].stats.energy,sim.fighters[1].stats.energy],"moves":[sim.fighters[0].move_id,sim.fighters[1].move_id],"states":[sim.fighters[0].state,sim.fighters[1].state],"events":sim.events.duplicate(true)})
