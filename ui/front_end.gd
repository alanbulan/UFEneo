class_name UfeFrontEnd
extends Control
signal action_requested(action: String)
signal sound_requested(id: String, owner: int)
var page: String=""
var body: MarginContainer
var content: VBoxContainer
var model:=UfeRosterModel.new()
var grid: RosterGrid
var selections: Array=["ultraman","zetton"]
var confirmed: Array=[false,false]
var active_player: int=0
var previews: Array=[]
var names: Array=[]
var selection_hint: Label
var category: String="all"
var era: String="all"
var series: String="all"
var mode: String="cpu"
var vs_age: float=0
var toast: Toast
const PAGE_FADE_DURATION: float=0.18
const PAGE_FADE_STAGGER: float=0.02
const PAGE_FADE_MAX_DELAY: float=0.04
var transition_age: float=0.5
var transition_layers: Array[Dictionary]=[]
var settings_values: Dictionary
var long_names: bool=false
var archive_index: int=0
var archive_view: UfeArchivePanel
var focus_buttons: Array=[]
var form_choices: Array=[]
var selected_forms: Array=["ultraman__type_c","default"]
var stage_selector: UfeStageMusicSelect
var stage_options: Dictionary={}
var control_bindings: UfeControlBindings
func _ready() -> void:
	theme=PixelPanel.NEO_THEME
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(PixelStarfield.new())
	body=MarginContainer.new();body.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left","right","top","bottom"]:body.add_theme_constant_override("margin_"+side,10)
	add_child(body)
	content=VBoxContainer.new();body.add_child(content)
	var toast_center:=CenterContainer.new();toast_center.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE);toast_center.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(toast_center)
	toast=Toast.new();toast_center.add_child(toast)
	settings_values=UfePlayerSettings.values()
func label(parent: Node, value: String, font_size: int=12) -> Label:
	var result:=Label.new();result.text=value;result.add_theme_font_size_override("font_size",font_size);parent.add_child(result);return result
func button(parent: Node, value: String, action: Callable) -> PixelButton:
	var result:=PixelButton.new(value);parent.add_child(result);result.pressed.connect(action);return result
func stretch(parent: Node) -> Control:
	var result:=Control.new();result.size_flags_vertical=Control.SIZE_EXPAND_FILL;result.size_flags_horizontal=Control.SIZE_EXPAND_FILL;parent.add_child(result);return result
func open(next: String) -> void:
	_finish_page_transition()
	if is_instance_valid(control_bindings):control_bindings.cancel_capture()
	control_bindings=null
	page=next;visible=true
	for child in content.get_children():content.remove_child(child);child.queue_free()
	grid=null;previews=[];names=[];form_choices=[];archive_view=null;stage_selector=null
	focus_buttons=[]
	match page:
		"title":_title()
		"select":_select()
		"stage":_stage()
		"vs":_vs()
		"archive":_archive()
		"settings":_settings()
		"controls":_controls()
		"commands":
			var commands:=UfeCommandPages.new();content.add_child(commands);commands.set_fighter(UfeBattleFormCatalog.prepare(selections[0],mode=="training").definition)
			button(content,"返回",func():action_requested.emit("back"))
	for node in content.find_children("*","Button",true,false):
		if node is PixelButton:focus_buttons.append(node)
	if page!="select":_focus_first.call_deferred()
	_begin_page_transition()

func _begin_page_transition() -> void:
	transition_age=0.0
	# 仅淡入新页内容；星空和Toast不参与，避免整屏增亮。
	for child in content.get_children():
		var layer:=child as CanvasItem
		if layer==null or not layer.visible:continue
		transition_layers.append({"node":layer,"alpha":layer.modulate.a})
		layer.modulate.a=0.0

func _finish_page_transition() -> void:
	for state in transition_layers:
		var layer: CanvasItem=state.node
		if is_instance_valid(layer):layer.modulate.a=float(state.alpha)
	transition_layers.clear()

func is_transitioning() -> bool:
	return not transition_layers.is_empty()

func _notification(what: int) -> void:
	if what==NOTIFICATION_VISIBILITY_CHANGED and not is_visible_in_tree():
		_finish_page_transition()

func _focus_first() -> void:
	if page=="stage" and is_instance_valid(stage_selector):stage_selector.focus_current();return
	if page=="commands":
		var commands:=content.get_child(0) as UfeCommandPages
		commands.tabs.tabs[commands.page].grab_focus()
		return
	if not focus_buttons.is_empty() and is_instance_valid(focus_buttons[0]) and focus_buttons[0].is_inside_tree():focus_buttons[0].grab_focus()
func _title() -> void:
	var stage:=Control.new()
	stage.size_flags_vertical=Control.SIZE_EXPAND_FILL
	stage.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	content.add_child(stage)
	var cover:=preload("res://ui/kit/title_cover.gd").new()
	stage.add_child(cover)
	cover.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# 完整群像上方不盖大面板；底部使用统一像素按钮的紧凑横排。
	var menu:=HBoxContainer.new()
	menu.add_theme_constant_override("separation",3)
	content.add_child(menu)
	for item in [["对战电脑","cpu"],["本地双人","local"],["训练","training"]]:
		button(menu,item[0],func():mode=item[1];confirmed=[false,false];open("select"))
	button(menu,"档案",func():open("archive"))
	button(menu,"设置",func():open("settings"))
	button(menu,"退出",func():action_requested.emit("quit"))
	for option in menu.get_children():option.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	label(content,"WASD / 方向键选择　J / 小键盘1确认　Esc返回").horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
func _header(title: String) -> void:
	var row:=HBoxContainer.new();content.add_child(row)
	var heading_label:=label(row,title);heading_label.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	button(row,"返回",func():action_requested.emit("back"))
func _select() -> void:
	category="all";era="all";series="all";model.filter()
	_header("共同选人 · "+{"cpu":"对战电脑","local":"本地双人","training":"训练"}[mode])
	var tabs:=PixelTabBar.new();content.add_child(tabs);tabs.set_tabs(["全部","奥特曼","怪兽","宇宙人"])
	tabs.tab_changed.connect(func(index):category=["all","ultra","kaiju","alien"][index];_filter())
	var filters:=HBoxContainer.new();content.add_child(filters)
	label(filters,"年代")
	var eras:=PixelChoice.new();eras.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	for value in ["全部年代","昭和","平成","新生代","令和"]:eras.add_item(value)
	filters.add_child(eras);eras.item_selected.connect(func(index):era=["all","showa","heisei","newgen","reiwa"][index];_filter())
	label(filters,"作品")
	var works:=PixelChoice.new();works.size_flags_horizontal=Control.SIZE_EXPAND_FILL;works.custom_minimum_size.x=150;works.add_item("全部作品")
	for work in model.catalog.series:works.add_item(work.name);works.set_item_tooltip(works.item_count-1,work.name)
	filters.add_child(works);works.item_selected.connect(func(index):series="all" if index==0 else str(model.catalog.series[index-1].id);_filter())
	button(filters,"鼠标：切换玩家",func():active_player=1-active_player;_preview())
	var preview_row:=HBoxContainer.new();preview_row.custom_minimum_size.y=64;content.add_child(preview_row)
	for player in range(2):
		var art:=SlidePortrait.new();preview_row.add_child(art);previews.append(art)
		art.face_player(player)
		var col:=VBoxContainer.new();col.size_flags_horizontal=Control.SIZE_EXPAND_FILL;col.size_flags_stretch_ratio=1;preview_row.add_child(col)
		var name_view:=FighterName.new(12,true);name_view.size_flags_horizontal=Control.SIZE_EXPAND_FILL;col.add_child(name_view);names.append(name_view)
		var forms:=PixelChoice.new();col.add_child(forms);form_choices.append(forms)
		forms.item_selected.connect(func(index):
			selected_forms[player]=str(forms.get_item_metadata(index));confirmed[player]=false;_preview())
	grid=RosterGrid.new();content.add_child(grid);grid.selected_ids=selections;grid.bind(model)
	grid.picked.connect(func(index):choose(active_player,index))
	selection_hint=label(content,"")
	selection_hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	selection_hint.custom_minimum_size.y=24
	_preview()
func _filter() -> void:
	model.filter(category,era,series);grid.bind(model);_preview()
func choose(player: int,index: int) -> void:
	if index<0 or index>=model.filtered.size():return
	if selections[player]==model.filtered[index].id:return
	selections[player]=model.filtered[index].id;confirmed[player]=false
	var options: Array=UfeFighterDisplay.select_forms(str(selections[player]))
	selected_forms[player]=options[0].id if not options.is_empty() else "default"
	for form in options:
		if form.implemented:selected_forms[player]=form.id;break
	grid.selected_ids=selections;grid.reveal(index);_preview()
func confirm(player: int) -> void:
	if not UfeRosterModel.implemented(selections[player]):toast.show_message("该角色未实装");return
	var definition: Dictionary=UfeContentDatabase.read_json("res://content/fighters/%s/definition.json"%selections[player])
	if not definition.get("playable",true) and not definition.get("pilot_manual_ready",false):toast.show_message("该角色首批仍有未完成动作，暂未开放自由训练");return
	if not definition.get("playable",true) and not UfeBattleFormCatalog.battle_playable(str(selections[player])) and mode!="training":toast.show_message("试制角色目前仅开放训练模式");return
	var available: Array=UfeFighterDisplay.select_forms(str(selections[player])).filter(func(form):return form.id==selected_forms[player] and bool(form.implemented))
	if available.is_empty():toast.show_message("该形态未实装或已撤下");return
	confirmed[player]=true;_preview()
	if confirmed[0] and confirmed[1]:open("stage")
func _entry(id: String) -> Dictionary:
	for entry in model.entries:
		if entry.id==id:return entry
	return {}
func _preview() -> void:
	for player in range(previews.size()):
		var id:=str(selections[player])
		var options: Array=UfeFighterDisplay.select_forms(id)
		if not options.any(func(form):return form.id==selected_forms[player] and bool(form.implemented)):
			for form in options:
				if bool(form.implemented):
					selected_forms[player]=str(form.id)
					confirmed[player]=false
					break
		previews[player].show_fighter(id)
		names[player].set_fighter(id,"%dP "%[player+1],(" ✓" if confirmed[player] else "")+(" · 终极战斗形态 · 超长角色名称布局审查" if long_names else ""),str(selected_forms[player]))
		var choice: PixelChoice=form_choices[player]
		if str(choice.get_meta("fighter_id",""))!=id:
			choice.clear()
			for form in options:
				choice.add_item(str(form.name)+("" if form.implemented else "（未实装）"))
				var index:=choice.item_count-1
				choice.set_item_metadata(index,str(form.id))
				choice.set_item_identity(index,UfeFighterDisplay.resolved_id(id,str(form.id)))
				choice.set_item_disabled(index,not bool(form.implemented))
				if form.id==selected_forms[player]:choice.select(index)
			choice.set_meta("fighter_id",id)
	var offscreen:=""
	for player in range(2):
		var index:=model.index_of(selections[player])
		if index<0:offscreen+=" %dP在筛选外"%(player+1)
		else:
			@warning_ignore("integer_division")
			var player_row:=index/10
			@warning_ignore("integer_division")
			var first_row:=grid.scroll_vertical/RosterGrid.ROW_HEIGHT
			@warning_ignore("integer_division")
			var last_row:=(grid.scroll_vertical+grid.size.y)/RosterGrid.ROW_HEIGHT
			if player_row<first_row or player_row>last_row:offscreen+=" %dP在视区外"%(player+1)
	selection_hint.text="%d个对象 · 鼠标%dP · J / 小键盘1确认%s\nQ/E 或 小键盘7/9：战斗外形态 / 配色；未实装项不可选"%[model.filtered.size(),active_player+1,offscreen]

func _stage() -> void:
	_header("选择场景与配乐")
	stage_selector=UfeStageMusicSelect.new()
	stage_selector.fighter_ids=selections.duplicate()
	stage_selector.form_ids=selected_forms.duplicate()
	stage_selector.size_flags_vertical=Control.SIZE_EXPAND_FILL
	content.add_child(stage_selector)
	stage_selector.confirmed.connect(func(options: Dictionary):stage_options=options;vs_age=0;open("vs"))
	stage_selector.back_requested.connect(func():action_requested.emit("music_preview:select");open("select"))
	stage_selector.preview_requested.connect(func(id: String):action_requested.emit("music_preview:"+id))

func _vs() -> void:
	_header("即将开战")
	var versus:=PixelVS.new(selections)
	versus.sound_requested.connect(func(id,owner_index):sound_requested.emit(str(id),int(owner_index)))
	content.add_child(versus)
	var row:=HBoxContainer.new();content.add_child(row)
	for player in range(2):
		var slot:=HBoxContainer.new();slot.size_flags_horizontal=Control.SIZE_EXPAND_FILL;slot.alignment=BoxContainer.ALIGNMENT_CENTER;row.add_child(slot)
		var portrait:=PortraitFrame.new();portrait.picture.flip_h=player==1;slot.add_child(portrait);portrait.set_fighter(str(selections[player]),str(selected_forms[player]))
		var name_view:=FighterName.new(12,true);slot.add_child(name_view);name_view.set_fighter(str(selections[player]),"","",str(selected_forms[player]))

func _archive() -> void:
	_header("角色图鉴")
	archive_view=UfeArchivePanel.new()
	archive_view.selected_id="zetton" if archive_index==1 else "ultraman"
	content.add_child(archive_view)

func _settings() -> void:
	settings_values=UfePlayerSettings.values()
	_header("设置")
	var center:=CenterContainer.new();center.size_flags_vertical=Control.SIZE_EXPAND_FILL;content.add_child(center)
	var panel:=PixelPanel.new();panel.custom_minimum_size.x=420;center.add_child(panel)
	var col:=VBoxContainer.new();panel.add_child(col)
	for key in ["sfx","voice","music"]:
		var row:=HBoxContainer.new();col.add_child(row)
		label(row,{"sfx":"音效","voice":"语音","music":"音乐"}[key]).custom_minimum_size.x=60
		var slider:=PixelSlider.new();slider.min_value=0;slider.max_value=100;slider.step=1;slider.value=float(settings_values[key])*100;slider.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(slider)
		var number:=label(row,str(int(slider.value))+"%");number.custom_minimum_size.x=48
		slider.value_changed.connect(func(value):settings_values[key]=value/100.0;number.text=str(int(value))+"%";UfePlayerSettings.apply(settings_values))
	button(col,"全屏 / 窗口",func():settings_values.fullscreen=not settings_values.fullscreen;UfePlayerSettings.apply(settings_values))
	var ai_row:=HBoxContainer.new();col.add_child(ai_row);label(ai_row,"电脑难度")
	var difficulty:=PixelChoice.new();difficulty.size_flags_horizontal=Control.SIZE_EXPAND_FILL;ai_row.add_child(difficulty)
	for value in ["简单","普通","困难"]:difficulty.add_item(value)
	difficulty.select(["easy","normal","hard"].find(settings_values.get("ai_difficulty","normal")))
	difficulty.item_selected.connect(func(index):settings_values.ai_difficulty=["easy","normal","hard"][index];UfePlayerSettings.apply(settings_values))
	button(col,"键位设置 · 键盘 / 手柄",func():open("controls"))
	label(col,"音量与显示模式会自动保存。").horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER

func _controls() -> void:
	var row:=HBoxContainer.new();content.add_child(row)
	var heading:=label(row,"键位设置");heading.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	button(row,"返回设置",func():open("settings"))
	control_bindings=UfeControlBindings.new()
	control_bindings.size_flags_vertical=Control.SIZE_EXPAND_FILL
	content.add_child(control_bindings)

func capture_binding_input(event: InputEvent) -> bool:
	return is_visible_in_tree() and page=="controls" and is_instance_valid(control_bindings) and control_bindings.capture_event(event)

func handle_key(key: int) -> bool:
	if page=="stage" and is_instance_valid(stage_selector) and stage_selector.handle_key(key):return true
	if page!="select":
		focus_buttons=[]
		for node in content.find_children("*","Button",true,false):
			if node is PixelButton and node.is_visible_in_tree():focus_buttons.append(node)
		if key in [KEY_W,KEY_S]:
			var focus_index:=focus_buttons.find(get_viewport().gui_get_focus_owner())
			if not focus_buttons.is_empty():focus_buttons[posmod(focus_index+(-1 if key==KEY_W else 1),focus_buttons.size())].grab_focus()
			return true
		if key==KEY_J:
			var focused:=get_viewport().gui_get_focus_owner()
			if focused is Button:focused.pressed.emit()
			return true
		return false
	if key in [KEY_Q,KEY_E,KEY_KP_7,KEY_KP_9]:
		var p:=0 if key in [KEY_Q,KEY_E] else 1
		var choice: PixelChoice=form_choices[p]
		if choice.item_count<=1:return true
		var step: int=-1 if key in [KEY_Q,KEY_KP_7] else 1
		var next:=choice.selected
		for attempt in range(choice.item_count):
			next=posmod(next+step,choice.item_count)
			if not choice.is_item_disabled(next):break
		if next!=choice.selected and not choice.is_item_disabled(next):choice.select(next);choice.item_selected.emit(next)
		return true
	var player:=1 if key in [KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,KEY_KP_1] else 0
	var index:=model.index_of(selections[player]);index=maxi(0,index)
	match key:
		KEY_A,KEY_LEFT:index-=1
		KEY_D,KEY_RIGHT:index+=1
		KEY_W,KEY_UP:index-=10
		KEY_S,KEY_DOWN:index+=10
		KEY_J,KEY_KP_1:confirm(player);return true
		KEY_ENTER:confirm(0 if not confirmed[0] else 1);return true
		_:return false
	choose(player,clampi(index,0,model.filtered.size()-1));return true
func _process(delta: float) -> void:
	if not visible:
		_finish_page_transition()
		return
	if is_transitioning():
		transition_age+=delta
		for index in range(transition_layers.size()):
			var state: Dictionary=transition_layers[index]
			var layer: CanvasItem=state.node
			if not is_instance_valid(layer):continue
			var delay:=minf(float(index)*PAGE_FADE_STAGGER,PAGE_FADE_MAX_DELAY)
			var progress:=clampf((transition_age-delay)/PAGE_FADE_DURATION,0.0,1.0)
			layer.modulate.a=float(state.alpha)*(1.0-pow(1.0-progress,3.0))
		if transition_age>=PAGE_FADE_DURATION+PAGE_FADE_MAX_DELAY:
			_finish_page_transition()
	if page=="vs":
		vs_age+=delta
		if vs_age>=1.2:action_requested.emit("begin_match");hide();page="battle"
