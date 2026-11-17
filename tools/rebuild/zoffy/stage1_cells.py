"""佐菲 stage1 单帧落格：全套共用一个源像素比例。

art/STYLE.md：同一动作整帧统一尺度和根点；不得按姿势外框归一身高。
本工具不按每帧 bbox 拉成同一高度，而是：

1. 以已批准图鉴定稿 catalogue-173.png 的 32 色板为唯一色板；
2. 用直立待机帧的站高定出"源像素→原生像素"的单一比例（目标站高 154）；
3. 全部帧乘同一比例，屈膝、腾空收腿保留真实压低/腾空高度；
4. 缩放后二值 Alpha，水平按脚底段重心对到 anchor x=96，
   站立帧脚底贴 183，腾空帧由 foot_row 参数给出。

用法：
    .venv/bin/python tools/rebuild/zoffy/stage1_cells.py
"""
from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/media/art"))
from catalogue_native import (  # noqa: E402
    apply_palette, build_palette, harden_alpha, trim,
)

APPROVED = ROOT / "art/fighters/zoffy/model/catalogue-173.png"
CELL = 192
ANCHOR_X = 96
BASELINE = 184
# 与已装 154 战斗待机同档的在屏站高。
TARGET_STANDING = 154
SCALE_SOURCE = "art/fighters/zoffy/stage1/idle/frames/raw-00-v3.png"

FRAMES = [
    ("idle-00", "art/fighters/zoffy/stage1/idle/frames/raw-00-v3.png", 183),
    ("idle-01", "art/fighters/zoffy/stage1/idle/frames/raw-01-v4.png", 183),
    ("walk-00", "art/fighters/zoffy/stage1/walk/frames/raw-00-v3.png", 183),
    ("walk-01", "art/fighters/zoffy/stage1/walk/frames/raw-01-v4.png", 183),
    ("jump-00", "art/fighters/zoffy/stage1/jump/frames/raw-00-v3.png", 183),
]


def head_height(mask: np.ndarray) -> int:
    """头顶到颈（头宽峰值之后最窄行）的行数。"""
    ys = np.nonzero(mask.any(axis=1))[0]
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    window = [
        (y, int(mask[y].sum())) for y in range(top, bottom + 1)
        if top + int(height * 0.12) <= y <= top + int(height * 0.50)
    ]
    neck, _ = min(window, key=lambda item: item[1])
    return neck - top


def foot_center(mask: np.ndarray, fraction: float = 0.08) -> float:
    ys = np.nonzero(mask.any(axis=1))[0]
    bottom = int(ys.max())
    top = max(int(ys.min()), bottom - max(1, int((bottom - int(ys.min()) + 1) * fraction)))
    band = mask[top:bottom + 1]
    total = band.sum()
    if total == 0:
        return mask.shape[1] / 2.0
    return float((band.sum(axis=0) * np.arange(band.shape[1])).sum() / total)


def components(mask: np.ndarray) -> int:
    seen = np.zeros_like(mask, bool)
    count = 0
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x] and not seen[y, x]:
                count += 1
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                                and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
    return count


def solid_source(path: Path) -> Image.Image:
    return trim(harden_alpha(Image.open(path).convert("RGBA")))


def build(source: Path, out: Path, palette: list, scale: float, foot_row: int) -> dict:
    solid = solid_source(source)
    size = (max(1, round(solid.width * scale)), max(1, round(solid.height * scale)))
    scaled = harden_alpha(solid.resize(size, Image.BOX))
    scaled = apply_palette(scaled, palette)
    mask = np.array(scaled)[:, :, 3] > 0
    center = foot_center(mask)
    canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, (round(ANCHOR_X - center), foot_row + 1 - scaled.height))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)

    array = np.array(canvas)
    visible = array[:, :, 3] > 0
    ys, xs = np.where(visible)
    return {
        "frame": out.stem,
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output": out.relative_to(ROOT).as_posix(),
        "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "scale": round(scale, 6),
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "height": int(ys.max() - ys.min() + 1),
        "width": int(xs.max() - xs.min() + 1),
        "head_height": head_height(visible),
        "colors": int(len(np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0))),
        "components": components(visible),
        "foot_row": int(ys.max()),
        "alpha": sorted({int(v) for v in np.unique(array[:, :, 3])}),
    }


def main() -> int:
    palette = build_palette(trim(harden_alpha(Image.open(APPROVED).convert("RGBA"))), 32)
    reference = solid_source(ROOT / SCALE_SOURCE)
    scale = TARGET_STANDING / reference.height
    reports = [build(ROOT / source, ROOT / f"reports/zoffy/stage1/{name}-cell.png",
                     palette, scale, foot_row)
               for name, source, foot_row in FRAMES]
    print(json.dumps({"scale": round(scale, 6), "scale_source": SCALE_SOURCE,
                      "frames": reports}, ensure_ascii=False, indent=1))
    ok = all(r["components"] == 1 and r["alpha"] == [0, 255] and r["colors"] <= 32 for r in reports)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
