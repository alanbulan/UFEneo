"""七角色返工诊断第一阶段：三角色逐帧只读测量与数据交叉核。

本脚本只读 assets/content/reports，产出只写 art/fighters/<id>/stage1/rework-20261112/。
不生成图片、不安装、不改运行时、不复制其它角色数据。
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = _layout_root
FIGHTERS = ("ultraman-zero", "ultraman-justice", "ultraman-gaia")
AUDIT = ROOT / "reports/review/2026-11-12/seven-character-defects/audit.json"
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
POLICY = ROOT / "content/presentation/charge_overlay_policy.json"
REVIEW_DIR = ROOT / "reports/review/2026-11-12/seven-character-defects"

# 站姿类门：来自任务书 §1.1 / AGENTS「逐帧体型一致性是硬门」。
STANDING_TOL = 0.08
NEIGHBOR_TOL = 0.10
DIFF_MIN = 0.10
# 腾空/蹲/躺/被投/倒地/起身/落地缓冲等「姿态例外」。名称按运行时实际语义，
# 不因名字放行同一 clip 里的直立帧；still inspect 高度和骨长代理。
POSTURE_EXCEPTIONS = {
    "air_apex", "air_crush", "air_fall", "air_pulse", "air_recover", "air_rise",
    "air_special", "air_tech", "air_throw", "air_light", "air_heavy",
    "vertical_light", "vertical_heavy", "diagonal_light", "diagonal_heavy",
    "dive", "chase_light1", "chase_light2", "chase_end", "chase_takeoff",
    "dash", "dash_start", "dash_stop", "dash_light", "dash_heavy",
    "takeoff", "land", "crouch", "crouch_start", "crouch_rise", "crouch_turn",
    "crouch_guard", "crouch_blockstun", "crouch_light", "crouch_light2",
    "crouch_sweep", "slide", "sweep", "low_pulse", "bounce", "bounce_crush",
    "bounce_sweep", "down", "ko", "getup", "wake_low", "wake_mid",
    "thrown_forward", "thrown_back", "thrown_air", "thrown_dash",
    "throw_forward", "throw_back", "dash_throw", "motion_41236",
    "motion_623", "backstep", "back_counter", "dodge", "dodge_counter",
    "roll_forward", "roll_back", "air_recover", "flip_forward", "flip_back",
    "vertical_jump", "jump", "hit_air", "launch", "launcher", "hit_launch",
    "hit_down", "defeat", "guardbreak", "stun", "guard_hit", "blockstun",
    "crouch_block", "low_guard", "low_blockstun",
}
# 这些是直立/近直立 clip，即便名字里带 throw/special 也按站姿门核。
STANDING_FORCE = {
    "idle", "walk_forward", "walk_back", "turn", "guard", "block",
    "light1", "light2", "light3", "heavy", "spin_heavy", "crush", "tackle",
    "special", "special2", "special3", "pulse", "ranged_forward",
    "motion_214", "motion_22", "motion_236", "motion_41236",
    "guard_counter", "back_counter", "charge_start", "charge", "charge_stop",
    "win", "victory", "intro", "taunt", "timeout", "burst",
    "hit_mid", "hit_high", "hit_low", "hit", "blockstun",
}
# 投射类与三槽：人物帧不得含任何离体 FX；以连通块 + 高饱和亮色辅助判定。
BAKED_FX_SUSPECT_CLIPS = {
    "special", "special2", "special3", "air_special",
    "pulse", "low_pulse", "air_pulse", "ranged_forward",
    "motion_214", "motion_22", "light1", "light2", "light3",
    "charge_start", "charge", "charge_stop",
}
CHROMA_HIGH = 90  # 辅助：高饱和亮色像素占比，不作唯一判据
BRIGHT_THRESHOLD = 190

STORYBOARD_CLIPS = [
    "idle", "walk_forward", "walk_back", "light1", "light2", "light3", "heavy",
    "special", "special2", "special3", "air_special", "dash_throw", "launcher",
    "hit_mid", "down", "ko", "win", "guard", "turn",
    "charge_start", "charge", "charge_stop",
]

# 固定身份卡片：来自各角色 stage1/cells/cells.json、requests.json、官方来源 JSON 和实读 SHA。
IDENTITY = {
    "ultraman-zero": {
        "display": "赛罗奥特曼 · 基本红蓝形态",
        "idle_pixel": "art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png",
        "production_reference": "art/fighters/ultraman-zero/stage1/idle/frames/pixel-raw-02-official-side-anchor.png",
        "official_side": "art/fighters/ultraman-zero/stage1/idle/references/zero-side-head-official.png",
        "official_full": "art/fighters/ultraman-zero/sources/tsuburaya-zero/hero-zero.png",
        "official_urls": [
            "https://tsuburaya-prod.com/news/7732",
            "https://tsuburaya-prod.com/heroes/ultraman-zero",
        ],
        "orientation": "官方头部裁图为人物朝画面右方的右侧近侧脸；装机帧同为朝右固定侧视。",
        "structure": (
            "双头镖为额侧左右并列的两枚弯刃，贴头壳有宽基座、刃缘有转折凹口；"
            "朝右时两刃自额前向头顶后上方折起，刃尖 x 小于眼列 x，基座靠近眼列上方。"
            "蓝色额灯在双刃根之间、黄色眼在面罩前缘；层叠银蓝肩胸甲、蓝计时器，无披风。"
        ),
        "relative_test": (
            "先判朝右；在眼列 x 左右各约 26 px 头部列带内，取两枚亮银刃的最高/最前像素均值 x，"
            "分别与黄眼列 x 比：刃尖/后掠端 x 应小于眼列 x，宽基座应贴眼列上方且不低于眼；"
            "禁止把最高行当冠顶，禁止用正面/3/4 图判侧视。"
        ),
        "palette_source": "art/fighters/ultraman-zero/stage1/cells/cells.json",
        "recognition": ["蓝额灯", "黄色眼", "红银蓝基本形态", "双头镖", "彩色计时器"],
        "limb_basis": (
            "以 identity-idle-pixel.png 原生 256 格为准：头壳/双刃约 32 px 高，"
            "上臂约 12–14 px 厚、前臂 10–12 px、大腿 17–20 px、小腿 11–14 px、"
            "握拳 12–15 px；这些是目视像素块量级，不是自动造型通过。"
        ),
    },
    "ultraman-justice": {
        "display": "杰斯提斯奥特曼 · 标准型",
        "idle_pixel": "art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png",
        "production_reference": "art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png",
        "official_side": "art/fighters/ultraman-justice/stage1/idle/references/justice-side-head-ugf-head-neck.png",
        "official_full": "art/fighters/ultraman-justice/sources/tsuburaya-justice-2019/official-standard-01.png",
        "official_urls": [
            "https://tsuburaya-prod.com/heroes/ultraman-justice",
            "https://animageplus.jp/articles/detail/34533",
        ],
        "orientation": (
            "官方 UGF 剧照裁图为面朝画面右方的近纯右侧头/颈；official-standard-01/02 是正面与"
            "3/4 格斗架势，只核身份和架势，不冒充 90° 侧视。装机帧面朝右。"
        ),
        "structure": (
            "标准型是银红贴身皮套，中央高而窄的银色头冠 blade，冠根与额头相连、尖端向上；"
            "朝右时冠前缘在眼列 x 附近，冠体向后展开、后缘在眼列 x 后方；"
            "深色面罩/口部板、薄贴身肩甲、胸灯与额灯青绿色，金色侧饰仅从侧视裁图读轮廓。"
        ),
        "relative_test": (
            "先判朝右；取冠尖/冠前缘与眼列 x 同口径比较：冠尖端不低于眼、向前不超过眼列太多，"
            "冠后缘 x 小于眼列 x；面罩前缘/下颌在眼列 x 附近。蓝色额灯在本侧视不可读，"
            "不得按正面照片的颜色位置写侧视提示词。"
        ),
        "palette_source": "art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png",
        "recognition": ["青绿额灯", "青绿胸灯", "银红标准型", "中央头冠", "薄贴身肩甲"],
        "limb_basis": (
            "以候选04 256 格现用文件为准：头壳约 23×32 px，上臂约 10–12 px、"
            "前臂 9–11 px、大腿 15–18 px、小腿 10–12 px、握拳 10–12 px、贴身肩甲薄层；"
            "该量级来自根 2026-11-09 记录与原生格目视，不拿正面图测 90° 侧头宽。"
        ),
    },
    "ultraman-gaia": {
        "display": "盖亚奥特曼 · V2",
        "idle_pixel": "art/fighters/ultraman-gaia/stage1/idle/frames/identity-idle-pixel.png",
        "production_reference": "art/fighters/ultraman-gaia/stage1/idle/frames/pixel-raw-02-explicit-canvas.png",
        "official_side": None,
        "official_full": "art/fighters/ultraman-gaia/sources/official-pose-20261109-hero/hero_gaia-1.png",
        "official_urls": ["https://tsuburaya-prod.com/heroes/ultraman-gaia"],
        "orientation": (
            "当前已存官方完整皮套 hero_gaia-1.png 是正面中立；ref-01.webp 是正面偏 3/4 格斗架势。"
            "仓库没有可签的本人 90° 真实侧视来源，装机帧朝右但侧视结构只能以已签待机像素锚和"
            "该两张正面图交叉核；制作代理若需重定标志结构，须先找本人真实侧视来源，不得猜侧面。"
        ),
        "structure": (
            "V2 头部是中央细长金色额刃与银色头壳、浅黄眼；宽黑内带加金边的 V 字胸甲，"
            "中央青蓝三角胸灯，红银躯体，无披风。正面判据：金额刃在两眼之间上伸、"
            "眼列与额刃左右对称；侧视前后方向当前标内容缺口，不能用 3/4 图冒充 90° 侧视基准。"
        ),
        "relative_test": (
            "在正面来源上，额刃中心 x 应落在两眼 x 中点附近，V 字黑金胸甲下尖与青蓝胸灯同轴；"
            "装机朝右侧视时金额刃/头壳前缘应在眼列 x 附近，金刃向后掠向头顶。"
            "因无真实侧视来源，侧视 x 方向只作待核项，不写进生成规格。"
        ),
        "palette_source": "art/fighters/ultraman-gaia/stage1/cells/cells.json",
        "recognition": ["浅黄眼", "金额刃", "青蓝三角胸灯", "黑金 V2 胸甲", "红银 V2"],
        "limb_basis": (
            "以 192 格 identity-idle-pixel.png 为准：头壳宽 22 px（记录为人工解剖 ROI）、"
            "站高 154 px、上臂约 9–11 px、前臂 8–10 px、大腿 14–17 px、小腿 9–12 px、"
            "握拳 9–11 px，四肢粗细与官方 V2 皮套正常体量一致，不增肌、不画披风。"
        ),
    },
}

MOVES_BASIS = {
    "ultraman-zero": {
        "doc": "content/fighters/ultraman-zero/MOVES.md",
        "s1": "赛罗集束射线 Wide Zero Shot：右前臂宽青蓝束，24/32/16，72 tick。",
        "s2": "艾梅利姆切割 Emerium Slash：额灯青绿细束带新月刃波，32/32/16，80 tick。",
        "s3": "赛罗头镖 Zero Slugger：双实体飞刃、外飞回收，32/48/16，96 tick。",
        "air": "空中集束射线是游戏改编，原剧无空中发射依据，不冒称原剧。",
        "gap": "MOVES.md 只记已装状态和名称，未给剧集/时码/逐帧镜头；原剧一级/二级/三级名称仍属内容依据缺口，制作代理不得补编镜头。",
    },
    "ultraman-justice": {
        "doc": "content/fighters/ultraman-justice__standard/MOVES.md",
        "s1": "闪光效应：双掌收胸灯双手聚能，橙色宽束，1 格。",
        "s2": "杰斯提斯粉碎：右掌收腰、单臂破坏光线并可使屏障无力化，2 格。",
        "s3": "比库托流姆光线 Victorium Beam：双手举过头顶、头部水晶聚能后双掌发射，标准型最强必杀，3 格。",
        "air": "标准型 air_special 在 MOVES.md 标『不适用』，现有 8 帧空中必杀属游戏改编，不得冒充原剧招式。",
        "gap": "MOVES.md 明确资料是官方页招式名＋文字资料站＋游戏页，无逐帧剧集镜头、集数/时码；三槽独立技能有据，但具体姿态仍是文字依据。",
    },
    "ultraman-gaia": {
        "doc": "content/fighters/ultraman-gaia/MOVES.md",
        "s1": "光子冰刀 Photon Edge：头部水晶聚能拉出光刃、鞭状横斩，V1/V2 可用。",
        "s2": "量子流线 Quantum Stream：双臂 T 字转右臂 L 字发射，V2 威力 2 倍。",
        "s3": "光子粉碎机 Photon Crusher：V2 继承自阿古茹的头部必杀光线，三段蓄能为游戏编排；光子流线是 SV 专用，不得借来凑槽。",
        "air": "空中量子流线是游戏改编，原剧无空中向下发射依据。",
        "gap": "MOVES.md 写明光色均为次级资料游戏取色，未逐帧核对影片、未写集数/时码；当前 V2 不开放 SV 技能。",
    },
}

# 制作代理可直接照着逐帧重画的本人分镜：joints 是相对前一帧的位移与动作相位。
# 数值描述为关节动作目标，不是对旧帧的测量结论；相邻差分/循环门见每 clip 的 gate 字段。
GENERIC_POSE = {
    "anchor": "双脚前后错步、屈膝下沉、双拳胸前护架；本人头冠/头镖/额灯/胸灯与锚一致，四肢粗细不重标定。",
    "no_fx": "帧内只有人物本体；光束/光刃/弹体/颗粒/蓄气圈一律留给运行时，不画进人物帧。",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jload(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def jdump(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def abs_path(rel: str) -> Path:
    return ROOT / rel


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def components(mask: np.ndarray, connectivity: int = 4):
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=connectivity)
    sizes = sorted((int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, count)), reverse=True)
    return len(sizes), sizes


def frame_metrics(rgba: np.ndarray):
    alpha = rgba[:, :, 3]
    mask128 = alpha >= 128
    ys, xs = np.where(mask128)
    if not len(ys):
        return dict(height=0, width=0, bbox=None, area=0, components4=0, components8=0,
                    comp4_sizes=[], comp8_sizes=[], alpha_levels=[], colors=0,
                    bright_chroma=0, bright_area=0, head_band_top=None, bottom=int(alpha.shape[0] - 1))
    top, bottom, left, right = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    c4, s4 = components(mask128, 4)
    c8, s8 = components(mask128, 8)
    rgb = rgba[:, :, :3]
    visible = rgb[mask128]
    colors = len(np.unique(visible.reshape(-1, 3), axis=0))
    mx = visible.max(axis=1).astype(int)
    mn = visible.min(axis=1).astype(int)
    bright = (mx >= BRIGHT_THRESHOLD) & ((mx - mn) >= CHROMA_HIGH)
    # 头部列带代理：以主体水平 bbox 中央 ±26 px，不用整帧最高行（AGENTS）。
    cx = (left + right) / 2
    band = mask128[:, max(0, int(cx - 26)):min(mask128.shape[1], int(cx + 26))]
    hys = np.where(band.any(axis=1))[0]
    return dict(
        height=bottom - top + 1, width=right - left + 1,
        bbox=[left, top, right, bottom], area=int(mask128.sum()),
        components4=c4, components8=c8, comp4_sizes=s4[:8], comp8_sizes=s8[:8],
        alpha_levels=sorted(int(v) for v in np.unique(alpha)),
        colors=int(colors), bright_chroma=int(bright.sum()), bright_area=int(mask128.sum()),
        head_band_top=int(hys.min()) if len(hys) else None,
        bottom=bottom,
    )


def silhouette_diff(a: np.ndarray, b: np.ndarray) -> float:
    """逐帧根点对齐剪影对称差分 / 两帧并集，头镖/披风/四肢真实位移都计入。"""
    ma = np.asarray(a, dtype=bool)
    mb = np.asarray(b, dtype=bool)
    union = np.logical_or(ma, mb).sum()
    return float(np.logical_xor(ma, mb).sum() / union) if union else 0.0


def bbox_aligned_diff(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """归一化剪影差分：各帧 alpha>=128 主体 bbox 左上角对齐后算 XOR/Union。

    用于区分「关节真的动了」与「同姿势整图平移」；原根点差分仍为主门。
    两个口径都 <0.10 才是同姿势复制/冻结的强证据。
    """
    def crop(mask):
        ys, xs = np.where(mask)
        if not len(ys):
            return np.zeros((1, 1), dtype=bool), (0, 0)
        t, b, l, r = ys.min(), ys.max(), xs.min(), xs.max()
        return mask[t:b + 1, l:r + 1], (int(l), int(t))

    a, off_a = crop(mask_a)
    b, off_b = crop(mask_b)
    h = max(a.shape[0] + max(0, off_a[1] - off_b[1]),
            b.shape[0] + max(0, off_b[1] - off_a[1]))
    w = max(a.shape[1] + max(0, off_a[0] - off_b[0]),
            b.shape[1] + max(0, off_b[0] - off_a[0]))
    canvas_a = np.zeros((h, w), dtype=bool)
    canvas_b = np.zeros((h, w), dtype=bool)
    ay, ax = max(0, off_a[1] - off_b[1]), max(0, off_a[0] - off_b[0])
    by, bx = max(0, off_b[1] - off_a[1]), max(0, off_b[0] - off_a[0])
    canvas_a[ay:ay + a.shape[0], ax:ax + a.shape[1]] = a
    canvas_b[by:by + b.shape[0], bx:bx + b.shape[1]] = b
    union = np.logical_or(canvas_a, canvas_b).sum()
    return float(np.logical_xor(canvas_a, canvas_b).sum() / union) if union else 0.0


def clip_frames(fighter: str, clip: dict):
    texture = abs_path(clip["texture"].removeprefix("res://"))
    atlas = np.array(Image.open(texture).convert("RGBA"))
    out = []
    for rect in clip["rects"]:
        x, y, w, h = map(int, rect)
        out.append(atlas[y:y + h, x:x + w])
    return texture, out


def effect_ids(obj, out: set[str]):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in {"effect", "trail_effect", "return_effect", "spark", "block_spark", "impact_effect", "block_effect"} and isinstance(value, str) and value:
                out.add(value)
            if key == "projectile_impacts" and isinstance(value, dict):
                out.update(str(k) for k in value if isinstance(k, str))
                out.update(str(v) for v in value.values() if isinstance(v, str))
            effect_ids(value, out)
    elif isinstance(obj, list):
        for value in obj:
            effect_ids(value, out)


def collect_effects(fighter: str):
    ids = set()
    files = {}
    cdir = ROOT / "content/fighters" / fighter
    for path in sorted((cdir / "moves").glob("*.json")):
        data = jload(path)
        local = set()
        effect_ids(data, local)
        ids.update(local)
        files[path.stem] = dict(path=rel(path), sha256=sha(path), effect_ids=sorted(local),
                                frame_count=len(data.get("frames", [])),
                                startup=data.get("startup"), active=data.get("active"), recovery=data.get("recovery"),
                                sprite_max=max((f.get("sprite", 0) for f in data.get("frames", [])), default=None),
                                sprite_unique=sorted(set(f.get("sprite", 0) for f in data.get("frames", []))))
    state = cdir / "state_frames.json"
    st = jload(state)
    local = set()
    effect_ids(st, local)
    ids.update(local)
    files["state_frames"] = dict(path=rel(state), sha256=sha(state), effect_ids=sorted(local),
                                 states={k: len(v) for k, v in st.items()})
    files["definition"] = dict(path=rel(cdir / "definition.json"), sha256=sha(cdir / "definition.json"))
    phase3 = jload(PHASE3)
    policy = jload(POLICY)
    placements = policy.get("placements", {}).get(fighter, {})
    for s, placement in placements.items():
        e = placement.get("effect")
        if e:
            ids.add(e)
    registration = {}
    for eid in sorted(ids):
        e = phase3.get(eid)
        if e:
            texture = abs_path(e["texture"].removeprefix("res://"))
            actual = sha(texture) if texture.is_file() else None
            registration[eid] = dict(registered=True, atlas=rel(texture), atlas_sha256_actual=actual,
                                     atlas_sha256_recorded=e.get("atlas_sha256"), sha_match=actual == e.get("atlas_sha256"),
                                     dedicated_to=e.get("dedicated_to"), rects=len(e.get("rects", [])),
                                     phase3_path=rel(PHASE3), phase3_sha256=sha(PHASE3))
        else:
            registration[eid] = dict(registered=False, phase3_path=rel(PHASE3), phase3_sha256=sha(PHASE3))
    return st, files, registration, dict(path=rel(POLICY), sha256=sha(POLICY), placements=placements)


def classify_clip(name: str, row: dict, state_oob: list, move_oob: list, frozen: dict, flags: dict):
    reasons = []
    if name in state_oob or name in move_oob:
        reasons.append("sprite 越界 / 时间轴冻结")
    if row["baked_fx"]["suspect"]:
        reasons.append("烘焙特效或独立块")
    if row["standing"]["deviation_frames"]:
        reasons.append("站姿类体型偏差 >8%")
    if row["standing"]["neighbor_jump_frames"]:
        reasons.append("相邻站姿高度突变 >10%")
    if row["diff"]["below_gate_pairs"]:
        reasons.append("相邻剪影差分 <0.10")
    if not row["diff"]["loop_ok"] and row["diff"]["loop_pair_diff"] is not None:
        reasons.append("循环首尾不接")
    if flags.get("state_freeze"):
        reasons.append("state_frames 冻结段")
    if flags.get("pose_issues"):
        reasons.append("起手/发力/收势或姿态模板问题")
    if flags.get("identity_risk"):
        reasons.append("本人身份/标志结构待核")
    if not reasons:
        return "keep", reasons
    if name in state_oob or name in move_oob or flags.get("state_freeze"):
        return "fix_timeline", reasons
    if row["baked_fx"]["suspect"] or flags.get("pose_issues"):
        return "redraw", reasons
    if row["standing"]["deviation_frames"] or row["standing"]["neighbor_jump_frames"]:
        return "fix_scale", reasons
    if flags.get("identity_risk"):
        return "fix_identity", reasons
    if row["diff"]["below_gate_pairs"] or not row["diff"]["loop_ok"]:
        return "fix_pose", reasons
    return "fix_pose", reasons


def measure_fighter(fighter: str):
    out_dir = ROOT / "art/fighters" / fighter / "stage1/rework-20261112"
    manifest_path = ROOT / "assets/fighters" / fighter / "animations/manifest.json"
    manifest = jload(manifest_path)
    clips = manifest["clips"]
    audit = jload(AUDIT)["characters"][fighter]
    state, content_files, registration, policy = collect_effects(fighter)
    move_files = content_files
    # state frame sprite range / freeze runs / OOB
    state_oob = []
    state_freeze = {}
    for key, frames in state.items():
        nf = len(clips.get(key, {}).get("rects", []))
        mx = max((f.get("sprite", 0) for f in frames), default=-1)
        if nf == 0 or mx >= nf:
            state_oob.append(key)
        seq = [f.get("sprite", 0) for f in frames]
        runs = []
        for value, grp in __import__("itertools").groupby(seq):
            runs.append((value, len(list(grp))))
        longest = max((n for _, n in runs), default=0)
        state_freeze[key] = dict(frame_count=len(frames), clip_frames=nf, sprite_max=mx,
                                 longest_same_sprite=longest, oob=mx >= nf if nf else True,
                                 frozen_segments=[dict(sprite=v, ticks=n) for v, n in runs if n >= 10])
    move_oob = []
    move_freeze = {}
    for mid, row in move_files.items():
        if mid in {"state_frames", "definition"}:
            continue
        nf = len(clips.get(mid, {}).get("rects", []))
        mx = row["sprite_max"]
        if nf == 0 or mx is None or mx >= nf:
            move_oob.append(mid)
        move_freeze[mid] = dict(clip_frames=nf, sprite_max=mx, sprite_unique=row["sprite_unique"],
                                frame_count=row["frame_count"], unused_sprites=sorted(set(range(nf)) - set(row["sprite_unique"])))
    idle_height = audit["idle_height"]
    scale_cells = jload(ROOT / "art/fighters" / fighter / "stage1/cells/cells.json")
    clip_rows = {}
    atlas_hashes = {}
    for name, clip in sorted(clips.items()):
        texture, frames = clip_frames(fighter, clip)
        atlas_hashes.setdefault(rel(texture), sha(texture))
        metrics = [frame_metrics(f) for f in frames]
        masks = [f[:, :, 3] >= 128 for f in frames]
        diffs = [round(silhouette_diff(masks[i - 1], masks[i]), 4) for i in range(1, len(masks))]
        bbox_diffs = [round(bbox_aligned_diff(masks[i - 1], masks[i]), 4) for i in range(1, len(masks))]
        loop_value = round(silhouette_diff(masks[-1], masks[0]), 4) if len(masks) > 1 and clip.get("loop", False) else None
        loop_bbox_value = round(bbox_aligned_diff(masks[-1], masks[0]), 4) if len(masks) > 1 and clip.get("loop", False) else None
        below = [dict(pair=[i - 1, i], diff=diffs[i - 1]) for i in range(1, len(diffs) + 1) if diffs[i - 1] < DIFF_MIN]
        bbox_below = [dict(pair=[i - 1, i], diff=bbox_diffs[i - 1]) for i in range(1, len(bbox_diffs) + 1) if bbox_diffs[i - 1] < DIFF_MIN]
        frozen_candidates = [dict(pair=[i - 1, i], root_diff=diffs[i - 1], bbox_diff=bbox_diffs[i - 1])
                             for i in range(1, len(diffs) + 1) if diffs[i - 1] < 0.02 and bbox_diffs[i - 1] < 0.02]
        is_standing = name in STANDING_FORCE or (name not in POSTURE_EXCEPTIONS and not re.search(r"air|down|throw|throw|fall|bounce|crouch|sweep|launch|jump|dash|dive|roll|wake|getup|ko|defeat|stun|block", name))
        deviations, neighbor_jumps = [], []
        for i, m in enumerate(metrics):
            dev = abs(m["height"] - idle_height) / idle_height
            if is_standing and dev > STANDING_TOL:
                deviations.append(dict(frame=i, height=m["height"], deviation=round(dev, 4)))
            if i and is_standing:
                prev = metrics[i - 1]["height"]
                jump = abs(m["height"] - prev) / max(1, prev)
                if jump > NEIGHBOR_TOL:
                    neighbor_jumps.append(dict(pair=[i - 1, i], heights=[prev, m["height"]], jump=round(jump, 4)))
        baked = []
        for i, m in enumerate(metrics):
            if name in BAKED_FX_SUSPECT_CLIPS and m["components4"] > 1:
                baked.append(dict(frame=i, components4=m["components4"], components8=m["components8"],
                                  comp4_sizes=m["comp4_sizes"], comp8_sizes=m["comp8_sizes"],
                                  bright_chroma=m["bright_chroma"],
                                  note="独立连通块；须看原生格判断是否烘焙特效/独立飞行物"))
            # 与人物连通的高亮光块：连通=1 也不能冒充无 FX，登记颜色异常供联系表人眼核。
            if name in BAKED_FX_SUSPECT_CLIPS and m["bright_area"] and m["bright_chroma"] / m["bright_area"] > 0.055:
                baked.append(dict(frame=i, kind="connected_high_chroma_candidate",
                                  bright_chroma=m["bright_chroma"], bright_area=m["bright_area"],
                                  ratio=round(m["bright_chroma"] / m["bright_area"], 4),
                                  note="高饱和亮块可能与手/头镖连通，须按原生格和本人识别色核"))
        clip_rows[name] = dict(
            frame_count=len(frames), cell=clip["cell"], anchor=clip["anchor"],
            anchors=clip.get("anchors"), anchor_y=clip.get("anchor_y"),
            rects=clip["rects"], ticks=clip["ticks"], loop=bool(clip.get("loop", False)),
            atlas_path=rel(texture), atlas_sha256=atlas_hashes[rel(texture)],
            manifest_atlas_sha256=clip.get("atlas_sha256"),
            atlas_sha_match=clip.get("atlas_sha256") == atlas_hashes[rel(texture)],
            frames=metrics,
            standing=dict(classification="standing" if is_standing else "posture_exception",
                          baseline_height=idle_height,
                          deviation_frames=deviations, neighbor_jump_frames=neighbor_jumps,
                          exception_reason=None if is_standing else "蹲/躺/腾空/被投/深屈膝/披风或伸展姿态；仍登记高度和骨长代理"),
            diff=dict(pair_diffs=diffs, below_gate_pairs=below, gate=DIFF_MIN,
                      bbox_aligned_pair_diffs=bbox_diffs, bbox_aligned_below_gate_pairs=bbox_below,
                      frozen_pose_candidates=frozen_candidates,
                      loop_pair_diff=loop_value, loop_bbox_aligned_diff=loop_bbox_value,
                      loop_ok=(loop_value is None or loop_value < DIFF_MIN * 2)),
            baked_fx=dict(suspect=bool(baked), candidates=baked),
            state_frames=state_freeze.get(name),
            move_frames=move_freeze.get(name),
            audit_height=audit["height_by_clip"].get(name),
        )
    # clip 分类
    for name, row in clip_rows.items():
        flags = dict(
            state_freeze=bool(row["state_frames"] and row["state_frames"]["frozen_segments"] and row["state_frames"]["oob"]),
            pose_issues=(name in STORYBOARD_CLIPS and (row["frame_count"] < 2 or row["diff"]["below_gate_pairs"] or row["baked_fx"]["suspect"])),
            identity_risk=(name in {"idle", "special3", "air_special"} and IDENTITY[fighter]["official_side"] is None),
        )
        cls, reasons = classify_clip(name, row, state_oob, move_oob, state_freeze, flags)
        row["category"], row["category_reasons"] = cls, reasons
        if name in STORYBOARD_CLIPS:
            row["storyboard_required"] = True
        else:
            row["storyboard_required"] = False
    # 特效登记基线：每个角色专属 FX 资源 SHA，以及所有引用 id 的检查。
    own_effects = {}
    for eid, entry in jload(PHASE3).items():
        if entry.get("dedicated_to") == fighter:
            p = abs_path(entry["texture"].removeprefix("res://"))
            own_effects[eid] = dict(path=rel(p), sha256=sha(p) if p.is_file() else None,
                                    recorded_sha256=entry.get("atlas_sha256"),
                                    match=(sha(p) == entry.get("atlas_sha256") if p.is_file() else False))
    return dict(
        fighter=fighter, audit=dict(path=rel(AUDIT), sha256=sha(AUDIT), idle_height=idle_height,
                                    state_sprite_oob=audit["state_sprite_oob"]),
        identity=IDENTITY[fighter],
        cells=dict(path=rel(ROOT / "art/fighters" / fighter / "stage1/cells/cells.json"),
                   sha256=sha(ROOT / "art/fighters" / fighter / "stage1/cells/cells.json"),
                   scale=scale_cells.get("scale"), target_standing=scale_cells.get("target_standing"),
                   cell=scale_cells.get("cell"), anchor=scale_cells.get("anchor"),
                   top_level_cell=manifest.get("cell"), top_level_anchor=manifest.get("anchor")),
        manifest=dict(path=rel(manifest_path), sha256=sha(manifest_path), clip_count=len(clips),
                      total_frames=sum(len(c["rects"]) for c in clips.values()),
                      cell=manifest.get("cell"), anchor=manifest.get("anchor")),
        clips=clip_rows,
        content_files=content_files,
        effect_registration=registration,
        own_effects=own_effects,
        policy=policy,
        state_frames=state_freeze,
        move_frames=move_freeze,
        moves_basis=MOVES_BASIS[fighter],
        review_sheets={
            f"seven_{k}.png": dict(path=rel(REVIEW_DIR / f"seven_{k}.png"), sha256=sha(REVIEW_DIR / f"seven_{k}.png"))
            for k in ("idle", "walk_forward", "special")
        } | {
            f"{fighter}_{k}.png": dict(path=rel(REVIEW_DIR / f"{fighter}_{k}.png"), sha256=sha(REVIEW_DIR / f"{fighter}_{k}.png"))
            for k in ("A", "B")
        } | {
            "cross_idle.png": dict(path=rel(REVIEW_DIR / "cross_idle.png"), sha256=sha(REVIEW_DIR / "cross_idle.png")),
            "cross_walk.png": dict(path=rel(REVIEW_DIR / "cross_walk.png"), sha256=sha(REVIEW_DIR / "cross_walk.png")),
            "cross_special.png": dict(path=rel(REVIEW_DIR / "cross_special.png"), sha256=sha(REVIEW_DIR / "cross_special.png")),
            "grid_defects.png": dict(path=rel(REVIEW_DIR / "grid_defects.png"), sha256=sha(REVIEW_DIR / "grid_defects.png")),
        },
        thresholds=dict(subject="alpha>=128", connectivity_primary=4, connectivity_aux=8,
                        standing_height_tolerance=STANDING_TOL, standing_neighbor_tolerance=NEIGHBOR_TOL,
                        silhouette_diff_min=DIFF_MIN, idle_breath={"head_vertical_range": 4, "adjacent_wrap": 2, "horizontal_drift": 2},
                        walk={"phases": 8, "eye_vertical_range": 8, "adjacent": 4, "support_world_drift": 8},
                        emission_error_px=2, palette_colors_max=32, binary_alpha=[0, 255]),
    )


def main():
    for fighter in FIGHTERS:
        data = measure_fighter(fighter)
        out_dir = ROOT / "art/fighters" / fighter / "stage1/rework-20261112"
        jdump(out_dir / "measurement_evidence.json", data)
        print(fighter, "clips", len(data["clips"]), "frames", data["manifest"]["total_frames"],
              "categories", dict(Counter(row["category"] for row in data["clips"].values())))


if __name__ == "__main__":
    main()
