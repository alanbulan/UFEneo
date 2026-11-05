class_name UfeSideAudio
extends Node
const PROJECTILE_EXPIRY = preload("res://presentation/projectile_expiry.gd")
# 受击恢复只换低姿图与轮廓，原crouch→guard的入态声键/时点不提前。
static func _state_entry_key(f: UfeFighter) -> String:
	return "crouch" if f.state=="crouch" and f.has_hit_crouch_guard_resume() else f.animation_key()

## 只读模拟/动作数据，音效、原剧发声和音乐分别走总线。
const MIX_HEADROOM_DB: float=-3.0
var voices: Array[AudioStreamPlayer]=[]
var character_players: Array[AudioStreamPlayer]=[]
var loops: Array[AudioStreamPlayer]=[]
var music: AudioStreamPlayer
var music_director: UfeBattleMusicDirector
var cache: Dictionary={}
var catalog: Dictionary={}
var cursor: int=0
var last_tick: int=-1
var last_states: Array=["",""]
var last_moves: Array=["",""]
var last_foot: Array=[-1,-1]
var last_frames: Array=["",""]
var context: String=""
var battle_index: int=0
var played: Array=[]
var ceremonial: String=""
var state_sounds: Dictionary={}
var character_states: Array=["",""]
var voice_cues: Dictionary={}
var preview_voice_cursor: int=0
var stopped: Array=[]
var suppressed: Array=[]
var projectile_audio:Dictionary={}
var flight_players:Array=[]
var flight_match:UfeMatchDirector
var flight_move_cache:Dictionary={}
var cue_match: UfeMatchDirector
var ending_voices: Dictionary={}
var intro_voices: Dictionary={}

func _ready() -> void:
	catalog=UfeContentDatabase.read_json("res://content/audio/runtime.json")
	var settings: Dictionary=UfeContentDatabase.read_json("res://content/settings/audio.json")
	state_sounds=UfeContentDatabase.read_json("res://content/audio/state_events.json")
	if FileAccess.file_exists("res://content/presentation/projectile_audio.json"):
		projectile_audio=UfeContentDatabase.read_json("res://content/presentation/projectile_audio.json")
	# 三类声音叠加后仍需PCM输出余量；独立于用户保存的各类音量。
	if AudioServer.get_bus_index("UFE_mix")<0:
		AudioServer.add_bus(1)
		AudioServer.set_bus_name(1,"UFE_mix")
	var mix_bus: int=AudioServer.get_bus_index("UFE_mix")
	AudioServer.set_bus_volume_db(mix_bus,MIX_HEADROOM_DB)
	AudioServer.set_bus_send(mix_bus,"Master")
	for key in ["sfx","voice","music"]:
		var bus: String="UFE_"+key
		if AudioServer.get_bus_index(bus)<0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count-1,bus)
		AudioServer.set_bus_volume_db(AudioServer.get_bus_index(bus),float(settings.get(key+"_db",0)))
		AudioServer.set_bus_send(AudioServer.get_bus_index(bus),"UFE_mix")
	AudioServer.set_bus_volume_db(0,float(settings.get("master_db",0)))
	for i in range(16):voices.append(_player("UFE_sfx"))
	for i in range(2):
		character_players.append(_player("UFE_voice"))
		loops.append(_player("UFE_sfx"))
	music=_player("UFE_music")
	music_director=UfeBattleMusicDirector.new()
	add_child(music_director)
	music_director.setup(self,music)
	set_context("battle")

func _player(bus: String) -> AudioStreamPlayer:
	var p:=AudioStreamPlayer.new()
	p.bus=bus
	add_child(p)
	return p

func stream(id: String) -> AudioStream:
	if not catalog.sounds.has(id):return null
	var item: Dictionary=catalog.sounds[id]
	if not cache.has(id):
		var source: AudioStream=load(item.path)
		if source==null:return null
		var value: AudioStream=source.duplicate()
		if value is AudioStreamWAV and bool(item.get("loop",false)):
			value.loop_mode=AudioStreamWAV.LOOP_FORWARD
			value.loop_begin=0
			value.loop_end=int(value.get_length()*value.mix_rate)
		cache[id]=value
	return cache[id]

func play_id(id: String,player: AudioStreamPlayer=null,owner: int=-1,owner_state: String="") -> void:
	var value:=stream(id)
	if value==null:return
	var usage: String=str(catalog.sounds[id].get("usage","character_voice" if catalog.sounds[id].get("kind","")=="voice" else "sfx"))
	if player==null and usage in ["character_voice","state_voice"]:
		# 旧VS音频接口只传ID；无归属的一次性展示发声按两名展示角色的调用顺序分配。
		if owner<0 and usage=="character_voice":
			owner=preview_voice_cursor%character_players.size()
			preview_voice_cursor+=1
			voice_cues.erase(owner)
		if owner<0 or owner>=character_players.size():return
		if usage=="state_voice" and owner_state.is_empty():return
		if str(voice_cues.get(owner,""))==id:return
		voice_cues[owner]=id
		player=character_players[owner]
		character_states[owner]=owner_state if usage=="state_voice" else ""
		ending_voices.erase(owner)
		intro_voices.erase(owner)
	if player==null:
		player=voices[cursor%voices.size()]
		cursor+=1
	player.stream=value
	player.volume_db=float(catalog.sounds.get(id,{}).get("gain_db",0))
	player.play()
	played.append({"tick":last_tick,"id":id,"bus":player.bus,"player":owner,"usage":usage,"owner_state":owner_state})

func cue(id: String,contact: bool=false,owner: int=-1,owner_state: String="") -> void:
	var key: String=("guard" if id=="block" else "hit_heavy" if id in ["heavy","special","throw"] else "hit_light") if contact else resolve(id)
	if key=="charge" and cue_match!=null and owner>=0 and owner<cue_match.fighters.size():
		if not UfeChargeEffectPolicy.allows_charge(cue_match.fighters[owner]):
			suppressed.append({"tick":last_tick,"id":key,"player":owner,"reason":"outside_q_charge_or_burst"})
			return
		# 通用Q声归属本人循环槽，离开Q当帧即可停止，不能遗留在一次性声池。
		play_id(key,loops[owner],owner,owner_state)
		return
	play_id(key,null,owner,owner_state)

func resolve(id: String) -> String:
	return id if catalog.sounds.has(id) else str(catalog.aliases.get(id,id))

func flight_sound(p:Dictionary) -> String:
	var binding:Variant=projectile_audio.get(str(p.get("effect","")),{})
	if binding is String:return binding
	return str(binding.get("moves",{}).get(str(p.get("move","")),""))

func _flight_keeps_contact(p:Dictionary) -> bool:
	var binding:Variant=projectile_audio.get(str(p.get("effect","")),{})
	return bool(p.get("beam",false)) and binding is Dictionary and bool(binding.get("keep_after_contact",false))

func _flight_sounds_for_move(f:UfeFighter) -> Array:
	var key:=f.definition.id+"/"+f.move_id
	if flight_move_cache.has(key):return flight_move_cache[key]
	var result:Array=[]
	var move:Dictionary=f.definition.moves.get(f.move_id,{})
	var shots:Array=[move.get("projectile",{})]
	for frame in move.get("frames",[]):
		shots.append_array(frame.get("shots",[]))
		if frame.has("counter_shot"):shots.append(frame.counter_shot)
	for shot in shots:
		var sound:=flight_sound({"effect":shot.get("effect",""),"move":f.move_id})
		if not sound.is_empty() and not result.has(sound):result.append(sound)
	flight_move_cache[key]=result
	return result

func _clear_flights() -> void:
	for row in flight_players:
		row.node.stop()
		row.node.queue_free()
	flight_players.clear()
	flight_match=null

func _sync_flights(sim:UfeMatchDirector) -> void:
	if not is_same(flight_match,sim):
		_clear_flights()
		flight_match=sim
	for i in range(flight_players.size()-1,-1,-1):
		var row:Dictionary=flight_players[i]
		var alive:bool=not sim.finished and (not bool(row.projectile.get("connected",false)) or _flight_keeps_contact(row.projectile)) and sim.projectiles.any(func(p):return is_same(p,row.projectile))
		if alive:
			row.node.volume_db=float(catalog.sounds.get(str(row.id),{}).get("gain_db",0))+linear_to_db(maxf(0.0001,float(row.projectile.get("end_alpha",1000))/1000.0))
			continue
		row.node.stop()
		row.node.queue_free()
		stopped.append({"tick":sim.tick,"player":int(row.projectile.owner),"id":row.id,"reason":"projectile_hit" if bool(row.projectile.get("connected",false)) else "projectile_end"})
		var binding:Variant=projectile_audio.get(str(row.projectile.get("effect","")),{})
		if binding is Dictionary and PROJECTILE_EXPIRY.eligible(row.projectile,binding,sim.finished):
			var expiry_sound:=str(binding.get("expiry_sound",""))
			if not expiry_sound.is_empty():play_id(expiry_sound,null,int(row.projectile.owner))
		flight_players.remove_at(i)
	if sim.finished:return
	for p in sim.projectiles:
		if (bool(p.get("connected",false)) and not _flight_keeps_contact(p)) or int(p.get("life",0))<=0:continue
		var sound:=flight_sound(p)
		if sound.is_empty() or flight_players.any(func(row):return is_same(row.projectile,p)):continue
		var player:=_player("UFE_sfx")
		flight_players.append({"projectile":p,"node":player,"id":sound})
		play_id(sound,player,int(p.owner))

func _remember_intro_voice(owner: int, fighter: String) -> void:
	var id: String=resolve(str(catalog.voices.get(fighter,{}).get("intro","")))
	var item: Dictionary=catalog.sounds.get(id,{})
	var policy: Variant=item.get("intro_tail",{})
	if not policy is Dictionary or str(policy.get("fighter_id",""))!=fighter:return
	if str(item.get("usage",""))!="character_voice" or bool(item.get("loop",false)):return
	var player: AudioStreamPlayer=character_players[owner]
	if str(voice_cues.get(owner,""))!=id or not player.playing or player.stream!=stream(id):return
	var seconds: float=player.stream.get_length()
	if not is_finite(seconds) or seconds<=0:return
	intro_voices[owner]={"id":id,"stream":player.stream,"fighter":fighter,"ticks":0,"limit":ceili(seconds*60.0)+12,"passive_states":policy.get("passive_states",[])}

func _sync_intro_voices(sim: UfeMatchDirector,intro_active: bool,result_source: UfeMatchDirector=null) -> void:
	for owner in intro_voices.keys():
		var row: Dictionary=intro_voices[owner]
		var player: AudioStreamPlayer=character_players[owner]
		if player.stream!=row.stream or not player.playing:
			intro_voices.erase(owner)
			continue
		var f:=sim.fighters[owner]
		var ended: bool=sim.finished or (result_source!=null and result_source.finished)
		var interrupted: bool=f.definition.id!=str(row.fighter) or ended or (not intro_active and f.state not in row.passive_states)
		if interrupted:
			player.stop()
			intro_voices.erase(owner)
			stopped.append({"tick":last_tick,"player":owner,"id":row.id,"reason":"intro_voice_interrupted"})
			continue
		row.ticks=int(row.ticks)+1
		if int(row.ticks)>int(row.limit):
			player.stop()
			intro_voices.erase(owner)
			stopped.append({"tick":last_tick,"player":owner,"id":row.id,"reason":"intro_voice_budget_exceeded"})

func _remember_ending_voice(owner: int, fighter: String, event: String) -> void:
	var id: String=resolve(str(catalog.voices.get(fighter,{}).get(event,"")))
	var item: Dictionary=catalog.sounds.get(id,{})
	if str(item.get("usage","")) not in ["character_voice","state_voice"] or bool(item.get("loop",false)):return
	var player: AudioStreamPlayer=character_players[owner]
	# 同一sync已调度的down会被voice_cues去重，也属于本次实际结算声。
	if str(voice_cues.get(owner,""))!=id or not player.playing or player.stream!=stream(id):return
	var seconds: float=player.stream.get_length()
	if not is_finite(seconds) or seconds<=0:return
	ending_voices[owner]={"id":id,"stream":player.stream,"ticks":0,"limit":ceili(seconds*60.0)+12}

func _sync_ending_voices() -> void:
	for owner in ending_voices.keys():
		var row: Dictionary=ending_voices[owner]
		var player: AudioStreamPlayer=character_players[owner]
		if player.stream!=row.stream or not player.playing:
			ending_voices.erase(owner)
			continue
		row.ticks=int(row.ticks)+1
		if int(row.ticks)>int(row.limit):
			player.stop()
			ending_voices.erase(owner)
			stopped.append({"tick":last_tick,"player":owner,"id":row.id,"reason":"ending_voice_budget_exceeded"})

func has_pending_ending_voice() -> bool:
	for owner in ending_voices.keys():
		var player: AudioStreamPlayer=character_players[owner]
		# Godot暂停人物声时playing为false；恢复前仍须保护这条已登记尾声。
		if player.stream==ending_voices[owner].stream and (player.playing or player.stream_paused):return true
		ending_voices.erase(owner)
	return false

func begin_finish(original: UfeMatchDirector, display: UfeMatchDirector) -> void:
	# 只把既有飞行声转接到同一弹体的只读副本，不在KO重新播放攻击声。
	if not is_same(flight_match,original):return
	var refs: Array=original.terminal_view.get("projectile_refs",[])
	for row in flight_players:
		for i in range(refs.size()):
			if is_same(refs[i],row.projectile) and i<display.projectiles.size():
				row.projectile=display.projectiles[i]
				break
	flight_match=display

func voice(index: int,fighter: String,event: String) -> void:
	if catalog.voices.has(fighter) and catalog.voices[fighter].has(event):cue(catalog.voices[fighter][event],false,index)

func configure_battle_music(ids: Array,stage: String,settings: Dictionary) -> void:
	if music_director==null:return
	music_director.configure(ids,stage,settings)
	if context=="battle":
		music_director.context=""
		music_director.set_context("battle")

func preview_music(id: String) -> void:
	context="preview"
	if music_director!=null:music_director.preview(id)

func set_context(value: String) -> void:
	if context==value and (music_director==null or music_director.context==value):return
	context=value
	if music_director!=null:music_director.set_context(value)

func suspend_battle() -> void:
	# 页面早退不再消费战斗sync；离页时显式停止战斗声，音乐由页面context接管。
	for player in voices+character_players+loops:player.stop()
	_clear_flights()
	voice_cues.clear()
	character_states=["",""]
	ending_voices.clear()
	intro_voices.clear()

func next_battle() -> void:
	battle_index+=1
	context="battle"
	if music_director!=null:music_director.start_round(battle_index)
	last_tick=-1
	last_states=["",""]
	last_moves=["",""]
	last_foot=[-1,-1]
	last_frames=["",""]
	ceremonial=""
	voice_cues.clear()
	preview_voice_cursor=0
	character_states=["",""]
	ending_voices.clear()
	intro_voices.clear()
	for p in loops+character_players:p.stop()
	_clear_flights()

func ceremony(sim: UfeMatchDirector,intro: int,_ending_tick: int) -> void:
	var value: String="intro" if intro>0 else "ending" if sim.finished else ""
	if value!=ceremonial:
		ceremonial=value
		if value=="intro":
			cue("entry")
			for i in range(2):
				var fighter: String=sim.fighters[i].definition.id
				voice(i,fighter,"intro" if catalog.voices.get(fighter,{}).has("intro") else "attack")
				_remember_intro_voice(i,fighter)
		elif value=="ending":
			ending_voices.clear()
			for i in range(2):
				var fighter: String=sim.fighters[i].definition.id
				var event: String="timeout" if sim.remaining<=0 else "victory" if i==sim.winner else "down"
				voice(i,fighter,event)
				_remember_ending_voice(i,fighter,event)

func sync(sim: UfeMatchDirector,frozen: bool,intro_active: bool=false,result_source: UfeMatchDirector=null) -> void:
	cue_match=sim
	if music_director!=null:music_director.sync(result_source if result_source!=null else sim,frozen,intro_active)
	for p in voices+character_players+loops:p.stream_paused=frozen
	for row in flight_players:row.node.stream_paused=frozen
	if frozen:return
	var new_tick:bool=sim.tick!=last_tick
	if new_tick:last_tick=sim.tick
	_sync_intro_voices(sim,intro_active,result_source)
	_sync_ending_voices()
	_sync_flights(sim)
	if not new_tick:return
	voice_cues.clear()
	for i in range(2):
		var f:=sim.fighters[i]
		var changed: bool=f.state!=last_states[i]
		if not str(character_states[i]).is_empty() and f.animation_key()!=str(character_states[i]):
			character_players[i].stop()
			stopped.append({"tick":last_tick,"player":i,"state":character_states[i],"reason":"state_exit"})
			character_states[i]=""
		if f.move_id!=last_moves[i] and not f.move_id.is_empty():voice(i,f.definition.id,"super" if f.move_id.begins_with("special") or UfeBattleTransform.is_command(f.move_id) or f.move_id=="super_special3" else "attack")
		if changed:
			var key: String=_state_entry_key(f)
			for e in state_sounds.get(f.definition.id,{}).get(key,[]):cue(str(e.id),false,i,key)
			if f.state in ["down","bounce"]:
				voice(i,f.definition.id,"down")
		if f.state=="walk":
			var foot: int=f.state_tick/16
			var foot_sound: String="step"
			var walk_key: String="walk_forward" if f.resolver.previous_x*f.facing>0 else "walk_back"
			var steps: Dictionary=catalog.get("footsteps",{}).get(f.definition.id,{}).get(walk_key,{})
			if not steps.is_empty():
				var cycle: int=int(steps.cycle_ticks)
				var phase: int=f.state_tick%cycle
				var contact: int=0
				for k in range(steps.contacts.size()):
					if phase>=int(steps.contacts[k]):contact=k
				foot=(f.state_tick/cycle)*steps.contacts.size()+contact
				foot_sound=str(steps.sounds[contact%steps.sounds.size()])
			if foot!=int(last_foot[i]):cue(foot_sound,false,i)
			last_foot[i]=foot
		else:last_foot[i]=-1
		var frame_key: String=f.animation_key()+":"+str(int(f.frame().get("sprite",-1)))
		if frame_key!=str(last_frames[i]):
			var cues: Array=catalog.get("frame_sounds",{}).get(f.definition.id,{}).get(f.animation_key(),{}).get(str(int(f.frame().get("sprite",-1))),[])
			for e in cues:cue(str(e.id),false,i,f.animation_key())
			# 数据声明的提拉声只在真实抓中后播放；空抓仍走动作，但不能发出抱起声。
			var move_audio: Dictionary=f.definition.moves.get(f.move_id,{}).get("audio",{})
			var captured:=sim.fighters[1-i]
			if move_audio.has("lift") and int(f.frame().get("sprite",-1))==int(move_audio.get("lift_sprite",-2)) and captured.state=="thrown" and int(captured.combat.thrower)==i:
				cue(str(move_audio.lift),false,i)
		last_frames[i]=frame_key
		var wanted: String=str(f.frame().get("audio_loop","charge" if f.state=="charge" else ""))
		if resolve(wanted)=="charge" and not UfeChargeEffectPolicy.allows_charge(f):wanted=""
		# 尚无audio对象的旧数据，按原有beam_loop弹体保留缺省声；新招式只读audio_loop。
		if not f.frame().has("audio_loop") and f.move_id.begins_with("special") and f.frame().has("beam_origin"):
			var legacy_move: Dictionary=f.definition.moves.get(f.move_id,{})
			if not legacy_move.has("audio") and legacy_move.get("frames",[]).any(func(frame):return frame.get("shots",[]).any(func(shot):return str(shot.get("effect",""))=="beam_loop")):
				wanted="beam_loop"
		# 显式声明飞行声的招式不再用人物攻击窗维持同一个声音。
		if wanted in _flight_sounds_for_move(f):wanted=""
		if wanted.is_empty():loops[i].stop()
		elif not loops[i].playing or loops[i].stream!=stream(wanted):play_id(wanted,loops[i])
		last_states[i]=f.state
		last_moves[i]=f.move_id
		if int(f.stats.hp)>0 and int(f.stats.hp)<=300 and sim.tick%60==0:
			var profile_key: String="audio_profile:"+f.definition.id
			if not catalog.has(profile_key):
				var profile_path: String="res://content/fighters/%s/profile.json"%f.definition.id
				catalog[profile_key]=UfeContentDatabase.read_json(profile_path) if FileAccess.file_exists(profile_path) else {}
			var profile: Dictionary=catalog[profile_key]
			# 旧档案没有音频标志时沿用其已有的彩色计时器说明；不改其它角色档案。
			var timer: Dictionary=profile.get("audio_timer",{"enabled":str(profile.get("text","")).contains("彩色计时器")})
			if bool(timer.get("enabled",false)):cue(str(timer.get("sound","timer")),false,i)
	# 只替换该受投者这一次撞地的通用land，不影响同tick的其他落地声。
	var custom_slam_victims: Dictionary={}
	for event in sim.events:
		if event.kind=="throw_slam":
			var slam:=resolve(data_contact_id(sim,event))
			if not slam.is_empty() and stream(slam)!=null:custom_slam_victims[1-int(event.player)]=true
	# 帧内发声在自动起手发声之后调度，精确帧事件拥有最后覆盖权。
	for event in sim.events:
		var owner:=int(event.get("player",-1))
		if str(event.kind).begins_with("capture_"):capture_event(sim,event,owner)
		if event.kind=="sound":
			if resolve(str(event.id))=="charge" and owner>=0 and owner<sim.fighters.size() and not UfeChargeEffectPolicy.allows_charge(sim.fighters[owner]):
				suppressed.append({"tick":last_tick,"id":"charge","player":owner,"reason":"outside_q_charge_or_burst"})
			elif resolve(str(event.id))=="land" and custom_slam_victims.has(owner):
				suppressed.append({"tick":last_tick,"id":"land","player":owner,"reason":"custom_throw_slam"})
			else:cue(str(event.id),false,owner,sim.fighters[owner].animation_key() if owner>=0 and owner<sim.fighters.size() else "")
		if event.kind in ["hit","block"]:
			var heavy: bool=int(event.get("feedback",{}).get("hitstop",0))>=8
			var custom:=data_contact_id(sim,event)
			if event.has("guard_sound"):cue(str(event.guard_sound),false,int(event.get("guarded_by",1-owner)))
			elif custom.is_empty():cue("block" if event.kind=="block" else "heavy" if heavy else "light",true,owner)
			else:cue(custom,false,owner)
			if event.kind=="hit":
				var victim:int=1-owner
				var victim_id:String=sim.fighters[victim].definition.id
				var down_id:String=resolve(str(catalog.voices.get(victim_id,{}).get("down","")))
				# 只保护本次sync确实已调度的倒地声；没有有效down的旧角色仍播hit。
				if down_id.is_empty() or str(voice_cues.get(victim,""))!=down_id:voice(victim,victim_id,"hit")
		if event.kind=="throw_slam":
			var slam:=data_contact_id(sim,event)
			if not slam.is_empty():cue(slam,false,owner)
		if event.kind in ["throw_tech","projectile_block","projectile_reflect","projectile_absorb"]:
			if event.has("guard_sound"):cue(str(event.guard_sound),false,owner)
			else:cue("block",true,owner)
		if event.kind=="weapon_return" and event.has("sound"):cue(str(event.sound),false,owner)
		if event.kind=="absorb_counter":cue("pulse",false,owner)
		if event.kind=="teleport":cue("dodge",false,owner)

func _exit_tree() -> void:
	for row in flight_players:
		if is_instance_valid(row.node):row.node.stop()

func data_contact_id(sim: UfeMatchDirector,event: Dictionary) -> String:
	var index:=int(event.get("player",-1))
	if index<0 or index>=sim.fighters.size():return ""
	var moves: Dictionary=sim.fighters[index].definition.moves
	var move: Dictionary=moves.get(str(event.get("move","")),{})
	return str(move.get("audio",{}).get(str(event.kind),""))

func capture_event(sim: UfeMatchDirector,event: Dictionary,owner: int) -> void:
	if owner<0 or owner>=sim.fighters.size():return
	var actor := sim.fighters[owner]
	var move: Dictionary=actor.definition.moves.get(str(event.get("move","")),{})
	if not move.has("capture"):return
	var key := str(event.kind)
	if key=="capture_phase":key+=":"+str(event.phase)
	elif key=="capture_fail":
		var reason := str(event.reason)
		key+=":guard" if reason=="guard" or reason in ["projectile_reflect","projectile_absorb","projectile_block"] else ":miss"
	var id := str(move.get("audio",{}).get(key,""))
	if not id.is_empty():cue(id,false,owner)
