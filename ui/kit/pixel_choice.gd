class_name PixelChoice
extends Button
## 保留选项接口；像素组件弹层允许每行按本人/形态使用主题颜色。
class ChoicePopup extends PopupPanel:
	func _input(event: InputEvent) -> void:
		if visible and PixelChoice.handle_active_input(event):get_viewport().set_input_as_handled()

signal item_selected(index: int)
static var active_choice: PixelChoice
static var dismissed_pointer_position: Vector2i
static var wait_for_pointer_motion: bool=false
var caption: Label
var selected: int=-1
var item_count: int:
	get:return items.size()
var items: Array[Dictionary]=[]
var popup:=ChoicePopup.new()
var options:=VBoxContainer.new()
var scroll:=ScrollContainer.new()
var popup_index: int=-1

func _init() -> void:
	theme=PixelPanel.NEO_THEME
	theme_type_variation="PixelChoice"
	custom_minimum_size=Vector2(92,28)
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	clip_text=true
	text_overrun_behavior=TextServer.OVERRUN_NO_TRIMMING
	pressed.connect(show_popup)

func _ready() -> void:
	caption=Label.new()
	caption.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	PixelTextBounds.layout(self,caption)
	caption.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
	caption.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	caption.mouse_filter=Control.MOUSE_FILTER_IGNORE
	caption.add_theme_constant_override("outline_size",2)
	caption.add_theme_color_override("font_outline_color",Color("101827"))
	add_child(caption)
	for state in ["font_color","font_hover_color","font_pressed_color","font_focus_color","font_disabled_color","font_hover_pressed_color"]:add_theme_color_override(state,Color.TRANSPARENT)
	popup.theme=PixelPanel.NEO_THEME
	popup.popup_hide.connect(_popup_hidden)
	add_child(popup)
	scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus=true
	popup.add_child(scroll)
	options.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	options.add_theme_constant_override("separation",0)
	scroll.add_child(options)
	_refresh_caption()

func add_item(label: String, id: int=-1) -> void:
	items.append({"text":label,"id":id if id>=0 else items.size(),"metadata":null,"disabled":false,"tooltip":"","identity":""})
	if selected<0:select(0)

func clear() -> void:
	popup.hide()
	items.clear()
	selected=-1
	_refresh_caption()

func select(index: int) -> void:
	selected=index if index>=0 and index<items.size() else -1
	_refresh_caption()

func get_item_text(index: int) -> String:return str(items[index].text)
func get_item_metadata(index: int) -> Variant:return items[index].metadata
func get_item_id(index: int) -> int:return int(items[index].id)
func get_selected_id() -> int:return get_item_id(selected) if selected>=0 else -1
func get_item_index(id: int) -> int:
	for index in range(items.size()):
		if get_item_id(index)==id:return index
	return -1
func set_item_text(index: int, value: String) -> void:
	items[index].text=value
	if index==selected:_refresh_caption()
func is_item_disabled(index: int) -> bool:return bool(items[index].disabled)
func set_item_metadata(index: int, value: Variant) -> void:items[index].metadata=value
func set_item_tooltip(index: int, value: String) -> void:items[index].tooltip=value
func set_item_disabled(index: int, value: bool) -> void:items[index].disabled=value
func set_item_identity(index: int, id: String) -> void:
	items[index].identity=id
	if index==selected:_refresh_caption()

func get_popup() -> PopupPanel:return popup

func _popup_hidden() -> void:
	if active_choice==self:active_choice=null
	# 原生弹层消失会让静止指针重新进入下方控件，不能因此覆盖刚确认的身份。
	dismissed_pointer_position=DisplayServer.mouse_get_position()
	wait_for_pointer_motion=true
	if is_visible_in_tree():grab_focus()

func _exit_tree() -> void:
	if active_choice==self:active_choice=null

static func allows_hover_selection() -> bool:
	if is_instance_valid(active_choice) and active_choice.popup.visible:return false
	if wait_for_pointer_motion:
		if DisplayServer.mouse_get_position()==dismissed_pointer_position:return false
		wait_for_pointer_motion=false
	return true

static func handle_active_input(event: InputEvent) -> bool:
	if not is_instance_valid(active_choice) or not active_choice.popup.visible:return false
	if not event is InputEventKey and not event is InputEventJoypadButton and not event is InputEventJoypadMotion:return false
	if event.is_action_pressed("ui_cancel") or (event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE) or (event is InputEventJoypadButton and event.pressed and event.button_index==JOY_BUTTON_B):
		active_choice.popup.hide()
	elif event.is_action_pressed("ui_up") or (event is InputEventKey and event.pressed and event.keycode==KEY_W) or (event is InputEventJoypadButton and event.pressed and event.button_index==JOY_BUTTON_DPAD_UP):
		active_choice._move_popup(-1)
	elif event.is_action_pressed("ui_down") or (event is InputEventKey and event.pressed and event.keycode==KEY_S) or (event is InputEventJoypadButton and event.pressed and event.button_index==JOY_BUTTON_DPAD_DOWN):
		active_choice._move_popup(1)
	elif event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and event.keycode in [KEY_J,KEY_KP_1]) or (event is InputEventJoypadButton and event.pressed and event.button_index==JOY_BUTTON_A):
		active_choice._activate_popup(active_choice.popup_index)
	return true

func _move_popup(step: int) -> void:
	for attempt in range(items.size()):
		popup_index=posmod(popup_index+step,items.size())
		if not is_item_disabled(popup_index):
			var button:=options.get_child(popup_index) as Button
			button.grab_focus()
			scroll.ensure_control_visible(button)
			return

func _activate_popup(index: int) -> void:
	if index<0 or index>=items.size() or is_item_disabled(index):return
	select(index)
	popup.hide()
	item_selected.emit(index)

func show_popup() -> void:
	if disabled or items.is_empty():return
	if is_instance_valid(active_choice) and active_choice!=self:active_choice.popup.hide()
	active_choice=self
	popup_index=selected
	for child in options.get_children():options.remove_child(child);child.queue_free()
	var focus_item: Button
	for index in range(items.size()):
		var button:=PixelButton.new(get_item_text(index))
		button.alignment=HORIZONTAL_ALIGNMENT_LEFT
		button.disabled=is_item_disabled(index)
		button.tooltip_text=str(items[index].tooltip)
		button.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		options.add_child(button)
		button.caption.add_theme_color_override("font_color",UfeFighterDisplay.name_color(str(items[index].identity)))
		button.pressed.connect(func():_activate_popup(index))
		button.focus_entered.connect(func():popup_index=index)
		if index==selected and not button.disabled:focus_item=button
	var factor:=get_screen_transform().get_scale().abs()
	popup.content_scale_factor=maxf(1.0,factor.x)
	var minimum:=options.get_combined_minimum_size()
	scroll.custom_minimum_size=Vector2(maxf(size.x,minimum.x),minf(220.0,minimum.y))
	popup.reset_size()
	var screen_point:=get_screen_transform()*Vector2(0,size.y)
	# get_screen_transform在原生Window下已含桌面位置，嵌入Window下为根窗口坐标。
	popup.position=Vector2i(screen_point)
	popup.popup()
	if focus_item!=null:focus_item.grab_focus()

func _process(_delta: float) -> void:_refresh_caption()

func _refresh_caption() -> void:
	if caption==null:return
	caption.text=get_item_text(selected) if selected>=0 else ""
	caption.add_theme_color_override("font_color",UfeFighterDisplay.name_color(str(items[selected].identity)) if selected>=0 else UfeFighterDisplay.name_color(""))
	var margin:=PixelTextBounds.insets(self)
	custom_minimum_size.y=maxf(28,caption.get_minimum_size().y+margin.y+margin.w+4)
