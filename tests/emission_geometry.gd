extends SceneTree
## 验证裁片、偏心锚点、左右翻转及整数比例的几何关系，不评价画面。
var errors:Array=[]
func check(ok:bool,message:String) -> void:
	if not ok:errors.append(message)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var clips:Dictionary=UfeContentDatabase.read_json("res://content/presentation/phase3_projectiles.json")
	for key in ["beam_start","seven_fx_wide_start","jack_short_start","ace_timer_shot_start","taro_storium_body","leo_lion_start"]:
		var clip:Dictionary=clips[key]
		for r in clip.rects:
			for facing in [1,-1]:
				for centered in [true,false]:
					for factor in [1,2,3]:
						var sprite:=Sprite2D.new()
						sprite.texture=load(clip.texture)
						sprite.region_enabled=true
						sprite.region_rect=Rect2(r[0],r[1],r[2],r[3])
						sprite.centered=centered
						sprite.scale=Vector2(factor,factor)
						UfeEffectGeometry.apply_anchor(sprite,clip,r,facing)
						var pivot:Vector2=Vector2(clip.anchor[0],clip.anchor[1])
						if facing<0:pivot.x=float(r[2])-pivot.x
						check(((sprite.get_rect().position+pivot)*sprite.scale).length()<0.001,"锚点变换错位 "+key)
						sprite.free()
	# 无anchor的既有居中弹体保持原位置；第一次读取带偏心anchor后不能污染复用槽。
	var probe:=Sprite2D.new()
	UfeEffectGeometry.apply_anchor(probe,{"anchor":[0,4]},[0,0,128,8],1)
	check(probe.offset==Vector2(64,0),"额灯飞行束以图集左端接发射点")
	UfeEffectGeometry.apply_anchor(probe,{},[0,0,64,64],-1)
	check(probe.offset==Vector2.ZERO,"默认居中弹体不继承上个特效偏移")
	probe.free()
	check_following_beams()
	for error in errors:printerr(error)
	var output_path:="res://reports/emission-geometry.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--emission-geometry-output="):output_path=arg.trim_prefix("--emission-geometry-output=")
	FileAccess.open(output_path,FileAccess.WRITE).store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors}))
	print("EMISSION_GEOMETRY ","通过" if errors.is_empty() else "失败")
	quit(0 if errors.is_empty() else 1)

func check_following_beams() -> void:
	for facing in [1,-1]:
		var sim:=UfeBattleFormCatalog.match_for("ultraman-taro","zetton",true)
		var emitter:=sim.fighters[0]
		emitter.move_id="motion_236";emitter.move_tick=9;emitter.facing=facing
		sim.fighters[1].x=emitter.x-facing*700
		UfeProjectileResolver.emit(sim,0)
		check(sim.projectiles.size()==2,"泰罗双束必须独立出生")
		var cinematic:=UfeSuperCinematic.new();cinematic._ready()
		for current in range(10,17):
			emitter.move_tick=current
			UfeProjectileResolver.advance(sim,[])
			var expected:Array=[[39,90],[59,115]] if current<=12 else [[39,92],[55,113]]
			check(sim.projectiles.size()==2,"双束应持续覆盖当前相")
			var before:=sim.state_hash()
			cinematic.sync(sim,333,7)
			check(sim.state_hash()==before,"双束表现层不能改模拟")
			var tile:=0
			for n in range(sim.projectiles.size()):
				var p:Dictionary=sim.projectiles[n]
				check(int(p.x)==emitter.x+facing*int(expected[n][0]) and int(p.height)==int(expected[n][1]),"逐束跟随未贴对应掌心："+str([facing,current,n]))
				var sprite:Sprite2D=cinematic.beam_parts[tile]
				var clip:Dictionary=cinematic.effect_clips[p.effect]
				# native_fan旧长束以左端离手，clip.anchor是普通Sprite的中心；
				# 仅emission_anchor图集使用其显式锚，不能把两种来源混为一谈。
				var pivot:Vector2=Vector2(clip.anchor[0],clip.anchor[1]) if bool(clip.get("emission_anchor",false)) else Vector2(clip.get("emission_surface_x",0),sprite.region_rect.size.y/2)
				if facing<0:pivot.x=sprite.region_rect.size.x-pivot.x
				var actual:Vector2=sprite.position+(sprite.get_rect().position+pivot)*sprite.scale
				check(actual.distance_to(UfeEffectGeometry.beam_position(p,0,333,7))<0.001,"逐束绘制原点或镜像错位")
				tile+=ceili(float(p.length)/float(sprite.region_rect.size.x))
		cinematic.free()
		# 新字段缺帧只用本束anchor，不能读共用beam_origin；旧束保持原回退。
		emitter.move_tick=1
		var old_frame:Dictionary=emitter.frame().duplicate(true)
		emitter.frame().beam_origin=[9,10]
		check(UfeProjectileResolver.beam_origin(emitter,{"anchor":[3,4]})==[9,10],"未声明跟随的旧束行为改变")
		check(UfeProjectileResolver.beam_origin(emitter,{"anchor":[3,4],"origin_by_frame":{"0":[5,6]}})==[3,4],"独立束缺帧应使用自己的anchor")
		emitter.definition.moves.motion_236.frames[1]=old_frame
		check(not UfeMoveData.valid_follow_origin({"beam":true,"origin_by_frame":{"01":[1,2]}},30),"非规范帧键应拒绝")
		check(not UfeMoveData.valid_follow_origin({"beam":true,"origin_by_frame":{"30":[1,2]}},30),"越界帧应拒绝")
		check(not UfeMoveData.valid_follow_origin({"beam":true,"origin_by_frame":{"0":[1.5,2]}},30),"非整数坐标应拒绝")
		check(not UfeMoveData.valid_follow_origin({"origin_by_frame":{"0":[1,2]}},30),"非持续束应拒绝跟随")
	check_legacy_replay()

func check_legacy_replay() -> void:
	var a:Dictionary=UfeBattleFormCatalog.prepare("ultraman-taro",true)
	var b:Dictionary=UfeBattleFormCatalog.prepare("zetton",true)
	var forms:Dictionary={"ultraman-taro":a.form,"zetton":b.form}
	var current:=UfeMatchDirector.new(a.definition,b.definition,load("res://content/rules/neo.tres"),UfeContentDatabase.states(),forms)
	var current_fingerprint:=current.content_fingerprint
	var saved:Dictionary=a.definition.moves.motion_236.duplicate(true)
	for frame in a.definition.moves.motion_236.frames:
		for shot in frame.get("shots",[]):shot.erase("origin_by_frame")
	var previous:=UfeMatchDirector.new(a.definition,b.definition,load("res://content/rules/neo.tres"),UfeContentDatabase.states(),forms)
	check(current_fingerprint!=previous.content_fingerprint,"双束数据变化必须更新泰罗对局指纹")
	var replay:=UfeReplayRecorder.new()
	replay.append([UfeInputFrame.make(),UfeInputFrame.make()],previous)
	var path:="user://emission-taro-legacy.replay.json"
	check(replay.save_file(path)==OK,"旧内容指纹回放写入失败")
	check(UfeReplayRecorder.load_file(path,current_fingerprint)==null and UfeReplayRecorder.last_error.contains("招式数据已改变"),"旧泰罗回放必须明确拒绝")
	a.definition.moves.motion_236=saved
