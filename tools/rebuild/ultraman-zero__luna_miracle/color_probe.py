"""列出图内指定纵向比例的饱和色，帮助锁定额灯/眼/计时器的真实颜色。"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = ROOT / path
    top_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.20
    bottom_ratio = float(sys.argv[3]) if len(sys.argv) > 3 else 0.60
    image = Image.open(path).convert("RGBA")
    array = np.array(image)
    visible = array[:, :, 3] > 0
    ys = np.nonzero(visible.any(axis=1))[0]
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    band = np.zeros_like(visible)
    band[top + int(height * top_ratio):top + int(height * bottom_ratio)] = True
    pixels = array[:, :, :3][visible & band].reshape(-1, 3)
    counts = Counter(tuple(int(v) for v in c) for c in pixels)
    rows = []
    for color, count in counts.items():
        r, g, b = color
        score = max(g, b) - r + b // 4 + g // 4
        rows.append((score, count, color))
    rows.sort(reverse=True)
    print("top saturated colors")
    for score, count, color in rows[:40]:
        print(score, count, color)
    print("count", len(counts))

    yellow = [(count, color) for color, count in counts.items()
              if color[0] > 160 and color[1] > 120 and color[2] < 140
              and color[0] - color[2] > 50]
    yellow.sort(reverse=True)
    print("yellow")
    for count, color in yellow[:15]:
        print(count, color)
    green = [(count, color) for color, count in counts.items()
             if color[1] > 100 and color[1] - color[0] > 20 and color[1] - color[2] > 5]
    green.sort(reverse=True)
    print("green")
    for count, color in green[:15]:
        print(count, color)
    cyan = [(count, color) for color, count in counts.items()
            if color[2] > 140 and color[1] > 95 and color[2] - color[0] > 50]
    cyan.sort(reverse=True)
    print("cyan")
    for count, color in cyan[:15]:
        print(count, color)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
