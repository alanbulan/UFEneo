"""量眼行脸宽与头部蓝色灯位：用于身份比例核对（只报数值）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def analyze(path: Path) -> dict:
    image = Image.open(path).convert("RGBA")
    array = np.array(image)
    alpha = array[:, :, 3]
    rgb = array[:, :, :3].astype(int)
    visible = alpha >= 128
    ys, xs = np.where(visible)
    if not len(ys):
        return {"path": str(path), "error": "empty"}
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    blue = (rgb[:, :, 2] > 150) & (rgb[:, :, 2] - rgb[:, :, 0] > 60) \
        & (rgb[:, :, 2] - rgb[:, :, 1] > 20) & visible
    bys, bxs = np.where(blue)
    clusters = []
    if len(bys):
        # 按行分组蓝色像素质心
        rows = {}
        for y, x in zip(bys.tolist(), bxs.tolist()):
            rows.setdefault(y, []).append(x)
        row_list = sorted(rows.items())
        groups = []
        current = []
        for y, xs_row in row_list:
            if current and y - current[-1][0] > 3:
                groups.append(current)
                current = []
            current.append((y, xs_row))
        if current:
            groups.append(current)
        for group in groups:
            gy = [y for y, _ in group]
            gx = [x for _, row in group for x in row]
            y0, y1 = min(gy), max(gy)
            # 脸宽取该组蓝色所在行的头列带轮廓宽
            mid = (y0 + y1) // 2
            row_mask = visible[mid]
            runs = []
            start = None
            for x in range(row_mask.shape[0]):
                if row_mask[x] and start is None:
                    start = x
                elif not row_mask[x] and start is not None:
                    runs.append((start, x - 1))
                    start = None
            if start is not None:
                runs.append((start, row_mask.shape[0] - 1))
            clusters.append({
                "y": [y0, y1], "x": [min(gx), max(gx)],
                "row_mid": mid, "row_runs": runs,
                "row_width_all": sum(b - a + 1 for a, b in runs),
            })
    return {
        "path": str(path),
        "size": list(image.size),
        "bbox": [int(xs.min()), top, int(xs.max()), bottom],
        "standing": height,
        "blue_clusters": clusters,
    }


if __name__ == "__main__":
    for text in sys.argv[1:]:
        print(json.dumps(analyze(Path(text)), ensure_ascii=False))
