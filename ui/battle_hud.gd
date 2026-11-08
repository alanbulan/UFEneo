class_name UfeBattleHUD
extends Control
signal action_requested(action: String)
var menu: PixelPanel
var commands: UfeCommandPages
var selection: PixelPanel
var settings: PixelPanel
var home: PixelPanel
var selection_buttons: Array[Button]=[]
var selection_names: Array[FighterName]=[]
var input_history: Array=[[],[]]
var review_long_text: bool=false
var debug_visible: bool=false
var debug_label: Label
var names: Array[FighterName]=[]
var result_name: FighterName
var result_panel: PixelPanel
var portraits: Array[PortraitFrame]=[]
var primary_display_id: String=""
var primary_display_form: String=""
var transform_hints: Array[Label]=[]
var health: Array[PixelGauge]=[]
var stamina: Array[PixelGauge]=[]
var energy: Array=[[],[]]
var combos: Array[PixelCombo]=[]
var combo_age: Array[int]=[0,0]
var previous_combo: Array[int]=[0,0]
var timer: Label
var timer_frame: NinePatchRect
var word: TextureRect
var top_bar: HBoxContainer
var bottom_bar: HBoxContainer
var framing_top_overlays: Array[Control] = []
var arena_space: Control
var word_center: CenterContainer
var word_key: String=""
var word_age: int=0
var commands_list: PixelList
var help_label: Label
var toast: Toast
var dummy_name: String="站立"
var dummy_relative: bool=false
var dummy_facing_button: Button

func text(parent: Node, value: String, font_size: int=12) -> Label:
	var label:=Label.new()
	label.text=value
	label.add_theme_font_size_override("font_size",font_size)
	label.mouse_filter=Control.MOUSE_FILTER_IGNORE
	parent.add_child(label)
	return label

func ignore(node: Control) -> void: node.mouse_filter=Control.MOUSE_FILTER_IGNORE

func margin(parent: Node, value: int=8) -> MarginContainer:
	var node:=MarginContainer.new()
	for side in ["left","right","top","bottom"]: node.add_theme_constant_override("margin_"+side,value)
	ignore(node)
	parent.add_child(node)
	return node

func spacer(parent: Node) -> Control:
	var node:=Control.new()
	node.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	node.size_flags_vertical=Control.SIZE_EXPAND_FILL
	ignore(node)
	parent.add_child(node)
	return node

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme=PixelPanel.NEO_THEME
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	ignore(self)
	var outer:=margin(self)
	outer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var column:=VBoxContainer.new()
	ignore(column)
	outer.add_child(column)
	var top:=HBoxContainer.new()
	top_bar=top
	top.add_theme_constant_override("separation",8)
	ignore(top)
	column.add_child(top)
	_player_top(top,0)
	var clock:=CenterContainer.new()
	clock.custom_minimum_size=Vector2(48,44)
	ignore(clock)
	top.add_child(clock)
	timer_frame=NinePatchRect.new()
	timer_frame.texture=theme.get_icon("timer","NeoKit")
	timer_frame.custom_minimum_size=Vector2(48,40)
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]: timer_frame.set_patch_margin(side,6)
	ignore(timer_frame)
	clock.add_child(timer_frame)
	var number_center:=CenterContainer.new()
	ignore(number_center)
	clock.add_child(number_center)
	number_center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	timer=text(number_center,"90",24)
	_player_top(top,1)
	arena_space=Control.new()
	arena_space.size_flags_vertical=Control.SIZE_EXPAND_FILL
	ignore(arena_space)
	column.add_child(arena_space)
	for i in range(2):
		var anchor:=CenterContainer.new()
		anchor.anchor_left=0.18 if i==0 else 0.82
		anchor.anchor_right=anchor.anchor_left
		anchor.anchor_top=0.27
		anchor.anchor_bottom=0.27
		ignore(anchor)
		arena_space.add_child(anchor)
		var combo:=PixelCombo.new()
		anchor.add_child(combo)
		combos.append(combo)
	word_center=CenterContainer.new()
	word_center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ignore(word_center)
	arena_space.add_child(word_center)
	var ceremony:=HBoxContainer.new()
	ceremony.add_theme_constant_override("separation",8)
	ignore(ceremony)
	word_center.add_child(ceremony)
	word=TextureRect.new()
	word.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ignore(word)
	ceremony.add_child(word)
	word.hide()
	result_panel=PixelPanel.new("dialog")
	ceremony.add_child(result_panel)
	result_name=FighterName.new(14,true)
	result_panel.add_child(result_name)
	result_panel.hide()
	var bottom:=HBoxContainer.new()
	bottom_bar=bottom
	ignore(bottom)
	column.add_child(bottom)
	_player_bottom(bottom,0)
	spacer(bottom)
	_player_bottom(bottom,1)
	var debug_margin:=margin(self)
	debug_margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	debug_margin.add_theme_constant_override("margin_top",60)
	var debug_column:=VBoxContainer.new()
	ignore(debug_column)
	debug_margin.add_child(debug_column)
	debug_label=text(debug_column,"",12)
	debug_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	debug_label.hide()
	_build_overlays()

func _player_top(parent: Node, player: int) -> void:
	var row:=HBoxContainer.new()
	row.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	ignore(row)
	parent.add_child(row)
	var portrait:=PortraitFrame.new()
	portrait.picture.flip_h=player==1
	var data:=VBoxContainer.new()
	data.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	ignore(data)
	if player==0:
		row.add_child(portrait)
		row.add_child(data)
	else:
		row.add_child(data)
		row.add_child(portrait)
	portraits.append(portrait)
	var label:=FighterName.new(12)
	data.add_child(label)
	label.align_right(player==1)
	names.append(label)
	var gauge:=PixelGauge.new("health",player==1)
	data.add_child(gauge)
	health.append(gauge)
	var sub:=text(data,"1P" if player==0 else "2P",12)
	sub.horizontal_alignment=HORIZONTAL_ALIGNMENT_LEFT if player==0 else HORIZONTAL_ALIGNMENT_RIGHT

func _player_bottom(parent: Node, player: int) -> void:
	var column:=VBoxContainer.new()
	column.custom_minimum_size.x=226
	ignore(column)
	parent.add_child(column)
	var row:=HBoxContainer.new()
	ignore(row)
	column.add_child(row)
	text(row,"能量")
	for i in range(3):
		var gauge:=PixelGauge.new("energy",player==1)
		gauge.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		row.add_child(gauge)
		if player==1:row.move_child(gauge,0)
		energy[player].append(gauge)
	var lower:=HBoxContainer.new()
	ignore(lower)
	column.add_child(lower)
	text(lower,"体力")
	var gauge:=PixelGauge.new("stamina",player==1)
	gauge.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	lower.add_child(gauge)
	if player==1:lower.move_child(gauge,0)
	stamina.append(gauge)
	var transform_hint:=text(column,"↓↓ + P 可变身",11)
	transform_hint.visible=false
	transform_hints.append(transform_hint)

func _dialog(title: String, width: int=240) -> PixelPanel:
	var center:=CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ignore(center)
	add_child(center)
	var panel:=PixelPanel.new("dialog")
	panel.custom_minimum_size.x=width
	center.add_child(panel)
	var column:=VBoxContainer.new()
	panel.add_child(column)
	text(column,title).horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	panel.hide()
	return panel

func _button(panel: PixelPanel, value: String, action: String) -> PixelButton:
	var button:=PixelButton.new(value)
	button.pressed.connect(func(): action_requested.emit(action))
	panel.get_child(0).add_child(button)
	return button

func _build_overlays() -> void:
	menu=_dialog("暂停")
	for item in [["继续","pause"],["再战","restart"],["招式表 / 操作提示","commands"],["训练设置","settings"],["返回主菜单","home"],["判定框开关 F1","boxes"]]: _button(menu,item[0],item[1])
	settings=_dialog("训练设置")
	for item in [["训练 / 对战电脑 F3","training"],["本地双人","local"],["对手行为 F5","dummy"],["训练角色 F6","select"],["播放回放 F4","replay"],["返回暂停菜单","back_pause"]]: _button(settings,item[0],item[1])
	_button(settings,"录制陪练（2P）","dummy_record")
	_button(settings,"循环播放陪练录制","dummy_playback")
	dummy_facing_button=_button(settings,"陪练方向：原始左右","dummy_facing")
	home=_dialog("奥特曼格斗进化Neo",288)
	for item in [["继续对战","pause"],["重新开始","restart"],["训练模式","training"],["返回暂停菜单","back_pause"]]: _button(home,item[0],item[1])
	selection=_dialog("训练角色选择")
	for item in [["","select_first"],["","select_second"],["开始对局","select_confirm"]]: selection_buttons.append(_button(selection,item[0],item[1]))
	for player in range(2):
		var name_view:=FighterName.new(12)
		selection_buttons[player].add_child(name_view)
		name_view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		for side in ["left","right"]:name_view.add_theme_constant_override("margin_"+side,8)
		selection_names.append(name_view)
	var command_center:=CenterContainer.new()
	command_center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ignore(command_center)
	add_child(command_center)
	commands=UfeCommandPages.new()
	command_center.add_child(commands)
	commands.hide()
	var toast_anchor:=CenterContainer.new()
	toast_anchor.anchor_left=0.5
	toast_anchor.anchor_right=0.5
	toast_anchor.anchor_top=0.82
	toast_anchor.anchor_bottom=0.82
	ignore(toast_anchor)
	add_child(toast_anchor)
	toast=Toast.new()
	toast_anchor.add_child(toast)

func close_overlays() -> void:
	for panel in [menu,commands,settings,home,selection]: panel.hide()

func show_pause(value: bool) -> void:
	close_overlays()
	menu.visible=value
	if value: (menu.get_child(0).get_child(1) as Button).grab_focus()

func update_match(sim: UfeMatchDirector, message: String, intro: int, training: bool) -> void:
	dummy_facing_button.text="陪练方向：随当前朝向" if dummy_relative else "陪练方向：原始左右"
	(settings.get_child(0).get_child(1) as Button).text="当前：训练 / 切换对战" if training else "当前：对战 / 切换训练"
	(settings.get_child(0).get_child(3) as Button).text="对手行为："+dummy_name
	for i in range(2):
		var f:=sim.fighters[i]
		names[i].set_fighter(f.definition.id,""," · 长名称布局审查" if review_long_text else "",f.form_id)
		if i==0:
			primary_display_id=f.definition.id
			primary_display_form=f.form_id
		portraits[i].set_fighter(f.definition.id,f.form_id)
		transform_hints[i].visible=UfeBattleTransform.can_transform(f) and not sim.finished
		health[i].update_value(float(f.stats.hp)/f.definition.max_health,1.0/60,sim.tick)
		stamina[i].update_value(float(f.stats.stamina)/1000,1.0/60,sim.tick)
		for j in range(3): energy[i][j].update_value((float(f.stats.energy)-j*1000)/1000,1.0/60,sim.tick)
		var combo: int=int(f.combat.combo)
		if combo!=previous_combo[i]: combo_age[i]=0
		combo_age[i]+=1
		previous_combo[i]=combo
		combos[i].text="%d 连击"%combo if combo>=2 else ""
		combos[i].pivot_offset=combos[i].size/2
		combos[i].scale=Vector2(2,2) if combo_age[i]<5 else Vector2.ONE
	# 结算占用顶部HUD区域；保持原生像素大小，给高个和举拳演出留出完整空间。
	top_bar.visible=not sim.finished
	var ceremony_parent: Node=self if sim.finished else arena_space
	if word_center.get_parent()!=ceremony_parent:
		word_center.reparent(ceremony_parent,false)
		word_center.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE if sim.finished else Control.PRESET_FULL_RECT)
		if sim.finished:
			word_center.offset_top=8
			word_center.offset_bottom=8
	result_panel.visible=sim.finished and sim.winner>=0
	if result_panel.visible:result_name.set_fighter(sim.fighters[sim.winner].definition.id,""," 获胜",sim.fighters[sim.winner].form_id)
	timer.text="%02d"%ceili(sim.remaining/60.0)
	var low: bool=(int(sim.fighters[0].stats.hp)>0 and int(sim.fighters[0].stats.hp)<=300) or (int(sim.fighters[1].stats.hp)>0 and int(sim.fighters[1].stats.hp)<=300)
	timer_frame.texture=theme.get_icon("timer_red" if low and sim.tick%30<15 else "timer","NeoKit")
	debug_label.visible=debug_visible
	debug_label.text=message+"\n"
	for i in range(2):
		var f:=sim.fighters[i]
		debug_label.text+="P%d %s %s 帧%d 连段%d\n输入 %s\n"%[i+1,f.state,f.move_id,f.move_tick,f.combat.combo," ".join(input_history[i])]
	var next: String="ready" if intro>24 else "fight" if intro>0 else "time_up" if sim.finished and sim.remaining<=0 else "draw" if sim.finished and sim.winner<0 else "victory" if sim.finished else ""
	if next!=word_key:
		word_key=next
		word_age=0
	word_age+=1
	word.visible=not next.is_empty() and (not sim.finished or word_age<240)
	if not next.is_empty():
		word.texture=theme.get_icon("word_"+next,"NeoKit")
		word.pivot_offset=word.size/2
		word.scale=Vector2(2,2) if not sim.finished and word_age<4 else Vector2.ONE
		word.modulate.a=minf(1,word_age/5.0)

func record_inputs(inputs: Array) -> void:
	for i in range(2):
		var frame: UfeInputFrame=inputs[i]
		var value:="%d:%d"%[UfeShotoMotionParser.to_numpad(frame.x,frame.y),frame.buttons]
		if input_history[i].is_empty() or input_history[i].back()!=value:
			input_history[i].append(value)
			if input_history[i].size()>12: input_history[i].pop_front()

func show_commands(data: UfeFighterDefinition, fighters: Array=[]) -> void:
	var was_visible:=commands.visible
	close_overlays()
	commands.set_fighter(data,primary_display_form if data.id==primary_display_id else "")
	commands.set_match_fighters(fighters)
	commands.visible=not was_visible
	if commands.visible and commands.match_choices.visible:commands.match_buttons[0].grab_focus()

func show_selection(ids: Array) -> void:
	close_overlays()
	for i in range(2):selection_names[i].set_fighter(str(ids[i]),"玩家%d："%[i+1])
	selection.show()

## 与世界共用同一Viewport坐标。容器延迟排版期间同时保守采用新最小高度，
## 绘制前由镜头再次读取最终布局；不把暂停/Ready等有意叠层当作障碍。
func battle_safe_rect() -> Rect2:
	var viewport_rect := get_viewport_rect()
	var safe := arena_space.get_global_rect().intersection(viewport_rect)
	var layout_ready := safe.has_area()
	var outer: MarginContainer = top_bar.get_parent().get_parent()
	var inner := outer.get_global_rect() if layout_ready else viewport_rect
	inner.position.y += outer.get_theme_constant("margin_top")
	inner.size.y -= outer.get_theme_constant("margin_top")+outer.get_theme_constant("margin_bottom")
	if not layout_ready:safe=inner
	var top := safe.position.y
	var bottom := safe.end.y
	if top_bar.visible:
		top = maxf(top,inner.position.y+top_bar.get_combined_minimum_size().y)
		if layout_ready:top=maxf(top,top_bar.get_global_rect().end.y)
	if bottom_bar.visible:
		bottom = minf(bottom,inner.end.y-bottom_bar.get_combined_minimum_size().y)
		if layout_ready:bottom=minf(bottom,bottom_bar.get_global_rect().position.y)
	for overlay in framing_top_overlays:
		if is_instance_valid(overlay) and overlay.is_visible_in_tree():
			var rect := overlay.get_global_rect()
			top = maxf(top,rect.position.y+maxf(rect.size.y,overlay.get_combined_minimum_size().y))
	if word_center.get_parent()==self and word_center.is_visible_in_tree():
		# 结算刚reparent时size还可能残留原arena高度；TOP_WIDE的目标高度是内容最小值。
		top = maxf(top,word_center.get_global_rect().position.y+word_center.get_combined_minimum_size().y)
	# 两个原生像素缓冲覆盖整数吸附及最近邻边缘；水平保留舞台边距。
	var left := maxf(viewport_rect.position.x+16,safe.position.x+2)
	var right := minf(viewport_rect.end.x-16,safe.end.x-2)
	return Rect2(left,top+2,maxf(1,right-left),maxf(1,bottom-top-4))
