extends SceneTree
# 对任意同协议驱动逐条解包实际输入，不补tick、不改原trace。
func _initialize() -> void:call_deferred("run")

func run() -> void:
	var driver_path:String="";var trace_path:String="";var output:String=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--state-review-driver="):driver_path=arg.trim_prefix("--state-review-driver=")
		if arg.begins_with("--state-review-trace="):trace_path=arg.trim_prefix("--state-review-trace=")
		if arg.begins_with("--state-review-output="):output=arg.trim_prefix("--state-review-output=")
	if not driver_path.begins_with("res://content/fighters/") or not driver_path.ends_with("_review_driver.gd") or trace_path.is_empty() or output.is_empty() or FileAccess.file_exists(output):
		quit(2);return
	var data:Variant=JSON.parse_string(FileAccess.get_file_as_string(trace_path))
	if not data is Dictionary or not data.has("trace"):quit(2);return
	var driver=load(driver_path).new();driver.movie_part=int(data.get("part",-1))
	var errors:Array=[];var previous:int=-1;var sim:UfeMatchDirector;var observations:int=0
	for row in data.trace:
		if driver.section(int(row.movie_frame))!=int(row.section):errors.append(str(row.movie_frame)+"实际分组不符")
		if int(row.section)!=previous:
			previous=int(row.section);driver.review_frame=int(row.movie_frame)
			var ids:Array=driver.matchup()
			sim=UfeBattleFormCatalog.match_for(ids[0],ids[1],true);driver.prepare_match(sim)
		var tick:int=int(row.tick)
		if tick==sim.tick+1:sim.step([UfeInputFrame.unpack(row.inputs[0]),UfeInputFrame.unpack(row.inputs[1])])
		elif tick!=sim.tick:errors.append(str(row.movie_frame)+"真实tick跳变")
		if sim.state_hash()!=row.state_hash:errors.append(str(row.movie_frame)+"实际输入重放hash差异")
		observations+=1
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"errors":errors,"observations":observations,"trace":trace_path,"driver":driver_path,"scope":"只解包实际主游戏InputFrame；逐tick独立模拟，不补帧，不改资源。"},"\t"))
	quit(0 if errors.is_empty() else 1)
