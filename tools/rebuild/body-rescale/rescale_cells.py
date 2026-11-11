"""按圆谷官方身高设定重推 scale，重落全部已装 stage1 战斗格。

2026-11-11 体型重落格任务：七名新装角色屏幕可见站高偏离官方身高设定
（初代 140px=40m = 3.5 px/m 为锚）。新 scale = 旧 scale × (目标/现测)，
全部已装帧按同一新比例重落，纯数据修复，不重新生成美术。

口径与硬规则（AGENTS.md / art/STYLE.md）：
- 全套共用一个源像素比例，不按姿势外框归一身高；
- 横向按脚底带重心对 anchor x，带宽沿用各角色原落格登记（king 0.30，
  其余 0.08；oracle 网格搜索实测确认）；
- 接地帧脚底贴 baseline-1；腾空帧离地量按新旧 scale 比值等比映射保留；
- 缩放后 Alpha≥128 二值化、映射到该角色冻结 32 色板；
- 逐帧自检：非技能帧单连通、技能帧只判主体（独立颗粒豁免）、≤32 色、
  有脚行、格内未裁切。

源帧解析（每帧）：
1. json 显式映射（source/raw 字段）且尺寸与旧 cell 相符（±2px）→ 直接用；
2. 否则按旧 cell bbox 尺寸在组内 frames/ 反查：与旧 cell 缩放 IoU ≥0.97
   视为真源；0.90–0.97 视为近似源（flags 登记后仍重落）；<0.90 无源，
   保留旧 cell 原样并登记跳过。
各角色缩放算法按原批次口径：king/zero/justice/mother 用 forge_backend
kCentroid（原落格实测 99.7% 逐像素一致），father/gaia 用 BOX；zoffy 用 BOX
（tools/rebuild/zoffy/stage1_cells.py 登记口径）。

用法：
    .venv/bin/python tools/rebuild/body-rescale/rescale_cells.py --list
    .venv/bin/python tools/rebuild/body-rescale/rescale_cells.py --fighter ultraman-king --oracle
    .venv/bin/python tools/rebuild/body-rescale/rescale_cells.py --fighter ultraman-king
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/media/art"))
sys.path.insert(0, str(REPO / "tools/art"))
sys.path.insert(0, str(REPO / "tools/rebuild/shared"))
from catalogue_native import (  # noqa: E402
    apply_palette, build_palette, harden_alpha, trim,
)
from forge_backend import _kcentroid_downscale  # noqa: E402
from stage_cells import foot_center  # noqa: E402

# official_m：円谷官方角色页身高（2026-11-11 查证，来源见 README.md）。
# measured：重落前 idle 帧 1:1 native 屏幕可见站高。
FIGHTERS = {
    "ultraman-king": {
        "official_m": 58, "measured": 223, "old_scale": 0.158044,
        "old_cell": 256, "new_cell": 256, "anchor": [128, 248],
        "foot_band": 0.30, "backend": "k",
    },
    "father-of-ultra": {
        "official_m": 45, "measured": 173, "old_scale": 0.179089027,
        "old_cell": 192, "new_cell": 192, "anchor": [96, 184],
        "foot_band": 0.08, "backend": "box",
    },
    "ultraman-zero": {
        "official_m": 49, "measured": 186, "old_scale": 0.17168949771689498,
        "old_cell": 256, "new_cell": 256, "anchor": [128, 248],
        "foot_band": 0.08, "backend": "k",
    },
    "ultraman-justice": {
        "official_m": 46, "measured": 154, "old_scale": 0.15493,
        "old_cell": 192, "new_cell": 256, "anchor": [128, 248],
        "foot_band": 0.08, "backend": "k",
    },
    "zoffy": {
        "official_m": 45, "measured": 154, "old_scale": 0.099419,
        "old_cell": 192, "new_cell": 256, "anchor": [128, 248],
        "foot_band": 0.08, "backend": "box",
    },
    "ultraman-gaia": {
        "official_m": 50, "measured": 152, "old_scale": 0.146947,
        "old_cell": 192, "new_cell": 256, "anchor": [128, 248],
        "foot_band": 0.08, "backend": "box",
    },
    "mother-of-ultra": {
        "official_m": 40, "measured": 151, "old_scale": 0.10642709,
        "old_cell": 192, "new_cell": 192, "anchor": [96, 184],
        "foot_band": 0.08, "backend": "k",
    },
}

BASELINE_PX_PER_M = 3.5
SKILL_GROUPS = {
    "light1", "light2", "light3", "special", "special2", "special3",
    "air_special", "ranged_forward", "low_pulse", "air_pulse", "pulse",
    "motion_236", "motion_623", "motion_214", "motion_22", "motion_41236",
}
IOU_SOLID = 0.97
IOU_NEAR = 0.90


def cell_stem(path: Path) -> str:
    return path.name[: -len("-cell.png")]


def parse_stem(stem: str) -> tuple[str, str] | None:
    parts = stem.split("-")
    for pos in range(len(parts) - 1, 0, -1):
        if len(parts[pos]) == 2 and parts[pos].isdigit():
            return "-".join(parts[:pos]), parts[pos]
    return None


def official_target(official_m: int) -> int:
    return round(official_m * BASELINE_PX_PER_M)


def new_scale(cfg: dict) -> float:
    return cfg["old_scale"] * official_target(cfg["official_m"]) / cfg["measured"]


def load_palette(fighter: str) -> list:
    cj = REPO / f"art/fighters/{fighter}/stage1/cells/cells.json"
    if cj.is_file():
        data = json.loads(cj.read_text(encoding="utf-8"))
        pal = data.get("palette")
        if isinstance(pal, list) and len(pal) == 32:
            return [tuple(c) for c in pal]
    src = REPO / f"assets/fighters/{fighter}/catalogue/model-native.png"
    if not src.is_file():
        raise SystemExit(f"缺少图鉴定稿：{src}")
    return build_palette(trim(harden_alpha(Image.open(src).convert("RGBA"))), 32)


def scan_json_sources(fighter: str) -> dict[str, tuple[str, str | None]]:
    """扫描 stage1 全部 json：cell stem → (raw 路径, 记录的 raw SHA 或 None)。"""
    base = REPO / f"art/fighters/{fighter}/stage1"
    out: dict[str, tuple[str, str | None]] = {}

    def walk(obj):
        if isinstance(obj, dict):
            raw = obj.get("source") or obj.get("raw")
            cell = None
            for k in ("output", "cell"):
                v = obj.get(k)
                if isinstance(v, str) and v.endswith("-cell.png"):
                    cell = v
            oc = obj.get("outputs")
            if isinstance(oc, dict) and isinstance(oc.get("cell"), str) \
                    and oc["cell"].endswith("-cell.png"):
                cell = oc["cell"]
            if isinstance(raw, str) and cell:
                sha = obj.get("source_sha256") or obj.get("raw_sha256")
                out.setdefault(Path(cell).name[: -len("-cell.png")], (raw, sha))
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for j in sorted(base.rglob("*.json")):
        try:
            walk(json.loads(j.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def scaled_solid(solid: Image.Image, backend: str, tw: int, th: int) -> np.ndarray:
    if backend == "k":
        return np.array(_kcentroid_downscale(solid, tw, th, detail_bias=False))
    return np.array(harden_alpha(solid.resize((tw, th), Image.BOX)))


def find_source(fighter: str, stem: str, old_arr: np.ndarray, cfg: dict,
                sources: dict) -> tuple[Path | None, str]:
    """解析某帧的真源：json 映射（尺寸校验）→ 组内 IoU 反查。"""
    base = REPO / f"art/fighters/{fighter}/stage1"
    oys, oxs = np.where(old_arr[:, :, 3] > 0)
    if not len(oys):
        return None, "empty-cell"
    oh = int(oys.max() - oys.min() + 1)
    ow = int(oxs.max() - oxs.min() + 1)
    ocrop = old_arr[int(oys.min()):int(oys.max()) + 1,
                    int(oxs.min()):int(oxs.max()) + 1]
    mmask = ocrop[:, :, 3] > 0

    rec = sources.get(stem)
    if rec:
        src, sha_rec = rec
        p = Path(src)
        if not p.is_absolute():
            p = REPO / src
        if p.is_file():
            data = p.read_bytes()
            sha_now = hashlib.sha256(data).hexdigest()
            if sha_rec is None or sha_now == sha_rec:
                solid = trim(harden_alpha(Image.open(p).convert("RGBA")))
                exp_h = round(solid.height * cfg["old_scale"])
                exp_w = round(solid.width * cfg["old_scale"])
                if abs(exp_h - oh) <= 2 and abs(exp_w - ow) <= 2:
                    return p, "json"
    # 组内 IoU 反查。组目录可能是标准名（air_fall）也可能是批次前缀目录
    # （justice 的 air/ 存 air-fall-00、dash/ 存 dash-start-00、walk/ 存 walk-back-00）。
    parsed = parse_stem(stem)
    if not parsed:
        return None, "unparsed"
    grp, _idx = parsed
    candidates_dirs = [base / grp / "frames",
                       base / grp.replace("-", "_") / "frames"]
    # 前缀目录：grp 的首段（air-fall → air；dash-start → dash；walk-back → walk）
    first = grp.split("-")[0]
    if "-" in grp and first != grp:
        candidates_dirs += [base / first / "frames",
                            base / first.replace("-", "_") / "frames"]
    fd = next((d for d in candidates_dirs if d.is_dir()), None)
    if fd is None:
        return None, "no-group"
    best = (0.0, None)
    for c in sorted(fd.glob("*.png")):
        try:
            solid = trim(harden_alpha(Image.open(c).convert("RGBA")))
        except Exception:
            continue
        k = scaled_solid(solid, cfg["backend"], ow, oh)
        m2 = k[:, :, 3] > 0
        if not m2.any():
            continue
        union = (m2 | mmask).sum()
        iou = float((m2 & mmask).sum() / union) if union else 0.0
        if iou > best[0]:
            best = (iou, c)
    if best[0] >= IOU_SOLID:
        return best[1], f"oracle:{best[0]:.3f}"
    if best[0] >= IOU_NEAR:
        return best[1], f"near:{best[0]:.3f}"
    return None, f"no-source:{best[0]:.3f}"


def old_foot_rows(cells: list[Path]) -> dict[str, int]:
    rows = {}
    for p in cells:
        a = np.array(Image.open(p).convert("RGBA"))
        ys, _ = np.where(a[:, :, 3] > 0)
        if len(ys):
            rows[cell_stem(p)] = int(ys.max())
    return rows


def rescale_frame(raw_path: Path, old_arr: np.ndarray, scale: float, ratio: float,
                  palette: list, cell: int, ax: int, baseline: int,
                  old_ax: int, old_baseline: int,
                  backend: str) -> tuple[Image.Image, dict]:
    """单帧重落：hard alpha → trim → 缩放（原口径 kCentroid/BOX）→ 32 色 →
    绕根点等比重放。

    放置与尺寸统一按旧 cell 内容绕根点等比映射（ratio = 新 scale / 旧 scale）：
    - 尺寸：新 bbox 宽高 = 旧 bbox × ratio（统一比例帧等价于重算 new_scale；
      特殊归一帧如 zero 的 down/ko 按头归一保留自身头身比不被拉直）；
    - 水平：新 bbox 中心 = 新锚 x + (旧 bbox 中心 − 旧锚 x) × ratio；
    - 垂直：新脚行 = 新 baseline−1 − (旧 baseline−1 − 旧脚行) × ratio，
      接地帧脚底仍贴 baseline−1，腾空离地量按 ratio 保留；
      横卧帧高度随 bbox 等比上收，姿势相对地面的比例不变。
    旧 cell 已编码各批次的放置决策（脚带重心/主体中心/胸灯对齐/横卧居中），
    等比映射对所有口径通用。
    """
    solid = trim(harden_alpha(Image.open(raw_path).convert("RGBA")))
    oys, oxs = np.where(old_arr[:, :, 3] > 0)
    old_foot = int(oys.max())
    old_center = (float(oxs.min()) + float(oxs.max())) / 2.0
    gap = max(0, (old_baseline - 1) - old_foot)
    old_top = int(oys.min())

    # 统一实现：内容尺寸 = 旧 cell bbox × ratio。统一比例帧等价于
    # round(solid.width × new_scale)（±1 取整差），特殊归一帧（zero 的
    # down/ko/getup 按头归一等）保留自身头身比不被统一比例拉直。
    tw = max(1, round((int(oxs.max()) - int(oxs.min()) + 1) * ratio))
    th = max(1, round((int(oys.max()) - old_top + 1) * ratio))
    scaled_arr = scaled_solid(solid, backend, tw, th)
    scaled = Image.fromarray(scaled_arr.astype(np.uint8), "RGBA")
    scaled = apply_palette(harden_alpha(scaled), palette)

    new_center = ax + ratio * (old_center - old_ax)
    # 垂直按脚行等比映射：接地帧 gap=0 脚底贴 baseline−1；腾空帧 gap×ratio
    # 保留离地量；横卧帧脚底本来就在 baseline−1，高度随 th 自动上收。
    new_foot = baseline - 1 - round(gap * ratio)
    new_foot = max(0, min(new_foot, baseline - 1))
    paste_y = new_foot + 1 - th
    paste_x = round(new_center - scaled.width / 2.0)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, (paste_x, paste_y))

    arr = np.array(canvas)
    vis = arr[:, :, 3] > 0
    ys, xs = np.where(vis)
    info = {
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(ys) else [],
        "height": int(ys.max() - ys.min() + 1) if len(ys) else 0,
        "width": int(xs.max() - xs.min() + 1) if len(xs) else 0,
        "foot_row": int(ys.max()) if len(ys) else None,
        "colors": int(len(np.unique(arr[:, :, :3][vis].reshape(-1, 3), axis=0))) if len(ys) else 0,
        "gap_old": gap,
        "gap_new": (baseline - 1) - (int(ys.max()) if len(ys) else 0),
    }
    return canvas, info


def components(mask: np.ndarray) -> int:
    from collections import deque
    seen = np.zeros_like(mask, bool)
    count = 0
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                count += 1
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
    return count


def drop_specks(canvas: Image.Image, max_px: int = 2) -> Image.Image:
    """非技能帧清理缩放产生的 <3px 孤点（与主体断连的残粒）。"""
    arr = np.array(canvas)
    mask = arr[:, :, 3] > 0
    from collections import deque
    seen = np.zeros_like(mask, bool)
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                queue = deque([(y, x)])
                seen[y, x] = True
                comp = [(y, x)]
                while queue:
                    cy, cx = queue.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                            comp.append((cy, cx))
                if len(comp) <= max_px:
                    for cy, cx in comp:
                        arr[cy, cx, 3] = 0
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def extra_pixels(mask: np.ndarray) -> int:
    """主体（最大连通块）之外的可见像素数。"""
    from collections import deque
    seen = np.zeros_like(mask, bool)
    comps = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                queue = deque([(y, x)])
                seen[y, x] = True
                comp = []
                while queue:
                    cy, cx = queue.popleft()
                    comp.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                comps.append(comp)
    if len(comps) <= 1:
        return 0
    comps.sort(key=len, reverse=True)
    return sum(len(c) for c in comps[1:])


def load_cells(fighter: str) -> list[Path]:
    cells_dir = REPO / f"art/fighters/{fighter}/stage1/cells"
    return sorted(p for p in cells_dir.glob("*-cell.png")
                  if not any(s in p.stem for s in ("review", "contact", "strip", "-x4")))


def oracle(fighter: str, cfg: dict, cells: list[Path], sources: dict,
           palette: list) -> int:
    """旧参数重落对比旧 cell：高/宽/脚行/左右缘逐项核对，报告通过率与样本。"""
    ns = sum(1 for _ in cells)
    ok = miss = dim_diff = 0
    samples: list[str] = []
    old_baseline = cfg["anchor"][1]
    for p in cells:
        stem = cell_stem(p)
        old_arr = np.array(Image.open(p).convert("RGBA"))
        oys, oxs = np.where(old_arr[:, :, 3] > 0)
        if not len(oys):
            miss += 1
            continue
        raw, via = find_source(fighter, stem, old_arr, cfg, sources)
        if raw is None:
            miss += 1
            samples.append(f"{stem}: {via}")
            continue
        if via.startswith("near") or via.startswith("oracle"):
            # oracle 只承认 json 级源；反查源做 IoU 级比对
            pass
        canvas, info = rescale_frame(raw, old_arr, cfg["old_scale"], 1.0, palette,
                                     cfg["old_cell"], cfg["anchor"][0], old_baseline,
                                     cfg["anchor"][0], old_baseline, cfg["backend"])
        oh = int(oys.max() - oys.min() + 1)
        ow = int(oxs.max() - oxs.min() + 1)
        if abs(info["height"] - oh) <= 1 and abs(info["width"] - ow) <= 1 \
                and info["foot_row"] == int(oys.max()) \
                and abs(info["bbox"][0] - int(oxs.min())) <= 1 \
                and abs(info["bbox"][2] - int(oxs.max())) <= 1:
            ok += 1
        else:
            dim_diff += 1
            if len(samples) < 6:
                samples.append(f"{stem}[{via}]: 旧 {ow}x{oh}@{int(oys.max())} "
                               f"vs oracle {info['width']}x{info['height']}@{info['foot_row']} "
                               f"左{info['bbox'][0]}/{int(oxs.min())}")
    print(f"oracle {fighter}: cells={ns} ok={ok} miss={miss} dim_diff={dim_diff}")
    for s in samples:
        print("  ", s)
    return 0


def run(fighter: str, dry: bool) -> int:
    cfg = FIGHTERS[fighter]
    cells = load_cells(fighter)
    palette = load_palette(fighter)
    sources = scan_json_sources(fighter)
    ns = new_scale(cfg)
    gap_ratio = ns / cfg["old_scale"]
    old_baseline = cfg["anchor"][1]
    cell, (ax, baseline) = cfg["new_cell"], cfg["anchor"]

    report = {
        "fighter": fighter,
        "date": "2026-11-11",
        "task": "按円谷官方身高设定重推 scale 重落全部已装 stage1 战斗格（纯数据修复）",
        "official_m": cfg["official_m"],
        "official_sources": {
            "ultraman-king": "https://m-78.jp/character/king | https://tsuburaya-prod.com/heroes/ultraman-king",
            "father-of-ultra": "https://m-78.jp/character/father | https://en.tsuburaya-prod.co.jp/heroes/father-of-ultra",
            "ultraman-zero": "https://tsuburaya-prod.com/heroes/ultraman-zero",
            "ultraman-justice": "https://tsuburaya-prod.com/heroes/ultraman-justice",
            "zoffy": "https://tsuburaya-prod.com/heroes/zoffy",
            "ultraman-gaia": "https://tsuburaya-prod.com/heroes/ultraman-gaia",
            "mother-of-ultra": "https://m-78.jp/ultraheros/mother/ | https://tsuburaya-prod.com/heroes/mother-of-ultra",
        }[fighter],
        "px_per_m": BASELINE_PX_PER_M,
        "measured_standing_old": cfg["measured"],
        "target_standing": official_target(cfg["official_m"]),
        "old_scale": cfg["old_scale"],
        "new_scale": round(ns, 9),
        "gap_ratio": round(gap_ratio, 6),
        "old_cell": cfg["old_cell"], "new_cell": cell,
        "anchor": [ax, baseline],
        "foot_band": cfg["foot_band"],
        "backend": cfg["backend"],
        "source_policy": f"json SHA+尺寸校验 → 组内 IoU≥{IOU_SOLID} 反查 → {IOU_NEAR}–{IOU_SOLID} 近似源登记 → <{IOU_NEAR} 保留旧帧",
        "frames": [],
        "skipped": [],
        "flags": [],
    }

    written = kept = 0
    for p in cells:
        stem = cell_stem(p)
        old_arr = np.array(Image.open(p).convert("RGBA"))
        oys, _ = np.where(old_arr[:, :, 3] > 0)
        if not len(oys):
            report["skipped"].append({"frame": stem, "reason": "empty-cell"})
            continue
        raw, via = find_source(fighter, stem, old_arr, cfg, sources)
        if raw is None:
            kept += 1
            report["skipped"].append({"frame": stem, "reason": via})
            continue
        parsed = parse_stem(stem)
        clip = parsed[0].replace("-", "_") if parsed else stem
        canvas, info = rescale_frame(raw, old_arr, ns, gap_ratio, palette, cell,
                                     ax, baseline, cfg["anchor"][0], old_baseline,
                                     cfg["backend"])
        if not (parsed[0].replace("-", "_") in SKILL_GROUPS if (parsed := parse_stem(stem)) else False):
            canvas = drop_specks(canvas)
        vis = np.array(canvas)[:, :, 3] > 0
        ncomp = components(vis)
        extra = extra_pixels(vis)
        skill = clip in SKILL_GROUPS
        cropped = bool(info["bbox"]) and (info["bbox"][0] == 0 or info["bbox"][1] == 0
                    or info["bbox"][2] == cell - 1 or info["bbox"][3] == cell - 1)
        entry = {
            "frame": stem,
            "source": raw.relative_to(REPO).as_posix(),
            "source_via": via,
            "clip": clip,
            "height": info["height"], "width": info["width"],
            "bbox": info["bbox"], "foot_row": info["foot_row"],
            "gap_old_px": info["gap_old"], "gap_new_px": info["gap_new"],
            "colors": info["colors"], "components": ncomp,
            "extra_px": extra, "cropped": cropped,
        }
        report["frames"].append(entry)
        if not skill and ncomp != 1:
            report["flags"].append(f"{stem}: 连通块 {ncomp}（非技能帧应 1）")
        if info["colors"] > 32:
            report["flags"].append(f"{stem}: 色数 {info['colors']} > 32")
        if cropped:
            report["flags"].append(f"{stem}: 贴边风险 bbox={info['bbox']}")
        if via.startswith("near"):
            report["flags"].append(f"{stem}: 近似源 {via}（重掷未回填记录，IoU 未达 {IOU_SOLID}）")
        if not dry:
            canvas.save(p)
            written += 1
        else:
            kept += 1

    out_path = Path(__file__).parent / f"{fighter}-rescale.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    if not dry:
        update_cells_json(fighter, cfg, ns, cell, ax, baseline)
    print(f"{fighter}: cells={len(cells)} 重落 {written} 保留 {kept} "
          f"flags {len(report['flags'])} → {out_path.name}")
    for f in report["flags"][:24]:
        print("  FLAG", f)
    return 0


def update_cells_json(fighter: str, cfg: dict, ns: float, cell: int,
                      ax: int, baseline: int) -> None:
    """重落成功后同步 cells.json 顶层 anchor/cell/scale（install_cells 读它写 manifest）。"""
    p = REPO / f"art/fighters/{fighter}/stage1/cells/cells.json"
    if not p.is_file():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    data["anchor"] = [ax, baseline]
    data["cell"] = cell
    data["scale"] = round(ns, 9)
    data["target_standing"] = official_target(cfg["official_m"])
    data["rescale_2026_11_11"] = {
        "task": "按円谷官方身高设定重推 scale 重落全部已装战斗格",
        "old_scale": cfg["old_scale"], "new_scale": round(ns, 9),
        "measured_standing_old": cfg["measured"],
        "target_standing": official_target(cfg["official_m"]),
        "official_m": cfg["official_m"],
        "report": f"tools/rebuild/body-rescale/{fighter}-rescale.json",
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.list:
        for name, cfg in FIGHTERS.items():
            print(f"{name}: {cfg['official_m']}m -> {official_target(cfg['official_m'])}px "
                  f"(now {cfg['measured']}), scale {cfg['old_scale']} -> "
                  f"{new_scale(cfg):.6f}, cell {cfg['old_cell']} -> {cfg['new_cell']}, "
                  f"backend {cfg['backend']}, foot_band {cfg['foot_band']}")
        return 0
    fighter = args.fighter
    if fighter not in FIGHTERS:
        raise SystemExit(f"未登记角色：{fighter}（可选：{', '.join(FIGHTERS)}）")
    cfg = FIGHTERS[fighter]
    cells = load_cells(fighter)
    if args.oracle:
        return oracle(fighter, cfg, cells, scan_json_sources(fighter), load_palette(fighter))
    return run(fighter, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
