"""把已过照片门的像素整帧落到 256 制作格：188 站高、root [128,248]、脚底 247。

色板不套旧图鉴（旧图鉴缺黄眼/青绿额灯），按待机整帧重新定 32 色，
并把眼黄、额灯青绿、胸计时器亮蓝三色钉入色板；全套动作共用该色板。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/media/art"))
sys.path.insert(0, str(ROOT / "tools/art"))
import catalogue_native as cn  # noqa: E402
from stage_cells import foot_center, head_height  # noqa: E402

TARGET_HEIGHT = 188
PALETTE_SIZE = 32
CELL = 256
ANCHOR_X = 128
BASELINE = 248
FOOT_ROW = BASELINE - 1
PINNED = [
    ("eye_yellow", (241, 226, 2)),
    ("lamp_green", (1, 241, 177)),
    ("timer_blue", (0, 143, 253)),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def masked_colors(image: Image.Image) -> Counter:
    array = np.array(image.convert("RGBA"))
    visible = array[:, :, 3] > 0
    return Counter(tuple(int(v) for v in rgb)
                   for rgb in array[:, :, :3][visible].reshape(-1, 3))


def components(mask: np.ndarray) -> int:
    from collections import deque
    seen = np.zeros_like(mask, bool)
    count = 0
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if not mask[y, x] or seen[y, x]:
                continue
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


def foot_metrics(mask: np.ndarray) -> dict:
    ys = np.nonzero(mask.any(axis=1))[0]
    bottom = int(ys.max())
    height = int(ys.max() - ys.min() + 1)
    band_top = bottom - int(height * 0.06)
    band = mask[band_top:bottom + 1]
    columns = np.nonzero(band.any(axis=0))[0]
    groups = []
    for x in columns.tolist():
        if groups and x - groups[-1][-1] <= 3:
            groups[-1].append(x)
        else:
            groups.append([x])
    feet = []
    for group in groups:
        x0, x1 = group[0], group[-1]
        sub = mask[:, x0:x1 + 1]
        feet.append({"x": [int(x0), int(x1)], "bottom": int(np.nonzero(sub.any(axis=1))[0].max())})
    span = feet[-1]["x"][1] - feet[0]["x"][0] if len(feet) >= 2 else 0
    return {
        "feet": feet,
        "foot_outer_span": span,
        "foot_span_over_height": round(span / height, 4) if height else 0,
        "foot_bottom_delta": max(f["bottom"] for f in feet) - min(f["bottom"] for f in feet)
        if feet else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--name", default="identity-idle-candidate-01")
    parser.add_argument("--out-dir", default="art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames")
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    sprite = cn.downsample(cn.trim(cn.load_raw(source)), TARGET_HEIGHT)
    base_palette = cn.build_head_weighted_palette(sprite, PALETTE_SIZE)
    array = np.array(sprite)
    visible = array[:, :, 3] >= 128
    pixels = array[:, :, :3][visible].astype(np.int32)
    palette_array = np.array(base_palette, dtype=np.int32)
    distances = ((pixels[:, None, :] - palette_array[None, :, :]) ** 2).sum(axis=2)
    usage = np.bincount(distances.argmin(axis=1), minlength=len(base_palette))
    order = np.argsort(usage)
    palette = list(base_palette)
    pinned_record = []
    for index, (name, color) in zip(order[:len(PINNED)], PINNED):
        index = int(index)
        pinned_record.append({
            "name": name,
            "rgb": list(color),
            "replaced_rgb": list(base_palette[index]),
            "replaced_usage": int(usage[index]),
        })
        palette[index] = color

    quantized = cn.apply_palette(sprite.copy(), palette)
    quantized = cn.harden_alpha(quantized)
    mask = np.array(quantized)[:, :, 3] > 0
    center = foot_center(mask, 0.08)
    canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    left = round(ANCHOR_X - center)
    top = FOOT_ROW + 1 - quantized.height
    canvas.alpha_composite(quantized, (left, top))
    native_path = out_dir / f"{args.name}.png"
    canvas.save(native_path)
    preview_path = out_dir / f"{args.name}-x4.png"
    canvas.resize((CELL * 4, CELL * 4), Image.Resampling.NEAREST).save(preview_path)

    out_array = np.array(canvas)
    out_mask = out_array[:, :, 3] > 0
    ys, xs = np.nonzero(out_mask)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    height = int(ys.max() - ys.min() + 1)
    feet = foot_metrics(out_mask)
    colors = masked_colors(canvas)
    head = head_height(out_mask)
    palette_set = {tuple(c) for c in palette}
    pinned_present = {name: list(color) in [list(c) for c in palette]
                      for name, color in PINNED}
    recognition = {}
    for name, color in PINNED:
        count = sum(v for c, v in colors.items() if c == color)
        recognition[name] = {"rgb": list(color), "pixels_in_cell": int(count)}
    report = {
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source),
        "native": native_path.relative_to(ROOT).as_posix(),
        "native_sha256": sha256(native_path),
        "preview_x4": preview_path.relative_to(ROOT).as_posix(),
        "preview_x4_sha256": sha256(preview_path),
        "cell": [CELL, CELL],
        "anchor": [ANCHOR_X, BASELINE],
        "foot_row": FOOT_ROW,
        "placement": {"left": left, "top": top},
        "sprite_size": list(quantized.size),
        "foot_band_center": round(center, 2),
        "bbox": bbox,
        "height": height,
        "width": int(xs.max() - xs.min() + 1),
        "head_height_heuristic": head,
        "head_ratio_heuristic": round(head / height, 4) if height else 0,
        **feet,
        "alpha_values": sorted({int(v) for v in np.unique(out_array[:, :, 3])}),
        "components": components(out_mask),
        "visible_colors": len(colors),
        "palette_size": len(palette),
        "palette": [list(c) for c in palette],
        "pinned": pinned_record,
        "pinned_present": pinned_present,
        "recognition_pixels": recognition,
        "palette_used": [{"rgb": list(c), "pixels": int(v)} for c, v in colors.most_common()],
    }
    report_path = Path(args.report) if args.report else out_dir / f"{args.name}-report.json"
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
