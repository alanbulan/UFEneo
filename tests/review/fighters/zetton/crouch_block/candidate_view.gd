extends "res://presentation/side_view.gd"
## 完整沿用正式view，首次_ready后只在内存覆盖受方同名clip。
var candidate_contract: Dictionary={}
var candidate_contract_path: String=""
func _ready() -> void:
	assert(not candidate_contract.is_empty() and simulation.fighters[1].definition.id=="zetton")
	assert(walk_review_clip.is_empty())
	super._ready()
	var before: Dictionary=manifests[1].duplicate(true)
	manifests[1]=manifests[1].duplicate(true)
	manifests[1].clips.crouch_blockstun=candidate_contract.clip.duplicate(true)
	before.clips.crouch_blockstun=candidate_contract.clip.duplicate(true)
	assert(before==manifests[1])
	# 仅启用正式view已有的绝对PNG候选加载路径；不在super._ready前触发步行候选入口。
	walk_review_clip=candidate_contract_path
