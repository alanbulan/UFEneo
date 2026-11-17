"""用 ASCII 标签重写诊断联系表（PIL 默认字体无中文字形）。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
SHEET = ROOT / "art/fighters/ultraman-zero__luna_miracle/stage1/diagnostic/stance-view-angle-contact.png"

LABELS = [
    "ref-03 official suit photo (front 3/4)",
    "ref-02 official side head",
    "installed Zero side idle (stance only)",
    "stance-raw-00 REJECT: 3/4 front",
    "stance-raw-01 REJECT: 3/4 front",
    "stance-raw-02 REJECT: 3/4 front",
]
CELL_W = 420
GAP = 8
CELL_H = 664
START_Y = 26


def main() -> int:
    image = Image.open(SHEET).convert("RGB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    for index, label in enumerate(LABELS):
        x = (index % 3) * (CELL_W + GAP) + GAP
        y = (index // 3) * CELL_H + START_Y
        draw.rectangle((x, y - 30, x + CELL_W, y - 1), fill=(245, 245, 245))
        draw.text((x, y - 24), label, fill=(0, 0, 0), font=font)
    image.save(SHEET)
    print(SHEET, image.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
