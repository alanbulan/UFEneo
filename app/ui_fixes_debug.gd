class_name UfeUIFixesDebug
extends RefCounted
## 正式主游戏训练模式的界面取证驱动，不替换主场景或游戏脚本。
const IDS=["ultraman","ultraseven","ultraman-jack","ultraman-ace","ultraman-taro","ultraman-leo","gomora","neronga","red_king","eleking","black_king","zetton"]
var app
var mode: String
var output: String
var events: Array=[]
var checks: Dictionary={}
var switch_nodes: Array=[]
var battle_started: bool=false
var done: bool=false
var portrait_pair: Array[String]=["ultraman","ultraseven"]
var victory_winner: int=0
var victory_snapshot_tick: int=42
var victory_samples: Array=[]
var bounds_cache: Dictionary={}
var forms_popup_review: bool=false

func prepare(game: Control, review_mode: String, directory: String) -> void:
	app=game
	mode=review_mode
	output=directory
	DirAccess.make_dir_recursive_absolute(output)
	app.intro=0
	app.front.long_names="--review-long-text" in OS.get_cmdline_user_args()
	app.training_overlay.hide()
	# 复用既有showcase挂钩，仅显式头像参数启用本轮取证。
	if mode=="showcase":
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--portrait-pair="):mode="portraits"
			if arg.begins_with("--victory-pair="):mode="victory-review"
			if arg=="--forms-review":mode="forms-review"
			if arg=="--forms-popup-review":forms_popup_review=true
	if forms_popup_review:
		app.get_window().gui_embed_subwindows=true
		# 自动展开菜单时忽略真实鼠标悬停，避免弹窗收起后改选脚本指定的角色。
		app.get_viewport().gui_disable_input=true
	if mode=="victory-review":
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--victory-pair="):portrait_pair.assign(arg.trim_prefix("--victory-pair=").split(","))
			if arg.begins_with("--victory-winner="):victory_winner=clampi(int(arg.trim_prefix("--victory-winner=")),0,1)
			if arg.begins_with("--victory-snapshot-tick="):victory_snapshot_tick=int(arg.trim_prefix("--victory-snapshot-tick="))
	if mode=="portraits":
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--portrait-pair="):
				var requested:=arg.trim_prefix("--portrait-pair=").split(",")
				if requested.size()==2 and requested[0] in IDS and requested[1] in IDS:
					portrait_pair.assign(requested)
	if mode in ["switch","showcase","portraits","victory-review","forms-review"]:
		app.front.mode="training"
		app._show_page("select")
	else:
		app.front.hide()
		app.simulation.fighters[0].x=500
		app.simulation.fighters[1].x=563

func choose(player: int, id: String) -> void:
	app.front.choose(player,app.front.model.index_of(id))

func drive(tick: int) -> void:
	if done:return
	if mode=="victory-review":
		if tick==30:choose(0,portrait_pair[0]);choose(1,portrait_pair[1])
		if tick==90:app.front.handle_key(KEY_J)
		if tick==100:app.front.handle_key(KEY_KP_1)
		if tick==210:
			app.intro=0
			app.simulation.fighters[0].x=500
			# 布莱克王近爪的有效区在根点前105–144；过近会从对手身后挥空。
			var separation: int=128 if portrait_pair[victory_winner]=="black_king" else 63
			app.simulation.fighters[1].x=500+separation
			checks.finishing_distance=separation
			app.simulation.fighters[1-victory_winner].stats.hp=1
	elif mode=="forms-review":
		if forms_popup_review:
			if tick==30:choose(0,"gomora");choose(1,"zetton")
			if tick==45:app.front.form_choices[0].show_popup()
			if tick==80:
				app.front.form_choices[0].get_popup().hide()
				app.front.form_choices[1].show_popup()
			if tick==140:
				app.front.form_choices[1].get_popup().hide()
				choose(0,"ultraman");choose(1,"ultraman-taro")
			if tick==155:app.front.form_choices[0].show_popup()
			if tick==220:
				app.front.form_choices[0].get_popup().hide()
				app._show_page("archive")
			if tick==240:app.front.archive_view.show_character("ultraman-taro")
		else:
			if tick==30:choose(0,"gomora");choose(1,"zetton")
			if tick==90:choose(0,"red_king");choose(1,"eleking")
			if tick==150:choose(0,"ultraman");choose(1,"ultraman-taro")
	elif mode=="portraits":
		if tick==30:choose(0,portrait_pair[0]);choose(1,portrait_pair[1])
		if tick==90:app.front.handle_key(KEY_J)
		if tick==100:app.front.handle_key(KEY_KP_1)
		if tick==210:
			app.intro=0
			checks.confirmed_match=app.selected_fighters==portrait_pair
		if tick==300:app._show_page("archive")
		if tick in [320,390]:
			var id: String=portrait_pair[0 if tick==320 else 1]
			for button in app.front.archive_view.buttons:
				if str(button.get_meta("fighter_id"))==id:
					button.pressed.emit()
					app.front.archive_view.list_scroll.ensure_control_visible(button)
	elif mode=="switch":
		if tick==29:switch_nodes=node_ids()
		if tick>=30 and tick<150 and (tick-30)%18==0:
			app.front.handle_key(KEY_D if ((tick-30)/18)%2==0 else KEY_A)
	elif mode=="showcase":
		if tick==30:choose(0,"ultraman-leo");choose(1,"black_king")
		if tick==90:choose(0,"ultraman-taro");choose(1,"red_king")
		if tick==150:choose(0,"ultraman-jack");choose(1,"eleking")
		if tick==180:app.front.handle_key(KEY_J)
		if tick==190:app.front.handle_key(KEY_KP_1)
		if tick==280:
			battle_started=true
			app.intro=0
			app.simulation.fighters[0].x=500
			app.simulation.fighters[1].x=563
			checks.confirmed_match=app.selected_fighters==["ultraman-jack","eleking"]
		if tick in [600,640]:app._action("boxes")
		if tick==650:
			app.simulation.fighters[1].stats.hp=1
			app.simulation.fighters[0].x=500
			app.simulation.fighters[1].x=563
		if tick==780:app._show_page("archive")
		if tick>=810 and tick<2250 and (tick-810)%120==0:
			var id: String=IDS[(tick-810)/120]
			for button in app.front.archive_view.buttons:
				if str(button.get_meta("fighter_id"))==id:
					button.pressed.emit()
					app.front.archive_view.list_scroll.ensure_control_visible(button)
		if tick in [2290,2370,2450]:
			app.front.archive_view.category_tabs.tab_changed.emit({2290:1,2370:2,2450:3}[tick])
		if tick==2520:
			app.front.selections[0]="ultraman-taro"
			app.front.open("commands")
	else:
		# 边界样本只调整训练血量；真实掉血样本走主游戏输入、模拟和回放记录。
		app.paused=tick>=120
		if tick in [150,190,310,430]:
			var ratios:={150:1.0,190:0.5,310:0.15,430:0.0}
			for fighter in app.simulation.fighters:
				fighter.stats.hp=roundi(fighter.definition.max_health*ratios[tick])

func sample(player: int, tick: int) -> UfeInputFrame:
	var attack: bool=false
	if mode=="hud":attack=tick==(30 if player==0 else 85)
	if mode=="showcase":attack=tick in [310,470,670] if player==0 else tick==390
	if mode=="victory-review":attack=player==victory_winner and tick in [230,290,350]
	return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT if attack else 0)

func node_ids() -> Array:
	var result: Array=[app.front.previews[0].get_instance_id(),app.front.previews[1].get_instance_id(),app.front.grid.get_instance_id()]
	for cell in app.front.grid.cells:result.append(cell.get_instance_id())
	for picture in app.front.grid.pictures:result.append(picture.get_instance_id())
	return result

func observe(tick: int) -> void:
	if done:return
	if mode=="victory-review":
		app.training_overlay.hide()
		if app.simulation.finished:
			checks.real_finishing_hit=app.simulation.winner==victory_winner and app.simulation.fighters[1-victory_winner].stats.hp<=0
			_record_victory_sample(app.ending_tick)
			if app.ending_tick==victory_snapshot_tick:snapshot("victory-highest",tick)
			if app.ending_tick==70:snapshot("victory-hold",tick)
			if app.ending_tick==180:finish()
		if tick==550 and not app.simulation.finished:
			checks.real_finishing_hit=false
			finish()
	elif mode=="forms-review":
		if forms_popup_review and tick==280:
			checks.archive_forms_public_text=app.front.archive_view.description.text
			snapshot("archive-forms-taro",tick)
		if tick in [60,120,180]:
			var choices: Array=[]
			for player in range(2):
				var items: Array=[]
				var choice: PixelChoice=app.front.form_choices[player]
				for index in range(choice.item_count):items.append({"id":choice.get_item_metadata(index),"text":choice.get_item_text(index),"disabled":choice.is_item_disabled(index)})
				choices.append({"fighter":app.front.selections[player],"items":items})
			checks["forms-%d"%tick]=choices
			snapshot("forms-%d"%tick,tick)
	elif mode=="portraits":
		if tick==60:
			checks.portrait_paths={}
			for id in IDS:checks.portrait_paths[id]=UfeFighterDisplay.portrait(str(id)).resource_path
			snapshot("select",tick)
		if tick==130:snapshot("versus",tick)
		if tick==250:snapshot("hud",tick)
		if tick==350:snapshot("archive-"+portrait_pair[0],tick)
		if tick==420:snapshot("archive-"+portrait_pair[1],tick)
	elif mode=="switch":
		if tick in [29,30,31,32,34,38,42,48,49,50,52,58,66,84,120,160]:snapshot("switch-%03d"%tick,tick)
		if tick==160:
			checks.selection_nodes_reused=switch_nodes==node_ids()
			checks.wipe_hidden=not app.front.is_transitioning()
			checks.preview_opaque=app.front.previews[0].art.modulate.a==1.0 and app.front.previews[1].art.modulate.a==1.0
			checks.preview_single_layer=app.front.previews[0].get_child_count()==1 and app.front.previews[1].get_child_count()==1
	elif mode=="showcase":
		if tick==40:
			checks.portrait_paths={}
			checks.battle_forms_hidden=true
			checks.unimplemented_forms_disabled=true
			for id in IDS:
				checks.portrait_paths[id]=UfeFighterDisplay.portrait(str(id)).resource_path
				choose(0,str(id))
				var choice: PixelChoice=app.front.form_choices[0]
				for index in range(choice.item_count):
					var form_id:=str(choice.get_item_metadata(index))
					for form in UfeFighterDisplay.entry(str(id)).forms:
						if str(form.id)!=form_id:continue
						if str(form.get("switch","select"))=="battle":checks.battle_forms_hidden=false
						if not form.implemented and not choice.is_item_disabled(index):checks.unimplemented_forms_disabled=false
				var before: String=str(app.front.selected_forms[0])
				app.front.handle_key(KEY_Q);app.front.handle_key(KEY_E)
				if str(app.front.selected_forms[0])!=before:checks.unimplemented_forms_disabled=false
			choose(0,"ultraman-leo")
		if tick in [60,120,175]:snapshot("select-%03d"%tick,tick)
		if tick==220:snapshot("versus",tick)
		if tick==360:checks.showcase_real_hit_2p=app.simulation.fighters[1].stats.hp<app.simulation.fighters[1].definition.max_health
		if tick==450:checks.showcase_real_hit_1p=app.simulation.fighters[0].stats.hp<app.simulation.fighters[0].definition.max_health
		if tick in [300,333,413,710,750]:snapshot("battle-%03d"%tick,tick)
		if tick==620:snapshot("training-f1",tick)
		if tick==750:checks.real_finishing_hit=app.simulation.finished and app.simulation.winner==0
		if tick>=850 and tick<2290 and (tick-850)%120==0:snapshot("archive-"+str(app.front.archive_view.selected_id),tick)
		if tick in [2330,2410,2490]:snapshot({2330:"archive-ultra",2410:"archive-kaiju",2490:"archive-alien"}[tick],tick)
		if tick==2560:snapshot("commands-battle-form",tick)
	else:
		if tick==65:checks.real_hit_2p=app.simulation.fighters[1].stats.hp<app.simulation.fighters[1].definition.max_health
		if tick==115:checks.real_hit_1p=app.simulation.fighters[0].stats.hp<app.simulation.fighters[0].definition.max_health
		if tick in [48,104,170,206,290,326,410,446,530]:
			var key: String={48:"damage-2p",104:"damage-1p",170:"full",206:"half-trail",290:"half",326:"low-trail",410:"low",446:"zero-trail",530:"zero"}[tick]
			snapshot(key,tick)
	if tick==((330 if forms_popup_review else 210) if mode=="forms-review" else 449 if mode=="portraits" else 184 if mode=="switch" else 2619 if mode=="showcase" else 549) and mode!="victory-review":finish()

func _record_victory_sample(tick: int) -> void:
	# 等容器完成本帧布局后量边界，避免把上一帧的居中位置误当成最终画面。
	await RenderingServer.frame_post_draw
	var subjects: Array=[]
	for sprite in app.view.fighters:subjects.append(_sprite_bounds(sprite))
	victory_samples.append({"tick":tick,"winner":app.simulation.winner,"states":[app.simulation.fighters[0].state,app.simulation.fighters[1].state],"fighters":subjects,"word":_rect(app.hud.word.get_global_rect()) if app.hud.word.visible else [],"result":_rect(app.hud.result_panel.get_global_rect()),"word_scale":app.hud.word.scale.x})

func _rect(value: Rect2) -> Array:
	return [value.position.x,value.position.y,value.size.x,value.size.y]

func _sprite_bounds(sprite: Sprite2D) -> Array:
	var region:=Rect2i(sprite.region_rect) if sprite.region_enabled else Rect2i(Vector2i.ZERO,sprite.texture.get_size())
	var key:="%s:%s"%[sprite.texture.get_instance_id(),region]
	if not bounds_cache.has(key):bounds_cache[key]=sprite.texture.get_image().get_region(region).get_used_rect()
	var used: Rect2i=bounds_cache[key]
	var at:=Vector2(used.position)
	if sprite.flip_h:at.x=region.size.x-used.end.x
	return _rect(sprite.get_global_transform()*Rect2(sprite.offset+at,Vector2(used.size)))

func snapshot(key: String, tick: int) -> void:
	await RenderingServer.frame_post_draw
	app.get_viewport().get_texture().get_image().save_png(output+"/"+key+".png")
	var names: Array=[]
	var active_names: Array=app.front.content.find_children("*","MarginContainer",true,false) if app.front.visible else app.hud.names.duplicate()
	if not app.front.visible and app.hud.result_panel.visible:active_names.append(app.hud.result_name)
	for node in active_names:
		if not node is FighterName or not node.is_visible_in_tree():continue
		var text: String=node.name_label.text
		var needed: float=node.name_label.get_theme_font("font").get_string_size(text,HORIZONTAL_ALIGNMENT_LEFT,-1,node.name_label.get_theme_font_size("font_size")).x
		var title_needed: float=node.title_label.get_theme_font("font").get_string_size(node.title_label.text,HORIZONTAL_ALIGNMENT_LEFT,-1,node.title_label.get_theme_font_size("font_size")).x
		names.append({"fighter":node.fighter_id,"text":text,"width":node.name_label.size.x,"needed":needed,"height":node.name_label.size.y,"line_count":node.name_label.get_line_count(),"visible_lines":node.name_label.get_visible_line_count(),"name_rect":_rect(node.name_label.get_global_rect()),"title":node.title_label.text,"title_needed":title_needed,"title_width":node.title_label.size.x,"title_lines":node.title_label.get_line_count(),"title_rect":_rect(node.title_label.get_global_rect()),"container":_rect(node.get_global_rect()),"title_color":node.title_label.get_theme_color("font_color").to_html(),"name_color":node.name_label.get_theme_color("font_color").to_html()})
	var gauges: Array=[]
	for gauge in app.hud.health:
		gauges.append({"value":gauge.bar.value,"trail":gauge.ghost.value,"trail_visible":gauge.ghost.visible,"fill_mode":gauge.bar.fill_mode,"fill_region":gauge.bar.texture_progress.region,"frame":gauge.get_child(1).texture.resource_path})
	events.append({"frame":tick,"screenshot":key,"hp":[app.simulation.fighters[0].stats.hp,app.simulation.fighters[1].stats.hp],"name_layout":names,"gauges":gauges})

func finish() -> void:
	done=true
	app.set_physics_process(false)
	await RenderingServer.frame_post_draw
	var file:=FileAccess.open(output+"/events.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"mode":mode,"entry":"app/scenes/main.tscn","training":app.training,"checks":checks,"events":events,"victory_samples":victory_samples},"\t"))
	file.close()
	app.get_tree().quit()
