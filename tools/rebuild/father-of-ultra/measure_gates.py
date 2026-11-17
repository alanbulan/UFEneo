"""奥特之父 stage1 照片/像素候选的确定性测量（不判定造型，不编造结论）。

只做 AGENTS.md「美术与资源」里可机器读的项：
- 站高（Alpha≥128 bbox 顶→最低鞋底）、含双角头高（角尖→白须底，白须底由
  人工在放大裁图上确认后通过 --beard-y 传入）、站距（脚外缘，--stance-row 指定行）、
  双鞋底行（--sole-rows 传入人工读数，或按底部行宽自动候选）、
- 真 Alpha：四角、Alpha 档位，
- 辉光门：主体＝Alpha≥200 最大连通块，外扩 3px 后统计主体外 alpha≥16 / ≥200，
- 导引辅助线残留：洋红/青/绿/橙像素数。

用法：
    .venv/bin/python tools/rebuild/father-of-ultra/measure_gates.py <图片> \
        [--beard-y N] [--stance-row N] [--sole-rows A,B] [--target-standing 173]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path[:0] = [
    str(ROOT / "tools"),
    *[str(p) for p in (ROOT / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (ROOT / "tools/rebuild").iterdir() if p.is_dir()],
]

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

ALPHA_SOLID = 128
ALPHA_BODY = 200
ALPHA_DUST = 16
DILATE = 3
GUIDE_COLORS = {
    "magenta": lambda r, g, b: (r > 200) & (b > 200) & (g < 120),
    "cyan": lambda r, g, b: (g > 180) & (b > 180) & (r < 120),
    "green": lambda r, g, b: (g > 180) & (r < 120) & (b < 120),
    "orange": lambda r, g, b: (r > 200) & (g > 100) & (g < 200) & (b < 100),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(mask: np.ndarray) -> list[np.ndarray]:
    seen = np.zeros_like(mask, bool)
    found = []
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if not mask[y, x] or seen[y, x]:
                continue
            queue = deque([(y, x)])
            seen[y, x] = True
            pixels = []
            while queue:
                cy, cx = queue.popleft()
                pixels.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                            and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            found.append(np.array(pixels))
    found.sort(key=len, reverse=True)
    return found


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(radius):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--beard-y", type=int, default=None,
                        help="人工在放大裁图确认的白须最低点行")
    parser.add_argument("--stance-row", type=int, default=None,
                        help="量脚外缘的行；缺省用最低可见行")
    parser.add_argument("--sole-rows", default="",
                        help="人工读出的前后鞋底行，形如 1412,1409")
    parser.add_argument("--target-standing", type=int, default=173)
    parser.add_argument("--crops", default="", help="额外输出放大裁图的目录")
    parser.add_argument("--diagnostic", default="", help="诊断标注图输出路径")
    args = parser.parse_args(argv)

    path = Path(args.image)
    if not path.is_absolute():
        path = ROOT / path
    image = Image.open(path).convert("RGBA")
    array = np.array(image)
    alpha = array[:, :, 3]
    visible = alpha >= ALPHA_SOLID
    ys, xs = np.where(visible)
    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    standing = bottom - top + 1

    row_widths = {y: int(visible[y].sum()) for y in range(top, bottom + 1)}
    # 靴子按红色分量取，逐脚取各自鞋底行与外缘；披风同为红色但不落到鞋底行。
    rgb_int = array[:, :, :3].astype(int)
    red = (rgb_int[:, :, 0] > 70) & (rgb_int[:, :, 0] > rgb_int[:, :, 1] + 25) \
        & (rgb_int[:, :, 0] > rgb_int[:, :, 2] + 20) & visible
    boots = []
    for comp in components(red):
        if len(comp) < 500:
            continue
        ys_c, xs_c = comp[:, 0], comp[:, 1]
        if ys_c.mean() < top + standing * 0.55:
            continue
        boots.append({
            "bbox": [int(xs_c.min()), int(ys_c.min()), int(xs_c.max()), int(ys_c.max())],
            "px": int(len(comp)),
            "centroid": [round(float(xs_c.mean()), 1), round(float(ys_c.mean()), 1)],
        })
    boots.sort(key=lambda b: b["centroid"][1], reverse=True)
    boots = boots[:2]
    # 底部 40 行按行拆左右两段：披风在身后、不落到鞋底行，鞋底段最可靠。
    # 红色连通块常把披风与后靴连成一块，只作辅助记录，不作站距依据。
    bottom_runs = {}
    for y in range(max(top, bottom - 39), bottom + 1):
        cols = np.where(visible[y])[0]
        if not cols.size:
            continue
        runs = []
        start = prev = int(cols[0])
        for x in cols[1:]:
            x = int(x)
            if x - prev > 6:
                if prev - start + 1 >= 10:
                    runs.append((start, prev))
                start = x
            prev = x
        if prev - start + 1 >= 10:
            runs.append((start, prev))
        if runs:
            bottom_runs[y] = runs
    rear_sole = front_sole = None
    rear_left = front_right = None
    rows_with_two = 0
    for y in sorted(bottom_runs, reverse=True):
        runs = bottom_runs[y]
        if len(runs) < 2:
            continue
        rows_with_two += 1
        rear_left = runs[0][0] if rear_left is None else min(rear_left, runs[0][0])
        front_right = runs[-1][1] if front_right is None else max(front_right, runs[-1][1])
        rear_sole = y if rear_sole is None else max(rear_sole, y)
        front_sole = y if front_sole is None else max(front_sole, y)
    feet = None
    if rear_left is not None and front_right is not None:
        span = front_right - rear_left + 1
        mid = (rear_left + front_right) // 2
        rear_band = np.where(visible[:, :mid].any(axis=1))[0]
        front_band = np.where(visible[:, mid:].any(axis=1))[0]
        rear_sole = int(rear_band.max()) if rear_band.size else rear_sole
        front_sole = int(front_band.max()) if front_band.size else front_sole
        feet = {
            "method": "底部 40 行内逐行拆左右靴段，取两段外缘的最大跨；鞋底行按左右半幅最低行",
            "rows_with_two_boots": rows_with_two,
            "outer_left_x": rear_left,
            "outer_right_x": front_right,
            "span_px": span,
            "span_ratio": round(span / standing, 4),
            "sole_rows": [rear_sole, front_sole],
            "sole_diff_px": abs(rear_sole - front_sole),
            "red_components_aux": boots,
            "note": "靴段按 Alpha≥128 逐行拆段；红色连通块受披风牵连，只作辅助",
        }
        feet["span_pass"] = 0.65 <= feet["span_ratio"] <= 0.80
        feet["sole_diff_native_173"] = round(
            feet["sole_diff_px"] * args.target_standing / standing, 3)
        feet["sole_pass"] = feet["sole_diff_native_173"] <= 1
    row_bounds = {}
    for y in range(top, bottom + 1):
        cols = np.where(visible[y])[0]
        if cols.size:
            row_bounds[y] = [int(cols.min()), int(cols.max())]

    stance_row = args.stance_row if args.stance_row is not None else bottom
    stance_bounds = row_bounds.get(stance_row)
    stance_span = stance_bounds[1] - stance_bounds[0] + 1 if stance_bounds else 0

    head = None
    if args.beard_y is not None:
        head = {
            "horn_tip_y": top,
            "beard_bottom_y": args.beard_y,
            "head_height_px": args.beard_y - top + 1,
            "head_height_ratio": round((args.beard_y - top + 1) / standing, 4),
            "max_ratio": 0.2382,
            "pass": (args.beard_y - top + 1) / standing <= 0.2382,
        }

    soles = {}
    if args.sole_rows:
        rows = [int(v) for v in args.sole_rows.split(",") if v.strip()]
        if len(rows) == 2:
            diff = abs(rows[0] - rows[1])
            soles = {
                "sole_rows": rows,
                "diff_px": diff,
                "diff_native_173": round(diff * args.target_standing / standing, 3),
                "max_native": 1,
                "pass": diff * args.target_standing / standing <= 1,
            }

    body_mask = alpha >= ALPHA_BODY
    body_components = components(body_mask)
    body = body_components[0] if body_components else np.zeros_like(body_mask)
    body_mask_clean = np.zeros_like(body_mask)
    body_mask_clean[body[..., 0], body[..., 1]] = True
    outside = ~dilate(body_mask_clean, DILATE)
    outside_16 = int(((alpha >= ALPHA_DUST) & outside).sum())
    outside_200 = int(((alpha >= ALPHA_BODY) & outside).sum())
    dust = int(((alpha >= 1) & (alpha < ALPHA_DUST) & outside).sum())
    body_outside = int(((alpha >= ALPHA_DUST) & outside & (alpha < ALPHA_BODY)).sum())

    solid_components = components(visible)

    guide = {}
    rgb = array[:, :, :3].astype(int)
    for name, test in GUIDE_COLORS.items():
        mask = test(rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2])
        guide[name] = int(mask.sum())

    report = {
        "image": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix(),
        "sha256": sha256(path),
        "size": list(image.size),
        "mode": image.mode,
        "alpha_levels": int(len(np.unique(alpha))),
        "alpha_min_max": [int(alpha.min()), int(alpha.max())],
        "alpha_corners": [int(alpha[0, 0]), int(alpha[0, -1]),
                          int(alpha[-1, 0]), int(alpha[-1, -1])],
        "bbox_alpha128": [left, top, right, bottom],
        "standing_height_px": standing,
        "stance_row": stance_row,
        "stance_bounds": stance_bounds,
        "stance_span_px": stance_span,
        "stance_ratio": round(stance_span / standing, 4),
        "stance_range": [0.65, 0.80],
        "stance_pass": 0.65 <= stance_span / standing <= 0.80,
        "feet_from_boots": feet,
        "head": head,
        "soles": soles,
        "halo": {
            "body_px": int(body_mask_clean.sum()),
            "outside_alpha16": outside_16,
            "outside_alpha200": outside_200,
            "outside_alpha16_max": 100,
            "outside_alpha200_max": 0,
            "alpha16_pass": outside_16 <= 100,
            "alpha200_pass": outside_200 == 0,
            "alpha1_15_dust": dust,
            "outside_alpha16_200": body_outside,
            "note": "主体=alpha≥200 最大连通块，外扩3px；1–15 尘点只登记",
        },
        "solid_components_alpha128": {
            "count": len(solid_components),
            "largest_px": int(len(solid_components[0])) if solid_components else 0,
        },
        "guide_residue": guide,
        "row_width_tail": {str(y): row_widths[y] for y in range(max(top, bottom - 30), bottom + 1)},
        "row_bounds_tail": {str(y): row_bounds[y] for y in range(max(top, bottom - 30), bottom + 1) if y in row_bounds},
        "row_width_head": {str(y): row_widths[y] for y in range(top, min(bottom, top + 20) + 1)},
        "row_bounds_head": {str(y): row_bounds[y] for y in range(top, min(bottom, top + 20) + 1) if y in row_bounds},
    }

    if args.crops:
        out = Path(args.crops)
        out.mkdir(parents=True, exist_ok=True)
        stem = path.stem
        box = image.getchannel("A").getbbox()
        subject = image.crop(box)
        scale = max(1, 900 // max(subject.width, 1))
        subject.resize((subject.width * scale, subject.height * scale), Image.NEAREST) \
            .save(out / f"{stem}-subject-x{scale}.png")
        head_box = (max(0, left - 40), max(0, top - 10),
                    min(image.width, right + 40), min(image.height, top + int(standing * 0.28)))
        head_crop = image.crop(head_box)
        head_crop.resize((head_crop.width * 3, head_crop.height * 3), Image.NEAREST) \
            .save(out / f"{stem}-head-x3.png")
        foot_box = (max(0, left - 20), max(0, bottom - int(standing * 0.16)),
                    min(image.width, right + 20), min(image.height, bottom + 6))
        foot_crop = image.crop(foot_box)
        foot_crop.resize((foot_crop.width * 3, foot_crop.height * 3), Image.NEAREST) \
            .save(out / f"{stem}-feet-x3.png")

    if args.diagnostic:
        from PIL import ImageDraw

        diag = image.copy()
        draw = ImageDraw.Draw(diag)
        marks = [
            ("top", top, (0, 255, 0)),
            ("beard", args.beard_y, (255, 160, 0)),
            ("bottom", bottom, (0, 255, 255)),
            ("stance_row", stance_row, (255, 0, 255)),
        ]
        for label, y, color in marks:
            if y is None:
                continue
            draw.line([(0, y), (diag.width, y)], fill=color, width=2)
            draw.text((6, max(0, y - 14)), f"{label} y={y}", fill=color)
        if stance_bounds:
            for x in stance_bounds:
                draw.line([(x, max(0, stance_row - 90)), (x, stance_row + 2)], fill=(255, 0, 255), width=2)
            draw.text((stance_bounds[0], max(0, stance_row - 110)), f"span {stance_span}", fill=(255, 0, 255))
        diag_path = Path(args.diagnostic)
        if not diag_path.is_absolute():
            diag_path = ROOT / diag_path
        diag_path.parent.mkdir(parents=True, exist_ok=True)
        diag.save(diag_path)
        report["diagnostic"] = diag_path.relative_to(ROOT).as_posix() if diag_path.is_relative_to(ROOT) else diag_path.as_posix()

    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
