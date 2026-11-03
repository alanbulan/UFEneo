extends SceneTree
## 表现副本逻辑夹具，非真实输入/逐角色美术验收；正式main证据另存。
const IDS := ["ultraman","ultraseven","ultraman-jack","ultraman-ace","ultraman-taro","ultraman-leo","gomora","neronga","red_king","eleking","black_king","zetton","ultraman-blazar","ultraman-arc","ultraman-omega","ultraman-teo","ex_gomora","ex_red_king"]
var records: Array=[]
var errors: Array=[]

func _initialize() -> void:call_deferred("run")

func need(ok: bool, label: String) -> void:
	if not ok:errors.append(label)

func run() -> void:
	var output_path: String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--grounded-ko-output="):output_path=arg.trim_prefix("--grounded-ko-output=")
	assert(not output_path.is_empty() and not FileAccess.file_exists(output_path))
	var view:=UfeSideView.new()
	var variants: Array=IDS.duplicate()
	variants.append("super-taro")
	for identity in variants:
		var id: String="ultraman-taro" if identity=="super-taro" else str(identity)
		var opponent: String="zetton" if id!="zetton" else "ultraseven"
		var manifest: Dictionary=UfeContentDatabase.read_json(str(UfeContentDatabase.read_json("res://content/fighters/%s/definition.json"%id).presentation.manifest))
		for facing in [1,-1]:
			var source:=UfeBattleFormCatalog.match_for(id,opponent,false)
			source.finished=true;source.winner=1;source.fighters[0].stats.hp=0
			source.fighters[0].enter("defeat");source.fighters[1].enter("victory")
			if identity=="super-taro":source.fighters[0].form_id="super-taro"
			var source_hash: String=source.state_hash()
			var show:=UfeKoFinishPresentation.new()
			show.source=source
			show.scene=UfeBattleFormCatalog.match_for(id,opponent,false)
			var body:=show.scene.fighters[0]
			body.stats.hp=0;body.enter("down",35);body.facing=facing;body.x=512
			body.state_tick=maxi(0,body.definition.state_frames.get("down",[]).size()-1)
			var before: Dictionary=view._animation(body,manifest)
			need(not before.is_empty() and before.key=="down",str(identity)+":缺真实倒地整相")
			show._ceremony()
			var result:=show.scene.fighters[0]
			var after: Dictionary=view._animation(result,manifest)
			var label: String=str(identity)+"/"+str(facing)
			need(result.state=="defeat" and result.x==512 and result.height==0 and result.facing==facing,label+":结算状态或已落根点变化")
			need(before==after,label+":已躺整相在结算被站立相替换")
			need(source.state_hash()==source_hash and not source.fighters[0].motion.has("ko_grounded_pose"),label+":改写真实终局")
			need(not show.scene.fighters[1].motion.has("ko_grounded_pose"),label+":胜方误用败方倒地相")
			show.reset()
			need(show.scene==null and not show.active,label+":reset残留显示副本")
			need(view._animation(source.fighters[0],manifest).get("key","")=="defeat",label+":普通败北流程被全局替换")
			# 尚未倒地的败方仍播放本人的完整失败动画，不能跳过落地过程。
			show.source=source;show.scene=UfeBattleFormCatalog.match_for(id,opponent,false)
			show.scene.fighters[0].stats.hp=0;show.scene.fighters[0].enter("hit",20)
			show._ceremony()
			need(not show.scene.fighters[0].motion.has("ko_grounded_pose"),label+":非倒地误持末相")
			# 超时不进入末击慢放/落地持相；换新局也须清旧副本。
			var timeout:=UfeBattleFormCatalog.match_for(id,opponent,false)
			timeout.finished=true;timeout.remaining=0
			var timeout_hash: String=timeout.state_hash()
			need(is_same(show.sample(timeout,false),timeout) and show.scene==null and timeout.state_hash()==timeout_hash,label+":超时或换局残留旧KO副本")
			records.append({"identity":identity,"facing":facing,"whole_down_animation":before,"source_hash_preserved":source.state_hash()==source_hash})
	view.free()
	var output:=FileAccess.open(output_path,FileAccess.WRITE)
	assert(output!=null)
	output.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"records":records,
		"scope":"18现装身份及超级泰罗/双向的显示副本逻辑夹具；不冒称逐人物原输入/画面验收。",
		"fixture_state_writes":true,"main_game_input_evidence_separate":true,"generated_videos":0}))
	output.close()
	for error in errors:push_error(str(error))
	quit(0 if errors.is_empty() else 1)
