class_name UfeControlBindings
extends VBoxContainer
## 正式键位设置；绑定只改变设备输入，不改变技能和模拟数据。
class CapturePopup extends PopupPanel:
	var editor: UfeControlBindings
	func _input(event: InputEvent) -> void:
		if editor!=null and editor.capture_event(event):get_viewport().set_input_as_handled()

const LABELS := {"left":"向左","right":"向右","up":"向上 / 斜向","down":"向下 / 斜向", "light":"轻击", "heavy":"重击", "throw":"投技", "guard":"防御", "charge":"蓄气", "special":"必杀", "crush":"超重击", "ranged":"远程技", "dodge":"闪避", "jump":"独立跳跃", "transform":"切换形态", "power_crush":"蓄力超重击"}
const RESERVED_KEYS := [KEY_ESCAPE,KEY_ENTER,KEY_KP_ENTER,KEY_F1,KEY_F2,KEY_F3,KEY_F4,KEY_F5,KEY_F6,KEY_R]
var player: int=0
var device_kind: String="keyboard"
var row_list: VBoxContainer
var row_scroll: ScrollContainer
var message: Label
var popup:=CapturePopup.new()
var popup_heading: Label
var popup_hint: Label
var capturing: bool=false
var capture_action: String=""
var ignored_keys: Array[int]=[]
var ignored_buttons: Array[int]=[]
var binding_buttons: Dictionary={}

func _ready() -> void:
	theme=PixelPanel.NEO_THEME
	add_theme_constant_override("separation",4)
	var options:=HBoxContainer.new();add_child(options)
	var players:=PixelChoice.new();players.custom_minimum_size.x=80;options.add_child(players)
	players.add_item("玩家一");players.add_item("玩家二")
	players.item_selected.connect(func(index):cancel_capture();player=index;_build_rows())
	var devices:=PixelChoice.new();devices.custom_minimum_size.x=100;options.add_child(devices)
	devices.add_item("键盘");devices.add_item("手柄")
	devices.item_selected.connect(func(index):cancel_capture();device_kind="keyboard" if index==0 else "joypad";_build_rows())
	var reset_group:=PixelButton.new("恢复本组默认");options.add_child(reset_group)
	reset_group.pressed.connect(func():reset_bindings(false))
	var reset_all:=PixelButton.new("恢复全部默认");options.add_child(reset_all)
	reset_all.pressed.connect(func():reset_bindings(true))
	message=Label.new();message.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;message.custom_minimum_size.y=32;add_child(message)
	message.text="选择动作右侧按键后输入，可搭配Ctrl / Shift / Alt；同一主键不能重复分配。斜向由两个方向键同时按。"
	row_scroll=ScrollContainer.new();row_scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL
	row_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;row_scroll.follow_focus=true;add_child(row_scroll)
	row_list=VBoxContainer.new();row_list.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row_list.add_theme_constant_override("separation",2);row_scroll.add_child(row_list)
	popup.editor=self;popup.theme=PixelPanel.NEO_THEME;popup.transient=true;popup.exclusive=true
	popup.popup_hide.connect(_popup_hidden);add_child(popup)
	var panel:=PixelPanel.new("dialog");popup.add_child(panel)
	var column:=VBoxContainer.new();column.custom_minimum_size=Vector2(370,160);panel.add_child(column)
	# 原生弹层首次测量时容器还未分配宽度；让换行文本先有真实行宽，
	# 避免按零宽计算出近千像素最小高度并被Window永久放大。
	popup_heading=Label.new();popup_heading.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	popup_heading.custom_minimum_size.x=370;popup_heading.size.x=370;column.add_child(popup_heading)
	popup_hint=Label.new();popup_hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	popup_hint.custom_minimum_size=Vector2(370,62);popup_hint.size.x=370;column.add_child(popup_hint)
	var cancel:=PixelButton.new("取消");column.add_child(cancel);cancel.pressed.connect(cancel_capture)
	_build_rows()

func _build_rows() -> void:
	for child in row_list.get_children():row_list.remove_child(child);child.queue_free()
	binding_buttons.clear()
	for action_value in UfeInputRouter.ACTIONS:
		var action:=str(action_value)
		var row:=HBoxContainer.new();row_list.add_child(row)
		var action_label:=Label.new();action_label.text=str(LABELS.get(action,action));action_label.custom_minimum_size.x=94;action_label.vertical_alignment=VERTICAL_ALIGNMENT_CENTER;row.add_child(action_label)
		var value:=PixelButton.new(_binding_text(action));value.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(value)
		value.pressed.connect(func():begin_capture(action))
		value.focus_entered.connect(func():row_scroll.ensure_control_visible(value))
		binding_buttons[action]=value
		var clear:=PixelButton.new("清空");row.add_child(clear);clear.pressed.connect(func():_store(action,{"keycode":0} if device_kind=="keyboard" else {"kind":"none"}))
		var restore:=PixelButton.new("默认");row.add_child(restore);restore.pressed.connect(func():_store(action,null))
	var help:=Label.new();help.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	help.text="默认1P：WASD方向，J/K/L攻投，U防，I远程，O超重，P必杀；Q蓄气、N闪避、E形态。\nI加↖/↑/↗/↘/↙各直出一个原搓招；正中与←/→/↓仍是普通远程。\nEnter、Esc、F1–F6、R及手柄Start保留给暂停、调试和重开。手柄默认□+△必杀、上方向跳跃。"
	row_list.add_child(help)

func is_capturing() -> bool:return capturing

func begin_capture(action: String) -> void:
	cancel_capture()
	capture_action=action;capturing=true
	ignored_keys.clear();ignored_buttons.clear()
	for key in [KEY_J,KEY_KP_1,KEY_ENTER,KEY_KP_ENTER]:
		if Input.is_physical_key_pressed(key):ignored_keys.append(key)
	for pad in Input.get_connected_joypads():
		if Input.is_joy_button_pressed(pad,JOY_BUTTON_A):ignored_buttons.append(JOY_BUTTON_A)
	popup_heading.text="%dP · %s · %s"%[player+1,"键盘" if device_kind=="keyboard" else "手柄",LABELS.get(action,action)]
	popup_hint.text="请按新的主键，可同时按Ctrl / Shift / Alt / Win。\nEsc取消；点击取消也可保留原绑定。" if device_kind=="keyboard" else "请按手柄按钮，或推动摇杆 / 扳机。\nEsc或手柄返回取消；Start保留为暂停。"
	# 原生弹层随正式640×360界面的整数倍率缩放。
	popup.content_scale_factor=maxf(1.0,get_screen_transform().get_scale().abs().x)
	popup.reset_size()
	popup.popup_centered()

func cancel_capture() -> void:
	if not capturing:return
	capturing=false;capture_action="";ignored_keys.clear();ignored_buttons.clear()
	if popup.visible:popup.hide()
	if is_instance_valid(message):message.text="已取消，原绑定保持。"

func _popup_hidden() -> void:
	if capturing:cancel_capture()

func _exit_tree() -> void:cancel_capture()

func _notification(what: int) -> void:
	if what==NOTIFICATION_VISIBILITY_CHANGED and capturing and not is_visible_in_tree():cancel_capture()

func capture_event(event: InputEvent) -> bool:
	if not capturing:return false
	if event is InputEventKey:
		var code:=int(event.physical_keycode if event.physical_keycode!=0 else event.keycode)
		if code in ignored_keys:
			if not event.pressed:ignored_keys.erase(code)
			return true
		if not event.pressed or event.echo:return true
		if code==KEY_ESCAPE:cancel_capture();return true
		if device_kind!="keyboard":return true
		if code in [KEY_CTRL,KEY_SHIFT,KEY_ALT,KEY_META]:return true
		if code in RESERVED_KEYS:
			popup_hint.text="这个键保留给游戏菜单或快捷操作，请换一个键。\nEsc取消，原绑定不会改变。";return true
		_attempt({"keycode":code,"ctrl":event.ctrl_pressed,"alt":event.alt_pressed,"shift":event.shift_pressed,"meta":event.meta_pressed})
		return true
	if event is InputEventJoypadButton:
		if int(event.button_index) in ignored_buttons:
			if not event.pressed:ignored_buttons.erase(int(event.button_index))
			return true
		if not event.pressed:return true
		if event.button_index==JOY_BUTTON_BACK:cancel_capture();return true
		if device_kind!="joypad":return true
		if event.button_index==JOY_BUTTON_START:
			popup_hint.text="Start保留为暂停，请换一个按钮。\nEsc或手柄返回取消。";return true
		_attempt({"kind":"button","button":int(event.button_index)});return true
	if event is InputEventJoypadMotion:
		if device_kind=="joypad" and absf(event.axis_value)>=0.75:
			_attempt({"kind":"axis","axis":int(event.axis),"value":-1 if event.axis_value<0 else 1})
		return true
	return false

static func _key_signature(value: Variant) -> Array:
	if value is int or value is float:return [int(value),false,false,false,false]
	if not value is Dictionary:return [0,false,false,false,false]
	return [int(value.get("keycode",0)),bool(value.get("ctrl",false)),bool(value.get("alt",false)),bool(value.get("shift",false)),bool(value.get("meta",false))]

static func _joy_signatures(value: Variant) -> Array:
	if value is int or value is float:return [["button",int(value)]] if int(value)>=0 else []
	if not value is Dictionary:return []
	if str(value.get("kind","none"))=="button":return [["button",int(value.get("button",-1))]]
	if str(value.get("kind","none"))!="axis":return []
	var result: Array=[["axis",int(value.get("axis",0)),int(value.get("value",1))]]
	if value.has("dpad"):result.append(["button",int(value.dpad)])
	return result

func _effective_binding(settings: Dictionary, kind: String, owner_index: int, action: String) -> Variant:
	var field:="key_bindings" if kind=="keyboard" else "joy_bindings"
	var bindings: Dictionary=settings.get(field,{})
	var fallback: Dictionary=UfeInputRouter.default_key_binding(owner_index,action) if kind=="keyboard" else UfeInputRouter.default_joy_binding(owner_index,action)
	return bindings.get("p%d_%s"%[owner_index+1,action],fallback)

func conflict(action: String, value: Variant, proposed: Dictionary={}) -> String:
	var settings: Dictionary=UfePlayerSettings.values() if proposed.is_empty() else proposed
	return _mapping_conflict(player,device_kind,action,value,settings)

func _mapping_conflict(owner_index: int, kind: String, action: String, value: Variant, settings: Dictionary) -> String:
	var owners: Array=[0,1] if kind=="keyboard" else [owner_index]
	for other_player in owners:
		for action_value in UfeInputRouter.ACTIONS:
			var other:=str(action_value)
			if other_player==owner_index and other==action:continue
			if kind=="keyboard":
				var incoming:=_key_signature(value)
				if int(incoming[0])==0:continue
				var existing:=_key_signature(_effective_binding(settings,kind,other_player,other))
				# 修饰组合也占用主键，避免普通同键在实战中被组合覆盖。
				if int(incoming[0])!=int(existing[0]):continue
				# 2P默认的上方向和独立跳跃共用↑，是原有有意重合。
				if owner_index==1 and other_player==1 and action in ["up","jump"] and other in ["up","jump"] and incoming==existing and incoming==[KEY_UP,false,false,false,false]:continue
			else:
				var incoming:=_joy_signatures(value);var existing:=_joy_signatures(_effective_binding(settings,kind,other_player,other))
				if not incoming.any(func(item):return item in existing):continue
			return "%dP %s"%[other_player+1,LABELS.get(other,other)]
	return ""

func _attempt(value: Variant) -> void:
	var used:=conflict(capture_action,value)
	if not used.is_empty():
		popup_hint.text="这个主键或按钮已用于%s，请换一个。\nEsc取消，原绑定不会改变。"%used;return
	var action:=capture_action
	capturing=false;capture_action="";popup.hide();ignored_keys.clear();ignored_buttons.clear()
	_store(action,value)

func _store(action: String, value: Variant) -> void:
	var field:="key_bindings" if device_kind=="keyboard" else "joy_bindings"
	var current:=UfePlayerSettings.values()
	var bindings: Dictionary=current.get(field,{}).duplicate(true)
	var key:="p%d_%s"%[player+1,action]
	if value==null:bindings.erase(key)
	else:bindings[key]=value
	current[field]=bindings
	var used:=conflict(action,_effective_binding(current,device_kind,player,action),current)
	if not used.is_empty():
		message.text="未保存：此键位与%s冲突，请先调整冲突项。"%used;return
	var error:=UfePlayerSettings.apply({field:bindings})
	if error!=OK:message.text="保存失败，请检查设置文件是否可写。";return
	UfeInputRouter.configure()
	message.text="已保存并立即生效：%dP %s。"%[player+1,LABELS.get(action,action)]
	_build_rows()
	_focus_action.call_deferred(action)

func reset_bindings(all_groups: bool) -> void:
	cancel_capture()
	var current:=UfePlayerSettings.values()
	var updates: Dictionary={}
	var fields: Array=["key_bindings","joy_bindings"] if all_groups else ["key_bindings" if device_kind=="keyboard" else "joy_bindings"]
	for field in fields:
		var bindings: Dictionary=current.get(field,{}).duplicate(true)
		for key in bindings.keys():
			if all_groups or str(key).begins_with("p%d_"%[player+1]):bindings.erase(key)
		updates[field]=bindings
	var proposed:=current.duplicate(true);proposed.merge(updates,true)
	var owners: Array=[0,1] if all_groups else [player]
	for field in fields:
		var kind: String="keyboard" if field=="key_bindings" else "joypad"
		for owner_index in owners:
			for action_value in UfeInputRouter.ACTIONS:
				var action:=str(action_value)
				var used:=_mapping_conflict(owner_index,kind,action,_effective_binding(proposed,kind,owner_index,action),proposed)
				if not used.is_empty():
					message.text="未重置：默认%dP %s会与%s冲突。可先调整对方，或恢复全部默认。"%[owner_index+1,LABELS.get(action,action),used];return
	var error:=UfePlayerSettings.apply(updates)
	if error!=OK:message.text="保存失败，未应用重置。";return
	UfeInputRouter.configure();_build_rows()
	message.text="已恢复全部默认键位，音量与显示设置保持。" if all_groups else "已恢复当前玩家及设备的默认键位。"

func _focus_action(action: String) -> void:
	var target: Button=binding_buttons.get(action)
	if is_instance_valid(target):target.grab_focus();row_scroll.ensure_control_visible(target)

func _binding_text(action: String) -> String:
	if device_kind=="keyboard":return UfeInputRouter.binding_label(player,action)
	var value: Variant=UfeInputRouter.get_joy_binding(player,action)
	if value is int or value is float:value={"kind":"button","button":int(value)} if int(value)>=0 else {"kind":"none"}
	if not value is Dictionary or str(value.get("kind","none"))=="none":return "未绑定（沿组合输入）" if action in ["special","jump"] else "未绑定"
	if value.kind=="button":return _joy_button_text(int(value.button))
	var axis:=int(value.get("axis",0));var side:=int(value.get("value",1))
	var axis_name: String="L2" if axis==JOY_AXIS_TRIGGER_LEFT else "R2" if axis==JOY_AXIS_TRIGGER_RIGHT else "左摇杆" if axis in [JOY_AXIS_LEFT_X,JOY_AXIS_LEFT_Y] else "右摇杆" if axis in [JOY_AXIS_RIGHT_X,JOY_AXIS_RIGHT_Y] else "轴%d"%axis
	if axis in [JOY_AXIS_LEFT_X,JOY_AXIS_RIGHT_X]:axis_name+="←" if side<0 else "→"
	elif axis in [JOY_AXIS_LEFT_Y,JOY_AXIS_RIGHT_Y]:axis_name+="↑" if side<0 else "↓"
	elif axis not in [JOY_AXIS_TRIGGER_LEFT,JOY_AXIS_TRIGGER_RIGHT]:axis_name+="−" if side<0 else "+"
	if value.has("dpad"):axis_name+=" / "+_joy_button_text(int(value.dpad))
	return axis_name

static func _joy_button_text(index: int) -> String:
	return str({JOY_BUTTON_X:"□ / X",JOY_BUTTON_Y:"△ / Y",JOY_BUTTON_A:"× / A",JOY_BUTTON_B:"○ / B",JOY_BUTTON_LEFT_SHOULDER:"L1",JOY_BUTTON_RIGHT_SHOULDER:"R1",JOY_BUTTON_LEFT_STICK:"L3",JOY_BUTTON_RIGHT_STICK:"R3",JOY_BUTTON_DPAD_LEFT:"十字左",JOY_BUTTON_DPAD_RIGHT:"十字右",JOY_BUTTON_DPAD_UP:"十字上",JOY_BUTTON_DPAD_DOWN:"十字下",JOY_BUTTON_START:"Start",JOY_BUTTON_BACK:"返回"}.get(index,"按钮%d"%[index+1]))
