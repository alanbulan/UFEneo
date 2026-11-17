class_name UfePlayerSettings
extends RefCounted
const PATH="user://settings.json"
static func values() -> Dictionary:
	var defaults: Dictionary={"sfx":0.8,"voice":0.8,"music":0.65,"fullscreen":false,"ai_difficulty":"normal"}
	if FileAccess.file_exists(PATH):
		var data=JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if data is Dictionary:defaults.merge(data,true)
	return defaults
static func apply(data: Dictionary, persist: bool=true) -> Error:
	# 各设置页只提交自己的字段，保留键位、音量与其它已有偏好。
	var combined := values()
	combined.merge(data,true)
	if persist:
		var file:=FileAccess.open(PATH,FileAccess.WRITE)
		if file==null:return FileAccess.get_open_error()
		file.store_string(JSON.stringify(combined))
		file.flush()
		var error:=file.get_error()
		if error!=OK:return error
	for key in ["sfx","voice","music"]:
		var bus:=AudioServer.get_bus_index("UFE_"+key)
		if bus>=0:
			var value:=clampf(float(combined.get(key,0.8)),0,1)
			AudioServer.set_bus_volume_db(bus,linear_to_db(maxf(0.0001,value)))
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if combined.get("fullscreen",false) else DisplayServer.WINDOW_MODE_WINDOWED)
	return OK
