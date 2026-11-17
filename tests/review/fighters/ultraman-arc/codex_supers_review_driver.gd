extends UfeReviewDriver
@warning_ignore_start("integer_division")
const SPAN: int = 320
const MOVES: Array = ["special", "special2", "special3", "air_special"]
const CASES: Array = ["hit", "stand_guard", "whiff"]
const SECTIONS: int = 52
var sampled_frame: int = -1
var pre_step: Dictionary = {}
var p2: UfeInputFrame = UfeInputFrame.make()
var stills: Array = []
var trace_saved: bool = false
var charge_complete_age: int = -1
var jump_age: int = -1
var cast_age: int = -1
var goal_energy: int = 0

func _init() -> void: profile = "stage6_ultraman_arc_supers"
func section(frame: int) -> int: return mini(frame / SPAN, SECTIONS - 1)
func action(frame: int) -> String:
    var part: int = section(frame)
    return str(MOVES[part / 12 if part < 48 else part - 48])
func case_id(frame: int) -> String: return str(CASES[section(frame) % 3]) if section(frame) < 48 else "low_energy"
func combination(frame: int) -> int: return (section(frame) % 12) / 3 if section(frame) < 48 else 0
func mirrored(frame: int) -> bool: return combination(frame) % 2 == 1
func button_mask(frame: int) -> int: return 3 if action(frame) != "air_special" and case_id(frame) == "stand_guard" else UfeInputFrame.SPECIAL
func capture_length() -> int: return SPAN * SECTIONS
func length_frames() -> int: return capture_length() + 2
func boxes(_frame: int) -> bool: return false
func matchup() -> Array: return ["ultraman-arc", "zetton" if combination(review_frame) < 2 else "ultraseven"]
func label(frame: int) -> String:
    return "亚刻 · " + action(frame) + " · H蓄能→" + ("W→P" if action(frame) == "air_special" else "J＋K" if button_mask(frame) == 3 else "P") + " · " + case_id(frame) + " · " + ("朝左" if mirrored(frame) else "朝右") + " · 训练试制"

func prepare_match(sim: UfeMatchDirector) -> void:
    var own: UfeFighter = sim.fighters[0]
    var identity: String = action(review_frame)
    var facing: int = -1 if mirrored(review_frame) else 1
    assert(own.definition.moves.has(identity), "亚刻必杀尚未安装")
    var move: Dictionary = own.definition.moves[identity]
    assert(UfeMoveData.validate(move), "亚刻必杀数据不合法")
    var gap: int = int(move.get("review_whiff_gap", 700)) if case_id(review_frame) == "whiff" else int(move.get("review_fixture_gap", 180))
    own.x = 850 if facing < 0 else 430
    sim.fighters[1].x = own.x + facing * gap
    own.facing = facing
    sim.fighters[1].facing = -facing
    assert(int(own.stats.energy) == 0 and int(own.stats.stamina) == 1000, "必须真实零能初始，不设费用夹具")
    goal_energy = int(move.energy_cost) - (20 if case_id(review_frame) == "low_energy" else 0)
    sampled_frame = -1
    pre_step = {}
    p2 = UfeInputFrame.make()
    charge_complete_age = -1
    jump_age = -1
    cast_age = -1

func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
    sampled_frame = frame
    pre_step = simulation_data(sim)
    var age: int = frame % SPAN
    var own: UfeFighter = sim.fighters[0]
    p2 = UfeInputFrame.make(0, 0, UfeInputFrame.GUARD if case_id(frame) == "stand_guard" else 0)
    if age < 8 or cast_age >= 0: return UfeInputFrame.make()
    if charge_complete_age < 0:
        if int(own.stats.energy) < goal_energy: return UfeInputFrame.make(0, 0, UfeInputFrame.CHARGE)
        charge_complete_age = age
    # H释放后等正式charge_stop完整结束；不摆状态或把输入缓冲当出招。
    if action(frame) == "air_special":
        if jump_age < 0:
            if own.state != "idle": return UfeInputFrame.make()
            jump_age = age
            return UfeInputFrame.make(0, 1)
        if own.height <= 0 or age < jump_age + 8: return UfeInputFrame.make()
    elif own.state != "idle": return UfeInputFrame.make()
    cast_age = age
    return UfeInputFrame.make(0, 0, button_mask(frame))

func second_sample(_frame: int) -> UfeInputFrame: return p2

func node_data(node: Sprite2D) -> Dictionary:
    return {"path": str(node.get_path()), "visible": node.is_visible_in_tree(), "position": [node.position.x, node.position.y],
        "offset": [node.offset.x, node.offset.y], "scale": [node.scale.x, node.scale.y], "rotation": node.rotation,
        "flip_h": node.flip_h, "centered": node.centered, "z_index": node.z_index, "alpha": node.modulate.a,
        "region": [node.region_rect.position.x, node.region_rect.position.y, node.region_rect.size.x, node.region_rect.size.y],
        "texture": node.texture.resource_path if node.texture != null else ""}

func world_boxes(fighter: UfeFighter, values: Array) -> Array:
    var result: Array = []
    for local in values:
        var box: Rect2i = UfeHitResolver.world_box(fighter, local)
        result.append([box.position.x, box.position.y, box.size.x, box.size.y])
    return result

func simulation_data(sim: UfeMatchDirector) -> Dictionary:
    var pair: Array = []
    for fighter in sim.fighters:
        var data: Dictionary = fighter.frame()
        pair.append({"fighter": fighter.definition.id, "x": fighter.x, "height": fighter.height, "vx": fighter.vx, "vy": fighter.vy,
            "facing": fighter.facing, "state": fighter.state, "move": fighter.move_id, "move_tick": fighter.move_tick,
            "hp": fighter.stats.hp, "stamina": fighter.stats.stamina, "energy": fighter.stats.energy, "sprite": data.sprite,
            "hitboxes": data.hitboxes.duplicate(true), "hurtboxes": data.hurtboxes.duplicate(true),
            "world_hitboxes": world_boxes(fighter, data.hitboxes), "world_hurtboxes": world_boxes(fighter, data.hurtboxes),
            "attachments": data.get("attachments", []).duplicate(true), "connected": fighter.combat.connected,
            "beam_origin": data.get("beam_origin", []).duplicate(), "velocity": data.get("velocity", []).duplicate(),
            "cinematic_stage": data.get("cinematic_stage", ""), "pause_clock": data.get("pause_clock", false),
            "freeze_opponent": data.get("freeze_opponent", false), "audio_loop": data.get("audio_loop", "")})
    var shots: Array = sim.projectiles.duplicate(true)
    for shot in shots:
        var values: Array = []
        for box in UfeProjectileResolver.world_hitboxes(shot): values.append([box.position.x, box.position.y, box.size.x, box.size.y])
        shot.world_hitboxes = values
    return {"tick": sim.tick, "state_hash": sim.state_hash(), "pair": pair, "hitstop": sim.hitstop, "remaining": sim.remaining,
        "finished": sim.finished, "events": sim.events.duplicate(true), "projectiles": shots}

func observe_walk(frame: int, sim: UfeMatchDirector, view: UfeSideView) -> void:
    if frame >= capture_length(): return
    var row: Dictionary = simulation_data(sim)
    var consumed_tick: int = -1
    var consumed_move: String = ""
    if int(pre_step.get("hitstop", 0)) == 0:
        if str(pre_step.pair[0].move) in MOVES:
            consumed_move = str(pre_step.pair[0].move)
            consumed_tick = int(pre_step.pair[0].move_tick)
        elif str(row.pair[0].move) in MOVES:
            consumed_move = str(row.pair[0].move)
            consumed_tick = 0
    var phase: int = int(sim.fighters[0].definition.moves[consumed_move].frames[consumed_tick].sprite) if consumed_tick >= 0 else -1
    for i in range(2):
        row.pair[i].animation = view._animation(sim.fighters[i], view.manifests[i]).duplicate(true)
        row.pair[i].body_node = node_data(view.fighters[i])
    row.merge({"movie_frame": frame, "section": section(frame), "age": frame % SPAN, "case": case_id(frame), "action": action(frame),
        "simulation_stepped": sampled_frame == frame, "inputs": last_inputs.duplicate(true), "pre": pre_step.duplicate(true),
        "consumed_move": consumed_move, "consumed_move_tick": consumed_tick, "consumed_phase": phase,
        "camera": [view.camera_x, view.camera_y], "active_attachments": view.attachments_for(0).duplicate(true),
        "goal_energy": goal_energy, "charge_complete_age": charge_complete_age, "jump_age": jump_age, "cast_age": cast_age,
        "button_mask": button_mask(frame)})
    var attached: Array = []
    var ordinary: Array = []
    var beams: Array = []
    var trails: Array = []
    var impacts: Array = []
    for node in view.attached_slots[0]: attached.append(node_data(node))
    for node in view.projectile_sprites: ordinary.append(node_data(node))
    for node in view.cinematic.beam_parts: beams.append(node_data(node))
    for node in view.weapon_trails: trails.append(node_data(node))
    for particle in view.feedback.particles:
        impacts.append({"id": particle.id, "age": particle.age, "x": particle.x, "height": particle.height, "node": node_data(particle.node)})
    row.merge({"attached_nodes": attached, "projectile_nodes": ordinary, "beam_nodes": beams, "trail_nodes": trails, "impact_nodes": impacts,
        "cinematic_background_node": node_data(view.cinematic.background), "cinematic_portrait_node": node_data(view.cinematic.portrait),
        "main_nodes": {"root": str(view.get_tree().current_scene.get_path()), "view": str(view.get_path()),
            "feedback": str(view.feedback.get_path()), "super_cinematic": str(view.cinematic.get_path()),
            "super_active": view.cinematic.active, "super_background_visible": view.cinematic.background.visible,
            "super_portrait_visible": view.cinematic.portrait.visible}})
    trace.append(row)

func record_still(frame: int, part: int, path: String) -> void:
    stills.append({"frame": frame, "section": part, "path": path})

func save_file(path: String) -> void:
    if trace_saved: return
    if FileAccess.file_exists(path):
        push_error("拒绝覆盖亚刻必杀原trace：" + path)
        return
    var output: FileAccess = FileAccess.open(path, FileAccess.WRITE)
    if output == null:
        push_error("亚刻必杀trace保存失败")
        return
    output.store_string(JSON.stringify({"profile": profile, "trace": trace, "stills": stills, "generated_videos": 0,
        "source": "主游戏训练真实H蓄能/charge_stop→P或J+K，空中真实W后P；双对手双向命中/站防/远落空。980拒绝、1980降一级、2980降二级依现有自动档位；仅开局设站位朝向，组内只送双方InputFrame。"}))
    output.close()
    trace_saved = true
@warning_ignore_restore("integer_division")
