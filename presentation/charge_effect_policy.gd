class_name UfeChargeEffectPolicy
extends RefCounted
## 周身蓄气圈仅随真实Q起势/保持/收势。局部发射、武器及冲击由独立语义分类保留。
const CHARGE_STATES := ["charge_start","charge","charge_stop"]
const POLICY_PATH := "res://content/presentation/charge_overlay_policy.json"
static var registered: Dictionary = {}
static var policy: Dictionary = {}

static func data() -> Dictionary:
	if policy.is_empty():policy=UfeContentDatabase.read_json(POLICY_PATH)
	return policy

static func is_charging(f: UfeFighter) -> bool:
	return f.move_id.is_empty() and f.state in CHARGE_STATES

static func allows_charge(f: UfeFighter) -> bool:
	# 独立爆气仍可使用原冲击音；不因此放行周身Q光圈。
	return f.move_id=="burst" or is_charging(f)

static func charge_effects(f: UfeFighter, manifest: Dictionary) -> Dictionary:
	var id: String=f.definition.id
	if registered.has(id):return registered[id]
	var result := {"charge_aura":true,"charge_aura_orange":true}
	for effect in data().charge_only_effects:result[str(effect)]=true
	for state in CHARGE_STATES:
		for frame in f.definition.state_frames.get(state,[]):
			for item in frame.get("attachments",[]):result[str(item.effect)]=true
		var clip: Dictionary=manifest.get("clips",{}).get(state,{})
		for item in clip.get("attachments",[]):result[str(item.effect)]=true
		for items in clip.get("attachments_by_frame",[]):
			for item in items:result[str(item.effect)]=true
	registered[id]=result
	return result

static func filter(f: UfeFighter, manifest: Dictionary, attachments: Array, holding_opponent: bool = false) -> Array:
	var restricted := charge_effects(f,manifest)
	# 缠尾电流属于实际抓住受方后的攻击；未捕获时不能凭空罩住自己。
	var gated: Array=data().get("requires_throw_hold",[])
	attachments=attachments.filter(func(item):return holding_opponent or str(item.get("effect","")) not in gated)
	if not is_charging(f):
		return attachments.filter(func(item):return not restricted.has(str(item.get("effect",""))))
	var placements: Dictionary=data().get("placements",{})
	var layout: Dictionary=placements.get(f.definition.id,{}).get(f.state,{})
	# 形态没有单独蓄气落点时沿用本人基础形态，同一个人不因换形态丢失Q蓄气定位。
	if layout.is_empty() and f.definition.id!=f.base_definition.id:
		layout=placements.get(f.base_definition.id,{}).get(f.state,{})
	if layout.is_empty():return attachments
	# 仅替换表现副本，保持原Q动作、输入、能量增长与音效。
	var result: Array=[]
	for item in attachments:
		if not restricted.has(str(item.get("effect",""))):
			result.append(item)
			continue
		var replacement: Dictionary=layout.duplicate(true)
		var count: int=int(replacement.frames)
		replacement.sprite=posmod(f.state_tick,count) if bool(replacement.loop) else clampi(f.state_tick,0,count-1)
		replacement.erase("frames");replacement.erase("loop")
		result.append(replacement)
	return result
