extends "res://tests/review/fighters/ultraman-arc/codex_sword_followups_review_driver.gd"
## 复用完整节点/世界框快照，欧米伽只覆写本次真实输入和分组。
const CASES: Array = ["hit", "stand_guard", "crouch_guard", "whiff", "baseline"]
func _init() -> void: profile = "stage6_ultraman_omega_weapon_throws"
func section(frame: int) -> int: return mini(frame / 120, 39)
func action(frame: int) -> String: return "ranged_forward" if section(frame) < 20 else "motion_214"
func case_id(frame: int) -> String: return str(CASES[section(frame) % 5])
func combination(frame: int) -> int: return (section(frame) % 20) / 5
func capture_length() -> int: return 120 * 40
func matchup() -> Array: return ["ultraman-omega", "zetton" if combination(review_frame) < 2 else "ultraseven"]
func label(frame: int) -> String:
    return "欧米伽 · " + ("6＋I 头镖直投" if action(frame) == "ranged_forward" else "214＋I 头镖弧回") + " · " + case_id(frame) + " · " + ("朝左" if mirrored(frame) else "朝右") + " · 训练试制"
func sample(frame: int, sim: UfeMatchDirector) -> UfeInputFrame:
    sampled_frame = frame
    pre_step = simulation_data(sim)
    var age: int = frame % 120
    var facing: int = -1 if mirrored(frame) else 1
    var kind: String = case_id(frame)
    p2 = UfeInputFrame.make(0, -1 if kind == "crouch_guard" else 0, UfeInputFrame.GUARD if kind in ["stand_guard", "crouch_guard"] else 0)
    var button: int = 0 if kind == "baseline" else UfeInputFrame.RANGED
    if action(frame) == "motion_214":
        if age == 0: return UfeInputFrame.make(0, -1)
        if age == 1: return UfeInputFrame.make(-facing, -1)
        if age == 2: return UfeInputFrame.make(-facing, 0, button)
    elif age == 20: return UfeInputFrame.make(facing, 0, button)
    return UfeInputFrame.make()
func save_file(path: String) -> void:
    if trace_saved: return
    if FileAccess.file_exists(path):
        push_error("拒绝覆盖欧米伽掷返原trace")
        return
    var output: FileAccess = FileAccess.open(path, FileAccess.WRITE)
    if output == null:
        push_error("欧米伽掷返trace无法保存")
        return
    output.store_string(JSON.stringify({"profile": profile, "trace": trace, "stills": stills, "generated_videos": 0,
        "source": "原主游戏main.tscn训练；双对手双向真实6I/214I；组内只送双方InputFrame，无摆攻击状态、补tick或重置朝向。唯一独立头镖完整整数外飞/回程和真实节点。"}))
    output.close()
    trace_saved = true
