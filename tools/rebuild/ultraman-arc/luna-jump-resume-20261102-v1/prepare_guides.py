"""月亮基础跳跃接续：离线校验四份既有合同，新增十三份空中整姿guide；零POST。"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

sys.dont_write_bytecode = True
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PYTHON = Path("C:/Users/13080/.codex/venvs/ufeneo/Scripts/python.exe")
OLD = ROOT / "art/fighters/ultraman-arc__luna/stage2/jump-ground-guides-20261102-v2"
DRAFT = ROOT / "art/fighters/ultraman-arc__luna/stage2/jump-preparation-20261102-v1"
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/jump-air-guides-resume-20261102-v1"
OUT = ROOT / "reports/review/2026-11-02/luna-jump-resume-guides-v1"
PRIOR_REPORT = ROOT / "reports/review/2026-11-02/arc-luna-jump-ground-four-guides-v2"
IDENTITY = ROOT / "art/fighters/ultraman-arc__luna/stage2/walk-forward-repair-20261102-v1/references/identity.png"
MEASURES = ROOT / "art/fighters/ultraman-arc__luna/model/measurements.json"
TICKS = {"vertical_jump": [8, 7, 3, 8, 7], "flip_forward": [8, 8, 8, 9], "flip_back": [8, 8, 8, 9]}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


g = load_module("luna_original_ground_guide_helpers", ROOT / "tools/rebuild/ultraman-arc/luna_s2_jump_ground_guides_20261102_v2.py")
sha, read, rel, ref, save = g.sha, g.read, g.rel, g.ref, g.save

# 每张均为独立完整抽象姿态。角度只作用于新几何，不采样或变形人物PNG。
PLANS = [
    dict(action="vertical_jump", phase=0, label="上升初收腿，双臂抬起护胸", torso=0, head=0, near_arm=[113, -44], far_arm=[66, -100], near_leg=[100, 140, 20], far_leg=[65, 140, 0]),
    dict(action="vertical_jump", phase=1, label="上升深收束，胸髋与双臂共同压紧", torso=5, head=5, near_arm=[120, -60], far_arm=[80, -115], near_leg=[140, 45, 25], far_leg=[20, 135, 5]),
    dict(action="vertical_jump", phase=2, label="顶点短平衡，双臂展开双膝松收", torso=-3, head=-3, near_arm=[140, -50], far_arm=[36, -33], near_leg=[130, 68, 20], far_leg=[42, 115, 0]),
    dict(action="vertical_jump", phase=3, label="下落伸腿，双臂收回重建护架", torso=3, head=3, near_arm=[117, -15], far_arm=[60, -70], near_leg=[104, 105, 0], far_leg=[75, 98, 0]),
    dict(action="vertical_jump", phase=4, label="下落末段两靴朝下，留双膝缓冲", torso=4, head=4, near_arm=[114, 0], far_arm=[58, -48], near_leg=[107, 115, 20], far_leg=[65, 72, 10]),
    dict(action="flip_forward", phase=0, label="前翻入势：整胸前卷，双臂环收", torso=40, head=40, near_arm=[100, -75], far_arm=[70, -130], near_leg=[118, 5, 25], far_leg=[48, 155, 5]),
    dict(action="flip_forward", phase=1, label="前翻中段：头右下，髋左上", torso=135, head=135, near_arm=[120, -90], far_arm=[75, -135], near_leg=[150, 25, 20], far_leg=[25, 135, 0]),
    dict(action="flip_forward", phase=2, label="前翻后段：头左下，髋右上", torso=225, head=225, near_arm=[112, -65], far_arm=[85, -140], near_leg=[145, 10, 30], far_leg=[35, 150, 0]),
    dict(action="flip_forward", phase=3, label="完成前翻展开：双腿落回，双臂回护", torso=364, head=364, near_arm=[116, 3], far_arm=[55, -54], near_leg=[107, 115, 20], far_leg=[65, 72, 10]),
    dict(action="flip_back", phase=0, label="后翻入势：后仰抬胸，双臂上提", torso=-35, head=-35, near_arm=[120, -100], far_arm=[80, -145], near_leg=[130, 15, 20], far_leg=[35, 145, 0]),
    dict(action="flip_back", phase=1, label="后翻横身：头左髋右，双腿收卷", torso=-84, head=-84, near_arm=[125, -110], far_arm=[85, -145], near_leg=[145, 20, 25], far_leg=[25, 140, 5]),
    dict(action="flip_back", phase=2, label="后翻倒立：髋上头下，双臂随胸旋转", torso=-180, head=-180, near_arm=[115, -90], far_arm=[75, -140], near_leg=[145, 20, 30], far_leg=[35, 145, 0]),
    dict(action="flip_back", phase=3, label="完成后翻展开：双臂从上方回护", torso=-364, head=-364, near_arm=[105, -18], far_arm=[65, -62], near_leg=[109, 113, 20], far_leg=[65, 72, 10]),
]


def new_points(master, plan):
    hip = [128, 174.3]
    points = {"hip_center": hip}
    turn = lambda v: g.rotate(v, plan["torso"])
    for key in ["near_shoulder", "far_shoulder", "neck_base", "near_hip", "far_hip"]:
        points[key] = g.add(hip, turn(g.sub(master[key], master["hip_center"])))
    for key in ["skull_top", "chin", "ear", "eye"]:
        points[key] = g.add(points["neck_base"], g.rotate(g.sub(master[key], master["neck_base"]), plan["head"]))
    for side in ["near", "far"]:
        upper = math.dist(master[side + "_shoulder"], master[side + "_elbow"])
        fore = math.dist(master[side + "_elbow"], master[side + "_wrist"])
        a, b = plan[side + "_arm"]
        points[side + "_elbow"] = g.add(points[side + "_shoulder"], turn(g.vector(upper, a)))
        points[side + "_wrist"] = g.add(points[side + "_elbow"], turn(g.vector(fore, b)))
        points[side + "_fist"] = g.add(points[side + "_wrist"], turn(g.vector(7, b)))
        thigh = math.dist(master[side + "_hip"], master[side + "_knee"])
        shin = math.dist(master[side + "_knee"], master[side + "_ankle"])
        foot = math.dist(master[side + "_ankle"], master[side + "_toe"])
        a, b, c = plan[side + "_leg"]
        points[side + "_knee"] = g.add(points[side + "_hip"], turn(g.vector(thigh, a)))
        points[side + "_ankle"] = g.add(points[side + "_knee"], turn(g.vector(shin, b)))
        points[side + "_toe"] = g.add(points[side + "_ankle"], turn(g.vector(foot, c)))
    return points


def segment_lengths(points):
    pairs = [["skull_top", "chin"], ["neck_base", "hip_center"]]
    for side in ["near", "far"]:
        pairs.extend([[side + "_" + a, side + "_" + b] for a, b in [("shoulder", "elbow"), ("elbow", "wrist"), ("hip", "knee"), ("knee", "ankle"), ("ankle", "toe")]])
    return {"/".join(pair): math.dist(points[pair[0]], points[pair[1]]) for pair in pairs}


def dry_run(brief_path, label):
    brief = read(brief_path)
    arguments = [str(PYTHON), str(ROOT / "tools/art_pipeline.py"), "concept", "--brief", str(brief_path), "--out", str(ART / "not-submitted" / (label + ".png")), "--dry-run"]
    for attachment in brief["references"]:
        path = ROOT / attachment["path"]
        assert sha(path) == attachment["sha256"], path
        arguments.extend(["--reference", str(path)])
    result = subprocess.run(arguments, cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["request"]["quality"] == "high" and data["request"]["size"] == "1024x1024"
    assert data["request"]["background"] == "transparent" and data["reference_count"] == 2
    assert data["request"]["model"].startswith("gpt-image-") and data["endpoint"] == "/images/edits"
    path = OUT / "client-dry-runs" / (label + ".json")
    save(path, {"network_allowed_by_tool": False, "command": arguments, "result": data, "stderr": result.stderr, "output_image_written": False})
    assert not Path(data["output"]).exists()
    return ref(path)


def main():
    assert not ART.exists() and not OUT.exists()
    assert sha(OLD / "four-guide-contract.json") == "342b141b5e0d67c0f83cfecabb4fd7aafa8d4f62ae6f2b9b02825316b16ae0ea"
    assert sha(IDENTITY) == "d70d0f5fba22d54281b50703158ac2ba8ff1d29624f3020b4bdbe7c20992a6da"
    assert sha(MEASURES) == "2a55b6bc6f5ed8a0fd081bc1fd9b1dfbb7d936c094e978e0a08727ad6429d40c"
    prior_paths = [p for folder in [OLD, DRAFT] for p in folder.rglob("*") if p.is_file()]
    prior_paths.extend([IDENTITY, MEASURES, PRIOR_REPORT / "root-preflight-v1/root-acceptance.json"])
    protected = {rel(path): sha(path) for path in prior_paths}
    ART.mkdir(parents=True)
    OUT.mkdir(parents=True)
    accepted = read(PRIOR_REPORT / "root-preflight-v1/root-acceptance.json")
    assert accepted["authority"] == "root_delegated_by_user" and accepted["root_actual_images_opened"]
    assert accepted["contract_sha256"] == sha(OLD / "four-guide-contract.json")
    ground_rows = []
    for entry in read(OLD / "four-guide-contract.json")["requests_preparation_only"]:
        for name in ["brief", "prompt", "guide", "pose_target", "JPEG_preview"]:
            path = ROOT / entry[name]["path"]
            assert sha(path) == entry[name]["sha256"]
        brief_path = ROOT / entry["brief"]["path"]
        brief = read(brief_path)
        assert [row["sha256"] for row in brief["references"]] == [entry["guide"]["sha256"], sha(IDENTITY)]
        assert (ROOT / entry["prompt"]["path"]).read_text("utf-8").strip() == brief["prompt"].strip()
        preview = ROOT / entry["JPEG_preview"]["path"]
        with Image.open(preview) as im:
            assert im.format == "JPEG" and im.width <= 768 and preview.stat().st_size <= 150000
        ground_rows.append({"action": entry["action"], "phase": entry["phase"], "brief": ref(brief_path), "references": copy.deepcopy(brief["references"]), "project_client_dry_run": dry_run(brief_path, entry["action"] + "-" + str(entry["phase"]))})
    master = read(OLD / "four-guide-contract.json")["master_projected_planning_points"]
    lengths = segment_lengths(master)
    rows = []
    for plan in PLANS:
        action, phase = plan["action"], plan["phase"]
        path = ART / action / f"phase-{phase:02d}"
        path.mkdir(parents=True)
        points = new_points(master, plan)
        actual = segment_lengths(points)
        assert max(abs(actual[key] - value) for key, value in lengths.items()) < 1e-10
        # 完整几何点必须有布局余量；不通过逐相缩放来迁就画布。
        client = {key: g.xy(point) for key, point in points.items()}
        assert all(40 <= v <= 984 for point in client.values() for v in point), (action, phase, client)
        note = "髋/胸表面仅作虚拟根规划；不含世界跳高。整头与双臂随胸旋转，不能画正立脸或换近远肢。"
        guide = path / "pose-guide.png"
        picture = g.make_guide(guide, points, f"{action} {phase:02d} / {plan['label']}", note)
        preview_path = OUT / f"{action}-{phase:02d}-whole-guide.jpg"
        preview = g.jpeg(preview_path, picture.resize((768, 768), Image.Resampling.LANCZOS))
        ticks = TICKS[action]
        start, stop = sum(ticks[:phase]), sum(ticks[:phase + 1])
        visible_indices = list(range(max(2, start), min(33, stop)))
        target_path = path / "pose-target.json"
        save(target_path, {"action": action, "phase": phase, "authored_plan": plan, "native_planned_points": points, "client1024_planned_points": client, "virtual_root_client1024": [512, 960], "runtime_root_candidate": [160, 280], "master_surface_proxy_lengths": lengths, "planned_surface_proxy_lengths": actual, "input_relative_n_prediction": visible_indices, "not_source_measurements": True, "not_anatomical_bone_acceptance": True, "no_person_pixels_used": True, "no_runtime_rig": True})
        brief = copy.deepcopy(read(DRAFT / "drafts" / action / f"phase-{phase:02d}" / "brief.json"))
        brief["id"] = f"arc_luna_{action}_{phase:02d}_whole_air_guided_resume_20261102_v1"
        prompt = brief["prompt"].replace("IMAGE 1 is the accepted LUNA IDENTITY MASTER.", "IMAGE 2 is the accepted LUNA IDENTITY MASTER.")
        prompt = ("IMAGE 1 is a NEW COMPLETE ABSTRACT POSE GUIDE ONLY. IMAGE 2 is the accepted LUNA IDENTITY MASTER. White chains are the BRIGHT NEAR left limbs, dark chains are the DARK FAR right limbs; the same identities persist through the whole rotation. Draw exactly one NEW complete natural person in this guide pose, with image 2's body mass, head-shell size, armor silhouette and red/silver lower legs. NO BLUE shin/calf/boot armor. The guide's geometry, lines, circles, arrows, labels and background must never appear in the returned person. Both complete arms and shoulders, chest, pelvis and both complete legs change together. Redraw every body surface, face and armor in the planned orientation; never rotate, mirror, cut or paste an existing person PNG.\n" + prompt + f"\nComplete-pose direction: {plan['label']}。The abstract torso/head angle is {plan['torso']} degrees in screen-y-down space; it describes this new whole person, never an instruction to transform old pixels. Registration root is virtual, not the lowest boot or a ground contact. The simulation supplies all jump height and travel. 透明背景。\n")
        brief.update(prompt=prompt, references=[ref(guide), ref(IDENTITY)], source_sha256=sha(IDENTITY), guide_only_not_final_art=True, root_POST_decision_pending=True, root_pre_post_review_required=True, preparation_only_no_post=True, not_installed=True, pose_target=ref(target_path), supersedes_only_for_future_review=ref(DRAFT / "drafts" / action / f"phase-{phase:02d}" / "brief.json"))
        brief_path = path / "brief.json"
        save(brief_path, brief)
        prompt_path = path / "prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
        rows.append({"action": action, "phase": phase, "title": plan["label"], "brief": ref(brief_path), "guide": ref(guide), "pose_target": ref(target_path), "prompt": ref(prompt_path), "JPEG_preview": preview, "predicted_air_n": visible_indices, "source_table_ticks": ticks[phase], "actual_air_ticks_prediction": len(visible_indices), "returned_source": None, "root_actual_guide_review": False})
    assert len(rows) == 13 and len({read(ROOT / row["brief"]["path"])["prompt"] for row in rows}) == 13
    # 能力检查仅记录本机可用工具；不调用任何媒体路由或生成服务。
    doctor = Path("C:/Users/13080/.codex/skills/generate2dmedia/scripts/forge_doctor.py")
    doctor_result = subprocess.run([str(PYTHON), str(doctor), "--host-tools", "none", "--save", str(OUT / "forge-doctor.json")], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", check=False)
    save(OUT / "forge-doctor-receipt.json", {"exit_code": doctor_result.returncode, "stdout": doctor_result.stdout, "stderr": doctor_result.stderr, "no_media_route_called": True})
    assert doctor_result.returncode == 0
    assert all(sha(ROOT / name) == value for name, value in protected.items())
    contract = {"schema": "ufeneo.arc-luna.s2.jump-resume-guides.v1", "fighter": "ultraman-arc__luna", "prepared_by": "/root/luna_jump_resume", "same_complete_identity": ref(IDENTITY), "existing_ground_contract": ref(OLD / "four-guide-contract.json"), "existing_root_preflight": ref(PRIOR_REPORT / "root-preflight-v1/root-acceptance.json"), "existing_four_briefs_ready_for_root_client_submission": ground_rows, "new_air_guide_briefs_for_root_review": rows, "new_guides_use_no_person_pixels": True, "old_sources_or_drafts_rewritten": False, "all_17_final_person_sources_still_required": True, "trajectory_driven_required": True, "loop": False, "absolute_clock_only_source_arithmetic": ref(PRIOR_REPORT / "absolute-clock-and-state-key-map.json"), "air_consumes_absolute_n2_through_n32": True, "runtime_not_started": True, "POST_count": 0, "actual_cost_USD": 0, "budget_policy_note": "根按最新授权每新请求预占1美元、累计60及旧未知10占额；本工具不读写预算/密钥，不据旧根预审中的10美元历史阻停，也不代根批准POST。", "strict_dimensions_accepted": False, "new_person_art_accepted": False, "main_or_replay_accepted": False, "playable_or_transform_opened": False, "remaining": ["起跳2、垂直5、前翻4、后翻4、落地2的真实本人整源", "逐源实际Alpha、头壳与身体尺寸、相邻动作和共同159整图注册", "实际main双向720/1080自然8/9/7输入和原双方InputFrame独立回放", "追击跳、空攻与其它S2-S7不在本次基础跳跃合同内"]}
    save(ART / "jump-resume-contract.json", contract)
    save(OUT / "preflight-receipt.json", {"contract": ref(ART / "jump-resume-contract.json"), "first_ready_ground_brief": ground_rows[0], "protected_original_bytes": [{"path": key, "sha256": value} for key, value in protected.items()], "POST_count": 0, "new_person_frames_or_atlas": False, "Godot_started": False, "product_written": False, "git_written": False, "guide_visual_review": "pending actual view, record separately"})
    print(json.dumps({"contract": rel(ART / "jump-resume-contract.json"), "sha256": sha(ART / "jump-resume-contract.json"), "ground_client_dry_runs": len(ground_rows), "new_air_guides": len(rows), "POST_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
