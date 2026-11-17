"""form_switch 六帧落格：只引本形态待机锚，固定源比例，不逐帧重标定。

输入：stage2/form_switch/frames/form_switch-XX-raw-v2.png
输出：stage1/cells/form_switch-XX-cell.png 与 form_switch-cells.json
- 清理 <32 px 的孤立尘点，保留主体；不改造型。
- scale 取身份锚 cells.json（188/1526），脚底 247、根点 x=128、格 256。
- 色板取身份锚 32 色，整图映射。
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/art"))
sys.path.insert(0, str(ROOT / "tools/media/art"))
import stage_cells  # noqa: E402
from catalogue_native import harden_alpha, trim  # noqa: E402

FIGHTER = "ultraman-zero__strong_corona"
RAW = ROOT / f"art/fighters/{FIGHTER}/stage2/form_switch/frames"
CELLS = ROOT / f"art/fighters/{FIGHTER}/stage1/cells"
CELL = 256
ANCHOR_X = 128
FOOT_ROW = 247
MIN_COMPONENT = 32


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remove_specks(image: Image.Image, minimum: int) -> tuple[Image.Image, list]:
    array = np.array(image)
    mask = array[:, :, 3] > 0
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = np.zeros_like(mask, dtype=bool)
    sizes = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            points = []
            while q:
                cy, cx = q.popleft()
                points.append((cy, cx))
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            sizes.append(len(points))
            if len(points) >= minimum:
                for py, px in points:
                    out[py, px] = True
    array[:, :, 3] = np.where(out, array[:, :, 3], 0)
    return Image.fromarray(array, "RGBA"), sizes


def main() -> int:
    anchor = json.loads((CELLS / "cells.json").read_text(encoding="utf-8"))
    palette = [tuple(c) for c in anchor["palette"]]
    scale = float(anchor["scale"])
    records = []
    for i in range(6):
        raw = RAW / f"form_switch-{i:02d}-raw-v2.png"
        cleaned, sizes = remove_specks(harden_alpha(Image.open(raw).convert("RGBA")), MIN_COMPONENT)
        cleaned = trim(cleaned)
        clean_path = RAW / f"form_switch-{i:02d}-clean.png"
        cleaned.save(clean_path)
        out = CELLS / f"form_switch-{i:02d}-cell.png"
        row = stage_cells.build(
            clean_path, out, palette, scale, FOOT_ROW,
            anchor_x=ANCHOR_X, cell=CELL, foot_band=0.08,
        )
        row.update({
            "raw": raw.relative_to(ROOT).as_posix(),
            "raw_sha256": sha(raw),
            "clean": clean_path.relative_to(ROOT).as_posix(),
            "clean_sha256": sha(clean_path),
            "raw_size": list(Image.open(raw).size),
            "clean_size": list(cleaned.size),
            "specks_removed": len([s for s in sizes if s < MIN_COMPONENT]),
            "specks_px_removed": sum(s for s in sizes if s < MIN_COMPONENT),
            "tick": 10,
            "loop": False,
            "pose_note": (
                "蓄势深蹲" if i == 0 else
                "起转抬后脚" if i == 1 else
                "背向回望" if i == 2 else
                "转回侧背" if i == 3 else
                "落步收势" if i == 4 else
                "待机护架落定"
            ),
            "height_exception": i in (0, 1, 2, 3),
        })
        records.append(row)
    (CELLS / "form_switch-cells.json").write_text(
        json.dumps({
            "fighter": FIGHTER,
            "scale": scale,
            "scale_source": anchor["scale_source"],
            "cell": CELL,
            "anchor": [ANCHOR_X, FOOT_ROW + 1],
            "foot_row": FOOT_ROW,
            "frames": records,
            "authority": "root_delegated_by_user",
            "user_approved": False,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps([{k: r[k] for k in ("frame", "height", "width", "bbox", "components",
                                        "colors", "alpha", "foot_row", "output_sha256")}
                      for r in records], ensure_ascii=False, indent=1))
    return 0 if all(r["components"] == 1 and r["alpha"] == [0, 255] and r["colors"] <= 32
                    for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
