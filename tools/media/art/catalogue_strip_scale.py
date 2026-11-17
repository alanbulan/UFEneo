"""把已有图鉴待机条按声明站高重新缩放。

问题来源：先做待机条、后按身高标尺重采样定稿图时，定稿图变矮了，
anim-strip 还停在旧尺度，图鉴里一切换动画人物就变大一号。

做法：以 (192, 248) 根点为不动点，用最近邻缩放整帧，保持像素硬边、
二值 Alpha 和帧间原有起伏；缩放倍数由「声明站高 ÷ 当前中位站高」得出，
所有帧共用同一倍数，不逐帧拉平。

用法：
    python tools/media/art/catalogue_strip_scale.py --only agams wiki_xxx
    python tools/media/art/catalogue_strip_scale.py --all --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
CANVAS_WIDTH = 384
CANVAS_HEIGHT = 256
ROOT_X = 192
ROOT_Y = 248

sys.path.insert(0, str(ROOT / "tools/media/art"))
import catalogue_store  # noqa: E402


def frame_images(strip: Image.Image, frames: int) -> list[Image.Image]:
    return [strip.crop((CANVAS_WIDTH * i, 0, CANVAS_WIDTH * (i + 1), CANVAS_HEIGHT)) for i in range(frames)]


def standing_height(frame: Image.Image) -> int:
    rows = np.nonzero((np.array(frame)[:, :, 3] > 0).any(axis=1))[0]
    return int(rows.max() - rows.min() + 1) if rows.size else 0


def rescale(frame: Image.Image, factor: float) -> Image.Image:
    width = max(1, round(CANVAS_WIDTH * factor))
    height = max(1, round(CANVAS_HEIGHT * factor))
    scaled = frame.resize((width, height), Image.NEAREST)
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    canvas.paste(scaled, (round(ROOT_X - ROOT_X * factor), round(ROOT_Y - ROOT_Y * factor)))
    pixels = np.array(canvas)
    pixels[:, :, 3] = np.where(pixels[:, :, 3] > 0, 255, 0)
    return Image.fromarray(pixels)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", default=[])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tolerance", type=float, default=0.05)
    args = parser.parse_args()

    display = catalogue_store.load()["entries"]
    targets = list(display) if args.all else args.only
    report = []
    for catalogue_id in targets:
        entry = display.get(catalogue_id, {})
        strip_value = str(entry.get("strip", ""))
        declared = int(entry.get("visible_height_including_ornaments", 0) or 0)
        if not strip_value or declared <= 0:
            continue
        path = ROOT / strip_value.removeprefix("res://")
        if not path.is_file():
            continue
        with Image.open(path) as handle:
            strip = handle.convert("RGBA")
        frames = int(entry.get("frames", 1))
        if strip.width != CANVAS_WIDTH * frames or strip.height != CANVAS_HEIGHT or frames < 2:
            report.append({"id": catalogue_id, "action": "skipped_bad_strip"})
            continue
        images = frame_images(strip, frames)
        heights = [standing_height(image) for image in images]
        if not heights or min(heights) <= 0:
            continue
        median = float(np.median(heights))
        if abs(median - declared) <= args.tolerance * declared:
            continue
        factor = declared / median
        rebuilt = [rescale(image, factor) for image in images]
        result = Image.new("RGBA", (CANVAS_WIDTH * frames, CANVAS_HEIGHT), (0, 0, 0, 0))
        for index, image in enumerate(rebuilt):
            result.paste(image, (CANVAS_WIDTH * index, 0))
        after = [standing_height(image) for image in rebuilt]
        record = {"id": catalogue_id, "before": heights, "after": after, "factor": round(factor, 4)}
        if not args.dry_run:
            result.save(path)
            catalogue_store.update_entry(catalogue_id, {
                "strip": strip_value,
                "frames": frames,
                "strip_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
            record["action"] = "rescaled"
        else:
            record["action"] = "would_rescale"
        report.append(record)
    print(json.dumps({"count": len(report), "items": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
