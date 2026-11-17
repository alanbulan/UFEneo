class_name UfePhase3ZettonDefenseReview
extends UfePhase3ReactionReview
func _init() -> void:
	profile="phase3_zetton_defense"
	target_player=1
	complete_chain=true
func actions() -> Array: return ACTIONS+["walk_forward","walk_back"]
func names() -> Array:
	var result:=NAMES.duplicate()
	result[2]="杰顿站防 小键盘4"
	result[3]="杰顿蹲防 ↓+小键盘4"
	result[19]="杰顿空中受身 小键盘4"
	result[20]="杰顿起身下段 小键盘1"
	result[21]="杰顿起身中段 小键盘2"
	result[22]="杰顿护盾外推 / 防御后 ←+小键盘2 / 1格"
	result[23]="杰顿爆气 小键盘4+5 / 2格"
	result[24]="杰顿蓄能起 小键盘5"
	result[25]="杰顿蓄能循环 按住小键盘5"
	result[26]="杰顿蓄能收 松开小键盘5"
	result[27]="初代升击 → 追击跳 → 空轻两段 → 砸地弹地 → 杰顿倒地 → 后滚起身"
	return result+["杰顿前走：均匀节奏复查","杰顿后退：4帧拖步"]
func section_length() -> int: return 240
