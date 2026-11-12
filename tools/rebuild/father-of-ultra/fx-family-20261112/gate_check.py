"""只读复核：逐帧打印硬 Alpha 与主体外像素；违规时列出坐标。"""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
STAGING = ROOT / "reports/fx_father_family"


def label(mask):
    h, w = mask.shape
    labels = np.zeros((h, w), np.int32)
    sizes = []
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if labels[y, x]:
            continue
        current = len(sizes) + 1
        queue = deque([(y, x)])
        labels[y, x] = current
        count = 0
        while queue:
            cy, cx = queue.popleft()
            count += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                    labels[ny, nx] = current
                    queue.append((ny, nx))
        sizes.append(count)
    return labels, sizes


def main() -> None:
    provenance = json.loads((STAGING / "provenance.json").read_text(encoding="utf-8"))
    failures = 0
    for export in provenance["exports"]:
        atlas = np.array(Image.open(STAGING / export["id"] / "atlas.png").convert("RGBA"))
        alpha = atlas[..., 3]
        values = sorted(int(v) for v in np.unique(alpha))
        print(export["id"], "alpha", values)
        for index, (x, y, w, h) in enumerate(export["rects"]):
            sub = alpha[y:y + h, x:x + w]
            labels, sizes = label(sub >= 200)
            if not sizes:
                print("  frame", index, "EMPTY")
                failures += 1
                continue
            main_index = sizes.index(max(sizes)) + 1
            main = labels == main_index
            outside16 = (~main) & (sub >= 16)
            outside200 = (~main) & (sub >= 200)
            count16, count200 = int(outside16.sum()), int(outside200.sum())
            if count16 > 100 or count200:
                failures += 1
                coords = np.argwhere(outside200)[:12].tolist()
                print(f"  frame {index} FAIL outside16={count16} outside200={count200} coords={coords}")
    print("gate", "PASS" if failures == 0 else f"FAIL {failures}")


if __name__ == "__main__":
    sys.exit(main())
