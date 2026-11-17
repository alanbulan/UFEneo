extends SceneTree
## 只验证分档、专属/防御/投射物保留及原色材质；画面由主游戏录屏审查。
var problems: Array[String] = []

func _initialize() -> void:
	call_deferred("run")

func expect(condition: bool, message: String) -> void:
	if not condition: problems.append(message)

func run() -> void:
	var groups := {"light":UfeImpactFeedbackPolicy.LIGHT,"medium":UfeImpactFeedbackPolicy.MEDIUM,"heavy":UfeImpactFeedbackPolicy.HEAVY,"crush":UfeImpactFeedbackPolicy.CRUSH}
	var seen: Array[String] = []
	for tier in groups:
		for move in groups[tier]:
			expect(not move in seen, "重复矩阵招式："+move)
			seen.append(move)
			var event := {"kind":"hit","move":move,"projectile":false}
			var want := str(UfeImpactFeedbackPolicy.SHARED[tier])
			for fallback in ["impact_light", "impact_heavy"]:
				expect(UfeImpactFeedbackPolicy.impact_id(event,fallback)==want, "普通档不匹配："+move)
				expect(UfeImpactFeedbackPolicy.tier(event,fallback)==tier, "档名不匹配："+move)
			for fallback in ["arc_sword_hit", "blazar_sword623_hit", "teo_pulse_hit", "", "impact_guard"]:
				expect(UfeImpactFeedbackPolicy.impact_id(event,fallback)==fallback, "改动专属反馈："+move)
			event.projectile=true
			expect(UfeImpactFeedbackPolicy.impact_id(event,"impact_heavy")=="impact_heavy", "改动飞行道具："+move)
			event.projectile=false
			event.kind="block"
			expect(UfeImpactFeedbackPolicy.impact_id(event,"impact_guard")=="impact_guard", "改动防御："+move)
	for move in ["special1","special2","special3","motion236","motion623","sword_cut1","throw","unlisted"]:
		expect(UfeImpactFeedbackPolicy.impact_id({"kind":"hit","move":move},"impact_heavy")=="impact_heavy", "改动未列招式："+move)
	var feedback:=UfeCombatFeedback.new()
	root.add_child(feedback)
	await process_frame
	for tier in groups:
		var id: String=str(UfeImpactFeedbackPolicy.SHARED[tier])
		expect(feedback.clips.has(id), "新火花未注册："+id)
		if not feedback.clips.has(id):continue
		expect(not bool(feedback.clips[id].get("color_parameter",true)), "新火花仍允许单色乘色："+id)
		feedback.spawn(id,0,80,[0,0,0,1])
		expect(feedback.particles[-1].node.material==null, "原色火花被角色tint压黑："+id)
	feedback.spawn("impact_guard",0,80,[1,1,1,1])
	expect(feedback.particles[-1].node.material!=null,"旧防御材质路径改变")
	# 角色专属火花只换像素名：赛文五档都要有，且都得已登记、按原色播放。
	var seven: Dictionary=UfeContentDatabase.read_json("res://content/fighters/ultraseven/definition.json")
	var sparks: Dictionary=seven.get("presentation",{}).get("impact_sparks",{})
	for key in ["light","medium","heavy","crush","guard"]:
		expect(sparks.has(key),"赛文缺少档位火花："+key)
		if not sparks.has(key):continue
		var id: String=str(sparks[key])
		expect(feedback.clips.has(id),"赛文火花未注册："+id)
		if not feedback.clips.has(id):continue
		expect(bool(feedback.clips[id].get("ordinary_melee_only",false)),"赛文火花缺少普通拳脚标记："+id)
		expect(not bool(feedback.clips[id].get("color_parameter",true)),"赛文火花仍允许乘色："+id)
	print(JSON.stringify({"errors":problems,"simulation_changed":false,"visual_approval":false}))
	quit(0 if problems.is_empty() else 1)
