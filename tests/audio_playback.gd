extends SceneTree
## 音频子系统可用性：清单可解析、各类可加载、总线可建、播放能启动。
## 只证明资源与 AudioServer 链路通，不评价听感。
var player: AudioStreamPlayer

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/audio/runtime.json"))
	var sounds: Dictionary = catalog.get("sounds", {})
	var kinds := {}
	for id in sounds:
		var kind := str(sounds[id].get("kind", "sfx"))
		kinds[kind] = int(kinds.get(kind, 0)) + 1
	# 每类抽样三个，实际 load 成 AudioStream。
	var loaded := 0
	var failed: Array[String] = []
	for kind in kinds:
		var picked := 0
		for id in sounds:
			if str(sounds[id].get("kind", "sfx")) != kind: continue
			if load(str(sounds[id].path)) is AudioStream: loaded += 1
			else: failed.append(id)
			picked += 1
			if picked >= 3: break
	# 总线：与 side_audio 相同的建法。
	if AudioServer.get_bus_index("UFE_mix") < 0:
		AudioServer.add_bus(1)
		AudioServer.set_bus_name(1, "UFE_mix")
	var bus_ok := AudioServer.get_bus_index("UFE_mix") >= 0
	# 实际播放一个音效，确认 AudioServer 接受。
	var first_id := ""
	for id in sounds:
		if str(sounds[id].get("kind", "")) == "sfx": first_id = id; break
	var played := false
	player = AudioStreamPlayer.new()
	root.add_child(player)
	if not first_id.is_empty():
		player.stream = load(str(sounds[first_id].path)) as AudioStream
		if player.stream != null:
			player.play()
			played = player.playing
	var result := {
		"sounds": sounds.size(),
		"kinds": kinds,
		"loaded_sample": loaded,
		"failed_sample": failed,
		"mix_bus": bus_ok,
		"playback_started": played,
		"mix_rate": AudioServer.get_mix_rate(),
		"output_latency": AudioServer.get_output_latency(),
	}
	# 停播并断开流引用；AudioServer 在独立线程按真实时间回收 playback。
	player.stop()
	player.stream = null
	await process_frame
	OS.delay_msec(120)
	player.free()
	player = null
	print("AUDIO_PLAYBACK " + JSON.stringify(result))
	quit(0 if (failed.is_empty() and bus_ok and played) else 1)
