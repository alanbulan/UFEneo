extends "res://tools/rebuild/gomora/back_lift_resume/runtime/diagnostic_game.gd"
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
