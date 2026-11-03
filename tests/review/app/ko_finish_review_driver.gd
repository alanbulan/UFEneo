extends "res://tests/review/fighters/ultraman-arc/codex_supers_review_driver.gd"
## 主游戏终局专项。仅prepare_match设置明确登记的初始夹具，组内只送物理键事件。
var kind: String = "omega_beam"
var face: int = 1
var held_codes: Array = []
var initial: Dictionary = {}

func _init() -> void:
	profile = "ko_finish_main_game"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--ko-case="): kind = arg.trim_prefix("--ko-case=")
		if arg == "--ko-left": face = -1

func section(_frame: int) -> int: return 0
func length_frames() -> int: return 20002
func capture_length() -> int: return 20000
func boxes(_frame: int) -> bool: return false
func matchup() -> Array:
	return ["gomora" if kind == "transformed_ex" else "ex_gomora" if kind == "direct_ex_gomora" else "ex_red_king" if kind == "direct_ex_red_king" else "ultraman-omega", "zetton"]
func label(_frame: int) -> String:
	return "KO末击 · " + kind + " · " + ("朝左" if face < 0 else "朝右")

func prepare_match(sim: UfeMatchDirector) -> void:
	release_keys()
	cast_age = -1
	sampled_frame = -1
	pre_step = {}
	if kind != "full_replay":
		var own: UfeFighter = sim.fighters[0]
		own.x = 850 if face < 0 else 430
		own.facing = face
		sim.fighters[1].x = own.x + face * (100 if kind == "heavy" else 260)
		sim.fighters[1].facing = -face
		if kind != "timeout": sim.fighters[1].stats.hp = 1
		if kind == "transformed_ex": own.stats.hp = 500
	initial = {"ids": matchup(), "positions": [sim.fighters[0].x,sim.fighters[1].x],
		"facings": [sim.fighters[0].facing,sim.fighters[1].facing],
		"hp": [sim.fighters[0].stats.hp,sim.fighters[1].stats.hp],
		"natural_default_match": kind == "full_replay", "content_fingerprint": sim.content_fingerprint}

func key_event(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)

func release_keys() -> void:
	for code in held_codes: key_event(int(code),false)
	held_codes.clear()

func send_action(action: String) -> UfeInputFrame:
	var wanted: Array = []
	if not action.is_empty(): wanted.append(int(UfeInputRouter.get_key_binding(0,action).keycode))
	for code in held_codes:
		if code not in wanted: key_event(int(code),false)
	for code in wanted:
		if code not in held_codes: key_event(int(code),true)
	held_codes = wanted
	return UfeInputRouter.poll(0)

func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
	sampled_frame = frame
	pre_step = simulation_data(sim)
	p2 = UfeInputFrame.make()
	if frame < 83 or kind == "timeout": return send_action("")
	var own: UfeFighter = sim.fighters[0]
	if kind == "transformed_ex" and not own.transformed_this_round:
		if int(own.stats.energy) < 3000: return send_action("charge")
		return send_action("transform" if own.state == "idle" else "")
	if own.state in ["transform","form_entry"]: return send_action("")
	if kind != "full_replay" and cast_age >= 0: return send_action("")
	if kind == "heavy":
		if own.state != "idle": return send_action("")
		cast_age = frame
		return send_action("heavy")
	if kind == "pulse":
		if own.state != "idle": return send_action("")
		cast_age = frame
		return send_action("ranged")
	if int(own.stats.energy) < 3000: return send_action("charge")
	if own.state != "idle": return send_action("")
	cast_age = frame
	return send_action("special")

func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
	var row: Dictionary = simulation_data(sim)
	var display: Dictionary = simulation_data(view.simulation)
	for i in range(2):
		display.pair[i].animation = view._animation(view.simulation.fighters[i],view.manifests[i]).duplicate(true)
		display.pair[i].body_node = node_data(view.fighters[i])
	var beams: Array = []
	for node in view.cinematic.beam_parts:
		if node.visible: beams.append(node_data(node))
	var projectiles: Array = []
	for node in view.projectile_sprites:
		if node.visible: projectiles.append(node_data(node))
	var impacts: Array = []
	for particle in view.feedback.particles:
		impacts.append({"id":particle.id,"age":particle.age,"node":node_data(particle.node)})
	row.merge({"frame":frame,"case":kind,"simulation_stepped":sampled_frame == frame,
		"inputs":last_inputs.duplicate(true) if sampled_frame == frame else [[0,0,0],[0,0,0]],
		"display":display,"beam_nodes":beams,"projectile_nodes":projectiles,"impact_nodes":impacts,
		"ending_tick":view.ending_tick,"intro_tick":view.intro_tick,"window_size":[view.get_viewport().get_window().size.x,view.get_viewport().get_window().size.y]})
	trace.append(row)

func save_file(path: String) -> void:
	if trace_saved: return
	if FileAccess.file_exists(path):
		push_error("拒绝覆盖KO主游戏原trace")
		return
	var output := FileAccess.open(path,FileAccess.WRITE)
	if output == null:
		push_error("KO原输入trace无法保存")
		return
	output.store_string(JSON.stringify({"profile":profile,"case":kind,"initial":initial,"trace":trace,"stills":stills,
		"generated_videos":0,"hardware_keyboard_tested":false,"entry":"app/scenes/main.tscn"}))
	output.close()
	trace_saved = true
