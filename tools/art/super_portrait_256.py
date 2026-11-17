"""超必杀三级 CUT-IN 胸像的确定性 256 落格。

输入 1024 级 MCP 生图原始 PNG，输出 256×256、二值 Alpha、≤32 色、
主体单连通、四边留透明边距的胸像。步骤固定：

1. Alpha≥128 二值化；
2. 按 Alpha bbox 裁到主体；
3. 最近邻等比缩到目标高度（默认 240 px，最大宽度同）；
4. 在 256 画布上水平居中、底边留 8 px；
5. 整图逐像素映射到给定色板图的 ≤32 色集合（欧氏距离，无抖动）；
6. 再次硬化 Alpha，只保留 4 连通最大主体；
7. 输出并打印确定性度量。

不做换色、局部重涂、平滑、抖动或随机。色板图缺识别色时由调用者
按 AGENTS.md 选择现用待机锚图作色板源。

用法：
  .venv/bin/python -I tools/art/super_portrait_256.py \
      --raw art/fighters/<id>/stage1/super_portrait/portrait-1024-raw.png \
      --palette-image <palette.png> \
      --out art/fighters/<id>/stage1/super_portrait/portrait-256.png
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ALPHA_CUTOFF = 128
CANVAS = 256
TARGET_HEIGHT = 240
BOTTOM_MARGIN = 8
PALETTE_MAX = 32


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def harden_alpha(image: Image.Image) -> Image.Image:
    array = np.array(image.convert("RGBA"))
    array[..., 3] = np.where(array[..., 3] >= ALPHA_CUTOFF, 255, 0).astype(np.uint8)
    return Image.fromarray(array, "RGBA")


def load_palette(path: Path) -> list[tuple[int, int, int]]:
    array = np.array(Image.open(path).convert("RGBA"))
    visible = array[..., 3] > 0
    colors = sorted(
        {tuple(int(v) for v in color) for color in array[..., :3][visible]}
    )
    if not colors:
        raise ValueError(f"色板图没有可见像素: {path}")
    if len(colors) > PALETTE_MAX:
        raise ValueError(f"色板图颜色超过 {PALETTE_MAX}: {len(colors)}")
    return colors


def apply_palette(
    image: Image.Image, palette: list[tuple[int, int, int]]
) -> Image.Image:
    array = np.array(image.convert("RGBA"))
    visible = array[..., 3] > 0
    result = array.copy()
    if visible.any():
        palette_array = np.array(palette, dtype=np.int32)
        pixels = array[..., :3][visible].astype(np.int32)
        distances = ((pixels[:, None, :] - palette_array[None, :, :]) ** 2).sum(axis=2)
        chosen = palette_array[distances.argmin(axis=1)].astype(np.uint8)
        rgb = result[..., :3]
        rgb[visible] = chosen
        result[..., :3] = rgb
    return Image.fromarray(result, "RGBA")


def largest_component(image: Image.Image) -> tuple[Image.Image, list[int]]:
    array = np.array(image.convert("RGBA"))
    mask = array[..., 3] > 0
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            queue = deque([(y, x)])
            seen[y, x] = True
            points: list[tuple[int, int]] = []
            while queue:
                cy, cx = queue.popleft()
                points.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and mask[ny, nx]
                        and not seen[ny, nx]
                    ):
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            components.append(points)
    components.sort(key=len, reverse=True)
    if not components:
        raise ValueError("输入图没有可见像素")
    keep = np.zeros_like(mask, dtype=bool)
    for y, x in components[0]:
        keep[y, x] = True
    array[..., 3] = np.where(keep, 255, 0).astype(np.uint8)
    return Image.fromarray(array, "RGBA"), [len(component) for component in components]


def resize_to_canvas(image: Image.Image) -> Image.Image:
    hard = harden_alpha(image)
    box = hard.getchannel("A").getbbox()
    if box is None:
        raise ValueError("裁切前没有可见像素")
    subject = hard.crop(box)
    width, height = subject.size
    scale = min(TARGET_HEIGHT / height, TARGET_HEIGHT / width)
    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))
    subject = subject.resize(
        (new_width, new_height), Image.Resampling.NEAREST
    )
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    left = (CANVAS - new_width) // 2
    top = CANVAS - BOTTOM_MARGIN - new_height
    canvas.alpha_composite(subject, (left, top))
    return harden_alpha(canvas)


def metrics(image: Image.Image, palette_size: int, palette_source: Path) -> dict:
    array = np.array(image.convert("RGBA"))
    visible = array[..., 3] > 0
    ys, xs = np.where(visible)
    alpha_values = sorted({int(v) for v in np.unique(array[..., 3])})
    colors = sorted(
        {tuple(int(v) for v in color) for color in array[..., :3][visible]}
    )
    _, component_sizes = largest_component(image)
    return {
        "size": list(image.size),
        "alpha_values": alpha_values,
        "visible_colors": len(colors),
        "palette_size": palette_size,
        "palette_source": palette_source.as_posix(),
        "components_4conn": len(component_sizes),
        "component_sizes_top5": component_sizes[:5],
        "bbox_inclusive": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "margins": {
            "left": int(xs.min()),
            "top": int(ys.min()),
            "right": int(CANVAS - 1 - xs.max()),
            "bottom": int(CANVAS - 1 - ys.max()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--palette-image", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    palette = load_palette(args.palette_image)
    resized = resize_to_canvas(Image.open(args.raw).convert("RGBA"))
    quantized = harden_alpha(apply_palette(resized, palette))
    final, _ = largest_component(quantized)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    final.save(args.out)

    report = {
        "raw": args.raw.as_posix(),
        "raw_sha256": sha256(args.raw),
        "out": args.out.as_posix(),
        "out_sha256": sha256(args.out),
        **metrics(final, len(palette), args.palette_image),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
