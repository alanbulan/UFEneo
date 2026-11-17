"""只读：量一批源帧的裁后高度、脚底差与宽高，判断批次统一比例是否可行。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    rows = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.is_absolute():
            path = ROOT / path
        array = np.array(Image.open(path).convert("RGBA"))
        visible = array[:, :, 3] >= 128
        ys, xs = np.nonzero(visible)
        rows.append({
            "path": path.relative_to(ROOT).as_posix(),
            "size": [array.shape[1], array.shape[0]],
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "height": int(ys.max() - ys.min() + 1),
            "width": int(xs.max() - xs.min() + 1),
        })
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
