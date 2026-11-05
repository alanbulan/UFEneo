extends "res://tools/rebuild/gomora/back_lift_resume/runtime/game.gd"
## 只向当前候选view追加专用FX别名，正式表及原explosion不变。
func start_match() -> void:
	super.start_match()
	var before: Dictionary=view.feedback.clips.duplicate(true)
	var aliases: Dictionary=candidate_contract.get("feedback_effect_aliases",{})
	assert(aliases.size()==1 and aliases.has("gomora_candidate_ground_explosion"))
	for key in aliases:
		assert(not before.has(key))
		var expected: Dictionary=before.explosion.duplicate(true)
		expected.anchor=[72,120]
		assert(JSON.stringify(JSON.parse_string(JSON.stringify(expected)),"",true)==JSON.stringify(JSON.parse_string(JSON.stringify(aliases[key])),"",true))
		view.feedback.clips[key]=aliases[key].duplicate(true)
	for key in before:assert(view.feedback.clips[key]==before[key])
var ground_fx_phases: Dictionary={}
func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	for particle in view.feedback.particles:
		if str(particle.id)!="gomora_candidate_ground_explosion":continue
		var phase: int=int(particle.node.region_rect.position.x)/144
		if not ground_fx_phases.has(phase):
			ground_fx_phases[phase]=true;pending_stills+=1
			_save_still.call_deferred("ground-fx-%d"%phase,capture_tick-1)
func _save_still(label: String,requested_frame: int) -> void:
	await super._save_still(label,requested_frame)
	if not label.begins_with("ground-fx-"):return
	var matches: Array=review_driver.stills.filter(func(s):return s.key==label)
	assert(matches.size()==1)
	var item: Dictionary=matches[0]
	var expected: int=int(label.trim_prefix("ground-fx-"))
	item.ground_fx_phase=expected
	item.ground_fx_nodes=[]
	for particle in view.feedback.particles:
		if str(particle.id)!="gomora_candidate_ground_explosion":continue
		var node: Sprite2D=particle.node
		var actual_phase: int=int(node.region_rect.position.x)/144
		item.ground_fx_nodes.append({"id":particle.id,"age":particle.age,"phase":actual_phase,"offset":[node.offset.x,node.offset.y],"event_x":particle.x,"event_height":particle.height,"region":[node.region_rect.position.x,node.region_rect.position.y,node.region_rect.size.x,node.region_rect.size.y],"scale":[node.scale.x,node.scale.y],"visible":node.visible})
		if actual_phase!=expected:review_driver.failures.append({"kind":"ground_fx_capture_phase_mismatch","expected":expected,"actual":actual_phase})
	if item.actual_frame!=requested_frame or item.ground_fx_nodes.size()!=1:
		review_driver.failures.append({"kind":"ground_fx_capture_binding_mismatch","label":label})
