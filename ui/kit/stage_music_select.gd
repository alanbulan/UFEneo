class_name UfeStageMusicSelect
extends VBoxContainer
signal confirmed(options: Dictionary)
signal back_requested
signal preview_requested(id: String)
var options: Dictionary={}
var fighter_ids: Array=[]
var form_ids: Array=[]
var volume_slider: PixelSlider
var back_button: PixelButton
var begin_button: PixelButton
var category_choice: PixelChoice
var stage_scroll: ScrollContainer
var stage_cards: Array=[]
var stage_names: Array=[]
var track_choice: PixelChoice
var selected_name: Label
var detail: Label
var dynamic_button: PixelButton
var save_status: Label

func _ready() -> void:
	options=UfePlayerSettings.values()
	options["battle_stage"]=UfeBattleStageCatalog.valid_id(str(options.get("battle_stage",UfeBattleStageCatalog.default_id())))
	options["battle_music"]=UfeBattleMusicCatalog.valid_choice(str(options.get("battle_music","auto")))
	options["dynamic_music"]=bool(options.get("dynamic_music",true))
	theme=PixelPanel.NEO_THEME
	add_theme_constant_override("separation",6)
	var body:=HBoxContainer.new();body.size_flags_vertical=Control.SIZE_EXPAND_FILL;body.add_theme_constant_override("separation",8);add_child(body)
	var stages:=VBoxContainer.new();stages.size_flags_horizontal=Control.SIZE_EXPAND_FILL;body.add_child(stages)
	selected_name=_label(stages,"",12)
	category_choice=PixelChoice.new();stages.add_child(category_choice)
	for category in [["all","全部场景"],["classic","经典地点"],["solar","八大行星＋冥王星"],["original","原创场景"]]:
		if category[0]!="all" and not UfeBattleStageCatalog.entries().any(func(stage: Dictionary):return str(stage.get("category","original"))==category[0]):continue
		category_choice.add_item(category[1]);category_choice.set_item_metadata(category_choice.item_count-1,category[0])
	category_choice.select(0);category_choice.item_selected.connect(_apply_category)
	stage_scroll=ScrollContainer.new();stage_scroll.custom_minimum_size.y=160;stage_scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;stage_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;stage_scroll.follow_focus=true;stages.add_child(stage_scroll)
	var grid:=GridContainer.new();grid.columns=3;grid.add_theme_constant_override("h_separation",4);grid.add_theme_constant_override("v_separation",4);stage_scroll.add_child(grid)
	for stage in UfeBattleStageCatalog.entries():
		var tile:=PixelButton.new("");tile.custom_minimum_size=Vector2(128,76);tile.size_flags_horizontal=Control.SIZE_EXPAND_FILL;tile.tooltip_text=str(stage.name);grid.add_child(tile)
		var inside:=VBoxContainer.new();inside.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);inside.offset_left=3;inside.offset_top=3;inside.offset_right=-3;inside.offset_bottom=-3;inside.mouse_filter=Control.MOUSE_FILTER_IGNORE;inside.add_theme_constant_override("separation",1);tile.add_child(inside)
		var picture:=TextureRect.new();picture.texture=load(str(stage.thumbnail));picture.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;picture.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_COVERED;picture.custom_minimum_size=Vector2(122,50);picture.mouse_filter=Control.MOUSE_FILTER_IGNORE;inside.add_child(picture)
		var name_label:=_label(inside,str(stage.name),10);name_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
		stage_cards.append(tile);stage_names.append(name_label)
		tile.pressed.connect(_choose_stage.bind(str(stage.id)))
	detail=_label(stages,"",10);detail.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;detail.custom_minimum_size.y=25
	var music:=VBoxContainer.new();music.custom_minimum_size.x=190;music.add_theme_constant_override("separation",5);body.add_child(music)
	_label(music,"战斗配乐",12)
	track_choice=PixelChoice.new();track_choice.custom_minimum_size.x=190;music.add_child(track_choice)
	for track in UfeBattleMusicCatalog.options():
		track_choice.add_item(str(track.name));var index: int=track_choice.item_count-1;track_choice.set_item_metadata(index,str(track.id))
		if str(track.id)==str(options.battle_music):track_choice.select(index)
	track_choice.item_selected.connect(_choose_music)
	var note:=_label(music,_auto_hint(),10);note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;note.custom_minimum_size=Vector2(190,66)
	dynamic_button=PixelButton.new("");music.add_child(dynamic_button);dynamic_button.pressed.connect(_toggle_dynamic)
	_label(music,"音乐音量",10)
	var slider:=PixelSlider.new();volume_slider=slider;slider.min_value=0;slider.max_value=100;slider.step=1;slider.value=float(options.get("music",0.65))*100;music.add_child(slider)
	slider.value_changed.connect(func(value: float):options.music=value/100.0;_persist())
	save_status=_label(music,"",10);save_status.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var row:=HBoxContainer.new();row.add_theme_constant_override("separation",6);add_child(row)
	var back:=PixelButton.new("返回选人");back_button=back;back.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(back);back.pressed.connect(func():back_requested.emit())
	var begin:=PixelButton.new("开始对战");begin_button=begin;begin.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(begin);begin.pressed.connect(func():_persist();confirmed.emit(options.duplicate(true)))
	_refresh()

func _label(parent: Node,value: String,font_size: int) -> Label:
	var label:=Label.new();label.text=value;label.add_theme_font_size_override("font_size",font_size);label.mouse_filter=Control.MOUSE_FILTER_IGNORE;parent.add_child(label);return label

func _choose_stage(id: String) -> void:
	options.battle_stage=id;_persist();_refresh()

func _choose_music(index: int) -> void:
	options.battle_music=str(track_choice.get_item_metadata(index));_persist()
	var selected: String=str(options.battle_music)
	preview_requested.emit(UfeBattleMusicCatalog.for_fighter(str(fighter_ids[0]),str(form_ids[0]) if not form_ids.is_empty() else "") if selected=="auto" and not fighter_ids.is_empty() else selected)

func _toggle_dynamic() -> void:
	options.dynamic_music=not bool(options.dynamic_music);_persist();_refresh()

func _persist() -> void:
	var error: Error=UfePlayerSettings.apply({"battle_stage":options.battle_stage,"battle_music":options.battle_music,"dynamic_music":options.dynamic_music,"music":options.get("music",0.65)})
	if save_status!=null:save_status.text="偏好已保存" if error==OK else "偏好保存失败，当前局仍可使用"

func _refresh() -> void:
	var current:=UfeBattleStageCatalog.get_stage(str(options.battle_stage))
	selected_name.text="场景 · "+str(current.get("name",""))
	detail.text=str(current.get("summary",""))
	dynamic_button.text="高光变化："+("开启" if bool(options.dynamic_music) else "关闭")
	var stages:=UfeBattleStageCatalog.entries()
	for i in range(stage_names.size()):
		stage_names[i].text=str(stages[i].name)+(" ✓" if str(stages[i].id)==str(options.battle_stage) else "")

func focus_current() -> void:
	var stages:=UfeBattleStageCatalog.entries()
	for i in range(stages.size()):
		if str(stages[i].id)==str(options.battle_stage):stage_cards[i].grab_focus();stage_scroll.ensure_control_visible(stage_cards[i]);return

func _apply_category(index: int) -> void:
	var selected: String=str(category_choice.get_item_metadata(index))
	var stages:=UfeBattleStageCatalog.entries()
	for i in range(stage_cards.size()):stage_cards[i].visible=selected=="all" or str(stages[i].get("category","original"))==selected

func _auto_hint() -> String:
	var lines: PackedStringArray=[]
	for i in range(fighter_ids.size()):
		var id:=str(fighter_ids[i])
		var form:=str(form_ids[i]) if i<form_ids.size() else ""
		var track:=UfeBattleMusicCatalog.track(UfeBattleMusicCatalog.for_fighter(id,form))
		lines.append("%dP：%s"%[i+1,str(track.get("name","通用配乐"))])
		lines.append(UfeBattleMusicCatalog.association(id,form))
	return "\n".join(lines)

func handle_key(key: int) -> bool:
	var focused:=get_viewport().gui_get_focus_owner()
	var stage_index: int=stage_cards.find(focused)
	if key in [KEY_A,KEY_D] and stage_index>=0:
		var next: int=stage_index
		for attempt in range(stage_cards.size()):
			next=posmod(next+(-1 if key==KEY_A else 1),stage_cards.size())
			if stage_cards[next].visible:break
		stage_cards[next].grab_focus()
		stage_scroll.ensure_control_visible(stage_cards[next])
		_choose_stage(str(UfeBattleStageCatalog.entries()[next].id))
		return true
	if key in [KEY_W,KEY_S]:
		var controls: Array=[category_choice]
		controls.append_array(stage_cards.filter(func(card: Control):return card.visible))
		controls.append_array([track_choice,dynamic_button,volume_slider,back_button,begin_button])
		var index: int=controls.find(focused)
		controls[posmod(index+(-1 if key==KEY_W else 1),controls.size())].grab_focus()
		return true
	if key in [KEY_A,KEY_D] and focused==volume_slider:
		volume_slider.value+=-5 if key==KEY_A else 5
		return true
	if key==KEY_J and focused is Button:
		focused.pressed.emit()
		return true
	return false
