"""按行列网格切分动作图并保留最大连通块。"""
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
    parser.add_argument("strip")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--index-offset", type=int, default=0)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expect", type=int, default=0)
    parser.add_argument("--standing", action="store_true", default=True)
    parser.add_argument("--not-standing", dest="standing", action="store_false")
    args = parser.parse_args()

    strip_path = Path(args.strip)
    if not strip_path.is_absolute():
        strip_path = ROOT / strip_path
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    image = Image.open(strip_path).convert("RGBA")
    array = np.array(image)
    h, w = array.shape[:2]
    ch, cw = h // args.rows, w // args.cols
    frames = []
    idx = args.index_offset
    for row in range(args.rows):
        for col in range(args.cols):
            crop = array[row * ch:(row + 1) * ch, col * cw:(col + 1) * cw].copy()
            mask = crop[:, :, 3] >= 128
            keep = largest_component(mask)
            crop[~keep] = 0
            ys, xs = np.nonzero(keep)
            if len(ys) == 0:
                continue
            crop = crop[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
            name = f"{args.clip}-{idx:02d}"
            path = out_dir / f"{name}.png"
            Image.fromarray(crop, "RGBA").save(path)
            frames.append({
                "clip": args.clip,
                "index": idx,
                "source": path.relative_to(ROOT).as_posix(),
                "source_sha256": sha256(path),
                "size": [int(crop.shape[1]), int(crop.shape[0])],
                "standing": bool(args.standing),
            })
            idx += 1

    report = {
        "strip": strip_path.relative_to(ROOT).as_posix(),
        "strip_sha256": sha256(strip_path),
        "strip_size": [image.width, image.height],
        "grid": [args.rows, args.cols],
        "expected": args.expect,
        "count": len(frames),
        "frames": frames,
    }
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"frames": frames}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if (not args.expect or len(frames) == args.expect) else 1


if __name__ == "__main__":
    raise SystemExit(main())
