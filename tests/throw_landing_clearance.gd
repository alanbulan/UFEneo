extends SceneTree
## 四角色任意配对、双方朝向、场边：真实输入捕获，撞地及倒地期检查整数框。
var failures: Array[String]=[]
var results: Array=[]
var selection_results: Array=[]
var definitions: Dictionary={}
func check(ok: bool,label: String) -> void:
	if not ok and label not in failures:failures.append(label)
func _initialize() -> void:call_deferred("run")
func world_boxes(f: UfeFighter) -> Array:
	var boxes:=[]
	for b in f.frame().hurtboxes:
		boxes.append(Rect2i(f.x+int(b[0]) if f.facing>0 else f.x-int(b[0])-int(b[2]),f.height+int(b[1]),int(b[2]),int(b[3])))
	return boxes
func overlaps(a: UfeFighter,b: UfeFighter) -> bool:
	for aa in world_boxes(a):
		for bb in world_boxes(b):
			if aa.intersects(bb):return true
	return false
func run() -> void:
	var front:=UfeFrontEnd.new();root.add_child(front)
	for mode in ["training","cpu","local"]:
		front.mode=mode;front.selections=["gomora","zetton"];front.selected_forms=["default","default"];front.confirmed=[false,false]
		front.open("select");front.confirm(0)
		var first:=front.confirmed.duplicate()
		front.confirm(1)
		selection_results.append({"mode":mode,"after_first":first,"after_second":front.confirmed.duplicate(),"page":front.page,"forms":front.selected_forms.duplicate()})
		check(front.page=="vs" and front.confirmed==[true,true],"哥莫拉自由选人 "+mode)
	front.free()
	if "--selection-only" in OS.get_cmdline_user_args():
		print("GOMORA_SELECTION "+JSON.stringify({"failures":failures,"selection":selection_results}));quit(0 if failures.is_empty() else 1);return
	# 定义是只读数据；重复使用同一正式定义，避免每个朝向/场边重新解析招式JSON。
	for id in ["ultraman","ultraseven","zetton","gomora"]:definitions[id]=UfeContentDatabase.fighter(id,true)
	for actor in ["ultraman","ultraseven","zetton","gomora"]:
		for victim in ["ultraman","ultraseven","zetton","gomora"]:
			for action in ["throw_forward","throw_back"]:
				for facing in [1,-1]:
					for edge in [100,600,1150]:run_pair(actor,victim,action,facing,edge)
	var evidence_path:="res://reports/review/2026-10-23/gomora-fourth-installed/throw-landing-results.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--throw-results="):evidence_path=arg.trim_prefix("--throw-results=")
	FileAccess.open(evidence_path,FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"selection":selection_results,"pairs":results},"\t"))
	print("THROW_LANDING "+JSON.stringify({"failures":failures,"pairs":results.size()}));quit(0 if failures.is_empty() else 1)
func run_pair(actor: String,victim: String,action: String,facing: int,edge: int) -> void:
	var sim:=UfeMatchDirector.new(definitions[actor],definitions[victim],load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	var twin:=UfeMatchDirector.new(definitions[actor],definitions[victim],load("res://content/rules/neo.tres"),UfeContentDatabase.states())
	for match_sim in [sim,twin]:
		match_sim.fighters[0].x=edge
		match_sim.fighters[1].x=edge+facing*52
		match_sim.fighters[0].facing=facing
		match_sim.fighters[1].facing=-facing
	var key:=str([actor,victim,action,facing,edge]);var slams:=0;var checks:=0
	var authored:=int(sim.fighters[0].definition.moves[action].frames[-1].target.root[0]);var actual:=0
	var landed:=false;var max_error:=0
	for tick in range(90):
		var inputs:=[UfeInputFrame.make(),UfeInputFrame.make()]
		if tick==10:inputs[0]=UfeInputFrame.make(-facing if action=="throw_back" else 0,0,UfeInputFrame.THROW)
		sim.step(inputs);twin.step(inputs)
		check(sim.state_hash()==twin.state_hash(),"逐tick确定性 "+key)
		var a:=sim.fighters[0];var b:=sim.fighters[1]
		if b.state=="thrown" and a.frame().get("target",{}).get("mode","")=="hold":
			var grip: Array=a.frame().target.grip;var waist: Array=b.frame().grab_points.waist
			max_error=maxi(max_error,absi(a.x+a.facing*int(grip[0])-b.x-b.facing*int(waist[0]))+absi(a.height+int(grip[1])-b.height-int(waist[1])))
		for e in sim.events:
			if e.kind=="throw_slam":slams+=1;landed=true;actual=(b.x-a.x)*facing
		if landed and b.state in ["thrown","down"]:
			checks+=1;check(not overlaps(a,b),"落地/倒地框交叠 "+key)
		check(a.x>=28 and a.x<=1252 and b.x>=28 and b.x<=1252,"配对场边约束 "+key)
	check(slams==1 and checks>10,"真实捕获并唯一撞地 "+key)
	check(max_error==0,"抓点保持精确 "+key)
	results.append({"actor":actor,"victim":victim,"action":action,"facing":facing,"edge":edge,"authored":authored,"actual":actual,"outward_delta":absi(actual)-absi(authored),"max_grip_error":max_error,"ground_checks":checks})
