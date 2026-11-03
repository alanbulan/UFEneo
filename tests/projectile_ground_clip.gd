extends SceneTree
## 只为显式束裁地线；旧输入和原Sprite参数先存基线。
const OUT := "res://reports/review/2026-10-28/projectile-ground-clip-core-v1/"
var errors: Array=[]
var completed: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	if not ok:errors.append(label);printerr(label)
func write_json(name: String,value: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	FileAccess.open(OUT+name,FileAccess.WRITE).store_string(JSON.stringify(value,"\t",true)+"\n")
func legacy() -> Dictionary:
	var result: Dictionary={}
	for part in range(9):
		var driver:=UfePhase3SpecialReview.new();driver.review_frame=driver.S_STARTS[part]
		var ids: Array=driver.matchup();var sim:=UfeContentDatabase.match_for(str(ids[0]),str(ids[1]));driver.prepare_match(sim)
		var rows: Array=[]
		for age in range(driver.S_STARTS[part+1]-driver.S_STARTS[part]):
			if driver.wants_intro() and age<75:continue
			var tick: int=driver.S_STARTS[part]+age
			sim.step([driver.sample(tick,sim),driver.second_sample(tick)]);rows.append([sim.state_hash(),sim.events.duplicate(true),sim.projectiles.duplicate(true)])
		result[str(part)]={"fingerprint":sim.content_fingerprint,"rows":rows}
	return result
func legacy_view() -> Array:
	var view:=UfeSuperCinematic.new();root.add_child(view)
	var sim:=UfeContentDatabase.match_for();var rows: Array=[]
	for effect in ["beam_loop","teo_air_special_beam"]:
		for facing in [-1,1]:
			for age in [0,4,8,12]:
				sim.projectiles=[{"owner":0,"beam":true,"length":480,"effect":effect,"age":age,"x":400,"height":195,"facing":facing,"color":[1,1,1,1]}]
				view.sync(sim,320,17)
				rows.append({"effect":effect,"facing":facing,"age":age,"sprites":view.beam_parts.filter(func(s):return s.visible).map(func(s):return {"texture":s.texture.resource_path,"region":str(s.region_rect),"offset":str(s.offset),"scale":str(s.scale),"position":str(s.position),"flip_h":s.flip_h})})
	view.free();return rows
func test_contact() -> void:
	for facing in [-1,1]:
		for segmented in [false,true]:
			var p: Dictionary={"x":400,"height":2,"facing":facing,"age":0,"box":[0,-5,5,8],"clip_below_ground":true}
			if segmented:p.frame_hitboxes=[[[0,-5,5,8]]]
			var x:=401 if facing>0 else 398
			check(UfeProjectileResolver.contact_point(p,Rect2i(x,-2,1,1))==null,"地线下不形成身体或屏接触/%s/%s"%[facing,segmented])
			check(UfeProjectileResolver.contact_point(p,Rect2i(x,0,1,1))==Vector2i(x,0),"地线上实际框保持/%s/%s"%[facing,segmented])
			var cut: Variant=UfeProjectileResolver.contact_point(p,Rect2i(x,-2,1,4))
			check(cut==Vector2i(x,1),"交集中心在裁后的正高度内/%s/%s"%[facing,segmented])
			check(UfeProjectileResolver.world_hitboxes(p).all(func(b):return b.position.y>=0),"F1有效世界框与裁界相同/%s/%s"%[facing,segmented])
			p.erase("clip_below_ground")
			check(UfeProjectileResolver.contact_point(p,Rect2i(x,-2,1,1))!=null,"无字段旧弹体不裁判定/%s/%s"%[facing,segmented])
			if not segmented:check(UfeProjectileResolver.world_hitboxes(p)==[UfeMatchDirector.projectile_box(p)],"旧F1仍是原单矩形/%s"%facing)
	var sim:=UfeContentDatabase.match_for()
	UfeProjectileResolver.spawn(sim,0,{"beam":true,"clip_below_ground":true},"pulse")
	check(sim.projectiles[0].clip_below_ground is bool and sim.projectiles[0].clip_below_ground,"显式字段保存整数模拟快照")
	UfeProjectileResolver.spawn(sim,0,{},"pulse")
	check(not sim.projectiles[1].has("clip_below_ground"),"旧弹体不加缺省字段")
	completed.append("contact")
func test_visual() -> void:
	var view:=UfeSuperCinematic.new();root.add_child(view)
	var sim:=UfeContentDatabase.match_for();var rows: Array=[]
	var clip: Dictionary=view.effect_clips.teo_air_special_beam
	var texture: Texture2D=load(clip.texture);var image:=texture.get_image()
	for facing in [-1,1]:
		for height in [0,58,195,500]:
			for age in [0,4,8,12]:
				var p: Dictionary={"owner":0,"beam":true,"length":480,"effect":"teo_air_special_beam","age":age,"x":400,"height":height,"facing":facing,"color":[1,1,1,1],"clip_below_ground":true}
				sim.projectiles=[p];view.sync(sim,320,17)
				var s: Sprite2D=view.beam_parts[0];var r: Array=clip.rects[age/4]
				check(s.region_rect.position==Vector2(int(r[0]),int(r[1])) and s.region_rect.size.x==int(r[2]),"裁地线不改图集起点及宽/%s/%s/%s"%[facing,height,age])
				check(s.scale==Vector2.ONE and s.position==UfeEffectGeometry.beam_position(p,0,320,17),"裁地线不缩放/旋转/移动原点/%s/%s/%s"%[facing,height,age])
				check(s.offset==Vector2(-16 if facing>0 else 16-480,-18) and s.flip_h==(facing<0),"裁地线保左右锚点/%s/%s/%s"%[facing,height,age])
				check(int(s.region_rect.size.y)==mini(320,height+18+1),"实际region含高度0像素并裁去下方/%s/%s/%s"%[facing,height,age])
				var minimum:=9999;var visible_pixels:=0
				for y in range(int(s.region_rect.size.y)):
					for x in range(int(s.region_rect.size.x)):
						if image.get_pixel(int(r[0])+x,int(r[1])+y).a>0:
							minimum=mini(minimum,height+18-y);visible_pixels+=1
				check(minimum>=0 and visible_pixels>0,"实际纹理Alpha没有像素中心越地/%s/%s/%s"%[facing,height,age])
				rows.append({"facing":facing,"height":height,"age":age,"region_height":s.region_rect.size.y,"minimum_alpha_world_height":minimum,"visible_alpha_pixels":visible_pixels})
	view.free();write_json("visual-geometry-result.json",rows);completed.append("visual")
func test_validation() -> void:
	var valid: Dictionary=UfeContentDatabase.fighter("ultraman").moves.pulse.duplicate(true)
	valid.projectile.beam=true;valid.projectile.clip_below_ground=true
	check(UfeMoveData.validate(valid),"持续束显式裁地线合法")
	for value in [0,1,"true",[],null]:
		var bad:=valid.duplicate(true);bad.projectile.clip_below_ground=value
		check(not UfeMoveData.validate(bad),"非bool地界字段拒收/%s"%[value])
		bad=valid.duplicate(true);bad.projectile.erase("clip_below_ground");bad.frames[0].shots=[{"beam":true,"clip_below_ground":value}]
		check(not UfeMoveData.validate(bad),"逐帧shots同门/%s"%[value])
	var flying:=valid.duplicate(true);flying.projectile.beam=false
	check(not UfeMoveData.validate(flying),"裁界目前只开放持续束")
	completed.append("validation")
func run() -> void:
	if "--baseline" in OS.get_cmdline_user_args():
		write_json("legacy-before.json",legacy());write_json("legacy-view-before.json",legacy_view())
		print("GROUND_CLIP_BASELINE_SAVED");quit(0);return
	if "--compare" in OS.get_cmdline_user_args():
		var current:=legacy();var visual:=legacy_view()
		check(JSON.parse_string(FileAccess.get_file_as_string(OUT+"legacy-before.json"))==JSON.parse_string(JSON.stringify(current)),"旧真实输入状态/事件/弹体/指纹保持")
		check(JSON.parse_string(FileAccess.get_file_as_string(OUT+"legacy-view-before.json"))==JSON.parse_string(JSON.stringify(visual)),"无新字段的旧束Sprite参数逐值保持")
		write_json("legacy-after.json",current);write_json("legacy-view-after.json",visual)
	test_contact();test_visual();test_validation()
	check(completed==["contact","visual","validation"],"全部专项分支执行结束")
	write_json("logic-result.json",{"passed":errors.is_empty(),"errors":errors,"completed":completed})
	print("GROUND_CLIP ","PASS" if errors.is_empty() else errors);quit(0 if errors.is_empty() else 1)
