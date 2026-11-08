extends UfeReviewDriver
@warning_ignore_start("integer_division")
## 正式main入口；组内只送双方InputFrame，不改资源、坐标、状态、费用或时钟。
const SPAN: int = 320
const CASES: Array = ["hit_p", "hit_pair", "stand_guard", "crouch_guard", "whiff", "interrupt_startup", "interrupt_volley", "cancel_attempt", "jump_evade", "dodge_escape", "low_energy", "punish_recovery"]
var movie_part: int = 0
var override_case: String = ""
var sampled_frame: int = -1
var sent_counter: bool = false
var sent_cancel: bool = false
var sent_evade: bool = false
var charge_complete_age: int = -1
var cast_age: int = -1
var passive: UfeInputFrame = UfeInputFrame.make()
var before: Dictionary = {}
var decision: Dictionary = {}
var stills: Array = []
var trace_saved: bool = false

func _init() -> void:
	profile = "teo_arrow1_formal_20261101_v1"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--teo-arrow1-part="): movie_part = int(arg.trim_prefix("--teo-arrow1-part="))
		if arg.begins_with("--teo-arrow1-case="): override_case = arg.trim_prefix("--teo-arrow1-case=")
	assert(movie_part >= 0 and movie_part < 4)
	assert(override_case.is_empty() or override_case in CASES)

func case_count() -> int: return 1 if not override_case.is_empty() else CASES.size()
func section(frame: int) -> int: return movie_part * CASES.size() + mini(frame / SPAN, case_count() - 1)
func capture_length() -> int: return case_count() * SPAN
func length_frames() -> int: return capture_length() + 2
func case_id(frame: int) -> String: return override_case if not override_case.is_empty() else str(CASES[section(frame) % CASES.size()])
func matchup() -> Array: return ["ultraman-teo", "zetton" if movie_part < 2 else "ultraseven"]
func mirrored(_frame: int) -> bool: return movie_part % 2 == 1
func initial_distance(frame: int) -> int: return 680 if case_id(frame) == "whiff" else 58 if case_id(frame) in ["interrupt_startup","interrupt_volley","punish_recovery"] else 160
func boxes(frame: int) -> bool: return case_id(frame) in ["hit_pair","crouch_guard","interrupt_startup","punish_recovery","cancel_attempt"]
func label(frame: int) -> String: return "提欧 · 青梭连射（本作一级编排） · " + case_id(frame) + " · " + ("朝左" if mirrored(frame) else "朝右")

func setup_data() -> Dictionary:
	var left: int = 850 if mirrored(review_frame) else 350
	var facing: int = -1 if mirrored(review_frame) else 1
	return {"fighters":matchup(),"positions":[left,left + facing * initial_distance(review_frame)],"facings":[facing,-facing]}

func prepare_match(sim: UfeMatchDirector) -> void:
	sent_counter = false
	sent_cancel = false
	sent_evade = false
	charge_complete_age = -1
	cast_age = -1
	sampled_frame = -1
	before = {}
	decision = {}
	passive = UfeInputFrame.make()
	var setup: Dictionary = setup_data()
	for i in range(2):
		sim.fighters[i].x = int(setup.positions[i])
		sim.fighters[i].facing = int(setup.facings[i])
	assert(sim.fighters[0].definition.id == "ultraman-teo")
	assert(sim.fighters[0].stats.energy == 0 and sim.fighters[0].stats.stamina == 1000 and sim.fighters[0].stats.hp == 1000)

func world_boxes(fighter: UfeFighter, values: Array) -> Array:
	var result: Array = []
	for local in values:
		var box: Rect2i = UfeHitResolver.world_box(fighter, local)
		result.append([box.position.x,box.position.y,box.size.x,box.size.y])
	return result

func snapshot(sim: UfeMatchDirector) -> Dictionary:
	var pair: Array = []
	for fighter in sim.fighters:
		var data: Dictionary = fighter.frame()
		pair.append({"fighter":fighter.definition.id,"x":fighter.x,"height":fighter.height,"facing":fighter.facing,
			"state":fighter.state,"state_tick":fighter.state_tick,"move":fighter.move_id,"move_tick":fighter.move_tick,
			"hp":fighter.stats.hp,"energy":fighter.stats.energy,"stamina":fighter.stats.stamina,
			"combat":fighter.combat.duplicate(true),"frame":data.duplicate(true),
			"world_hitboxes":world_boxes(fighter,data.hitboxes),"world_hurtboxes":world_boxes(fighter,data.hurtboxes)})
	var projectile_boxes: Array = []
	for projectile in sim.projectiles:
		var effective: Array = []
		for box in UfeProjectileResolver.world_hitboxes(projectile): effective.append([box.position.x,box.position.y,box.size.x,box.size.y])
		projectile_boxes.append({"owner":projectile.owner,"move":projectile.move,"age":projectile.age,"x":projectile.x,"height":projectile.height,"boxes":effective})
	return {"projectile_world_hitboxes":projectile_boxes,"tick":sim.tick,"state_hash":sim.state_hash(),"remaining":sim.remaining,"hitstop":sim.hitstop,
		"finished":sim.finished,"pair":pair,"projectiles":sim.projectiles.duplicate(true),"events":sim.events.duplicate(true)}

func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
	sampled_frame = frame
	before = snapshot(sim)
	decision = {"request":""}
	var age: int = frame % SPAN
	var kind: String = case_id(frame)
	var own: UfeFighter = sim.fighters[0]
	var other: UfeFighter = sim.fighters[1]
	var guard: bool = kind in ["stand_guard","crouch_guard"] or (kind == "punish_recovery" and not sent_counter)
	passive = UfeInputFrame.make(0,-1 if kind == "crouch_guard" else 0,UfeInputFrame.GUARD if guard else 0)
	if kind == "interrupt_startup" and not sent_counter and own.move_id == "special" and own.move_tick >= 6:
		sent_counter = true
		passive = UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		decision.counter = "陪练实际K中断首发前起手"
	if kind == "interrupt_volley" and not sent_counter and own.move_id == "special" and own.move_tick >= 25:
		sent_counter = true
		passive = UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
		decision.counter = "首发已出后实际K中断后续送掌"
	if kind == "punish_recovery" and not sent_counter and own.move_id == "special" and own.move_tick >= 41 and other.move_id.is_empty() and other.state in ["idle","guard"]:
		sent_counter = true
		passive = UfeInputFrame.make(0,0,UfeInputFrame.LIGHT)
		decision.counter = "近距离防御后实际J尝试惩罚收招"
	if kind == "jump_evade" and not sent_evade and own.move_id == "special" and own.move_tick >= 14:
		sent_evade = true
		passive = UfeInputFrame.make(0,1,0)
		decision.counter = "陪练真实上跳规避青梭"
	if kind == "dodge_escape" and not sent_evade and own.move_id == "special" and own.move_tick >= 24:
		sent_evade = true
		passive = UfeInputFrame.make(0,0,UfeInputFrame.DODGE)
		decision.counter = "陪练真实N侧闪规避青梭"
	if kind == "cancel_attempt" and not sent_cancel and own.move_id == "special" and own.move_tick >= 45:
		sent_cancel = true
		decision.request = "收招中实际K尝试"
		return UfeInputFrame.make(0,0,UfeInputFrame.HEAVY)
	if cast_age >= 0: return UfeInputFrame.make()
	var wanted: int = 980 if kind == "low_energy" else 1000
	if charge_complete_age < 0:
		if int(own.stats.energy) < wanted:
			decision.request = "Q实际蓄能"
			return UfeInputFrame.make(0,0,UfeInputFrame.CHARGE)
		charge_complete_age = age
	if own.state != "idle": return UfeInputFrame.make()
	cast_age = age
	decision.request = "J+K" if kind == "hit_pair" else "不足一格实际P" if kind == "low_energy" else "P"
	return UfeInputFrame.make(0,0,UfeInputFrame.LIGHT | UfeInputFrame.HEAVY if kind == "hit_pair" else UfeInputFrame.SPECIAL)

func second_sample(_frame: int) -> UfeInputFrame: return passive

func node_data(node: Sprite2D) -> Dictionary:
	return {"visible":node.is_visible_in_tree(),"rotation":node.rotation,"position":[node.position.x,node.position.y],
		"offset":[node.offset.x,node.offset.y],"scale":[node.scale.x,node.scale.y],"flip_h":node.flip_h,
		"centered":node.centered,"z_index":node.z_index,
		"region":[node.region_rect.position.x,node.region_rect.position.y,node.region_rect.size.x,node.region_rect.size.y],
		"texture":node.texture.resource_path if node.texture != null else ""}

func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	if frame >= capture_length(): return
	var stepped: bool = sampled_frame == frame
	if not stepped:
		before = snapshot(sim)
		last_inputs = [[0,0,0],[0,0,0]]
		decision = {"request":"正式75观察登场，未推进模拟"}
	var row: Dictionary = snapshot(sim)
	for i in range(2):
		row.pair[i].animation = view._animation(sim.fighters[i],view.manifests[i]).duplicate(true)
		row.pair[i].body_node = node_data(view.fighters[i])
	var attached: Array = []
	var flying: Array = []
	var impacts: Array = []
	for node in view.attached_slots[0]: attached.append(node_data(node))
	for node in view.projectile_sprites: flying.append(node_data(node))
	var trails: Array = []
	for node in view.weapon_trails: trails.append(node_data(node))
	for particle in view.feedback.particles:
		impacts.append({"id":particle.id,"age":particle.age,"x":particle.x,"height":particle.height,"node":node_data(particle.node)})
	row.merge({"movie_frame":frame,"section":section(frame),"age":frame % SPAN,"case":case_id(frame),
		"case_setup":setup_data(),"simulation_stepped":stepped,"entry":"app/scenes/main.tscn","training":false,
		"content_fingerprint":sim.content_fingerprint,"inputs":last_inputs.duplicate(true),"pre":before.duplicate(true),
		"decision":decision.duplicate(true),"charge_complete_age":charge_complete_age,"cast_age":cast_age,
		"camera":[view.camera_x,view.camera_y],"active_attachments":view.attachments_for(0).duplicate(true),
		"attached_nodes":attached,"projectile_nodes":flying,"weapon_trail_nodes":trails,"impact_nodes":impacts,
		"intro_tick":view.intro_tick,"view_position":[view.position.x,view.position.y]})
	trace.append(row)

func record_still(frame: int, part: int, path: String) -> void:
	stills.append({"frame":frame,"section":part,"path":path,"sha256":FileAccess.get_sha256(path)})

func save_file(path: String) -> void:
	if trace_saved: return
	if FileAccess.file_exists(path):
		push_error("拒绝覆盖提欧一级原trace")
		return
	var output: FileAccess = FileAccess.open(path,FileAccess.WRITE)
	if output == null:
		push_error("提欧一级trace无法保存")
		return
	output.store_string(JSON.stringify({"profile":profile,"part":movie_part,"override_case":override_case,
		"span":SPAN,"case_names":CASES,"trace":trace,"stills":stills,"generated_videos":0,
		"source":"正式main非训练，本人已正式开放；默认满HP满体零能。只在开局设站位/朝向，真实Q恰到1000或费用负例980，完整收气后P/J+K；组内不改模拟。"}))
	output.close()
	trace_saved = true
@warning_ignore_restore("integer_division")
