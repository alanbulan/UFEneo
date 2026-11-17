"""清掉生成图里与人物断开的漂浮颗粒，只保留最大主体；不改人物像素。"""
from __future__ import annotations

import hashlib
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
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    if not source.is_absolute():
        source = ROOT / source
    if not target.is_absolute():
        target = ROOT / target
    image = Image.open(source).convert("RGBA")
    array = np.array(image)
    mask = array[:, :, 3] > 0
    comps = components(mask)
    comps.sort(key=len, reverse=True)
    keep = np.zeros_like(mask, bool)
    for y, x in comps[0]:
        keep[y, x] = True
    removed = mask & ~keep
    array[removed] = 0
    cleaned = Image.fromarray(array, "RGBA")
    cleaned.save(target)

    alpha = array[:, :, 3]
    ys, xs = np.nonzero(alpha)
    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    height = bottom - top + 1
    band_top = bottom - int(height * 0.06)
    band = alpha[band_top:bottom + 1] > 0
    columns = np.nonzero(band.any(axis=0))[0]
    groups = []
    for x in columns.tolist():
        if groups and x - groups[-1][-1] <= 3:
            groups[-1].append(x)
        else:
            groups.append([x])
    foot_span = groups[-1][-1] - groups[0][0] if len(groups) >= 2 else 0
    print({
        "source": source.relative_to(ROOT).as_posix(),
        "target": target.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "target_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "size": list(cleaned.size),
        "components_before": len(comps),
        "removed_pixels": int(removed.sum()),
        "bbox": [left, top, right, bottom],
        "height": height,
        "width": right - left + 1,
        "foot_groups": [[g[0], g[-1]] for g in groups],
        "foot_outer_span": foot_span,
        "foot_span_over_height": round(foot_span / height, 4) if height else 0,
        "touches_edge": left == 0 or top == 0 or right == cleaned.width - 1
                        or bottom == cleaned.height - 1,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
