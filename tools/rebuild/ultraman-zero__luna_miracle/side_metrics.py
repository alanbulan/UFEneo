"""侧视门度量：朝向、眼列、冠鳍尖/根 x、两脚底差、Alpha 档数（只读）。"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def metrics(path: Path) -> dict:
    image = Image.open(path).convert("RGBA")
    array = np.array(image)
    alpha = array[:, :, 3]
    visible = alpha > 0
    ys, xs = np.nonzero(visible)
    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    height = bottom - top + 1
    width = right - left + 1

    r = array[:, :, 0].astype(int)
    g = array[:, :, 1].astype(int)
    b = array[:, :, 2].astype(int)
    head_rows = np.zeros_like(visible)
    head_rows[top:top + max(1, int(height * 0.22))] = True
    eye = visible & head_rows & (r > 170) & (g > 130) & (b < 130) & ((r - b) > 60)
    if eye.any():
        ey, ex = np.nonzero(eye)
        eye_box = [int(ex.min()), int(ey.min()), int(ex.max()), int(ey.max())]
        eye_cx = float(ex.mean())
        eye_cy = float(ey.mean())
        eye_px = int(eye.sum())
    else:
        eye_box, eye_cx, eye_cy, eye_px = None, None, None, 0

    head = visible & head_rows
    hy, hx = np.nonzero(head)
    head_box = [int(hx.min()), int(hy.min()), int(hx.max()), int(hy.max())]
    head_cx = float(hx.mean())
    facing = "right" if eye_cx is not None and eye_cx > head_cx else "left"

    # 头部蓝冠鳍：头顶 22% 内、眼行以上的蓝色像素。
    crest_zone = visible & head_rows
    if eye_cy is not None:
        crest_zone &= np.arange(array.shape[0])[:, None] < eye_cy
    blue = crest_zone & (b > 80) & ((b - r) > 35) & ((b - g) > 10)
    crest = {}
    if blue.any():
        by, bx = np.nonzero(blue)
        tip_y = int(by.min())
        tip_rows = by <= tip_y + 2
        tip_x = float(bx[tip_rows].mean())
        root_y = int(by.max())
        root_rows = by >= root_y - 2
        root_x = float(bx[root_rows].mean())
        crest = {
            "pixels": int(blue.sum()),
            "bbox": [int(bx.min()), int(by.min()), int(bx.max()), int(by.max())],
            "tip_y": tip_y,
            "tip_x": round(tip_x, 1),
            "root_y": root_y,
            "root_x": round(root_x, 1),
            "tip_minus_eye_x": round(tip_x - eye_cx, 1) if eye_cx is not None else None,
            "root_minus_eye_x": round(root_x - eye_cx, 1) if eye_cx is not None else None,
            "tip_minus_head_center_x": round(tip_x - head_cx, 1),
        }

    band_top = bottom - int(height * 0.06)
    band = alpha[band_top:bottom + 1] > 0
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
        sub = alpha[:, x0:x1 + 1] > 0
        foot_ys = np.nonzero(sub.any(axis=1))[0]
        feet.append({"x": [int(x0), int(x1)], "bottom": int(foot_ys.max())})
    foot_span = feet[-1]["x"][1] - feet[0]["x"][0] if len(feet) >= 2 else 0
    ground_delta = max(f["bottom"] for f in feet) - min(f["bottom"] for f in feet) if feet else None

    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": [image.width, image.height],
        "alpha_levels": len(np.unique(alpha)),
        "bbox": [left, top, right, bottom],
        "height": height,
        "width": width,
        "margins": {"left": left, "top": top, "right": image.width - 1 - right,
                    "bottom": image.height - 1 - bottom},
        "facing": facing,
        "eye": {"bbox": eye_box, "center_x": round(eye_cx, 1) if eye_cx is not None else None,
                "center_y": round(eye_cy, 1) if eye_cy is not None else None,
                "pixels": eye_px},
        "head_box": head_box,
        "head_center_x": round(head_cx, 1),
        "crest": crest,
        "feet": feet,
        "foot_outer_span": foot_span,
        "foot_span_over_height": round(foot_span / height, 4) if height else 0,
        "foot_bottom_delta": ground_delta,
    }


def main() -> int:
    rows = [metrics(Path(arg) if Path(arg).is_absolute() else ROOT / arg) for arg in sys.argv[1:]]
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
