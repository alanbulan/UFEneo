class_name UfeInputRouter
extends RefCounted
const ACTIONS := ["left","right","up","down","light","heavy","throw","guard","charge","special","crush","ranged","dodge","jump","transform","power_crush"]
const KEYS := [[KEY_A,KEY_D,KEY_W,KEY_S,KEY_J,KEY_K,KEY_L,KEY_U,KEY_Q,KEY_P,KEY_O,KEY_I,KEY_N,KEY_SPACE,KEY_E,KEY_G],
	[KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,KEY_KP_1,KEY_KP_2,KEY_KP_3,KEY_KP_4,KEY_KP_5,KEY_KP_6,KEY_KP_0,KEY_KP_7,KEY_KP_9,KEY_KP_ADD,KEY_KP_PERIOD,KEY_KP_8]]
const BUTTONS := [-1,-1,-1,-1,JOY_BUTTON_X,JOY_BUTTON_Y,JOY_BUTTON_A,-1,-1,-1,JOY_BUTTON_B,JOY_BUTTON_RIGHT_SHOULDER,JOY_BUTTON_LEFT_SHOULDER,-1,JOY_BUTTON_LEFT_STICK,JOY_BUTTON_RIGHT_STICK]
static var slots := UfeControllerSlots.new()
static var key_bindings: Dictionary = {}
static var joy_bindings: Dictionary = {}

static func default_key_binding(player: int, action: String) -> Dictionary:
	var index := ACTIONS.find(action)
	return {"keycode":int(KEYS[player][index]) if index>=0 else 0,"ctrl":false,"alt":false,"shift":false,"meta":false}

static func default_joy_binding(_player: int, action: String) -> Dictionary:
	var index := ACTIONS.find(action)
	if index<0:return {"kind":"none"}
	if index<4:
		return {"kind":"axis","axis":JOY_AXIS_LEFT_X if index<2 else JOY_AXIS_LEFT_Y,"value":-1 if index in [0,2] else 1,"dpad":[JOY_BUTTON_DPAD_LEFT,JOY_BUTTON_DPAD_RIGHT,JOY_BUTTON_DPAD_UP,JOY_BUTTON_DPAD_DOWN][index]}
	if index in [7,8]:return {"kind":"axis","axis":JOY_AXIS_TRIGGER_LEFT if index==7 else JOY_AXIS_TRIGGER_RIGHT,"value":1}
	if int(BUTTONS[index])>=0:return {"kind":"button","button":int(BUTTONS[index])}
	return {"kind":"none"}

static func get_key_binding(player: int, action: String) -> Dictionary:
	var name := "p%d_%s"%[player+1,action]
	var raw: Variant = key_bindings.get(name,default_key_binding(player,action))
	var result := default_key_binding(player,action)
	if raw is int or raw is float:result.keycode=maxi(0,int(raw))
	elif raw is Dictionary:
		result.keycode=maxi(0,int(raw.get("keycode",0)))
		for modifier in ["ctrl","alt","shift","meta"]:result[modifier]=bool(raw.get(modifier,false))
	return result

static func get_joy_binding(player: int, action: String) -> Dictionary:
	var name := "p%d_%s"%[player+1,action]
	var raw: Variant = joy_bindings.get(name,default_joy_binding(player,action))
	if raw is int or raw is float:return {"kind":"button","button":int(raw)} if int(raw)>=0 else {"kind":"none"}
	return raw.duplicate(true) if raw is Dictionary else default_joy_binding(player,action)

static func binding_label(player: int, action: String) -> String:
	var binding := get_key_binding(player,action)
	var code := int(binding.keycode)
	if code<=0:return "未绑定"
	var parts := PackedStringArray()
	for pair in [["ctrl","Ctrl"],["alt","Alt"],["shift","Shift"],["meta","Meta"]]:
		if bool(binding.get(pair[0],false)):parts.append(pair[1])
	var keypad := {KEY_KP_0:"小键盘0",KEY_KP_1:"小键盘1",KEY_KP_2:"小键盘2",KEY_KP_3:"小键盘3",KEY_KP_4:"小键盘4",KEY_KP_5:"小键盘5",KEY_KP_6:"小键盘6",KEY_KP_7:"小键盘7",KEY_KP_8:"小键盘8",KEY_KP_9:"小键盘9",KEY_KP_ADD:"小键盘+",KEY_KP_PERIOD:"小键盘."}
	parts.append(str(keypad.get(code,OS.get_keycode_string(code))))
	return "+".join(parts)

static func configure() -> void:
	configure_values(UfePlayerSettings.values())

static func configure_values(settings: Dictionary) -> void:
	key_bindings = settings.get("key_bindings",{}).duplicate(true)
	joy_bindings = settings.get("joy_bindings",{}).duplicate(true)
	if not InputMap.has_action("pause"):InputMap.add_action("pause")
	InputMap.action_erase_events("pause")
	var assigned := slots.update(Input.get_connected_joypads())
	for player in range(2):
		var device: int = int(assigned[player]) if int(assigned[player])>=0 else 1024+player
		for action in ACTIONS:
			var name := "p%d_%s"%[player+1,action]
			if not InputMap.has_action(name):InputMap.add_action(name,0.35)
			InputMap.action_erase_events(name)
			var binding := get_key_binding(player,action)
			if int(binding.keycode)>0:
				var key := InputEventKey.new()
				key.physical_keycode=int(binding.keycode) as Key
				key.ctrl_pressed=bool(binding.ctrl);key.alt_pressed=bool(binding.alt)
				key.shift_pressed=bool(binding.shift);key.meta_pressed=bool(binding.meta)
				InputMap.action_add_event(name,key)
			var pad := get_joy_binding(player,action)
			if str(pad.get("kind","none"))=="button":_add_pad_button(name,device,int(pad.button))
			elif str(pad.get("kind","none"))=="axis":
				var axis := InputEventJoypadMotion.new()
				axis.device=device;axis.axis=int(pad.axis) as JoyAxis;axis.axis_value=int(pad.value)
				InputMap.action_add_event(name,axis)
				if pad.has("dpad"):_add_pad_button(name,device,int(pad.dpad))
	for device in Input.get_connected_joypads():_add_pad_button("pause",device,JOY_BUTTON_START)

static func _add_pad_button(action: String, device: int, button: int) -> void:
	var event := InputEventJoypadButton.new()
	event.device=device;event.button_index=button as JoyButton
	InputMap.action_add_event(action,event)

static func _keyboard_actions(player: int) -> Dictionary:
	var winners: Dictionary = {}
	for owner in range(2):
		for action in ACTIONS:
			var binding := get_key_binding(owner,action)
			var code := int(binding.keycode)
			if code<=0 or not Input.is_physical_key_pressed(code):continue
			var score := 0
			var valid := true
			for pair in [["shift",KEY_SHIFT,1],["ctrl",KEY_CTRL,2],["alt",KEY_ALT,4],["meta",KEY_META,8]]:
				if bool(binding.get(pair[0],false)):
					if not Input.is_key_pressed(int(pair[1])):valid=false
					score+=16+int(pair[2])
			if not valid:continue
			var key := str(code)
			var candidate := {"player":owner,"action":action}
			if not winners.has(key) or score>int(winners[key].score):winners[key]={"score":score,"actions":[candidate]}
			elif score==int(winners[key].score):winners[key].actions.append(candidate)
	var result: Dictionary = {}
	for row in winners.values():
		for candidate in row.actions:
			if int(candidate.player)==player:result[str(candidate.action)]=true
	return result

static func _joy_held(player: int, action: String) -> bool:
	var device: int = int(slots.devices[player]) if int(slots.devices[player])>=0 else 1024+player
	var binding := get_joy_binding(player,action)
	if str(binding.get("kind","none"))=="button":return Input.is_joy_button_pressed(device,int(binding.button))
	if str(binding.get("kind","none"))=="axis":
		return Input.get_joy_axis(device,int(binding.axis))*int(binding.value)>0.35 or (binding.has("dpad") and Input.is_joy_button_pressed(device,int(binding.dpad)))
	return false

static func poll(player: int) -> UfeInputFrame:
	var keyboard := _keyboard_actions(player)
	var held: Dictionary = {}
	for action in ACTIONS:
		var binding := get_key_binding(player,action)
		# 同一主键带修饰时以最具体组合为准；保留原训练工具的action注入。
		var physical_held := int(binding.keycode)>0 and Input.is_physical_key_pressed(int(binding.keycode))
		var synthetic := not physical_held and Input.is_action_pressed("p%d_%s"%[player+1,action])
		held[action]=keyboard.has(action) or _joy_held(player,action) or synthetic
	var mask := 0
	for i in range(4,ACTIONS.size()):
		if bool(held[ACTIONS[i]]):mask |= 1 << (i-4)
	return UfeInputFrame.make(int(held.right)-int(held.left),int(held.up)-int(held.down),mask)
