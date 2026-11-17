"""把奥特之父待机像素整帧落到 stage1 制作格。

图鉴定稿 32 色板没有任何蓝色，直接套用会丢掉蓝胸灯识别色。按 AGENTS
「落格色板须保住本人额灯、计时器等识别色」，本脚本从**本张待机像素源**
重新定 32 色：金眼两档 + 蓝胸灯两档固定保留，其余 28 色用 MEDIANCUT
从全图可见像素学习；整图统一 RGB 最近色映射，不按身体区域局部重涂。

落格几何仍用 `tools/art/stage_cells.py` 的 build()：统一比例、二值 Alpha、
脚底段重心对 x=96、脚底贴 baseline-1；默认行为不改。本脚本只提供色板并
在落格后做确定性复核（站距、连通块、色数、金/蓝识别色、4× 精确重复、
导引色长直线残留）。

用法：
    .venv/bin/python tools/rebuild/father-of-ultra/land_idle_cell.py \
        --source art/fighters/father-of-ultra/stage1/idle/frames/pixel-raw-02.png \
        --out art/fighters/father-of-ultra/stage1/cells/idle-candidate-01-cell.png \
        --x4-out art/fighters/father-of-ultra/stage1/cells/x4/idle-candidate-01-x4.png
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path[:0] = [
    str(ROOT / "tools"),
    *[str(p) for p in (ROOT / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (ROOT / "tools/rebuild").iterdir() if p.is_dir()],
]

import stage_cells  # noqa: E402

GOLD = lambda r, g, b: (r > 140) & (g > 100) & (b < 100) & (r - b > 60)  # noqa: E731
BLUE = lambda r, g, b: (b > r + 25) & (b > g + 10) & (b > 70)  # noqa: E731
GUIDE_COLORS = {
    "magenta": lambda r, g, b: (r > 200) & (b > 200) & (g < 120),
    "cyan": lambda r, g, b: (g > 180) & (b > 180) & (r < 120),
    "green": lambda r, g, b: (g > 180) & (r < 120) & (b < 120),
    "orange": lambda r, g, b: (r > 200) & (g > 100) & (g < 200) & (b < 100),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pick_reserved(colors: np.ndarray, mask: np.ndarray, count: int = 2) -> list:
    """在识别色掩码内按亮度分暗/亮两组，各取最饱和的一色。

    最饱和色是该识别结构在高光/阴影里的真实源色；按出现次数取会落到
    大面积蓝色阴影的灰蓝上，蓝胸灯会被洗淡。
    """
    values, counts = np.unique(colors[mask], axis=0, return_counts=True)
    if len(values) == 0:
        return []
    values_int = values.astype(int)
    luminance = values_int.sum(axis=1)
    saturation = values_int.max(axis=1) - values_int.min(axis=1)
    order = np.argsort(luminance)
    half = max(1, len(order) // 2)
    picks = []
    for group in (order[:half], order[half:]):
        if len(group):
            picks.append(tuple(int(v) for v in values[group[np.argmax(saturation[group])]]))
    while picks and len(picks) < count:
        picks.append(picks[0])
    return picks[:count]


def build_palette(solid: Image.Image, scaled: Image.Image) -> tuple[list, dict]:
    full = np.array(solid)
    full_visible = full[:, :, 3] > 0
    full_colors = full[:, :, :3][full_visible].reshape(-1, 3)
    fr, fg, fb = (full_colors[:, i].astype(int) for i in range(3))
    gold = pick_reserved(full_colors, GOLD(fr, fg, fb), 2)
    blue = pick_reserved(full_colors, BLUE(fr, fg, fb), 2)

    array = np.array(scaled)
    visible = array[:, :, 3] > 0
    colors = array[:, :, :3][visible].reshape(-1, 3)
    r, g, b = (colors[:, i].astype(int) for i in range(3))
    sample = Image.fromarray(colors.reshape(1, -1, 3), "RGB")
    quantized = sample.quantize(colors=28, method=Image.MEDIANCUT,
                                dither=Image.Dither.NONE)
    raw = quantized.getpalette() or []
    median = [tuple(int(c) for c in raw[i * 3:i * 3 + 3])
              for i in range(min(28, len(raw) // 3))]
    palette: list = []
    for color in [*gold, *blue, *median]:
        if color not in palette:
            palette.append(color)
    values, counts = np.unique(colors, axis=0, return_counts=True)
    for index in np.argsort(-counts):
        if len(palette) >= 32:
            break
        color = tuple(int(v) for v in values[index])
        if color not in palette:
            palette.append(color)
    info = {
        "gold_reserved": gold,
        "blue_reserved": blue,
        "mediancut": median,
        "reserved_unique": len(dict.fromkeys([*gold, *blue])),
        "unique_before_fill": len(dict.fromkeys([*gold, *blue, *median])),
        "gold_pixels_scaled": int(GOLD(r, g, b).sum()),
        "blue_pixels_scaled": int(BLUE(r, g, b).sum()),
    }
    return palette[:32], info


def runs_of(row: np.ndarray) -> list:
    xs = np.where(row)[0]
    if not xs.size:
        return []
    out = []
    start = previous = int(xs[0])
    for x in xs[1:]:
        x = int(x)
        if x - previous > 1:
            out.append((start, previous))
            start = x
        previous = x
    out.append((start, previous))
    return out


def feet_measure(mask: np.ndarray) -> dict:
    ys = np.where(mask.any(axis=1))[0]
    bottom = int(ys.max())
    best = None
    for y in range(max(0, bottom - 12), bottom + 1):
        runs = runs_of(mask[y])
        if len(runs) < 2:
            continue
        span = runs[-1][1] - runs[0][0] + 1
        if best is None or span > best["span_px"]:
            best = {
                "stance_row": y,
                "outer_left_x": runs[0][0],
                "outer_right_x": runs[-1][1],
                "span_px": span,
                "runs": runs,
            }
    if best is None:
        return {"method": "格内底部 13 行逐行拆左右两段", "found": False}
    mid = (best["outer_left_x"] + best["outer_right_x"]) // 2
    rear = np.where(mask[:, :mid].any(axis=1))[0]
    front = np.where(mask[:, mid:].any(axis=1))[0]
    best["method"] = "格内底部 13 行逐行拆左右两段，取最大外缘跨；鞋底行按左右半幅最低行"
    best["rear_sole_row"] = int(rear.max())
    best["front_sole_row"] = int(front.max())
    best["sole_diff_px"] = abs(best["rear_sole_row"] - best["front_sole_row"])
    return best


def max_straight_run(mask: np.ndarray) -> int:
    best = 0
    for line in list(mask) + list(mask.T):
        run = 0
        for value in line:
            run = run + 1 if value else 0
            best = max(best, run)
    return int(best)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--x4-out", required=True)
    parser.add_argument("--target-standing", type=int, default=173)
    parser.add_argument("--cell", type=int, default=192)
    parser.add_argument("--anchor-x", type=int, default=96)
    parser.add_argument("--baseline", type=int, default=184)
    parser.add_argument("--beard-y", type=int, default=None,
                        help="格内人工确认的白须底行，用于同口径头高报告")
    args = parser.parse_args(argv)

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    solid = stage_cells.solid_source(source)
    scale = args.target_standing / solid.height
    width = max(1, round(solid.width * scale))
    scaled = stage_cells.harden_alpha(solid.resize((width, args.target_standing), Image.BOX))
    palette, palette_info = build_palette(solid, scaled)

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    frame = stage_cells.build(source, out, palette, scale, args.baseline - 1,
                              anchor_x=args.anchor_x, cell=args.cell, foot_band=0.08)

    cell = Image.open(out).convert("RGBA")
    cell_array = np.array(cell)
    mask = cell_array[:, :, 3] > 0
    x4 = cell.resize((args.cell * 4, args.cell * 4), Image.NEAREST)
    x4_out = Path(args.x4_out)
    if not x4_out.is_absolute():
        x4_out = ROOT / x4_out
    x4_out.parent.mkdir(parents=True, exist_ok=True)
    x4.save(x4_out)
    x4_array = np.array(x4)
    base_colors = {tuple(int(v) for v in c) for c in cell_array[:, :, :3][mask].reshape(-1, 3)}
    x4_colors = {tuple(int(v) for v in c) for c in x4_array[:, :, :3][x4_array[:, :, 3] > 0].reshape(-1, 3)}

    feet = feet_measure(mask)
    r, g, b = (cell_array[:, :, i].astype(int) for i in range(3))
    gold_mask = GOLD(r, g, b) & mask
    blue_mask = BLUE(r, g, b) & mask
    guide = {}
    for name, test in GUIDE_COLORS.items():
        color_mask = test(r, g, b) & mask
        guide[name] = {
            "pixels": int(color_mask.sum()),
            "max_straight_run": max_straight_run(color_mask),
        }

    ys = np.where(mask.any(axis=1))[0]
    xs = np.where(mask.any(axis=0))[0]
    top, bottom = int(ys.min()), int(ys.max())
    head = None
    if args.beard_y is not None:
        head = {
            "horn_tip_y": top,
            "beard_bottom_y": args.beard_y,
            "head_height_px": args.beard_y - top + 1,
            "head_height_ratio": round((args.beard_y - top + 1) / (bottom - top + 1), 4),
        }

    report = {
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source),
        "source_size": list(Image.open(source).size),
        "source_trimmed": list(solid.size),
        "source_scale": round(scale, 9),
        "target_standing": args.target_standing,
        "uniform_size": [width, args.target_standing],
        "palette": palette,
        "palette_info": palette_info,
        "frame": frame,
        "x4": {
            "path": x4_out.relative_to(ROOT).as_posix(),
            "sha256": sha256(x4_out),
            "size": list(x4.size),
            "exact_pixel_repeat_verified": bool(np.array_equal(
                x4_array[::4, ::4], cell_array)),
            "base_colors": len(base_colors),
            "x4_colors": len(x4_colors),
            "added_colors": len(x4_colors - base_colors),
        },
        "cell_bbox_inclusive": [int(xs.min()), top, int(xs.max()), bottom],
        "cell_standing": bottom - top + 1,
        "cell_width": int(xs.max() - xs.min() + 1),
        "cell_alpha": sorted({int(v) for v in np.unique(cell_array[:, :, 3])}),
        "cell_components": stage_cells.components(mask),
        "feet": feet,
        "recognition_colors": {
            "gold_pixels": int(gold_mask.sum()),
            "blue_pixels": int(blue_mask.sum()),
        },
        "guide_residue": guide,
        "head_ruler": head,
    }
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
