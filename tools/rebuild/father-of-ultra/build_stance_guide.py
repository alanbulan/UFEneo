"""用已过门的待机照片生成原生 173 的 4× 比例导引。

AGENTS：站姿导引必须以身体轮廓承载姿势——本脚本不再画并脚人物加洋红线，
而是把**已经摆成目标架势的照片本体**缩到最终原生站高 173，再 4× 最近邻放大，
在图上标冠顶/角尖、眼行、白须底三条横线与头部列带竖线。导引只作比例/姿势
记录与自测，不替代照片；像素整帧仍以照片为唯一参考。

用法：
    .venv/bin/python tools/rebuild/father-of-ultra/build_stance_guide.py \
        --photo art/fighters/father-of-ultra/stage1/idle/frames/stance-raw-21.png \
        --out art/fighters/father-of-ultra/stage1/idle/references/stance-guide-raw21-173x4.png
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path[:0] = [
    str(ROOT / "tools"),
    *[str(p) for p in (ROOT / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (ROOT / "tools/rebuild").iterdir() if p.is_dir()],
]

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ALPHA = 128
NATIVE_STANDING = 173
ZOOM = 4
CANVAS = (1536, 1024)
SOLE_Y = 960
EYE_BAND_NATIVE = 26


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--horn-y", type=int, required=True)
    parser.add_argument("--eye-y", type=int, required=True)
    parser.add_argument("--beard-y", type=int, required=True)
    parser.add_argument("--eye-x", type=int, required=True,
                        help="眼列中心（照片像素）")
    args = parser.parse_args(argv)

    photo = Path(args.photo)
    if not photo.is_absolute():
        photo = ROOT / photo
    image = Image.open(photo).convert("RGBA")
    array = np.array(image)
    visible = array[:, :, 3] >= ALPHA
    ys, xs = np.where(visible)
    left, top, right, bottom = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    standing = bottom - top + 1
    subject = image.crop((left, top, right + 1, bottom + 1))
    subject = subject.resize(
        (max(1, round(subject.width * NATIVE_STANDING / standing)), NATIVE_STANDING),
        Image.BOX)
    solid = np.array(subject)
    solid[:, :, 3] = np.where(solid[:, :, 3] >= ALPHA, 255, 0)
    subject = Image.fromarray(solid, "RGBA")
    big = subject.resize((subject.width * ZOOM, subject.height * ZOOM), Image.NEAREST)

    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    x_left = (CANVAS[0] - big.width) // 2
    y_top = SOLE_Y - big.height + 1
    canvas.alpha_composite(big, (x_left, y_top))

    scale = NATIVE_STANDING / standing
    def row(photo_y: int) -> int:
        return y_top + round((photo_y - top) * scale) * ZOOM
    def col(photo_x: int) -> int:
        return x_left + round((photo_x - left) * scale) * ZOOM

    horn_y = row(args.horn_y)
    eye_y = row(args.eye_y)
    beard_y = row(args.beard_y)
    eye_center = col(args.eye_x)
    band = EYE_BAND_NATIVE * ZOOM

    draw = ImageDraw.Draw(canvas)
    draw.line([(0, horn_y), (CANVAS[0], horn_y)], fill=(0, 220, 0, 255), width=2)
    draw.line([(0, eye_y), (CANVAS[0], eye_y)], fill=(0, 160, 255, 255), width=2)
    draw.line([(0, beard_y), (CANVAS[0], beard_y)], fill=(255, 150, 0, 255), width=2)
    draw.line([(0, SOLE_Y), (CANVAS[0], SOLE_Y)], fill=(0, 255, 255, 255), width=2)
    for x in (eye_center - band, eye_center + band):
        draw.line([(x, horn_y), (x, SOLE_Y)], fill=(255, 0, 255, 255), width=2)
    draw.text((8, horn_y - 16), f"horn tip y={horn_y}", fill=(0, 220, 0, 255))
    draw.text((8, eye_y - 16), f"eye row y={eye_y}", fill=(0, 160, 255, 255))
    draw.text((8, beard_y - 16), f"beard bottom y={beard_y}", fill=(255, 150, 0, 255))
    draw.text((8, SOLE_Y - 16), f"sole y={SOLE_Y}", fill=(0, 255, 255, 255))
    draw.text((eye_center + band + 6, horn_y + 6),
              f"head band +-{EYE_BAND_NATIVE} native px", fill=(255, 0, 255, 255))

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)

    native_width = subject.width
    head_px = round((args.beard_y - args.horn_y + 1) * scale)
    stance_native = round((right - left + 1) * scale)  # 照片外缘跨即站距（cape 与后靴同缘）
    report = {
        "photo": photo.relative_to(ROOT).as_posix(),
        "photo_sha256": sha256(photo),
        "photo_standing_px": standing,
        "photo_bbox": [left, top, right, bottom],
        "native_standing": NATIVE_STANDING,
        "native_width": native_width,
        "scale": round(scale, 6),
        "zoom": ZOOM,
        "canvas": list(CANVAS),
        "placed": {"x": x_left, "y": y_top, "w": big.width, "h": big.height},
        "lines": {
            "horn_tip_y": horn_y,
            "eye_row_y": eye_y,
            "beard_bottom_y": beard_y,
            "sole_y": SOLE_Y,
            "head_band_x": [eye_center - band, eye_center + band],
        },
        "self_measure": {
            "standing_px": SOLE_Y - horn_y + 1,
            "head_px": beard_y - horn_y + 1,
            "head_ratio": round((beard_y - horn_y + 1) / (SOLE_Y - horn_y + 1), 4),
            "stance_native_px": stance_native,
            "stance_ratio": round(stance_native / NATIVE_STANDING, 4),
            "note": "按贴入几何自测；照片实测见 requests.json",
        },
        "output": out.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(out),
        "output_size": list(canvas.size),
    }
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
