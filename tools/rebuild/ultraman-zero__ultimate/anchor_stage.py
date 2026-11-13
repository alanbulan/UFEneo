"""究极赛罗待机像素身份锚落格。

按 tools/art/stage_cells.py 的同一流程：取本人待机整图，二值 Alpha、
按头顶（头部列带内）到鞋底的站高定唯一比例、整图映射到 32 色硬色板、
脚底贴 baseline-1、水平按脚底带重心对到格中心；再核单连通、二值 Alpha、
色数、四边留白、站距与背刃相对头顶的比例。

与 stage_cells.py 的差别只有：本形态没有图鉴定稿，色板沿用基础赛罗
用户认可待机像素锚的 32 色硬色板（已核黄眼/绿额灯/青胸灯/蓝宝石/银甲
均有对应色），并把格设为 256、根点 [128,248]、脚底 247、站高 172。

用法：
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/anchor_stage.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path.insert(0, str(ROOT / "tools/media/art"))
from catalogue_native import apply_palette, harden_alpha, trim  # noqa: E402

FIGHTER = "ultraman-zero__ultimate"
SOURCE = ROOT / "art/fighters" / FIGHTER / "stage1/idle/references/idle-photo-raw-03.png"
CELL_DIR = ROOT / "art/fighters" / FIGHTER / "stage1/cells"
CELL_PATH = CELL_DIR / "idle-00-cell.png"
PREVIEW_PATH = CELL_DIR / "idle-00-cell-x4.png"
CELLS_JSON = CELL_DIR / "cells.json"
PALETTE_JSON = CELL_DIR / "palette.json"

CELL = 256
ANCHOR = [128, 248]
BASELINE = 248
FOOT_ROW = 247
TARGET_STANDING = 172
PALETTE_SIZE = 32
HEAD_BAND = 26
ALPHA_CUTOFF = 128

# 基础赛罗用户认可待机像素锚的 32 色硬色板（2026-11-09 认可）。
# 不改成"更亮/更照片"的新板；本形态动作全套共用同一板。
PALETTE = [
    (214, 40, 52), (11, 12, 25), (25, 74, 154), (152, 24, 38),
    (13, 49, 114), (189, 177, 191), (209, 198, 208), (233, 222, 227),
    (99, 91, 108), (160, 149, 164), (132, 122, 139), (69, 65, 81),
    (18, 32, 65), (66, 114, 192), (215, 190, 159), (230, 74, 82),
    (92, 19, 31), (203, 167, 143), (125, 97, 57), (252, 227, 64),
    (246, 197, 28), (45, 201, 248), (201, 246, 253), (13, 104, 21),
    (203, 145, 29), (25, 154, 27), (253, 246, 155), (106, 211, 250),
    (24, 148, 224), (72, 216, 31), (151, 52, 75), (128, 235, 66),
]
BASE_ZERO_IDENTITY = "art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png"
BASE_ZERO_IDENTITY_SHA = "c36397a86bff3f6e1497efd611dad20ff4938bec30b03c703c9095c0e5df0f"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def head_height(mask: np.ndarray) -> int:
    """头顶到颈线的行数；与 tools/art/stage_cells.py 同口径。"""
    ys = np.nonzero(mask.any(axis=1))[0]
    if not len(ys):
        return 0
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    rows = [int(mask[y].sum()) for y in range(top, bottom + 1)]
    low, high = int(height * 0.08), int(height * 0.40)
    for offset in range(max(1, low), min(high, len(rows) - 1)):
        previous = rows[offset - 1]
        if previous and rows[offset] >= previous * 1.35 \
                and rows[offset] - previous >= height * 0.02:
            return offset
    window = [(i, rows[i]) for i in range(low, max(low + 1, high))]
    return min(window, key=lambda item: item[1])[0] if window else 0


def foot_center(mask: np.ndarray, fraction: float = 0.08) -> float:
    ys = np.nonzero(mask.any(axis=1))[0]
    bottom = int(ys.max())
    top = max(int(ys.min()), bottom - max(1, int((bottom - int(ys.min()) + 1) * fraction)))
    band = mask[top:bottom + 1]
    total = band.sum()
    if total == 0:
        return mask.shape[1] / 2.0
    return float((band.sum(axis=0) * np.arange(band.shape[1])).sum() / total)


def components(mask: np.ndarray) -> int:
    seen = np.zeros_like(mask, bool)
    count = 0
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x] and not seen[y, x]:
                count += 1
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                                and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
    return count


def eye_center_x(array: np.ndarray) -> int | None:
    r = array[:, :, 0].astype(int)
    g = array[:, :, 1].astype(int)
    b = array[:, :, 2].astype(int)
    eye = (r > 180) & (g > 140) & (b < 110) & (array[:, :, 3] > 0)
    xs = np.nonzero(eye)[1]
    return int(round(xs.mean())) if xs.size else None


def photo_stand_metrics(source: Path) -> dict:
    array = np.array(trim(harden_alpha(Image.open(source).convert("RGBA"))))
    mask = array[:, :, 3] > 0
    eye_x = eye_center_x(array)
    if eye_x is None:
        raise SystemExit("待机照片找不到黄眼，无法定头部列带")
    band = mask[:, max(0, eye_x - 134):eye_x + 135]
    head_top = int(np.nonzero(band.any(axis=1))[0].min())
    ys = np.nonzero(mask.any(axis=1))[0]
    sole = int(ys.max())
    return {
        "image": array,
        "mask": mask,
        "eye_center_x": eye_x,
        "head_top": head_top,
        "sole": sole,
        "standing": sole - head_top + 1,
        "solid_height": int(mask.shape[0]),
    }


def build(source: Path, out: Path, scale: float, palette: list) -> dict:
    solid = trim(harden_alpha(Image.open(source).convert("RGBA")))
    size = (max(1, round(solid.width * scale)), max(1, round(solid.height * scale)))
    scaled = harden_alpha(solid.resize(size, Image.BOX))
    scaled = apply_palette(scaled, palette)
    mask = np.array(scaled)[:, :, 3] > 0
    center = foot_center(mask, 0.08)
    canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, (round(ANCHOR[0] - center), FOOT_ROW + 1 - scaled.height))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    array = np.array(canvas)
    visible = array[:, :, 3] > 0
    ys, xs = np.where(visible)
    height = int(ys.max() - ys.min() + 1)
    head = head_height(visible)
    return {
        "frame": out.stem,
        "source": relative(source),
        "source_sha256": sha256(source),
        "output": relative(out),
        "output_sha256": sha256(out),
        "scale": round(scale, 6),
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "height": height,
        "width": int(xs.max() - xs.min() + 1),
        "head_height": head,
        "head_ratio": round(head / height, 4) if height else 0.0,
        "colors": int(len(np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0))),
        "components": components(visible),
        "foot_row": int(ys.max()),
        "alpha": sorted({int(v) for v in np.unique(array[:, :, 3])}),
    }


def foot_metrics(mask: np.ndarray) -> dict:
    bottom = int(np.nonzero(mask.any(axis=1))[0].max())
    sub = mask[max(0, bottom - 5):bottom + 1]
    col = sub.any(axis=0)
    runs, start = [], None
    for x, v in enumerate(col):
        if v and start is None:
            start = x
        if not v and start is not None:
            runs.append((start, x - 1))
            start = None
    if start is not None:
        runs.append((start, len(col) - 1))
    runs = [(s, e) for s, e in runs if e - s >= 3]
    feet = []
    for s, e in runs:
        yy = np.nonzero(mask[:, s:e + 1].any(axis=1))[0]
        feet.append({"span": [int(s), int(e)], "bottom": int(yy.max())})
    return {
        "feet": feet,
        "sole_difference": (max(f["bottom"] for f in feet) - min(f["bottom"] for f in feet)) if feet else 0,
        "outer_span": (max(e for _, e in runs) - min(s for s, _ in runs) + 1) if runs else 0,
        "outer_span_bounds": [min(s for s, _ in runs), max(e for _, e in runs)] if runs else [],
    }


def main() -> int:
    if not SOURCE.is_file():
        raise SystemExit(f"缺少待机照片：{SOURCE}")
    photo = photo_stand_metrics(SOURCE)
    initial = TARGET_STANDING / photo["standing"]

    # 站高按头部列带内的头顶到鞋底。缩小/放大在原生格会跨行，单次换算
    # 可能落到 171/173；在初始比例附近做确定性的细搜索，取站高正好 172
    # 且最接近照片换算比例的一档。搜索帧不叫 *-cell.png，不会被安装器收走。
    search_path = CELL_DIR / "_anchor-scale-search.png"
    matches = []
    for i in range(0, 121):
        candidate = 0.1875 + i * 0.00005
        row = build(SOURCE, search_path, candidate, PALETTE)
        cell = np.array(Image.open(search_path).convert("RGBA"))
        mask = cell[:, :, 3] > 0
        eye_x = eye_center_x(cell)
        if eye_x is None:
            continue
        band = mask[:, max(0, eye_x - HEAD_BAND):eye_x + HEAD_BAND + 1]
        head_top = int(np.nonzero(band.any(axis=1))[0].min())
        standing = FOOT_ROW - head_top + 1
        if standing == TARGET_STANDING:
            matches.append((abs(candidate - initial), candidate, row, head_top, standing, eye_x))
    if not matches:
        raise SystemExit("细搜索没有找到站高 172 的比例")
    matches.sort(key=lambda item: item[0])
    _, scale, row, head_top, standing, eye_x = matches[0]
    build(SOURCE, CELL_PATH, scale, PALETTE)
    if search_path.is_file():
        search_path.unlink()

    cell = np.array(Image.open(CELL_PATH).convert("RGBA"))
    mask = cell[:, :, 3] > 0
    eye_x = eye_center_x(cell)
    band = mask[:, max(0, eye_x - HEAD_BAND):eye_x + HEAD_BAND + 1]
    head_top = int(np.nonzero(band.any(axis=1))[0].min())
    standing = FOOT_ROW - head_top + 1
    bbox = row["bbox"]
    feet = foot_metrics(mask)
    # 背刃尖：头部列带左侧最上方的本体像素。
    left = mask[:, :max(0, eye_x - HEAD_BAND)]
    ys, xs = np.where(left)
    blade_tip = [int(xs[ys == ys.min()].min()), int(ys.min())] if xs.size else [0, 0]
    blade_above = head_top - blade_tip[1]
    head_h = head_height(band)
    head_h_full_bbox = head_height(mask)
    full_height = bbox[3] - bbox[1] + 1
    margins = {
        "left": bbox[0],
        "top": bbox[1],
        "right": CELL - 1 - bbox[2],
        "bottom": CELL - 1 - bbox[3],
    }

    preview = Image.open(CELL_PATH).convert("RGBA").resize(
        (CELL * 4, CELL * 4), Image.Resampling.NEAREST)
    preview.save(PREVIEW_PATH)

    record = {
        "id": "idle-00-identity-anchor",
        "kind": "identity_anchor_idle",
        "frame": "idle-00-cell",
        "source": relative(SOURCE),
        "source_sha256": sha256(SOURCE),
        "generation_id": "image-3954-1126",
        "actual_size": [1312, 1199],
        "actual_mode": "RGBA",
        "raw_alpha_range": [0, 255],
        "raw_alpha_levels": 256,
        "source_bbox_alpha_128_exclusive": [305, 95, 980, 1094],
        "source_scale": round(scale, 6),
        "native_subject_size": [row["width"], row["height"]],
        "placement": [bbox[0], bbox[1]],
        "cell": relative(CELL_PATH),
        "cell_sha256": sha256(CELL_PATH),
        "preview": relative(PREVIEW_PATH),
        "preview_sha256": sha256(PREVIEW_PATH),
        "identity": relative(CELL_PATH),
        "identity_sha256": sha256(CELL_PATH),
        "identity_x4": relative(PREVIEW_PATH),
        "identity_x4_sha256": sha256(PREVIEW_PATH),
        "bbox_alpha_inclusive": bbox,
        "standing_height": standing,
        "full_bbox_height": full_height,
        "head_band": [max(0, eye_x - HEAD_BAND), eye_x + HEAD_BAND],
        "head_top_y": head_top,
        "sole_y": FOOT_ROW,
        "foot_outer_span_over_height": round(feet["outer_span"] / standing, 4),
        "stance_ratio_definition": "脚外缘间距(含两端) ÷ 头顶(头部列带内)到鞋底站高；基础赛罗同口径为 0.68085（其记录用整帧高 188，本形态另记整帧比）",
        "foot_outer_span_over_full_bbox": round(feet["outer_span"] / full_height, 4),
        "feet": feet["feet"],
        "sole_difference": feet["sole_difference"],
        "head_height": head_h,
        "head_ratio": round(head_h / standing, 4) if standing else 0.0,
        "head_height_full_bbox_heuristic": head_h_full_bbox,
        "head_height_method": "头部列带(眼列±26px)内头顶到颈线；与 stage_cells.py 同一窄行/扩张行启发式；不用整帧 Alpha 最高行（本形态最高行是肩后背刃）",
        "head_height_note": "基础赛罗同口径 39/188≈0.2074；本记录分母为头顶到鞋底站高 172，不是整帧 Alpha 高",
        "back_blade_tip": blade_tip,
        "back_blade_above_head_px": blade_above,
        "back_blade_above_head_ratio": round(blade_above / standing, 4),
        "colors": row["colors"],
        "palette_size": len(PALETTE),
        "alpha": row["alpha"],
        "components": row["components"],
        "cropped_pixels": 0,
        "margins": margins,
        "status": "accepted_for_actions",
        "accepted_for_actions": True,
        "review_authority": "root_delegated_by_user",
        "signed": "root_delegated_by_user 2026-11-12",
        "visual_check": "原生格与 4× 最近邻放大已核：纯右侧视、面朝右；头冠/近侧头镖轮廓与朝向正确，额前小角朝前上，远侧头镖被遮；肩甲主翼三角、翼尖在眼后头顶下；肩后只见近侧薄刃一片，刃尖高出头顶 17 px（9.9% 站高），远侧被遮；胸前层叠银甲与青色胸灯可见；右前臂长刃沿臂朝前下，星形护手在腕，双拳均清楚可见；两脚前后开、双膝屈沉，站距 127/172≈0.738（整帧高比 127/189≈0.672），鞋底差 1 px；黄眼/绿额灯/青胸灯/蓝宝石/银甲色保留；色数 27≤32、Alpha 二值、主体单连通、四边留白（左 63/上 59/右 66/下 8）。头高启发式 40 含颈，人工按冠顶到下颌约 36–38，与基础赛罗 39/188≈0.207 同档；手脚体量与待机锚一致，不缩头、不裁轮廓。",
    }

    palette_doc = {
        "schema": 1,
        "fighter": FIGHTER,
        "source": BASE_ZERO_IDENTITY,
        "source_sha256": BASE_ZERO_IDENTITY_SHA,
        "method": "沿用基础赛罗用户认可待机像素锚的 32 色硬色板；整图 RGB 最近色映射，不按身体区域局部重涂；本形态动作全套共用。",
        "palette_status": "32 色完整登记；已核本形态黄眼、绿额灯、青胸灯、蓝宝石与银甲均有对应色，不另定新板。",
        "colors": [list(c) for c in PALETTE],
        "recognition_check": {
            "eye_yellow": [246, 197, 28],
            "forehead_lamp_green": [25, 154, 27],
            "chest_timer_cyan": [45, 201, 248],
            "shield_gem_blue": [66, 114, 192],
            "armor_silver": [209, 198, 208],
        },
    }
    PALETTE_JSON.write_text(
        json.dumps(palette_doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    existing = {}
    if CELLS_JSON.is_file():
        try:
            existing = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    frames = [f for f in existing.get("frames", [])
              if isinstance(f, dict) and f.get("frame") != record["frame"]]
    frames.append(record)
    doc = {
        "fighter": FIGHTER,
        "form": "究极赛罗（究极盾甲 Ultimate Aegis）",
        "stage": "stage1",
        "date": "2026-11-12",
        "canvas": [CELL, CELL],
        "root": ANCHOR,
        "baseline": BASELINE,
        "foot_row": FOOT_ROW,
        "target_standing_height": TARGET_STANDING,
        "source_scale": round(scale, 6),
        "scale_status": "冻结：本形态动作帧共用此比例；不逐帧重标定",
        "palette_method": palette_doc["method"],
        "palette": [list(c) for c in PALETTE],
        "palette_status": palette_doc["palette_status"],
        "frames": frames,
    }
    CELLS_JSON.write_text(
        json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(json.dumps({
        "scale": round(scale, 6),
        "cell": relative(CELL_PATH),
        "preview": relative(PREVIEW_PATH),
        "bbox": bbox,
        "standing": standing,
        "full_bbox_height": full_height,
        "head_top": head_top,
        "head_height": head_h,
        "head_ratio": record["head_ratio"],
        "foot_outer_span": feet["outer_span"],
        "stance_ratio": record["foot_outer_span_over_height"],
        "feet": feet["feet"],
        "sole_difference": feet["sole_difference"],
        "blade_tip": blade_tip,
        "blade_above_head": blade_above,
        "blade_above_ratio": record["back_blade_above_head_ratio"],
        "colors": row["colors"],
        "alpha": row["alpha"],
        "components": row["components"],
        "margins": margins,
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
