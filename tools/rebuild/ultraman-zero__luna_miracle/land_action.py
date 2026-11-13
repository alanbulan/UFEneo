"""月神奇迹动作帧落格：同一待机锚比例、同一色板、256 格、根点 [128,248]。

用法：
    .venv/bin/python tools/rebuild/ultraman-zero__luna_miracle/land_action.py \
        --manifest tools/rebuild/ultraman-zero__luna_miracle/frames.json

清单条目：
    {"clip": "walk_forward", "index": 0, "source": "art/.../raw.png",
     "foot_row": 247, "standing": true}
输出：art/fighters/ultraman-zero__luna_miracle/stage1/cells/<clip>-<NN>-cell.png，
逐帧记录写回 cells.json 的 frames 列表。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
FIGHTER = "ultraman-zero__luna_miracle"
CELLS = ROOT / "art/fighters" / FIGHTER / "stage1/cells/cells.json"
CELL_DIR = ROOT / "art/fighters" / FIGHTER / "stage1/cells"
CELL = 256
ANCHOR_X = 128
BASELINE = 248
FOOT_ROW = 247
TARGET_STANDING = 188


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def largest_component(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    seen = np.zeros_like(mask, bool)
    best = np.zeros_like(mask, bool)
    best_size = 0
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            queue = deque([(y, x)])
            seen[y, x] = True
            cells = [(y, x)]
            while queue:
                cy, cx = queue.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < height and 0 <= nx < width \
                            and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
                        cells.append((ny, nx))
            if len(cells) > best_size:
                best_size = len(cells)
                best = np.zeros_like(mask, bool)
                for cy, cx in cells:
                    best[cy, cx] = True
    return best


def count_components(mask: np.ndarray) -> int:
    height, width = mask.shape
    seen = np.zeros_like(mask, bool)
    count = 0
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            count += 1
            queue = deque([(y, x)])
            seen[y, x] = True
            while queue:
                cy, cx = queue.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < height and 0 <= nx < width \
                            and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
    return count


def palette_map(array: np.ndarray, palette: np.ndarray) -> np.ndarray:
    visible = array[:, :, 3] >= 128
    pixels = array[:, :, :3].astype(np.int32)
    unique, inverse = np.unique(pixels.reshape(-1, 3), axis=0, return_inverse=True)
    nearest = np.empty(len(unique), dtype=np.intp)
    for start in range(0, len(unique), 8192):
        delta = unique[start:start + 8192, None].astype(np.int32) - palette
        nearest[start:start + 8192] = np.einsum("nki,nki->nk", delta, delta).argmin(axis=1)
    result = array.copy()
    result[:, :, :3] = palette[nearest[inverse]].reshape(array.shape[:2] + (3,))
    result[:, :, 3] = np.where(visible, 255, 0)
    result[~visible] = 0
    return result


def head_height(mask: np.ndarray) -> int:
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


def land(entry: dict, palette: np.ndarray, scale: float) -> dict:
    source = ROOT / entry["source"]
    image = Image.open(source).convert("RGBA")
    array = np.array(image)
    array[:, :, 3] = np.where(array[:, :, 3] >= 128, 255, 0).astype(np.uint8)
    visible = array[:, :, 3] > 0
    ys, xs = np.nonzero(visible)
    array = array[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
    trimmed = Image.fromarray(array, "RGBA")
    target_w = max(1, round(trimmed.width * scale))
    target_h = max(1, round(trimmed.height * scale))
    scaled = trimmed.resize((target_w, target_h), Image.BOX)
    scaled_array = np.array(scaled)
    scaled_array[:, :, 3] = np.where(scaled_array[:, :, 3] >= 128, 255, 0).astype(np.uint8)
    mapped = palette_map(scaled_array, palette)

    mask = mapped[:, :, 3] > 0
    keep = largest_component(mask)
    removed = int((mask & ~keep).sum())
    mapped[~keep] = 0
    mask = mapped[:, :, 3] > 0
    ys, xs = np.nonzero(mask)
    height = int(ys.max() - ys.min() + 1)
    width = int(xs.max() - xs.min() + 1)

    band_top = int(ys.max() - max(2, round(height * 0.08)))
    band = mask[band_top:int(ys.max()) + 1]
    columns = np.nonzero(band.any(axis=0))[0]
    center = float(columns.mean()) if len(columns) else (xs.min() + xs.max()) / 2.0
    left = int(round(ANCHOR_X - center))
    left = max(4, min(left, CELL - 5 - width))
    foot_row = int(entry.get("foot_row", FOOT_ROW))
    top = foot_row - (int(ys.max()) - int(ys.min()))
    canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    canvas.alpha_composite(Image.fromarray(mapped, "RGBA"), (left, top))

    out_array = np.array(canvas)
    out_mask = out_array[:, :, 3] > 0
    oy, ox = np.nonzero(out_mask)
    bbox = [int(ox.min()), int(oy.min()), int(ox.max()), int(oy.max())]
    out_height = int(oy.max() - oy.min() + 1)
    colors = len(np.unique(out_array[:, :, :3][out_mask].reshape(-1, 3), axis=0))
    components = count_components(out_mask)
    out_dir = CELL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{entry['clip']}-{int(entry['index']):02d}"
    out_path = out_dir / f"{name}-cell.png"
    canvas.save(out_path)
    preview = out_dir / f"{name}-x4.png"
    canvas.resize((CELL * 4, CELL * 4), Image.Resampling.NEAREST).save(preview)

    record = {
        "frame": name,
        "clip": entry["clip"],
        "index": int(entry["index"]),
        "source": rel(source),
        "source_sha256": sha256(source),
        "output": rel(out_path),
        "output_sha256": sha256(out_path),
        "preview_x4": rel(preview),
        "scale": round(scale, 8),
        "bbox": bbox,
        "height": out_height,
        "width": int(ox.max() - ox.min() + 1),
        "head_height": head_height(out_mask),
        "colors": colors,
        "components": components,
        "removed_pixels": removed,
        "foot_row": foot_row,
        "standing": bool(entry.get("standing", True)),
        "alpha": sorted({int(v) for v in np.unique(out_array[:, :, 3])}),
    }
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--scale", type=float, default=0.0)
    args = parser.parse_args()
    cells = json.loads(CELLS.read_text(encoding="utf-8"))
    palette = np.asarray(cells["palette"], dtype=np.int32)
    anchor = cells["identity_anchor"]
    scale = args.scale
    if not scale:
        # 锚源像素整帧裁到 Alpha bbox 后高 1059 → 落格 188；全套乘同一比例。
        # 不能用画布高度 1254，否则每帧会被缩到 81 px 左右。
        reference = Image.open(
            ROOT / anchor["production_reference"]["path"]).convert("RGBA")
        reference_alpha = np.array(reference)[:, :, 3] > 0
        rows = np.nonzero(reference_alpha.any(axis=1))[0]
        source_height = int(rows.max() - rows.min() + 1)
        scale = TARGET_STANDING / source_height
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    entries = manifest["frames"]
    if not args.scale:
        # 同一条带/同一批次的源分辨率一致：按该批中位站高定一个批次比例，
        # 批内不再逐帧归一；落到 188 后与锚的 130×188 同体量。
        heights = []
        for entry in entries:
            source = ROOT / entry["source"]
            array = np.array(Image.open(source).convert("RGBA"))
            rows = np.nonzero((array[:, :, 3] >= 128).any(axis=1))[0]
            heights.append(int(rows.max() - rows.min() + 1))
        heights.sort()
        median = heights[len(heights) // 2] if len(heights) % 2 else \
            (heights[len(heights) // 2 - 1] + heights[len(heights) // 2]) / 2
        scale = TARGET_STANDING / median
        manifest["batch_source_heights"] = heights
        manifest["batch_median_height"] = median
        manifest["scale_note"] = (
            f"本批源中位站高 {median}px → 188px，批次内统一比例；"
            "锚源像素整帧为 1059px，两者按各自站高归一到同一原生体量。"
        )
    rows = [land(entry, palette, scale) for entry in entries]
    by_name = {row["frame"]: row for row in cells.get("frames", [])}
    for row in rows:
        by_name[row["frame"]] = row
    cells["frames"] = list(by_name.values())
    cells["scale"] = round(scale, 8)
    cells["scale_source"] = anchor["production_reference"]["path"]
    cells["scale_note"] = "全套按待机像素整帧源高 1059 → 站高 188 的同一比例落格，不逐帧归一。"
    CELLS.write_text(json.dumps(cells, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    flags = []
    for row in rows:
        if row["components"] != 1:
            flags.append(f"{row['frame']}: 连通块 {row['components']}")
        if row["alpha"] != [0, 255]:
            flags.append(f"{row['frame']}: Alpha {row['alpha']}")
        if row["colors"] > 32:
            flags.append(f"{row['frame']}: 色数 {row['colors']}")
        if row["standing"] and abs(row["height"] - TARGET_STANDING) / TARGET_STANDING > 0.08:
            flags.append(f"{row['frame']}: 站高 {row['height']} 偏离 188 超过 8%")
    print(json.dumps({"scale": round(scale, 8), "frames": rows, "flags": flags},
                     ensure_ascii=False, indent=1))
    return 0 if not flags else 1


if __name__ == "__main__":
    raise SystemExit(main())
