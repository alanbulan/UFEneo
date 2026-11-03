class_name UfePixelPagesReview
extends UfePixelHudReview
var app: Node
var checks: Dictionary={}
var screenshots: Array=[]
var ko_frame: int=-1
var super_frame: int=-1
var recording_done: bool=false
var original_settings: Dictionary={}
const OUT="res://reports/review/2026-10-22-pixel-pages/"
func _init() -> void:profile="phase3_pixel_pages"
func length_frames() -> int:return 2700
func section(_frame: int) -> int:return 0
func boxes(_frame: int) -> bool:return false
func key(code: int) -> void:
	for pressed in [true,false]:
		var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=pressed
		app.get_viewport().push_input(event)
func click_button(text: String) -> void:
	for node in app.viewport.find_children("*","Button",true,false):
		if node.is_visible_in_tree() and node.text==text:
			click(node.get_global_rect().get_center());return
	checks["missing_button_"+text]=false
func click(point: Vector2) -> void:
	point=app.image.get_global_rect().position+point*app.image.stretch_shrink
	var move:=InputEventMouseMotion.new();move.position=point;move.global_position=point;app.get_viewport().push_input(move)
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new();event.position=point;event.global_position=point;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed
		app.get_viewport().push_input(event)
func snapshot(name: String) -> void:
	await RenderingServer.frame_post_draw
	app.get_viewport().get_texture().get_image().save_png(OUT+name+".png")
	screenshots.append(name)
func drive_controls(frame: int, root: Node) -> void:
	app=root
	match frame:
		0:original_settings=UfePlayerSettings.values().duplicate()
		50:snapshot("flow-title")
		90:click_button("训练")
		120:checks["title_to_shared_grid"]=app.front.page=="select";snapshot("flow-select")
		140:key(KEY_D)
		155:key(KEY_A)
		170:key(KEY_LEFT)
		185:key(KEY_RIGHT)
		200:key(KEY_J)
		225:key(KEY_KP_1)
		240:checks["both_confirm_to_vs"]=app.front.page=="vs";snapshot("flow-vs")
		400:checks["vs_to_training_match"]=not app.front.visible and app.training;snapshot("flow-training")
		960:key(KEY_F2)
		985:checks["f2_commands"]=app.hud.commands.visible;snapshot("flow-commands")
		1010:click_button("跳跃")
		1040:click_button("专属")
		1070:click_button("必杀")
		1100:key(KEY_F2)
		1140:key(KEY_ENTER)
		1170:click_button("训练设置")
		1200:click_button("对手行为：站立")
		1220:click_button("对手行为：下蹲")
		1240:click_button("对手行为：跳跃")
		1260:click_button("录制陪练（2P）")
		1280:checks["dummy_record_started"]=app.dummy_recording
		1380:key(KEY_ENTER)
		1410:click_button("训练设置")
		1440:click_button("循环播放陪练录制")
		1480:checks["dummy_tape_replays"]=not app.dummy_recording and app.dummy_tape.size()>60 and app.dummy_cursor>0;snapshot("flow-dummy-replay")
		1560:key(KEY_ENTER)
		1590:click_button("返回主菜单")
		1630:click_button("档案")
		1670:checks["archive_open"]=app.front.page=="archive";snapshot("flow-archive")
		1710:click_button("宇宙恐龙杰顿")
		1750:snapshot("flow-archive-zetton")
		1800:click_button("返回")
		1830:click_button("设置")
		1880:checks["settings_open"]=app.front.page=="settings";snapshot("flow-settings")
		1910:
			var sliders: Array=app.front.find_children("*","HSlider",true,false)
			if not sliders.is_empty():click(sliders[0].get_global_rect().get_center())
		1960:checks["volume_persisted"]=absf(float(UfePlayerSettings.values().sfx)-float(app.front.settings_values.sfx))<0.01
		1970:UfePlayerSettings.apply(original_settings)
		2000:click_button("返回")
		2040:click_button("本地双人")
		2090:app.front.long_names=true;app.front._preview();snapshot("flow-select-long")
		2140:
			app.front.grid.scroll_vertical=100000
		2180:
			checks["grid_bottom_virtualized"]=app.front.grid.first_row>0 and app.front.grid.loaded_cells<=50
			snapshot("flow-select-bottom")
		2220:click_button("宇宙人")
		2260:checks["alien_tab_separate"]=app.front.model.filtered.all(func(e):return e.selection_category=="alien");snapshot("flow-select-aliens")
		2300:click_button("返回")
		2340:click_button("对战电脑")
		2380:key(KEY_J)
		2400:key(KEY_KP_1)
		2550:checks["cpu_mode_starts"]=not app.front.visible and not app.training and not app.local
		2650:
			var file:=FileAccess.open(OUT+"navigation-evidence.json",FileAccess.WRITE)
			file.store_string(JSON.stringify({"checks":checks,"all_passed":not checks.values().has(false),"screenshots":screenshots,"tape_frames":app.dummy_tape.size()},"\t"))
func sample(frame: int,sim: UfeMatchDirector) -> UfeInputFrame:
	var a:=UfeInputFrame.make();passive=UfeInputFrame.make()
	if frame in [420,434,448]:a=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
	if frame==620:a=UfeInputFrame.make(0,0,UfeInputFrame.SPECIAL)
	if frame in [1290,1330]:passive=UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
	if frame>=1280 and frame<1290:passive=UfeInputFrame.make(-1,0)
	return a
func observe_walk(frame: int,sim: UfeMatchDirector,view: UfeSideView) -> void:
	trace.append({"frame":frame,"tick":sim.tick,"page":app.front.page if app!=null and app.front.visible else "battle","flash":view.feedback.flash.duplicate(),"finished":sim.finished,"states":[sim.fighters[0].state,sim.fighters[1].state],"animations":[view._animation(sim.fighters[0],view.manifests[0]),view._animation(sim.fighters[1],view.manifests[1])]})
