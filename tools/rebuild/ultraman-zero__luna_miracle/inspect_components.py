"""查看候选帧的 Alpha 连通块：输出最大块与按阈值保留的预览。"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def components(mask: np.ndarray):
    height, width = mask.shape
    seen = np.zeros_like(mask, bool)
    result = []
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
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
                        cells.append((ny, nx))
            result.append(cells)
    return result


def main() -> int:
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = ROOT / path
    out_dir = path.parent / "component-previews"
    out_dir.mkdir(exist_ok=True)
    image = Image.open(path).convert("RGBA")
    array = np.array(image)
    mask = array[:, :, 3] > 0
    comps = components(mask)
    comps.sort(key=len, reverse=True)
    print("components", len(comps), "top", [len(c) for c in comps[:20]])
    for threshold in (0, 100, 1000):
        keep = np.zeros_like(mask, bool)
        for cells in comps:
            if len(cells) > threshold:
                ys, xs = zip(*cells)
                keep[list(ys), list(xs)] = True
        preview = np.array(image)
        preview[~keep] = 0
        preview = Image.fromarray(preview, "RGBA")
        background = Image.new("RGBA", preview.size, (220, 220, 220, 255))
        background.alpha_composite(preview)
        out = out_dir / f"{path.stem}-keep-over-{threshold}.png"
        background.convert("RGB").save(out)
        print(out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
