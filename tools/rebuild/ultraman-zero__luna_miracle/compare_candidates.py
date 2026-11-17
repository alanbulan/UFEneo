"""把清理后的侧视候选按部位并排比较：全身、头、腿（ASCII 标签）。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]


def trim(image: Image.Image) -> Image.Image:
    array = np.array(image.convert("RGBA"))
    alpha = array[:, :, 3]
    ys, xs = np.nonzero(alpha)
    return image.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def resize_to_height(image: Image.Image, height: int) -> Image.Image:
    ratio = height / image.height
    return image.resize((max(1, round(image.width * ratio)), height), Image.LANCZOS)


def main() -> int:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        raise SystemExit("no candidates")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    images = []
    for path in paths:
        image = trim(Image.open(path).convert("RGBA"))
        images.append((path.stem, image))
    out_dir = paths[0].parent
    for label, height, top_ratio, bottom_ratio in (
        ("full", 620, 0.0, 1.0),
        ("head", 280, 0.0, 0.30),
        ("torso", 300, 0.22, 0.58),
        ("legs", 360, 0.50, 1.0),
    ):
        pieces = []
        for name, image in images:
            top = int(image.height * top_ratio)
            bottom = int(image.height * bottom_ratio)
            crop = image.crop((0, top, image.width, bottom))
            crop = resize_to_height(crop, height)
            pieces.append((name, crop))
        cell_w = max(piece.width for _, piece in pieces) + 24
        sheet = Image.new("RGBA", (cell_w * len(pieces), height + 30), (235, 235, 235, 255))
        draw = ImageDraw.Draw(sheet)
        for index, (name, piece) in enumerate(pieces):
            x = index * cell_w + (cell_w - piece.width) // 2
            draw.text((index * cell_w + 8, 6), name, fill=(0, 0, 0, 255), font=font)
            sheet.alpha_composite(piece, (x, 26))
        out = out_dir / f"compare-{label}.png"
        sheet.convert("RGB").save(out)
        print(out.relative_to(ROOT), sheet.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
