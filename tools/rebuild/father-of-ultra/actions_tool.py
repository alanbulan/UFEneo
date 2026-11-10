#!/usr/bin/env python3
"""奥特之父 stage1 动作帧落格、测量与联系表。

动作帧唯一参考是 `stage1/idle/frames/pixel-raw-02.png` 的派生洁净版
（生成时用，见 `idle/references/`）。生图模型会按待机源的低透明度红晕
额外补一层辉光；本工具落格前只保留 alpha>=200 主体最大连通块 1 px 内、
且 alpha>=128 的最大连通块，再交给 `tools/art/stage_cells.py` 的统一比例
落格。原始辉光像素数、清理参数与清理后连通块都写进记录，不冒充原始通过
辉光门。

子命令：
  inspect  测量原始图与清理后主体（不落格）
  land     按 JSON 清单逐帧清理、落格并合并进 cells.json
  sheet    从已落格帧生成 2x 最近邻联系表

清单条目：
  {"clip":"walk_forward","index":0,"name":"walk_forward-00",
   "source":"art/.../walk_forward/frames/walk_forward-00-raw-2.png",
   "generation_id":"image-...","prompt":"...","air":false,"foot_row":null}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path[:0] = [
    str(ROOT / "tools"),
    *[str(p) for p in (ROOT / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (ROOT / "tools/rebuild").iterdir() if p.is_dir()],
]

import stage_cells  # noqa: E402

CELL = 192
ANCHOR_X = 96
BASELINE = 184
TARGET_STANDING = 173
TARGET_HEAD_HEIGHT = 38
TARGET_HEAD_WIDTH = 32
HEAD_TOL = 0.08
HEAD_WIDTH_TOL = 0.12
CELLS_JSON = ROOT / "art/fighters/father-of-ultra/stage1/cells/cells.json"
SCALE_SOURCE = ROOT / "art/fighters/father-of-ultra/stage1/idle/frames/pixel-raw-02.png"
CLEAN_REFERENCE = ROOT / "art/fighters/father-of-ultra/stage1/idle/references/pixel-raw-02-clean-alpha.png"
CLEAN_REFERENCE_RGB0 = ROOT / "art/fighters/father-of-ultra/stage1/idle/references/pixel-raw-02-clean.png"

GOLD = lambda r, g, b: (r > 140) & (g > 100) & (b < 100) & (r - b > 60)  # noqa: E731
WHITE = lambda r, g, b: (r > 185) & (g > 185) & (b > 185)  # noqa: E731


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_palette() -> list:
    data = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
    return [tuple(int(v) for v in color) for color in data["palette"]]


def components(mask: np.ndarray) -> tuple[int, np.ndarray]:
    """4 连通块数量与最大块的布尔掩码。"""
    seen = np.zeros_like(mask, bool)
    count = 0
    best = np.zeros_like(mask, bool)
    best_n = 0
    height, width = mask.shape
    for y in range(height):
        row = mask[y]
        for x in range(width):
            if row[x] and not seen[y, x]:
                count += 1
                queue = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while queue:
                    cy, cx = queue.popleft()
                    cells.append((cy, cx))
                    if cy > 0 and mask[cy - 1, cx] and not seen[cy - 1, cx]:
                        seen[cy - 1, cx] = True
                        queue.append((cy - 1, cx))
                    if cy + 1 < height and mask[cy + 1, cx] and not seen[cy + 1, cx]:
                        seen[cy + 1, cx] = True
                        queue.append((cy + 1, cx))
                    if cx > 0 and mask[cy, cx - 1] and not seen[cy, cx - 1]:
                        seen[cy, cx - 1] = True
                        queue.append((cy, cx - 1))
                    if cx + 1 < width and mask[cy, cx + 1] and not seen[cy, cx + 1]:
                        seen[cy, cx + 1] = True
                        queue.append((cy, cx + 1))
                if len(cells) > best_n:
                    best_n = len(cells)
                    best = np.zeros_like(mask, bool)
                    for cy, cx in cells:
                        best[cy, cx] = True
    return count, best


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(radius):
        shifted = out.copy()
        shifted[1:, :] |= out[:-1, :]
        shifted[:-1, :] |= out[1:, :]
        shifted[:, 1:] |= out[:, :-1]
        shifted[:, :-1] |= out[:, 1:]
        out = shifted
    return out


def bbox(mask: np.ndarray) -> list | None:
    ys, xs = np.where(mask)
    if not len(ys):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def alpha_stats(im: Image.Image) -> dict:
    alpha = np.array(im.convert("RGBA"))[:, :, 3]
    return {
        "size": list(im.size),
        "mode": im.mode,
        "alpha_range": [int(alpha.min()), int(alpha.max())],
        "alpha_levels": int(len(np.unique(alpha))),
        "corners": [int(alpha[0, 0]), int(alpha[0, -1]), int(alpha[-1, 0]), int(alpha[-1, -1])],
    }


def despeckle_alpha(a: np.ndarray, min_pixels: int = 8) -> tuple[np.ndarray, int, int]:
    """移除 alpha 1–15 的尘点与 alpha>=200 的孤立小尘点（<min_pixels），不算主体。"""
    out = a.copy()
    alpha = out[:, :, 3]
    dust = (alpha > 0) & (alpha < 16)
    out[dust] = 0
    dust_count = int(dust.sum())
    alpha = out[:, :, 3]
    hard = alpha >= 200
    seen = np.zeros_like(hard, bool)
    removed = 0
    height, width = hard.shape
    for y in range(height):
        for x in range(width):
            if hard[y, x] and not seen[y, x]:
                queue = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while queue:
                    cy, cx = queue.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < height and 0 <= nx < width \
                                and hard[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                if len(cells) < min_pixels:
                    removed += len(cells)
                    for cy, cx in cells:
                        out[cy, cx, 3] = 0
    return out, removed, dust_count


def raw_measure(im: Image.Image) -> dict:
    a, despeckled, dust = despeckle_alpha(np.array(im.convert("RGBA")))
    alpha = a[:, :, 3]
    hard = alpha >= 200
    _, subject = components(hard)
    _, body = components(alpha >= 128)
    allowed = dilate(subject, 3)
    outside = allowed & ~subject
    return {
        **alpha_stats(Image.fromarray(a, "RGBA")),
        "dust_alpha_1_15_pixels": dust,
        "despeckled_alpha200_pixels": despeckled,
        "bbox_alpha0": bbox(alpha > 0),
        "subject_bbox_alpha200": bbox(subject),
        "subject_pixels_alpha200": int(subject.sum()),
        "halo_outside_alpha16": int(((alpha >= 16) & outside).sum()),
        "halo_outside_alpha200": int(((alpha >= 200) & outside).sum()),
        "alpha128_bbox": bbox(body),
        "alpha128_pixels": int(body.sum()),
    }


def clean_raw(im: Image.Image) -> tuple[Image.Image, dict]:
    """去掉主体外辉光，只留 alpha>=200 主体最大块 1 px 内、alpha>=128 的最大块。"""
    a, despeckled, dust = despeckle_alpha(np.array(im.convert("RGBA")))
    alpha = a[:, :, 3]
    hard = alpha >= 200
    _, subject = components(hard)
    allowed = dilate(subject, 1)
    keep_candidate = (alpha >= 128) & allowed
    count, keep = components(keep_candidate)
    out = a.copy()
    out[:, :, 3] = np.where(keep, alpha, 0)
    stats = {
        "method": "alpha 1–15 尘点与 alpha>=200 孤立尘点(<8px)先移除；主体最大块外扩1px 内取 alpha>=128 最大连通块；其余 alpha 置0",
        "dust_alpha_1_15_pixels": dust,
        "despeckled_alpha200_pixels": despeckled,
        "subject_bbox_alpha200": bbox(subject),
        "keep_bbox": bbox(keep),
        "keep_pixels": int(keep.sum()),
        "keep_components_after_cut": 1,
        "candidate_components": count,
        "removed_alpha16_pixels": int(((alpha >= 16) & ~keep).sum()),
        "removed_alpha200_pixels": int(((alpha >= 200) & ~keep).sum()),
        "corners": [int(out[0, 0, 3]), int(out[0, -1, 3]), int(out[-1, 0, 3]), int(out[-1, -1, 3])],
    }
    return Image.fromarray(out, "RGBA"), stats


def prepare_scaled(image: Image.Image, scale: float) -> Image.Image:
    solid = stage_cells.trim(stage_cells.harden_alpha(image))
    size = (max(1, round(solid.width * scale)), max(1, round(solid.height * scale)))
    return stage_cells.harden_alpha(solid.resize(size, Image.BOX))


def land_image(image: Image.Image, out: Path, palette: list, scale: float,
               foot_row: int, anchor_x: int = ANCHOR_X, cell: int = CELL,
               foot_band: float = 0.08, center_override: float | None = None) -> dict:
    scaled = prepare_scaled(image, scale)
    scaled = stage_cells.apply_palette(scaled, palette)
    mask = np.array(scaled)[:, :, 3] > 0
    center = center_override if center_override is not None else stage_cells.foot_center(mask, foot_band)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    x = round(anchor_x - center)
    y = foot_row + 1 - scaled.height
    canvas.alpha_composite(scaled, (x, y))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)

    array = np.array(canvas)
    visible = array[:, :, 3] > 0
    ys, xs = np.where(visible)
    return {
        "output": rel(out),
        "output_sha256": sha256(out),
        "scale": round(scale, 9),
        "bbox_inclusive": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "height": int(ys.max() - ys.min() + 1),
        "width": int(xs.max() - xs.min() + 1),
        "colors": int(len(np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0))),
        "components": stage_cells.components(visible),
        "alpha": sorted({int(v) for v in np.unique(array[:, :, 3])}),
        "foot_row": int(ys.max()),
        "placement": [int(x), int(y)],
        "scaled_size": [int(scaled.width), int(scaled.height)],
    }


def component_sizes(mask: np.ndarray) -> list:
    """返回各 4 邻接连通块像素数，降序。技能帧可有独立颗粒/弹体。"""
    seen = np.zeros_like(mask, bool)
    sizes = []
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x] and not seen[y, x]:
                size = 0
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    size += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                                and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                sizes.append(size)
    return sorted(sizes, reverse=True)


def head_measure(cell_path: Path) -> dict:
    a = np.array(Image.open(cell_path).convert("RGBA"))
    mask = a[:, :, 3] > 0
    r, g, b = (a[:, :, i].astype(int) for i in range(3))
    gold = GOLD(r, g, b) & mask
    # 技能帧掌心的淡金贴掌光点也会命中 GOLD；眼列取“最靠上且不少于 3px
    # 的金色连通块”，不能用全部金色像素的中位数，否则眼行会落到掌上。
    seen = np.zeros_like(gold, bool)
    candidates = []
    for y in range(gold.shape[0]):
        for x in range(gold.shape[1]):
            if gold[y, x] and not seen[y, x]:
                pts = []
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    pts.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < gold.shape[0] and 0 <= nx < gold.shape[1] \
                                and gold[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                if len(pts) >= 3:
                    candidates.append(pts)
    source = "gold_eyes_topmost"
    if candidates:
        pts = min(candidates, key=lambda p: np.median([q[0] for q in p]))
        eye_y = int(round(float(np.median([q[0] for q in pts]))))
        eye_x = int(round(float(np.mean([q[1] for q in pts]))))
    else:
        source = "fallback_no_gold"
        top = int(np.where(mask.any(axis=1))[0].min())
        eye_y = top + 29
        eye_x = ANCHOR_X
    band0, band1 = max(0, eye_x - 26), min(CELL - 1, eye_x + 26)
    band = mask[:, band0:band1 + 1]
    rows = np.where(band.any(axis=1))[0]
    crown_top = int(rows.min()) if len(rows) else None
    # 眼行取包含眼列像素的连续段宽度：护架拳、举起的手臂可能在同一行
    # 另起一段，不能拿整行最大最小差当“头宽”。
    widths = []
    for yy in range(max(0, eye_y - 1), min(CELL, eye_y + 2)):
        xs_row = np.where(mask[yy, band0:band1 + 1])[0]
        if not len(xs_row):
            continue
        runs = []
        start = previous = int(xs_row[0])
        for x in xs_row[1:]:
            x = int(x)
            if x - previous > 1:
                runs.append((start, previous))
                start = x
            previous = x
        runs.append((start, previous))
        run = min(runs, key=lambda r: 0 if r[0] <= eye_x - band0 <= r[1]
                  else min(abs(eye_x - band0 - r[0]), abs(eye_x - band0 - r[1])))
        widths.append(run[1] - run[0] + 1)
    head_width = min(widths) if widths else 0
    white = WHITE(r, g, b) & mask
    wx0, wx1 = max(0, eye_x - 8), min(CELL - 1, eye_x + 12)
    wy0, wy1 = max(0, eye_y), min(CELL, eye_y + 15)
    wys, _ = np.where(white[wy0:wy1, wx0:wx1 + 1])
    beard_bottom = wy0 + int(wys.max()) if len(wys) else None
    head_height = (beard_bottom - crown_top + 1) if (crown_top is not None and beard_bottom is not None) else None
    overall_top = int(np.where(mask.any(axis=1))[0].min())
    return {
        "eye_source": source,
        "eye_row_y": eye_y,
        "eye_center_x": eye_x,
        "head_band_x": [band0, band1],
        "crown_top_y": crown_top,
        "overall_top_y": overall_top,
        "head_width_eye_row_px": head_width,
        "beard_bottom_y": beard_bottom,
        "head_height_px": head_height,
        "head_height_delta_vs_idle_pct": round((head_height - TARGET_HEAD_HEIGHT) / TARGET_HEAD_HEIGHT * 100, 2) if head_height else None,
        "head_width_delta_vs_idle_pct": round((head_width - TARGET_HEAD_WIDTH) / TARGET_HEAD_WIDTH * 100, 2) if head_width else None,
        "above_head_structure": bool(overall_top < (crown_top or overall_top) - 2),
    }


def scale_for_source() -> float:
    solid = stage_cells.solid_source(SCALE_SOURCE)
    return TARGET_STANDING / solid.height


def process_entry(entry: dict, palette: list, scale: float, out_dir: Path,
                  foot_band: float = 0.08) -> dict:
    source = ROOT / entry["source"]
    raw = raw_measure(Image.open(source))
    cleaned, cleanup = clean_raw(Image.open(source))
    solid = stage_cells.trim(stage_cells.harden_alpha(cleaned))
    cell_height = max(1, round(solid.height * scale))
    air = bool(entry.get("air"))
    if air:
        requested = int(entry.get("foot_row") or TARGET_STANDING)
        foot_row = max(requested, cell_height - 1)
        foot_row = min(foot_row, BASELINE - 1)
        foot_mode = "air"
    else:
        foot_row = BASELINE - 1
        foot_mode = "ground"
    out = out_dir / f"{entry['name']}-cell.png"
    # 水平对位：默认脚底带 0.08；若人物越出格边，改用 0.20 覆盖腿段，
    # 仍越界则按整帧 bbox 居中。冲步/后蹬帧的脚底带不是人物中心，
    # 不能为了固定脚心把头部裁出格。
    scaled = prepare_scaled(cleaned, scale)
    scaled_mask = np.array(scaled)[:, :, 3] > 0
    band_used = entry.get("foot_band", foot_band)
    center = stage_cells.foot_center(scaled_mask, band_used)
    left = round(ANCHOR_X - center)
    right = left + scaled.width - 1
    if left < 0 or right >= CELL:
        band_used = 0.20
        center = stage_cells.foot_center(scaled_mask, band_used)
        left = round(ANCHOR_X - center)
        right = left + scaled.width - 1
    if left < 0 or right >= CELL:
        band_used = "bbox"
        center = (scaled.width - 1) / 2.0
        left = round(ANCHOR_X - center)
        right = left + scaled.width - 1
    landed = land_image(cleaned, out, palette, scale, foot_row,
                        foot_band=0.08 if isinstance(band_used, str) else band_used,
                        center_override=center)
    landed["foot_band_used"] = band_used
    landed["horizontal_fit"] = [int(left), int(right)]
    landed_mask = np.array(Image.open(out).convert("RGBA"))[:, :, 3] > 0
    landed["component_pixels"] = component_sizes(landed_mask)[:8]
    head = head_measure(out)
    head_gate = bool(entry.get("head_gate", True))
    components_gate = bool(entry.get("components_gate", True))
    hard = {
        "components_1": (not components_gate) or landed["components"] == 1,
        "alpha_binary": landed["alpha"] == [0, 255],
        "colors_le_32": landed["colors"] <= 32,
        "head_width_within_12pct": (not head_gate) or (
            head["head_width_eye_row_px"] > 0
            and abs(head["head_width_delta_vs_idle_pct"]) <= HEAD_WIDTH_TOL * 100),
        "raw_halo200_zero": raw["halo_outside_alpha200"] == 0,
        "raw_corners_zero": raw["corners"] == [0, 0, 0, 0],
        "fits_cell": cell_height <= CELL and scaled.width <= CELL
        and landed["placement"][1] >= 0 and left >= 0 and right < CELL,
    }
    rejects = [key for key, ok in hard.items() if not ok]
    if rejects:
        out.unlink(missing_ok=True)
    notes = []
    if raw["halo_outside_alpha16"] > 100:
        notes.append(f"原始 alpha>=16 辉光 {raw['halo_outside_alpha16']} px 超门，落格前按主体+1px 清理，清理后 {cleanup['removed_alpha16_pixels']} px 被移除")
    if head["head_height_px"] is not None and abs(head["head_height_delta_vs_idle_pct"]) > HEAD_TOL * 100:
        notes.append(f"头高 {head['head_height_px']} 偏离待机 {TARGET_HEAD_HEIGHT} 的 ±8%，需目视核对")
    if head["above_head_structure"]:
        notes.append("头部列带外有高于冠顶的结构（披风/手臂），冠顶按头部列带量取")
    if not head_gate:
        notes.append(entry.get("head_note") or "反应/翻滚/空中帧头部投影变化，头宽与头高只报告，不作硬门")
    if not components_gate:
        notes.append(f"技能帧按规则允许多连通块；主块 {landed['component_pixels'][0] if landed['component_pixels'] else 0} px，其余按独立光效/颗粒登记，不作整帧单连通硬门")
    return {
        "clip": entry["clip"],
        "index": int(entry["index"]),
        "name": entry["name"],
        "source": entry["source"],
        "source_sha256": sha256(source),
        "source_actual_size": raw["size"],
        "source_mode": raw["mode"],
        "generation_id": entry.get("generation_id"),
        "model": entry.get("model", "codex/gpt-image-2"),
        "quality": entry.get("quality", "high"),
        "requested_size": entry.get("requested_size", "1024x1536"),
        "prompt": entry.get("prompt"),
        "prompt_char_count": len(entry.get("prompt") or ""),
        "reference": rel(CLEAN_REFERENCE) if entry.get("reference", "clean-alpha") == "clean-alpha" else rel(CLEAN_REFERENCE_RGB0),
        "air": air,
        "head_gate": head_gate,
        "foot_mode": foot_mode,
        "raw": raw,
        "cleanup": cleanup,
        "landing": landed,
        "head": head,
        "hard_gates": hard,
        "rejects": rejects,
        "status": "accepted" if not rejects else "rejected",
        "notes": notes,
    }


def merge_cells(records: list, contact_sheets: list | None = None) -> dict:
    data = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
    block = data.get("actions_2026_11_10") or {}
    existing = {frame["name"]: frame for frame in block.get("frames", [])}
    for record in records:
        existing[record["name"]] = record
    frames = sorted(existing.values(), key=lambda f: (f["clip"], f["index"]))
    accepted = [f for f in frames if f["status"] == "accepted"]
    rejected = [f for f in frames if f["status"] != "accepted"]
    block.update({
        "date": "2026-11-10",
        "reference": {
            "anchor_cell": rel(ROOT / "art/fighters/father-of-ultra/stage1/cells/idle-candidate-01-cell.png"),
            "production_reference": rel(SCALE_SOURCE),
            "generation_reference": rel(CLEAN_REFERENCE),
            "generation_reference_sha256": sha256(CLEAN_REFERENCE),
            "note": "洁净版只把待机源 alpha<16 的辉光尘点置 0，人物像素未改；生图模型仍会补软红晕，落格时按主体最大连通块清理并记录。",
        },
        "scale_source": rel(SCALE_SOURCE),
        "scale": round(scale_for_source(), 9),
        "cell": CELL,
        "anchor": [ANCHOR_X, BASELINE],
        "target_standing": TARGET_STANDING,
        "target_head_height_px": TARGET_HEAD_HEIGHT,
        "target_head_width_px": TARGET_HEAD_WIDTH,
        "foot_band": 0.08,
        "frames": frames,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "flags": [f"{f['name']}: {', '.join(f['rejects'])}" for f in rejected],
        "notes": [
            "全部动作帧统一使用本文件 palette 的 32 色与 scale；不按单帧外框归一身高。",
            "动作帧只引待机像素源的洁净派生版一张；未追加其它角色、正面或 3/4 参考。",
            "头部比例按头部列带（眼列 ±26px）量冠顶，不用整帧最高行；白须底取面部正下方窄窗。",
        ],
    })
    if contact_sheets:
        block["contact_sheets"] = sorted(set(contact_sheets))
    data["actions_2026_11_10"] = block
    CELLS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return block


def load_font(size: int = 18):
    for path in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_sheet(names: list[str], out: Path, cols: int = 6) -> dict:
    data = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
    block = data.get("actions_2026_11_10", {})
    by_name = {f["name"]: f for f in block.get("frames", [])}
    missing = [n for n in names if n not in by_name or by_name[n]["status"] != "accepted"]
    names = [n for n in names if n not in missing]
    if not names:
        raise SystemExit("没有可排入联系表的已接收帧")
    zoom = 2
    cell = CELL * zoom
    label_h = 26
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + label_h)), (32, 32, 32))
    draw = ImageDraw.Draw(sheet)
    font = load_font(18)
    for i, name in enumerate(names):
        record = by_name[name]
        path = ROOT / record["landing"]["output"]
        image = Image.open(path).convert("RGBA").resize((cell, cell), Image.NEAREST)
        background = Image.new("RGBA", (cell, cell), (24, 24, 24, 255))
        background.alpha_composite(image)
        x = (i % cols) * cell
        y = (i // cols) * (cell + label_h)
        sheet.paste(background.convert("RGB"), (x, y))
        draw.text((x + 4, y + cell + 2), f"{name} h{record['landing']['height']} w{record['head']['head_width_eye_row_px']}", fill=(230, 230, 230), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return {"path": rel(out), "sha256": sha256(out), "frames": names, "missing": missing, "cols": cols}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("sources", nargs="+")

    p_land = sub.add_parser("land")
    p_land.add_argument("--manifest", required=True)
    p_land.add_argument("--out-dir", default="art/fighters/father-of-ultra/stage1/cells")
    p_land.add_argument("--names", nargs="+", default=None, help="只处理这些帧名")

    p_sheet = sub.add_parser("sheet")
    p_sheet.add_argument("--names", nargs="+", required=True)
    p_sheet.add_argument("--out", required=True)
    p_sheet.add_argument("--cols", type=int, default=6)

    args = parser.parse_args(argv)
    if args.cmd == "inspect":
        for text in args.sources:
            path = Path(text)
            if not path.is_absolute():
                path = ROOT / path
            raw = raw_measure(Image.open(path))
            _, cleanup = clean_raw(Image.open(path))
            print(json.dumps({"source": rel(path), "sha256": sha256(path), "raw": raw, "cleanup": cleanup},
                             ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "land":
        manifest = Path(args.manifest)
        if not manifest.is_absolute():
            manifest = ROOT / manifest
        entries = json.loads(manifest.read_text(encoding="utf-8"))
        if args.names:
            wanted = set(args.names)
            entries = [entry for entry in entries if entry["name"] in wanted]
            missing = wanted - {entry["name"] for entry in entries}
            if missing:
                raise SystemExit(f"清单缺少帧：{sorted(missing)}")
        palette = load_palette()
        scale = scale_for_source()
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
        records = [process_entry(entry, palette, scale, out_dir) for entry in entries]
        block = merge_cells(records)
        print(json.dumps({
            "accepted": [r["name"] for r in records if r["status"] == "accepted"],
            "rejected": [{"name": r["name"], "rejects": r["rejects"], "notes": r["notes"]} for r in records if r["status"] != "accepted"],
            "total_accepted": block["accepted_count"],
        }, ensure_ascii=False, indent=1))
        return 0 if all(r["status"] == "accepted" for r in records) else 1
    if args.cmd == "sheet":
        out = Path(args.out)
        if not out.is_absolute():
            out = ROOT / out
        print(json.dumps(make_sheet(args.names, out, args.cols), ensure_ascii=False, indent=1))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
