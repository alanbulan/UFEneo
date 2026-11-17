class_name UfeBattleMusicDirector
extends Node
## 双声道播放器交叉淡入。只读战斗状态，绝不修改体力、伤害、硬直或模拟时间。
const SILENCE_DB: float=-80.0
const FADE_SECONDS: float=0.9
var host: Node
var players: Array[AudioStreamPlayer]=[]
var gains: Array[float]=[0.0,0.0]
var targets: Array[float]=[0.0,0.0]
var slot_ids: Array[String]=["",""]
var music_cache: Dictionary={}
var context: String=""
var choice: String="auto"
var dynamic_music: bool=true
var fighters: Array=[]
var stage_id: String=""
var current_id: String=""
var round_index: int=0
var last_tick: int=-1
var phase: String="normal"
var envelope: float=1.0
var envelope_target: float=1.0
var history: Array=[]

func setup(audio_host: Node,primary: AudioStreamPlayer) -> void:
	host=audio_host
	players.append(primary)
	var secondary:=AudioStreamPlayer.new();secondary.bus="UFE_music";add_child(secondary);players.append(secondary)
	for player in players:player.stop();player.volume_db=SILENCE_DB

func configure(ids: Array,selected_stage: String,settings: Dictionary) -> void:
	fighters=ids.duplicate();stage_id=selected_stage
	choice=UfeBattleMusicCatalog.valid_choice(str(settings.get("battle_music","auto")))
	dynamic_music=bool(settings.get("dynamic_music",true))

func _stream(id: String) -> AudioStream:
	if music_cache.has(id):return music_cache[id] as AudioStream
	var track:=UfeBattleMusicCatalog.track(id)
	var result: AudioStream
	if track.has("path"):
		result=load(str(track.path)) as AudioStream
		if result!=null:
			result=result.duplicate()
			if result is AudioStreamOggVorbis:result.loop=true
			elif result is AudioStreamWAV:
				result.loop_mode=AudioStreamWAV.LOOP_FORWARD;result.loop_begin=0;result.loop_end=roundi(result.get_length()*result.mix_rate)
	elif host!=null:result=host.call("stream",id) as AudioStream
	if result!=null:music_cache[id]=result
	return result

func _base_track() -> String:
	if choice=="off":return ""
	if choice=="random":
		var options:=UfeBattleMusicCatalog.tracks().filter(func(item: Dictionary):return bool(item.get("selectable",true)))
		return str(options[randi()%options.size()].id) if not options.is_empty() else "battle_1"
	if choice!="auto":return choice
	if fighters.is_empty():return str(UfeBattleMusicCatalog.data().get("fallback","battle_1"))
	var owner_index: int=maxi(0,round_index-1)%fighters.size()
	return UfeBattleMusicCatalog.for_fighter(str(fighters[owner_index]))

func set_context(value: String) -> void:
	if context==value:return
	if value=="paused":
		context="paused";phase="paused";envelope_target=0.65 if dynamic_music else 1.0
		return
	if context=="paused" and value=="battle":
		context="battle";phase="normal";envelope_target=1.0;last_tick=-1
		return
	context=value;phase="normal";envelope_target=1.0
	_request(_base_track() if value=="battle" else "select" if value=="select" else "menu",-1,"context:"+value)

func start_round(index: int) -> void:
	round_index=index;last_tick=-1
	phase="intro";envelope=0.75;envelope_target=0.75
	for i in range(players.size()):players[i].stop();gains[i]=0.0;targets[i]=0.0;slot_ids[i]=""
	current_id="";context="battle"
	_request(_base_track(),0,"round_start")

func preview(id: String) -> void:
	context="preview";phase="preview";envelope_target=1.0
	var selected: String=id
	if id=="off":selected=""
	elif id=="random":
		var options:=UfeBattleMusicCatalog.tracks().filter(func(item: Dictionary):return bool(item.get("selectable",true)))
		selected=str(options[randi()%options.size()].id) if not options.is_empty() else "select"
	elif id=="auto":selected=_base_track()
	elif id!="select" and UfeBattleMusicCatalog.track(id).is_empty():selected="select"
	_request(selected,-1,"manual_preview")

func _request(id: String,tick: int,reason: String) -> void:
	if id==current_id and not id.is_empty():return
	if id.is_empty():
		current_id="";targets=[0.0,0.0];history.append({"tick":tick,"id":"","reason":reason});return
	var found: int=slot_ids.find(id)
	if found>=0 and players[found].playing:
		for i in range(targets.size()):targets[i]=1.0 if i==found else 0.0
		current_id=id;history.append({"tick":tick,"id":id,"reason":reason});return
	var stream:=_stream(id)
	if stream==null:
		history.append({"tick":tick,"id":id,"reason":"missing_track","requested_reason":reason});return
	# 快速连续选曲时复用更小声的一槽，保留当前主声，避免硬切正在主响的旧槽。
	var destination: int=0 if gains[0]<=gains[1] else 1
	players[destination].stop();players[destination].stream=stream
	players[destination].volume_db=SILENCE_DB;gains[destination]=0.0;players[destination].play()
	slot_ids[destination]=id
	for i in range(targets.size()):targets[i]=1.0 if i==destination else 0.0
	current_id=id;history.append({"tick":tick,"id":id,"reason":reason})

func sync(sim: UfeMatchDirector,frozen: bool,intro: bool=false) -> void:
	if context!="battle" or sim==null:return
	if frozen:
		phase="paused";envelope_target=0.65 if dynamic_music else 1.0
		return
	if sim.tick==last_tick:return
	last_tick=sim.tick
	if not dynamic_music:
		phase="normal";envelope_target=1.0;return
	if sim.finished:
		phase="ko";envelope_target=0.36;return
	if intro:
		phase="intro";envelope_target=0.72;return
	var super_owner: int=-1
	for i in range(sim.fighters.size()):
		var f:=sim.fighters[i]
		if f.move_id.begins_with("special") or f.move_id in ["super_special3","air_special"]:
			super_owner=i;break
	if super_owner>=0:
		# 必杀只压低背景音量突出技能声，不切换曲目：一首对战曲被必杀反复劫持
		# 会让整场音乐碎片化，也让非本人主题的角色每次必杀都跳曲。
		phase="super";envelope_target=0.55
		return
	var critical: bool=sim.fighters.any(func(f: UfeFighter):return int(f.stats.hp)>0 and int(f.stats.hp)*4<=f.definition.max_health)
	var clutch: bool=critical or sim.remaining<=900
	phase="clutch" if clutch else "normal"
	envelope_target=1.08 if clutch else 1.0
	var voices: Variant=host.get("character_players") if host!=null else null
	if voices is Array and voices.any(func(player: AudioStreamPlayer):return player.playing):envelope_target=minf(envelope_target,0.68)

func _process(delta: float) -> void:
	if players.size()!=2:return
	var elapsed: float=minf(delta,0.1)
	envelope=move_toward(envelope,envelope_target,elapsed*1.8)
	for i in range(players.size()):
		gains[i]=move_toward(gains[i],targets[i],elapsed/FADE_SECONDS)
		players[i].volume_db=linear_to_db(maxf(0.0001,gains[i]*envelope))
		if targets[i]==0.0 and gains[i]<=0.0001 and players[i].playing:
			players[i].stop();slot_ids[i]=""

func stop_all() -> void:
	for i in range(players.size()):players[i].stop();gains[i]=0.0;targets[i]=0.0;slot_ids[i]=""
	current_id="";context="";phase="normal";envelope=1.0;envelope_target=1.0

## 退出时停播并释放持有的音乐流，避免音频线程仍引用时留下 AudioStream 泄漏。
func release_streams() -> void:
	stop_all()
	for player in players:player.stream=null
	music_cache.clear()

func snapshot() -> Dictionary:
	return {"context":context,"choice":choice,"track":current_id,"dynamic":dynamic_music,"phase":phase,"gains":gains.duplicate(),"targets":targets.duplicate(),"envelope":envelope,"slots":slot_ids.duplicate(),"round":round_index,"positions":players.map(func(player: AudioStreamPlayer):return player.get_playback_position()),"playing":players.map(func(player: AudioStreamPlayer):return player.playing)}
