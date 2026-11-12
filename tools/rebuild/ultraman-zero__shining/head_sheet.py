"""头部原生像素对比：锚与候选按眼行对齐裁切，1:1 拼图。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def eye_anchor(path: Path) -> tuple[int, int, int, int]:
    array = np.array(Image.open(path).convert("RGBA"))
    alpha = array[:, :, 3]
    rgb = array[:, :, :3].astype(int)
    visible = alpha >= 128
    blue = (rgb[:, :, 2] > 150) & (rgb[:, :, 2] - rgb[:, :, 0] > 60) \
        & (rgb[:, :, 2] - rgb[:, :, 1] > 20) & visible
    ys, xs = np.where(blue)
    if not len(ys):
        raise SystemExit(f"找不到眼灯：{path}")
    # 取最上方的一组蓝色（眼部），排除胸灯/腕灯
    top = ys.min()
    mask = ys <= top + 80
    return int(xs[mask].min()), int(ys[mask].min()), int(xs[mask].max()), int(ys[mask].max())


def crop_head(path: Path, width: int = 340, height: int = 260) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    x0, y0, x1, y1 = eye_anchor(path)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    left = max(0, cx - width // 2)
    top = max(0, cy - int(height * 0.45))
    box = (left, top, min(image.width, left + width), top + height)
    crop = image.crop(box)
    plate = Image.new("RGBA", (width, height), (200, 200, 206, 255))
    plate.alpha_composite(crop, (0, 0))
    return plate.convert("RGB")


def main(argv: list[str]) -> int:
    paths = [Path(p) for p in argv[1:]]
    out = Path(argv[0])
    tiles = [crop_head(p) for p in paths]
    gap = 10
    width = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    sheet = Image.new("RGB", (width, tiles[0].height + 26), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 16)
    x = 0
    for path, tile in zip(paths, tiles):
        sheet.paste(tile, (x, 26))
        draw.text((x + 4, 4), path.stem, fill=(240, 240, 240), font=font)
        x += tile.width + gap
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
