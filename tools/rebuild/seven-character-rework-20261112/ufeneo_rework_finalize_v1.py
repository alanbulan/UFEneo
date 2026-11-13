"""把三角色只读测量结果收口为正式诊断交付。

只写自己负责的三个 rework-20261112 目录；不生成图片，不改 assets/content，不提交。
证据来源：各目录 measurement_evidence.json 与仓库内已读的规范、MOVES.md、联系表。
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]

import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image
import numpy as np

ROOT = _layout_root
FIGHTERS = ("ultraman-zero", "ultraman-justice", "ultraman-gaia")
REVIEW_DIR = ROOT / "reports/review/2026-11-12/seven-character-defects"
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
POLICY = ROOT / "content/presentation/charge_overlay_policy.json"
STORYBOARD_CLIPS = [
    "idle", "walk_forward", "walk_back", "light1", "light2", "light3", "heavy",
    "special", "special2", "special3", "air_special", "dash_throw", "launcher",
    "hit_mid", "down", "ko", "win", "guard", "turn",
    "charge_start", "charge", "charge_stop",
]

DISPLAY = {
    "ultraman-zero": "赛罗奥特曼 · 基本红蓝形态",
    "ultraman-justice": "杰斯提斯奥特曼 · 标准型",
    "ultraman-gaia": "盖亚奥特曼 · V2",
}
IDLE_PIXEL = {
    "ultraman-zero": "art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png",
    "ultraman-justice": "art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png",
    "ultraman-gaia": "art/fighters/ultraman-gaia/stage1/idle/frames/identity-idle-pixel.png",
}
PARTS = {
    "ultraman-zero": "双头镖自额前向头顶后上方折起、蓝额灯、黄眼、蓝计时器、层叠银蓝肩胸甲；无披风",
    "ultraman-justice": "中央高窄银冠、深色面罩与口部板、青绿额灯/胸灯、薄贴身肩甲；标准型无披风",
    "ultraman-gaia": "V2 金额刃、浅黄眼、宽黑内带金边 V 字胸甲、青蓝三角胸灯、红银 V2 躯体；无披风",
}
OFFICIAL_SIDE = {
    "ultraman-zero": {
        "path": "art/fighters/ultraman-zero/stage1/idle/references/zero-side-head-official.png",
        "source": "圆谷官方 2024 Zero15 拍立得右侧近侧脸裁图",
        "url": "https://tsuburaya-prod.com/news/7732",
        "angle": "人物朝画面右方的右侧近侧脸；只核头/颈/上胸，不是全身 90° 侧视",
        "orientation": "朝右",
    },
    "ultraman-justice": {
        "path": "art/fighters/ultraman-justice/stage1/idle/references/justice-side-head-ugf-head-neck.png",
        "source": "UGF 官方剧照左位真右侧视头/颈裁图；工具记录见 tools/rebuild/ultraman-justice/README.md:273",
        "url": None,
        "angle": "真右侧头/颈，身体不是全身纯侧视；官方四图为正面/3/4，不冒充 90° 侧视",
        "orientation": "朝右",
    },
    "ultraman-gaia": {
        "path": None,
        "source": None,
        "url": None,
        "angle": "内容缺口：仓库没有本人 90° 真实侧视来源；hero_gaia-1.png 是正面中立，ref-01.webp 是正面偏 3/4 格斗架势",
        "orientation": "装机帧朝右，但侧视标志结构前后方向未由真实侧视来源签定",
    },
}
OFFICIAL_FULL = {
    "ultraman-zero": ("art/fighters/ultraman-zero/sources/tsuburaya-zero/hero-zero.png", "圆谷官方角色页正面全身立像", "https://tsuburaya-prod.com/heroes/ultraman-zero"),
    "ultraman-justice": ("art/fighters/ultraman-justice/sources/tsuburaya-justice-2019/official-standard-01.png", "圆谷官方 Standard Mode 正面直立", "https://tsuburaya-prod.com/heroes/ultraman-justice"),
    "ultraman-gaia": ("art/fighters/ultraman-gaia/sources/official-pose-20261109-hero/hero_gaia-1.png", "圆谷官方 V2 正面中立", "https://tsuburaya-prod.com/heroes/ultraman-gaia"),
}
RECOGNITION = {
    "ultraman-zero": {"palette": [[45, 201, 248], [106, 211, 250], [24, 148, 224], [246, 197, 28], [252, 227, 64]], "names": ["蓝额灯/青蓝光束色", "黄眼", "蓝计时器"]},
    "ultraman-justice": {"palette": [[2, 177, 172], [14, 204, 199], [15, 143, 127]], "names": ["青绿额灯", "青绿胸灯"]},
    "ultraman-gaia": {"palette": [[8, 200, 211], [18, 225, 240], [245, 224, 36], [251, 247, 215]], "names": ["青蓝三角胸灯", "浅黄眼/金额刃"]},
}
KNOWN_VISUAL_FX = {
    "ultraman-zero": [{"clip": "light1", "frame": 2, "finding": "青白掌前光块/碎块；4 邻域 16 块、8 邻域 15 块，(45,201,248) 954 px", "sheet": "ultraman-zero_A.png"}],
    "ultraman-justice": [{"clip": "special3", "frame": 3, "finding": "红色 V 形光刃；虽 4/8 邻域均 1 连通，联系表目视确认已烘焙特效", "sheet": "ultraman-justice_B.png"}],
    "ultraman-gaia": [
        {"clip": "special3", "frame": 9, "finding": "橙红光刃；单连通不等于无 FX，亮黄/红像素 1104 px、主体高 158", "sheet": "ultraman-gaia_B.png"},
        {"clip": "ranged_forward", "frame": 4, "finding": "4/8 邻域均 6 块，主体 6215 px，独立块 502 px", "sheet": "联系表与逐帧重算"},
        {"clip": "ranged_forward", "frame": 5, "finding": "4/8 邻域均 2 块，主体 5732 px，独立块 298 px", "sheet": "联系表与逐帧重算"},
    ],
}
ROOT_CAUSES = {
    "ultraman-zero": [
        "时间轴接线错：state_frames.idle 60 行 sprite 0–5 对装机 1 帧、walk_forward 70 行 0–7 对装机 4 帧；side_view.gd:450 clampi 到末帧，待机/前走后段静默冻结。",
        "站姿类整人缩放：heavy 高度 130/165/128/155、launcher#4 213、intro#0 104；对锚 172 的姿态感知偏差 32 帧、相邻跳变 24 组。",
        "人物帧与 FX 未分离、动作模板化：light1#2 青白掌前光块与 16 个独立连通块；三槽联系表仍是护架/单臂前伸/双掌前推近似姿势。",
    ],
    "ultraman-justice": [
        "身份锚字节链断裂：requests.json 签署 SHA e1dbee… 的 192×192 锚在仓库中找不到；现用 idle-candidate-04-cell.png 是 256×256、SHA f9de9f…，且当前装机待机与 4× 图不同色板，青绿识别色在装机帧缺失。",
        "三槽运行时效果差异化不足：special/special2/special3/air_special 都引用 justice_fx_beam，仅改 spawn/length/thickness；与 MOVES.md 三槽不同技能、不同效果冲突；air_special 在 MOVES.md 明写「不适用」。",
        "帧序/体型/烘焙 FX 同时失守：special3#3 红色光刃、待机 1 帧与前后走 4 帧、motion_214/236/623 跳过中间 sprite；姿态感知偏差 43 帧、相邻跳变 25 组。",
    ],
    "ultraman-gaia": [
        "身份门内容缺口：仓库没有本人 90° 真实侧视来源，金额刃/头壳侧视前后方向不能由正面或 3/4 图猜写；MOVES.md 开头仍写「未安装」，与当前装机数据不一致。",
        "人物帧仍含烘焙特效与双重特效：special3#9 橙红光刃、ranged_forward#4/#5 独立块 502/298 px；投射类手中不得画弹体。",
        "尺度与接线口径冲突：cells.json 顶层 anchor [96,184] 与装机 clip [128,248] 不一致，definition.json 也保留旧 [96,184]/target_height 184；motion_623#3 高度 227、special3 多帧 134–143；姿态感知偏差 42 帧、相邻跳变 26 组。",
    ],
}
SHARED_NO_HASH = {"impact_guard", "impact_heavy", "impact_light", "beam_hit"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jload(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def jdump(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def absolute(rel: str | None) -> str | None:
    return str(ROOT / rel) if rel else None


def visible_palette(path: Path) -> list[list[int]]:
    a = np.asarray(Image.open(path).convert("RGBA"))
    mask = a[:, :, 3] >= 128
    colors = np.unique(a[:, :, :3][mask].reshape(-1, 3), axis=0)
    return [[int(v) for v in row] for row in colors]


def posture_exceptions(ev: dict) -> list[str]:
    return sorted(name for name, c in ev["clips"].items() if c["standing"]["classification"] == "posture_exception")


def move_spawn_examples(fighter: str) -> dict:
    out = {}
    for mid in ("special", "special2", "special3", "air_special", "ranged_forward", "pulse"):
        p = ROOT / "content/fighters" / fighter / "moves" / f"{mid}.json"
        if not p.is_file():
            continue
        d = jload(p)
        points = []
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in {"spawn", "anchor", "beam_origin", "return_anchor"} and isinstance(v, list) and len(v) == 2:
                        points.append({k: [int(x) if isinstance(x, (int, float)) else x for x in v]})
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(d)
        seen, uniq = set(), []
        for x in points:
            s = json.dumps(x, ensure_ascii=False, sort_keys=True)
            if s not in seen:
                seen.add(s)
                uniq.append(x)
        out[mid] = uniq[:8]
    return out


def final_category(fighter: str, name: str, auto: str) -> tuple[str, list[str], str]:
    if name in STORYBOARD_CLIPS:
        if fighter == "ultraman-zero" and name in {"idle", "walk_forward"}:
            return "fix_timeline", ["redraw"], "任务书点名：state_frames 越界冻结；同时须重做真呼吸/八相走路，不能只改数据"
        return "redraw", [], "任务书 §1.2/§1.3 点名：待机/走路/三槽/基础攻防/倒地胜利等存在模板化、帧数不足或需纯人物重画；联系表目视不支持 keep"
    return auto, [], "自动数值分类；联系表未逐帧覆盖，keep 只表示未触发数值门，不表示造型通过"


def stats(ev: dict, finals: dict) -> dict:
    primary = Counter(v["primary_category"] for v in finals.values())
    secondary = Counter(c for v in finals.values() for c in v["secondary_categories"])
    four = {
        "保留": primary["keep"],
        "修尺度/姿态/身份": primary["fix_scale"] + primary["fix_pose"] + primary["fix_identity"],
        "重画": primary["redraw"],
        "数据帧序修复": primary["fix_timeline"],
    }
    return {"primary": dict(sorted(primary.items())), "secondary": dict(sorted(secondary.items())), "four_groups": four,
            "clip_count": len(finals), "frame_count": sum(c["frame_count"] for c in ev["clips"].values())}


def identity_card(fighter: str, ev: dict) -> dict:
    cells_path = ROOT / "art/fighters" / fighter / "stage1/cells/cells.json"
    cells = jload(cells_path)
    idle_pixel = ROOT / IDLE_PIXEL[fighter]
    idle_clip = ev["clips"]["idle"]
    side = OFFICIAL_SIDE[fighter].copy()
    if side["path"]:
        side["absolute_path"] = absolute(side["path"])
        side["sha256"] = sha(ROOT / side["path"])
    full_path, full_angle, full_url = OFFICIAL_FULL[fighter]
    palette = cells.get("palette") or visible_palette(idle_pixel)
    palette = [[int(v) for v in c] for c in palette]
    conflicts = []
    if fighter == "ultraman-zero":
        conflicts += [
            "cells.json 早期字段 target_standing_height=188 是身份锚原生站高；2026-11-11 重标定后装机站高 172、scale 0.158767，本卡片以后者为唯一返工尺度。",
            "definition.json presentation.cell=288/target_height=188 是旧口径；装机 113 个 clip 为 256、air_special 为 288。",
            "assets/fighters/ultraman-zero/catalogue/model-native.png 的 32 色与冻结动作色板交集为 0；不可直接跑 stage_cells.py 默认色板。",
        ]
    elif fighter == "ultraman-justice":
        conflicts += [
            "requests.json / super_portrait/REPORT.md / tools/rebuild/ultraman-justice/README.md 记录已签锚 SHA e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d、192×192、root [96,184]；仓库内按 SHA 全盘查找无此文件。",
            "现用 idle-candidate-04-cell.png 为 256×256、SHA f9de9f2d…、站高 161；装机 idle/atlas.png 为 256×256、SHA d2ab7f80…、站高 161。",
            "4× 文件 idle-candidate-04-x4.png 保留青绿识别色 128 px，但当前 256 格锚与装机待机的青绿识别色为 0；cells.json 没有保存完整 32 色板，必须回源重建并冻结后再出动作帧。",
            "definition.json presentation.cell=288/target_height=184 与装机 256/161 不一致；另有 4 个 clip 仍为 192 格、root [96,184]。",
        ]
    else:
        conflicts += [
            "没有本人 90° 真实侧视来源；金额刃/头壳侧视前后方向禁止凭正面或 3/4 图写进生成规格。",
            "cells.json 顶层 anchor [96,184] 与全部装机 clip anchor [128,248] 不一致；definition.json 也保留 [96,184]/target_height 184。",
            "图鉴 model-native.png 色板与冻结动作色板交集为 0；不可直接跑 stage_cells.py 默认色板。",
            "MOVES.md 开头仍写未生成动作/未写 moves/未安装，是旧草案，不作为当前状态证明。",
        ]
    return {
        "fighter": fighter,
        "display": DISPLAY[fighter],
        "authority": "诊断代理只读复算；root_delegated_by_user 规则沿用，不冒称用户亲审",
        "idle_pixel_whole_frame": {
            "absolute_path": str(idle_pixel), "sha256": sha(idle_pixel),
            "size": list(Image.open(idle_pixel).size), "alpha": [0, 255],
            "visible_colors": len(visible_palette(idle_pixel)),
            "role": "动作帧唯一身份锚；4× 图只核配色/像素块，不单独作动作参考",
        },
        "installed_idle_atlas": {
            "absolute_path": absolute(idle_clip["atlas_path"]), "sha256": idle_clip["atlas_sha256"],
            "cell": idle_clip["cell"], "anchor": idle_clip["anchor"], "rects": idle_clip["rects"], "ticks": idle_clip["ticks"],
            "subject_height": idle_clip["frames"][0]["height"], "subject_bbox": idle_clip["frames"][0]["bbox"],
        },
        "production_reference": {"absolute_path": absolute(ev["identity"]["production_reference"]),
                                  "sha256": sha(ROOT / ev["identity"]["production_reference"])},
        "official_side": side,
        "official_full": {"absolute_path": absolute(full_path), "sha256": sha(ROOT / full_path), "angle": full_angle, "url": full_url},
        "official_extra": ({"absolute_path": str(ROOT / "art/fighters/ultraman-gaia/sources/ref-01.webp"),
                            "sha256": sha(ROOT / "art/fighters/ultraman-gaia/sources/ref-01.webp"),
                            "angle": "正面偏 3/4 格斗架势；不冒充 90° 侧视"} if fighter == "ultraman-gaia" else None),
        "orientation": ev["identity"]["orientation"],
        "structure": ev["identity"]["structure"],
        "front_back_criterion": ev["identity"]["relative_test"],
        "head_top_rule": "头部列带（眼列 x 左右各约 26 px）内最上方本体像素；禁止整帧 Alpha 最高行，披风/举拳/头镖外伸展件不算冠顶",
        "cell": {"width": cells.get("cell"), "anchor": cells.get("anchor"), "baseline": idle_clip["anchor"][1], "foot_row": idle_clip["anchor"][1] - 1},
        "standing_height_baseline": cells.get("target_standing"),
        "unique_scale": cells.get("scale"),
        "scale_source": cells.get("scale_source"),
        "per_clip_cell_policy": "逐 clip 取自身 cell/anchor/rects/ticks；288 或 192 格不得用第一组尺寸缩放其余组，不得回落顶层旧 anchor",
        "frozen_palette": {"size": len(palette), "colors": palette, "source": str(cells_path),
                           "recognition_colors": RECOGNITION[fighter],
                           "whole_image_mapping": True, "max_colors": 32,
                           "status": "可用基线" if fighter != "ultraman-justice" else "当前装机可见色基线；青绿识别色缺失，返工前须回源重建并冻结"},
        "limb_thickness_basis": ev["identity"]["limb_basis"],
        "identity_parts": PARTS[fighter],
        "recognition": ev["identity"]["recognition"],
        "allowed_posture_exceptions": posture_exceptions(ev),
        "exception_rule": "蹲/躺/被投/腾空/真实屈膝压低/披风展开允许高度变化，但必须逐帧登记数值并用头壳/骨长证明是姿势，不以「例外」放行整人缩放",
        "visual_review": "已看 seven_idle.png、seven_walk_forward.png、seven_special.png、grid_defects.png、cross_* 与本角色 _A/_B 联系表；站距/色数/Alpha 不冒充造型通过",
        "conflicts_and_gaps": conflicts,
    }


def clip_diagnosis(fighter: str, ev: dict) -> tuple[dict, dict]:
    finals = {}
    clips = {}
    known = KNOWN_VISUAL_FX[fighter]
    phase3 = jload(PHASE3)
    for name, c in sorted(ev["clips"].items()):
        primary, secondary, note = final_category(fighter, name, c["category"])
        if fighter == "ultraman-zero" and name in {"motion_214", "motion_236", "motion_623"}:
            secondary = sorted(set(secondary + ["fix_timeline"]))
        if fighter == "ultraman-justice" and name in {"motion_214", "motion_236", "motion_623"}:
            secondary = sorted(set(secondary + ["fix_timeline"]))
        if fighter == "ultraman-gaia" and name == "air_special":
            secondary = sorted(set(secondary + ["fix_identity", "redraw"]))
        independent = [{"frame": i, "components4": m["components4"], "components8": m["components8"],
                        "component_sizes4": m["comp4_sizes"], "component_sizes8": m["comp8_sizes"]}
                       for i, m in enumerate(c["frames"]) if m["components4"] > 1 or m["components8"] > 1]
        confirmed = [x for x in known if x["clip"] == name]
        auto_candidates = c["baked_fx"]["candidates"]
        timeline = {"state_frames": c["state_frames"], "move_frames": c["move_frames"]}
        skill = None
        if name in {"special", "special2", "special3", "air_special"}:
            mf = ev["content_files"].get(name, {})
            skill = {
                "basis": ev["moves_basis"][{"special": "s1", "special2": "s2", "special3": "s3", "air_special": "air"}[name]],
                "startup_active_recovery": [mf.get("startup"), mf.get("active"), mf.get("recovery")],
                "sprite_unique": c["move_frames"]["sprite_unique"] if c["move_frames"] else None,
                "runtime_effect_ids": sorted(set(mf.get("effect_ids", []))),
                "body_phase_verdict": "联系表显示模板化护架/前伸/平推，未证明本人起手→发力→收势；须按 storyboard.md 重画，不把 16 帧 × 10 tick 自动等同动作完成",
            }
        row = {
            "primary_category": primary,
            "secondary_categories": secondary,
            "category_note": note,
            "auto_category": c["category"],
            "auto_reasons": c["category_reasons"],
            "frame_count": c["frame_count"], "cell": c["cell"], "anchor": c["anchor"], "ticks": c["ticks"],
            "loop": c["loop"], "atlas_absolute_path": absolute(c["atlas_path"]),
            "atlas_sha256": c["atlas_sha256"], "atlas_sha_match": c["atlas_sha_match"],
            "frames": [{"frame": i, "height": m["height"], "width": m["width"], "bbox": m["bbox"],
                        "area": m["area"], "components4": m["components4"], "components8": m["components8"],
                        "colors": m["colors"], "alpha_levels": m["alpha_levels"], "head_band_top": m["head_band_top"]}
                       for i, m in enumerate(c["frames"])],
            "standing": c["standing"],
            "silhouette": {"root_pair_diffs": c["diff"]["pair_diffs"],
                           "bbox_aligned_pair_diffs": c["diff"]["bbox_aligned_pair_diffs"],
                           "below_gate_pairs": c["diff"]["below_gate_pairs"], "gate": c["diff"]["gate"],
                           "loop_pair_diff": c["diff"]["loop_pair_diff"],
                           "loop_bbox_aligned_diff": c["diff"]["loop_bbox_aligned_diff"],
                           "loop_ok_diagnostic": c["diff"]["loop_ok"],
                           "loop_rule": "循环首尾须目视可接；诊断辅助门 root/bbox 差分 <0.20，非画面通过"},
            "baked_fx": {
                "confirmed_by_contact_sheet": confirmed,
                "independent_component_frames": independent,
                "high_chroma_candidates": auto_candidates,
                "candidate_calibration": "高饱和亮色候选大量来自本人红银/深蓝本体，不单独判为烘焙 FX；真实判定取独立连通块 + 联系表目视",
                "hard_rule": "人物帧只剩本体，光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物全在运行时；投射类手中不得画弹体",
            },
            "timeline": timeline,
            "skill_phase": skill,
            "storyboard_required": name in STORYBOARD_CLIPS or primary == "redraw",
            "visual_review_status": ("联系表抽样已看，仍须原生格与 4× 逐帧目视" if name in STORYBOARD_CLIPS else "未逐帧目视；数值保留不等于造型通过"),
        }
        finals[name] = {"primary_category": primary, "secondary_categories": secondary}
        clips[name] = row
    st = stats(ev, finals)
    idle_count = ev["clips"]["idle"]["frame_count"]
    walk_counts = {k: ev["clips"][k]["frame_count"] for k in ("walk_forward", "walk_back") if k in ev["clips"]}
    state_oob = [{"clip": k, "rows": v["frame_count"], "clip_frames": v["clip_frames"], "sprite_max": v["sprite_max"],
                  "longest_same_sprite": v["longest_same_sprite"], "frozen_segments": v["frozen_segments"]}
                 for k, v in ev["state_frames"].items() if v["oob"] or v["frozen_segments"]]
    move_unused = [{"move": k, "clip_frames": v["clip_frames"], "sprite_unique": v["sprite_unique"],
                    "unused_sprites": v["unused_sprites"]}
                   for k, v in ev["move_frames"].items() if v["unused_sprites"]]
    reg = ev["effect_registration"]
    shared = sorted(eid for eid in reg if eid in SHARED_NO_HASH and reg[eid].get("registered") and not reg[eid].get("sha_match"))
    dedicated_bad = sorted(eid for eid in reg if eid not in SHARED_NO_HASH and (not reg[eid].get("registered") or not reg[eid].get("sha_match")))
    out = {
        "fighter": fighter, "schema": 1, "date": "2026-11-12", "stage": "只读诊断，未生成帧/未安装",
        "evidence": {"absolute_path": str(ROOT / f"art/fighters/{fighter}/stage1/rework-20261112/measurement_evidence.json"),
                     "sha256": sha(ROOT / f"art/fighters/{fighter}/stage1/rework-20261112/measurement_evidence.json")},
        "thresholds": ev["thresholds"],
        "summary": st,
        "idle_frame_count": idle_count,
        "walk_frame_counts": walk_counts,
        "idle_requirement": "真呼吸循环：双脚固定，头部纵幅 ≤4 px、相邻含首尾 ≤2 px、横漂 ≤2 px、一次下沉再回升；现 1 帧不合格",
        "walk_requirement": "前走/后走各 8 相：接触/下沉/交错/上升各两遍，眼纵幅 ≤8 px、相邻 ≤4 px、支撑点世界坐标偏差 ≤8 px；现 4 帧不合格",
        "state_timeline_defects": state_oob,
        "move_timeline_defects": move_unused,
        "side_view_freeze_root": "presentation/side_view.gd:450 把越界 sprite clampi 到 clip 末帧；core/fighters/fighter.gd 的 state_frames 仍决定 f.frame().sprite",
        "known_visual_fx": known,
        "three_slots": {"doc": absolute(ev["moves_basis"]["doc"]), "s1": ev["moves_basis"]["s1"],
                        "s2": ev["moves_basis"]["s2"], "s3": ev["moves_basis"]["s3"],
                        "air": ev["moves_basis"]["air"], "gap": ev["moves_basis"]["gap"],
                        "runtime_difference_risk": {
                            "ultraman-zero": "三槽分别 zero_fx_wide_beam / zero_fx_emerium_beam / zero_fx_slugger_flight+trail+catch，特效 id 已分化；仍须重画本人动作",
                            "ultraman-justice": "四招都引用 justice_fx_beam，仅改 spawn/length/thickness；不满足三槽独立实际效果",
                            "ultraman-gaia": "special 为贴头 strike、special2 gaia_fx_stream_beam、special3 gaia_fx_crusher_beam；air_special 用通用 beam_loop 且为游戏改编",
                        }[fighter]},
        "emission": {
            "emission_points_json": str(ROOT / "content/fighters" / fighter / "emission_points.json"),
            "exists": (ROOT / "content/fighters" / fighter / "emission_points.json").is_file(),
            "runtime_spawn_examples": move_spawn_examples(fighter),
            "gate": "tools/rebuild/shared/emission_check.py：新建逐帧人工依据表后按双向原生误差 ≤2 px 重核；本轮没有表，不能写发射点通过",
        },
        "effect_registration": {
            "phase3_absolute_path": str(PHASE3), "phase3_sha256": sha(PHASE3), "phase3_entry_count": len(phase3),
            "policy_absolute_path": str(POLICY), "policy_sha256": sha(POLICY),
            "policy_placements": ev["policy"]["placements"],
            "unregistered_ids": sorted(eid for eid, v in reg.items() if not v.get("registered")),
            "dedicated_sha_failures": dedicated_bad,
            "shared_entries_without_atlas_sha_field": shared,
            "shared_note": "impact_guard/impact_heavy/impact_light/beam_hit 是共享旧式条目，phase3 有条目且贴图文件存在，只是未写 atlas_sha256 字段；evidence 的 sha_match=False 不按未登记/失配处理",
            "conclusion": "本轮 effect id 登记不是缺陷；不得重复补登记当返工成果。换贴图后才按 SHA 补登记",
        },
        "clips": clips,
    }
    return out, finals


def asset_baseline(fighter: str, ev: dict, diag: dict) -> dict:
    out_dir = ROOT / "art/fighters" / fighter / "stage1/rework-20261112"
    clips = {}
    for name, c in sorted(ev["clips"].items()):
        clips[name] = {
            "absolute_atlas_path": absolute(c["atlas_path"]), "sha256": c["atlas_sha256"],
            "manifest_recorded_sha256": c["manifest_atlas_sha256"], "sha_match": c["atlas_sha_match"],
            "cell": c["cell"], "anchor": c["anchor"], "anchors": c["anchors"], "anchor_y": c["anchor_y"],
            "rects": c["rects"], "ticks": c["ticks"], "loop": c["loop"], "frame_count": c["frame_count"],
            "primary_category": diag["clips"][name]["primary_category"],
        }
    content = {}
    for key, row in ev["content_files"].items():
        p = ROOT / row["path"]
        content[key] = {"absolute_path": str(p), "sha256": sha(p), "effect_ids": row.get("effect_ids"),
                        "startup": row.get("startup"), "active": row.get("active"), "recovery": row.get("recovery")}
    own = {}
    for eid, row in ev["own_effects"].items():
        own[eid] = {"absolute_path": absolute(row["path"]), "sha256": row["sha256"],
                    "recorded_sha256": row["recorded_sha256"], "match": row["match"]}
    sheets = {}
    for k, row in ev["review_sheets"].items():
        sheets[k] = {"absolute_path": absolute(row["path"]), "sha256": row["sha256"]}
    sources = {}
    for key in ("idle_pixel", "production_reference", "official_side", "official_full"):
        rel = ev["identity"].get(key)
        if rel:
            sources[key] = {"absolute_path": absolute(rel), "sha256": sha(ROOT / rel)}
    if fighter == "ultraman-gaia":
        p = "art/fighters/ultraman-gaia/sources/ref-01.webp"
        sources["ref_01_webp"] = {"absolute_path": absolute(p), "sha256": sha(ROOT / p)}
    protected = []
    protected += [v["absolute_atlas_path"] for v in clips.values()]
    protected += [str(ROOT / f"assets/fighters/{fighter}/animations/manifest.json")]
    protected += [v["absolute_path"] for v in content.values()]
    protected += [str(PHASE3), str(POLICY)]
    protected += [v["absolute_path"] for v in sources.values()]
    protected += [v["absolute_path"] for v in sheets.values()]
    protected += [str(ROOT / f"art/fighters/{fighter}/stage1/cells/cells.json"),
                  str(ROOT / "reports/review/2026-11-12/seven-character-defects/audit.json"),
                  str(out_dir / "measurement_evidence.json"), str(Path(__file__).resolve())]
    return {
        "fighter": fighter, "schema": 1, "date": "2026-11-12", "read_only_baseline": True,
        "manifest": {"absolute_path": absolute(ev["manifest"]["path"]), "sha256": ev["manifest"]["sha256"],
                     "clip_count": ev["manifest"]["clip_count"], "total_frames": ev["manifest"]["total_frames"],
                     "top_level_cell": ev["manifest"]["cell"], "top_level_anchor": ev["manifest"]["anchor"]},
        "audit": {"absolute_path": absolute(ev["audit"]["path"]), "sha256": ev["audit"]["sha256"],
                  "idle_height": ev["audit"]["idle_height"], "state_sprite_oob": ev["audit"]["state_sprite_oob"]},
        "cells": {"absolute_path": str(ROOT / f"art/fighters/{fighter}/stage1/cells/cells.json"),
                  "sha256": ev["cells"]["sha256"], "scale": ev["cells"]["scale"],
                  "target_standing": ev["cells"]["target_standing"], "cell": ev["cells"]["cell"],
                  "anchor": ev["cells"]["anchor"]},
        "clips": clips,
        "content_files": content,
        "phase3": {"absolute_path": str(PHASE3), "sha256": sha(PHASE3), "entries": len(jload(PHASE3))},
        "charge_policy": {"absolute_path": str(POLICY), "sha256": sha(POLICY), "placements": ev["policy"]["placements"]},
        "registered_dedicated_effects": own,
        "identity_and_official_sources": sources,
        "review_sheets": sheets,
        "protected_files_do_not_overwrite": sorted(set(protected)),
        "install_policy": [
            "只允许逐 clip：.venv/bin/python tools/art/install_cells.py --fighter <id> --only <clip> --merge --dry-run，核后去掉 --dry-run",
            "安装前核该 clip 现有 cell/anchor/rects/ticks 与本次源一致；禁止全量重装、禁止用第一组格尺寸缩放其余组、禁止回落 cells.json 顶层旧 anchor",
            "现用 assets 图集、content 数据、phase3、policy、身份锚、官方来源、联系表、旧 cells.json、审计表与本诊断证据均不得被制作代理整批覆盖",
        ],
        "baseline_conflicts": identity_card(fighter, ev)["conflicts_and_gaps"],
    }


def phase_for(clip: str, i: int, n: int) -> str:
    if clip == "idle":
        return ["护架基线", "吸气下沉 1", "吸气下沉 2", "最低点", "呼气回升 1", "呼气回升 2", "回到基线", "回到基线"][min(i, 7)]
    if clip.startswith("walk_"):
        return ["接触 A", "下沉 A", "交错 A", "上升 A", "接触 B", "下沉 B", "交错 B", "上升 B", "循环收束"][min(i, 8)]
    if clip in {"charge_start", "charge", "charge_stop"}:
        return {"charge_start": ["Q 起势", "Q 起势加深", "Q 接保持"], "charge": ["Q 保持 1", "Q 保持 2", "Q 保持 3", "Q 保持 4"],
                "charge_stop": ["Q 收势", "回护架"]}[clip][min(i, n - 1)]
    if clip in {"special", "special2", "special3", "air_special", "pulse", "low_pulse", "air_pulse", "ranged_forward", "motion_214", "motion_22", "motion_236"}:
        if i < max(1, n // 4):
            return "起手"
        if i < max(2, n // 2):
            return "蓄力/引手"
        if i < max(3, n * 3 // 4):
            return "发力"
        return "收势"
    if clip in {"down", "ko"}:
        return ["失衡/落体", "倒地定型", "倒地保持"][min(i, 2)]
    if clip in {"win", "victory", "taunt"}:
        return ["胜利起势", "定型/收势", "保持"][min(i, 2)]
    if i == 0:
        return "起手"
    if i == n - 1:
        return "收势"
    return "发力/位移"


def joints(clip: str, phase: str, fighter: str) -> dict:
    p = phase
    if clip == "idle":
        return {"support": "前后脚均固定接地，脚外缘间距不重标定", "hip": "随呼吸 1–2 px 下沉/回升，不滑步",
                "shoulder": "双肩小幅起伏，肩宽与锚一致", "fists": "双拳胸前护架，仅随胸廓微动", "head": "朝右，头部纵幅 ≤4 px；" + PARTS[fighter]}
    if clip.startswith("walk_"):
        return {"support": "按 8 相换支撑脚，接触帧鞋底贴共同基线，支撑点世界坐标偏差 ≤8 px",
                "hip": "髋随下沉/上升 ≤8 px 眼纵幅；不整人缩放", "shoulder": "近远肩反向微摆，肩宽固定",
                "fists": "双拳护架随步态小幅反向摆，不复制同姿势", "head": "朝右稳定，眼纵幅 ≤8 px、相邻 ≤4 px；" + PARTS[fighter]}
    if clip in {"down", "ko", "defeat"}:
        return {"support": "倒地姿态例外：脚/膝/背按真实接触，不用站高门判缩放", "hip": "髋随失衡转体，骨长与锚一致",
                "shoulder": "近肩先着地/远肩滞后，肩宽不重标定", "fists": "双拳离护架、随躯干落下",
                "head": "头冠/头镖不穿地，头部列带单独量；" + PARTS[fighter]}
    if clip in {"guard", "block"}:
        return {"support": "后脚承重、前脚屈膝稳定", "hip": "髋微后坐", "shoulder": "双肩内收",
                "fists": "双前臂胸前交叉护架，拳体量同锚", "head": "朝右微低；" + PARTS[fighter]}
    if clip in {"charge_start", "charge", "charge_stop"}:
        return {"support": "双脚固定或真实 Q 微沉，不复制待机整帧", "hip": "重心随 Q 起势/保持/收势小幅变化",
                "shoulder": "肩随真实 Q 呼吸开合", "fists": "双拳由护架向蓄能位置再回收，帧内不画蓄气圈",
                "head": "朝右；" + PARTS[fighter]}
    if clip in {"special", "special2", "special3", "air_special", "pulse", "low_pulse", "air_pulse", "ranged_forward", "motion_214", "motion_22", "motion_236", "motion_623", "light1", "light2", "light3", "heavy", "launcher", "dash_throw", "hit_mid", "turn"}:
        m = {
            "起手": ("后脚承重、前脚轻触", "髋后坐/微转", "近肩后收、远肩护住", "双拳收护架或本人招式起手位", "头朝右微低"),
            "蓄力/引手": ("重心压向前脚", "髋继续转、膝屈下沉", "近肩拉开、远肩稳定", "一手引手、另一手护架；手中不画能量球/光刃/飞行物", "头朝目标，标志结构随头壳位移"),
            "发力": ("前脚踩实、后脚蹬送", "髋前送并带动躯干", "近肩前送、远肩回收", "手/臂/腿相对上一帧都有可见位移；只画本人本体", "头冠/额灯/胸灯与躯干同向，不裁切"),
            "收势": ("重心回两脚之间", "髋回正、膝保留余屈", "双肩回护架", "双拳或本人招式收手位，回到可接待机的姿态", "头回右侧视稳定位"),
        }
        key = "发力" if p.startswith(("发力", "位移")) else ("收势" if p == "收势" else ("蓄力/引手" if "蓄" in p or "保持" in p or "下沉" in p else "起手"))
        s, h, sh, f, hd = m[key]
        return {"support": s, "hip": h, "shoulder": sh, "fists": f, "head": hd + "；" + PARTS[fighter]}
    return {"support": "按该状态真实接触", "hip": "骨长与锚一致", "shoulder": "肩宽与锚一致",
            "fists": "双拳随实际动作位移，不复制上一帧", "head": "朝右；" + PARTS[fighter]}


def storyboard(fighter: str, ev: dict, diag: dict) -> str:
    targets = set(STORYBOARD_CLIPS) | {n for n, v in diag["clips"].items() if v["primary_category"] == "redraw"}
    basis = ev["moves_basis"]
    lines = [
        f"# {DISPLAY[fighter]} 逐帧分镜规格（2026-11-12 只读诊断）", "",
        "用途：给制作代理按唯一身份锚逐帧重画；本文件是动作规格与实测旧值，不是已生成帧、不是画面验收。",
        "身份锚只取 `identity_card.json` 的待机像素整帧；不追加多角度参考，不写角色没有的部件，不画光束/光晕/颗粒/蓄气圈/贴掌光/能量球/光刃/飞行物。",
        "四肢粗细、头肩比例、格宽、根点、唯一 scale 与冻结色板以 `identity_card.json` 为准；技能光色只在运行时特效规格定义。",
        f"本人结构：{PARTS[fighter]}。",
        "技能依据：" + "；".join([basis["s1"], basis["s2"], basis["s3"], basis["air"]]) + "。" + basis["gap"],
        "", "## 门禁", "",
        "- 主体 alpha≥128；4 邻域连通块=1（8 邻域辅助）；Alpha 仅 0/255；≤32 色整图统一映射；四边不裁切。",
        "- 站姿类对锚站高偏差 ≤8%、相邻站姿高度突变 ≤10%；蹲/躺/被投/腾空按姿态例外登记数值并用头壳/骨长证明。",
        "- 相邻根点剪影 XOR/Union ≥0.10，bbox 对齐差分同测；循环首尾目视可接，辅助门 <0.20。",
        "- 待机 6 相呼吸、头纵幅 ≤4 px、相邻含首尾 ≤2 px、横漂 ≤2 px；走路 8 相、眼纵幅 ≤8 px、相邻 ≤4 px、支撑点世界坐标偏差 ≤8 px。",
        "- 投射类手/身动作，手中不得画能量球/光刃/飞行物；Q 周身蓄气只在 charge_start/charge/charge_stop 的运行时层出现。",
        "- 发射点双向原生误差 ≤2 px，重画后先建 `content/fighters/<id>/emission_points.json` 再跑 `emission_check.py`。",
        "", "## 内容缺口（不得补编）", "",
    ]
    if fighter == "ultraman-justice":
        lines.append("- MOVES.md 明写标准型 `air_special` 不适用、不做独立空中必杀；现有 8 帧为游戏改编。分镜只作为「若主管决定保留游戏改编」的姿态规格，不得冒充原剧招式；若按原据收口，应删去独立空中必杀并由 `diagonal_light` 承接。")
        lines.append("- 当前锚 SHA 与签署 SHA 不一致、青绿识别色在装机帧缺失；阶段 A 未闭合前不得批量生图。")
    if fighter == "ultraman-gaia":
        lines.append("- 没有本人 90° 真实侧视来源；金额刃/头壳侧视前后方向是内容缺口，不写进提示词，不从正面/3/4 图猜侧面。")
        lines.append("- `air_special` 空中量子流线为游戏改编，原剧无空中向下发射依据；Photon Stream 是 SV 专用，当前 V2 不得借来凑第三槽。")
    if fighter == "ultraman-zero":
        lines.append("- `air_special` 空中集束射线为游戏改编，原剧无空中发射依据；三槽名称有文字依据但 MOVES.md 未给集数/时码/逐帧镜头。")
    lines += ["- 本轮无录屏、无实机、无听审；逻辑检查通过不能写成美术或听感通过。", ""]
    for name in sorted(targets):
        c = ev["clips"].get(name)
        if not c:
            continue
        old_n = c["frame_count"]
        if name == "idle":
            target_n = 6
        elif name.startswith("walk_"):
            target_n = 8
        else:
            target_n = old_n
        skill_note = ""
        if name in {"special", "special2", "special3", "air_special"}:
            key = {"special": "s1", "special2": "s2", "special3": "s3", "air_special": "air"}[name]
            skill_note = f"本人依据：{basis[key]}。{basis['gap']}"
            if fighter == "ultraman-justice" and name == "air_special":
                skill_note = "内容缺口：MOVES.md 标 `air_special` 不适用；以下只记现有游戏改编帧的纯人物修复规格，不补编原剧招式。"
            if name in {"special", "special2", "special3"}:
                skill_note += " 起手/发力/收势必须落到身体运动，不得用同一束或同一 pose 凑槽。"
        lines += [
            f"## `{name}`", "",
            f"- 旧帧数 {old_n}，目标帧数 {target_n}；cell={c['cell']}，anchor={c['anchor']}，ticks={c['ticks']}，loop={c['loop']}。",
            f"- 旧逐帧主体高度：{'; '.join(f'#{i}={m[chr(104)+chr(101)+chr(105)+chr(103)+chr(104)+chr(116)]}' for i, m in enumerate(c['frames']))}。",
            f"- 旧相邻根点差分：{c['diff']['pair_diffs']}；循环差分={c['diff']['loop_pair_diff']}；低于 0.10 的相邻对：{c['diff']['below_gate_pairs']}。",
            f"- 分类：{diag['clips'][name]['primary_category']} {diag['clips'][name]['secondary_categories']}；{diag['clips'][name]['category_note']}。",
            f"- 实测 confirmed FX/独立块：{diag['clips'][name]['baked_fx']['confirmed_by_contact_sheet']}；独立连通帧：{[x['frame'] for x in diag['clips'][name]['baked_fx']['independent_component_frames']]}。",
        ]
        if skill_note:
            lines.append(f"- {skill_note}")
        if name == "idle":
            lines.append("- 时间轴：须把 state_frames.idle 写成 6 行 sprite 0–5 并与 6 张 rects 对齐；赛罗现有 60 行 0–5 对 1 帧是越界冻结根因，杰斯提斯/盖亚现有 1 行也需同步重写。")
        if name.startswith("walk_"):
            lines.append("- 时间轴：须把 state_frames 对应 walk 写成 8 行 sprite 0–7 并与 8 张 rects 对齐；赛罗现有 70 行 0–7 对 4 帧越界，杰斯提斯/盖亚现有 4 行 0–3 需同步重写。")
        lines += ["", "| 帧 | 相位 | 支撑脚 | 髋 | 肩 | 双拳/手 | 头与本人部件 | 相对前一帧位移 | 旧相邻差分 | 目标差分 | 起手/发力/收势与循环 |", "|---:|---|---|---|---|---|---|---|---:|---:|---|"]
        for i in range(target_n):
            phase = phase_for(name, i, target_n)
            j = joints(name, phase, fighter)
            old_diff = c["diff"]["pair_diffs"][i] if i < len(c["diff"]["pair_diffs"]) else "新增相位，重测"
            if i == 0:
                delta = "以身份锚护架为基线；只改关节与重心"
            else:
                delta = f"手/臂/腿相对 #{i-1} 可见位移；不整人缩放、不复制上一姿势"
            loop = "循环首尾目视接上，辅助门 <0.20" if c["loop"] else "非循环；末帧回可接待机的护架"
            if name in {"charge_start", "charge", "charge_stop"}:
                loop += "；人物帧不画 Q 蓄气圈，运行时三态限定"
            if name in {"special", "special2", "special3", "air_special", "pulse", "low_pulse", "air_pulse", "ranged_forward"}:
                loop += "；FX 全在运行时层，发射/命中/收势逐帧可见"
            lines.append(f"| {i} | {phase} | {j['support']} | {j['hip']} | {j['shoulder']} | {j['fists']} | {j['head']} | {delta} | {old_diff} | ≥0.10 | {loop} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def diagnosis_md(fighter: str, ev: dict, diag: dict, card: dict) -> str:
    s = diag["summary"]
    known = KNOWN_VISUAL_FX[fighter]
    posture_dev = sum(len(c["standing"]["deviation_frames"]) for c in ev["clips"].values())
    posture_jump = sum(len(c["standing"]["neighbor_jump_frames"]) for c in ev["clips"].values())
    redraw = sorted(n for n, v in diag["clips"].items() if v["primary_category"] == "redraw")
    timeline = sorted(n for n, v in diag["clips"].items() if v["primary_category"] == "fix_timeline")
    order = {
        "ultraman-zero": ["先修赛罗 idle/walk_forward 时间轴与 6 相呼吸/8 相走路的对应关系", "重画 light1 与三槽/投射类纯人物帧", "按唯一 scale 修 heavy/launcher/intro/win 等站姿跳档", "补 emission_points.json 并逐 clip 安装、实机双朝向验收"],
        "ultraman-justice": ["先闭合身份锚 SHA/192→256 与青绿识别色缺口，未闭合不得生图", "裁定 air_special 是否按 MOVES.md「不适用」撤除；三槽拆开 justice_fx_beam 的运行时效果", "重画待机/走路/三槽/special3#3 红刃，修 motion_214/236/623 跳帧", "补 emission_points.json 并逐 clip 安装、实机双朝向验收"],
        "ultraman-gaia": ["先补本人 90° 真实侧视来源并定金额刃前后判据；同步清理 MOVES.md 旧草案与 cells/definition 顶层 anchor 冲突", "重画 special3#9、ranged_forward#4/#5 等含烘焙特效帧及全部投射类纯人物帧", "重画待机/8 相走路/三槽本人动作，修 special3、motion_623、charge 等站姿跳档", "补 emission_points.json 并逐 clip 安装、实机双朝向验收"],
    }[fighter]
    lines = [
        f"# {DISPLAY[fighter]} 返工诊断（2026-11-12）", "",
        "本轮是只读复算与联系表抽样目视，未生成新帧、未改 assets/content、未安装、未提交、未跑 Godot/verify、无录屏、未听审。",
        f"基线：manifest {ev['manifest']['clip_count']} clip / {ev['manifest']['total_frames']} 帧；现用待机站高 {ev['audit']['idle_height']}；唯一 scale {card['unique_scale']}；默认 cell/anchor {card['cell']}。证据 SHA 见 `asset_baseline.json`。",
        "", "## 本轮复算出的最严重 3 个根因", "",
    ]
    lines += [f"{i+1}. {x}" for i, x in enumerate(ROOT_CAUSES[fighter])]
    lines += [
        "", "## 数值与目视证据", "",
        f"- 站姿类按姿态例外分开后：对锚偏差 >8% 共 {posture_dev} 帧，相邻站姿跳变 >10% 共 {posture_jump} 组；姿态例外 clip {len(card['allowed_posture_exceptions'])} 个已逐帧登记高度，不以例外放行缩放。",
        f"- 待机装机 {diag['idle_frame_count']} 帧；前走/后走 {diag['walk_frame_counts']}。任务书要求真呼吸与 8 相换腿，当前均不足。",
        f"- state_frames 越界/冻结：{json.dumps(diag['state_timeline_defects'], ensure_ascii=False)}。",
        f"- moves 未用满 sprite：{json.dumps(diag['move_timeline_defects'], ensure_ascii=False)}。",
        f"- 联系表确认的烘焙 FX：" + "；".join(f"{x['clip']}#{x['frame']} {x['finding']}" for x in known) + "。",
        f"- 高饱和亮色候选不单独判 FX（本人红银/深蓝本体颜色会误报）；独立连通块与联系表结论在 `clip_diagnosis.json` 分列。",
        "", "## 逐 clip 分类统计", "",
        f"primary：{json.dumps(s['primary'], ensure_ascii=False)}；secondary：{json.dumps(s['secondary'], ensure_ascii=False)}。",
        f"任务书四类合并：{json.dumps(s['four_groups'], ensure_ascii=False)}。",
        f"`keep` 只是未触发自动数值门；未逐帧目视的 clip 不写造型通过。全部逐 clip 数值在 `clip_diagnosis.json`。",
        "", "## 重画优先级", "",
        f"P0（时间轴/身份门）：{', '.join(timeline) if timeline else '无 primary fix_timeline；身份与 anchor/色板缺口见 identity_card.json'}。",
        f"P1（纯人物重画，先去烘焙 FX 与双特效）：{', '.join(redraw[:18])}{' …' if len(redraw) > 18 else ''}。",
        "P2（修尺度/姿态/身份、补逐帧骨长证据）：见 `clip_diagnosis.json` 的 fix_scale / fix_pose / fix_identity 与 `storyboard.md` 的姿态例外登记。",
        "", "## 三槽、发射点与特效登记", "",
        f"- 依据文件：`{diag['three_slots']['doc']}`。{diag['three_slots']['s1']} {diag['three_slots']['s2']} {diag['three_slots']['s3']} {diag['three_slots']['air']}",
        f"- 差异风险：{diag['three_slots']['runtime_difference_risk']}。内容缺口：{diag['three_slots']['gap']}",
        f"- emission_points.json 存在={diag['emission']['exists']}；运行时 spawn/anchor 样例见 `clip_diagnosis.json.emission.runtime_spawn_examples`。重画后必须新建人工依据表，双向误差 ≤2 px 才算过。",
        f"- phase3 {diag['effect_registration']['phase3_entry_count']} 条；未登记 id={diag['effect_registration']['unregistered_ids']}；专属 SHA 不符={diag['effect_registration']['dedicated_sha_failures']}；Q 三态 placement 已登记。{diag['effect_registration']['conclusion']}",
        "", "## 返工顺序", "",
    ]
    lines += [f"{i+1}. {x}" for i, x in enumerate(order)]
    lines += [
        "", "## 每阶段验收命令与门值", "",
        "所有 Godot 导入/验证/录制经 `.venv/bin/python tools/godot_lock.py -- <命令>` 串行；不删活锁、不关用户进程。",
        "- 阶段 A：核 `identity_card.json` 的锚 SHA、真实侧视来源、标志结构前后判据、唯一 scale、≤32 色板识别色、逐 clip cell/anchor；造型须看原生格与严格 4×，站距/色数/Alpha 不代替造型。",
        "- 阶段 B：核 `storyboard.md` 每帧支撑脚/髋/肩/双拳/头/本人部件/位移/起手发力收势/相邻差分/循环；技能依据必须来自本人 MOVES.md 与 moves/*.json，无集数/时码标内容缺口。",
        "- 复算证据：`.venv/bin/python tools/rebuild/seven-character-rework-20261112/ufeneo_rework_diag_v1.py`（只读 assets/content/reports，重写三份 measurement_evidence.json）；另跑 `.venv/bin/python tools/check/frame_scale_jumps.py --fighter <id> --clip <clip> --verbose`。",
        "- 阶段 D 硬门：主体 alpha≥128；4 邻域连通块=1、8 邻域辅助；二值 Alpha；≤32 色整图映射；四边不裁；站姿类高度偏差 ≤8%、相邻跳变 ≤10%；相邻剪影 XOR/Union ≥0.10；循环首尾目视可接（辅助门 <0.20）；姿态例外登记高度与骨长。",
        "- 阶段 D 待机/走路：待机头纵幅 ≤4 px、相邻含首尾 ≤2 px、横漂 ≤2 px、一次下沉再回升；走路 8 相、眼纵幅 ≤8 px、相邻 ≤4 px、支撑点世界坐标偏差 ≤8 px。",
        "- 阶段 D 特效分离：人物帧单连通，主体外 alpha≥16 ≤100 px、主体外 alpha≥200=0（外扩 3 px 口径），alpha 1–15 尘点只登记；独立颗粒/飞行物硬门另判；PixelFX 运行时层硬 Alpha、≤8 色、亮芯/外焰/颗粒/相位变化。",
        "- 阶段 E：`.venv/bin/python tools/rebuild/shared/emission_check.py --characters <id>`（先建 emission_points.json，误差 ≤2 px）；`.venv/bin/python tools/art/install_cells.py --fighter <id> --only <clip> --merge --dry-run`，核 cell/anchor/rects/ticks/atlas SHA 后正式 `--only <clip> --merge`；禁止全量重装。",
        "- 阶段 F：`.venv/bin/python tools/godot_lock.py -- .venv/bin/python tools/verify.py --keep-going` 只证明逻辑/资源登记；另报逐帧美术门独立结果。主游戏 `开始游戏.command` / `app/scenes/main.tscn` 训练/F1，两个朝向、720/1080、真实输入、独立回放、原速逐动作看画面；必要时短录屏审后删除，无录屏写无录屏。",
        "", "## 风险", "",
    ]
    lines += [f"- {x}" for x in card["conflicts_and_gaps"]]
    lines += [
        "- `stage_cells.py` 默认色板来自 `assets/fighters/<id>/catalogue/model-native.png`，与本批冻结动作色板不一致；返工必须显式传本人冻结色板或走 `forge_backend` 等价离线接口，不按身体区域局部重涂。",
        "- 共享旧式 phase3 条目 impact_guard/impact_heavy/impact_light/beam_hit 未写 atlas_sha256 字段，不是未登记；不要为凑「补登记」改动已核资源。",
        "- 逐 clip 安装不得用本批第一组 cell/anchor 缩放其余组；杰斯提斯 4 个 192 格 clip 与三角色 288 格 air_special 必须按自身值。",
        "- 自动数值 keep 不等于造型通过；down/ko/win 等跨角色模板化仍须按本人身份看原生格联系表。",
        "", "## 明确「本轮没做的事」", "",
        "- 没有生成任何图片，没有改 `assets/`，没有改 `content/`，没有 git commit，没有安装或覆盖装机图集。",
        "- 没有跑 Godot、tools/verify.py、主游戏双朝向 720/1080、真实输入/独立回放/原速画面；无录屏，未听审，未冒称用户亲审。",
        "- 没有重建或补写 emission_points.json、没有重画任何帧、没有补编剧集/时码/原剧镜头；storyboard.md 是待制作规格，不是已完成动作。",
        "- 没有把逻辑检查、色数、站距、Alpha、连通块或文件数量写成美术/听感通过；诊断图表未另生成（本轮只交 JSON 与 Markdown 及证据脚本）。",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    for fighter in FIGHTERS:
        out_dir = ROOT / "art/fighters" / fighter / "stage1/rework-20261112"
        ev = jload(out_dir / "measurement_evidence.json")
        card = identity_card(fighter, ev)
        diag, _ = clip_diagnosis(fighter, ev)
        baseline = asset_baseline(fighter, ev, diag)
        jdump(out_dir / "identity_card.json", card)
        jdump(out_dir / "clip_diagnosis.json", diag)
        jdump(out_dir / "asset_baseline.json", baseline)
        (out_dir / "storyboard.md").write_text(storyboard(fighter, ev, diag), encoding="utf-8", newline="\n")
        (out_dir / "diagnosis.md").write_text(diagnosis_md(fighter, ev, diag, card), encoding="utf-8", newline="\n")
        print(fighter, diag["summary"]["primary"], diag["summary"]["four_groups"])


if __name__ == "__main__":
    main()
