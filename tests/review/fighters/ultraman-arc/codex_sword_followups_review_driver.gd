extends UfeReviewDriver
@warning_ignore_start("integer_division")
const SPAN: int = 120
const SWORD_CASES: Array = ["hit", "stand_guard", "whiff", "rear_hit"]
const THROW_CASES: Array = ["hit", "stand_guard", "whiff"]
const MOVES: Array = ["motion_214", "ranged_forward"]
var sampled_frame: int = -1
var pre_step: Dictionary = {}
var p2: UfeInputFrame = UfeInputFrame.make()
var stills: Array = []
var trace_saved: bool = false

func _init() -> void: profile = "stage6_ultraman_arc_sword_followups"
func section(frame: int) -> int: return mini(frame / SPAN, 27)
func action(frame: int) -> String: return "motion_214" if section(frame) < 16 else "ranged_forward"
func case_id(frame: int) -> String:
    var part: int = section(frame)
    return str(SWORD_CASES[part % 4] if part < 16 else THROW_CASES[(part - 16) % 3])
func combination(frame: int) -> int:
    var part: int = section(frame)
    return part / 4 if part < 16 else (part - 16) / 3
func mirrored(frame: int) -> bool: return combination(frame) % 2 == 1
func capture_length() -> int: return SPAN * 28
func length_frames() -> int: return capture_length() + 2
func boxes(_frame: int) -> bool: return false
func matchup() -> Array: return ["ultraman-arc", "zetton" if combination(review_frame) < 2 else "ultraseven"]
func label(frame: int) -> String:
    return "亚刻 · " + ("214＋I 回身光剑二连" if action(frame) == "motion_214" else "6＋I 光剑掷返") + " · " + case_id(frame) + " · " + ("朝左" if mirrored(frame) else "朝右") + " · 训练试制"

func prepare_match(sim: UfeMatchDirector) -> void:
    var own: UfeFighter = sim.fighters[0]
    var facing: int = -1 if mirrored(review_frame) else 1
    var identity: String = action(review_frame)
    assert(own.definition.moves.has(identity), "亚刻本批剑技尚未安装")
    var move: Dictionary = own.definition.moves[identity]
    assert(UfeMoveData.validate(move), "亚刻本批剑技帧数据不合法")
    var gap: int = int(move.get("review_whiff_gap", 600)) if case_id(review_frame) == "whiff" else int(move.get("review_fixture_gap", 80))
    var side: int = -1 if case_id(review_frame) == "rear_hit" else 1
    own.x = 850 if facing < 0 else 430
    sim.fighters[1].x = own.x + facing * gap * side
    own.facing = facing
    sim.fighters[1].facing = -facing * side
    sampled_frame = -1
    pre_step = {}
    p2 = UfeInputFrame.make()

func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
    sampled_frame = frame
    pre_step = simulation_data(sim)
    var age: int = frame % SPAN
    var facing: int = -1 if mirrored(frame) else 1
    p2 = UfeInputFrame.make(0, 0, UfeInputFrame.GUARD if case_id(frame) == "stand_guard" else 0)
    if action(frame) == "motion_214":
        # 真实2→1→4+I；前两步自然蹲起手，后方目标也不会在出招前被待机自动转身改朝向。
        if age == 0: return UfeInputFrame.make(0, -1)
        if age == 1: return UfeInputFrame.make(-facing, -1)
        if age == 2: return UfeInputFrame.make(-facing, 0, UfeInputFrame.RANGED)
    elif age == 20: return UfeInputFrame.make(facing, 0, UfeInputFrame.RANGED)
    return UfeInputFrame.make()

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
            "weapon_return_anchor": data.get("weapon_return_anchor", []).duplicate()})
    var shots: Array = sim.projectiles.duplicate(true)
    for shot in shots:
        var values: Array = []
        for box in UfeProjectileResolver.world_hitboxes(shot): values.append([box.position.x, box.position.y, box.size.x, box.size.y])
        shot.world_hitboxes = values
    return {"tick": sim.tick, "state_hash": sim.state_hash(), "pair": pair, "hitstop": sim.hitstop,
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
        "camera": [view.camera_x, view.camera_y], "active_attachments": view.attachments_for(0).duplicate(true)})
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
        push_error("拒绝覆盖亚刻本批剑技原trace：" + path)
        return
    var output: FileAccess = FileAccess.open(path, FileAccess.WRITE)
    if output == null:
        push_error("亚刻本批剑技trace保存失败")
        return
    output.store_string(JSON.stringify({"profile": profile, "trace": trace, "stills": stills, "generated_videos": 0,
        "source": "原主游戏main.tscn训练；双对手双向真实214I/6I，214另加背后站位证明首斩。组内只送双方InputFrame，无摆状态/补tick/重置朝向。214两挥刃沿既有单次接触规则；投剑记录完整整数飞行/回程和真实节点。"}))
    output.close()
    trace_saved = true
@warning_ignore_restore("integer_division")
