"""侧视候选联系表（ASCII 标签，PIL 默认字体）。"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("output")
    parser.add_argument("--width", type=int, default=260)
    parser.add_argument("--cols", type=int, default=6)
    args = parser.parse_args()
    directory = Path(args.directory)
    files = sorted(p for p in directory.iterdir() if p.suffix.lower() in SUFFIXES)
    if not files:
        raise SystemExit("no images")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    thumbs = []
    for path in files:
        with Image.open(path) as opened:
            image = opened.convert("RGB")
        ratio = args.width / image.width
        image = image.resize((args.width, max(1, int(image.height * ratio))))
        thumbs.append((path.name, image))
    cell_w = args.width + 8
    cell_h = max(image.height for _, image in thumbs) + 26
    rows = (len(thumbs) + args.cols - 1) // args.cols
    sheet = Image.new("RGB", (cell_w * args.cols, cell_h * rows), (235, 235, 235))
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbs):
        x = (index % args.cols) * cell_w + 4
        y = (index // args.cols) * cell_h + 20
        draw.text((x, y - 16), name, fill=(0, 0, 0), font=font)
        sheet.paste(image, (x, y))
    sheet.save(args.output)
    print(args.output, sheet.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
