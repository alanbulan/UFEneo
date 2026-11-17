"""提取单帧图主体并写入落格清单。"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
                        cells.append((ny, nx))
            if len(cells) > best_size:
                best_size = len(cells)
                best = np.zeros_like(mask, bool)
                for cy, cx in cells:
                    best[cy, cx] = True
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--out", required=True)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--standing", action="store_true", default=True)
    parser.add_argument("--not-standing", dest="standing", action="store_false")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)

    image = Image.open(source).convert("RGBA")
    array = np.array(image)
    mask = array[:, :, 3] >= 128
    keep = largest_component(mask)
    array[~keep] = 0
    ys, xs = np.nonzero(keep)
    crop = array[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
    Image.fromarray(crop, "RGBA").save(out)

    frame = {
        "clip": args.clip,
        "index": args.index,
        "source": out.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(out),
        "size": [int(crop.shape[1]), int(crop.shape[0])],
        "standing": bool(args.standing),
    }
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"frames": [frame]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"clip": args.clip, "index": args.index, "size": frame["size"], "out": frame["source"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
