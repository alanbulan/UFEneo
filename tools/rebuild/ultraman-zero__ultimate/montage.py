"""把多个 clip 的联系表拼成一张检查图，减少逐帧读图开销。

用法：
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/montage.py \
        --clips idle,walk_forward --out reports/montage-a.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
REPORTS = ROOT / "tools/rebuild/ultraman-zero__ultimate/reports"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    clips = [c.strip() for c in args.clips.split(",") if c.strip()]
    sheets = []
    for clip in clips:
        path = REPORTS / f"{clip}-contact.png"
        if not path.is_file():
            raise SystemExit(f"缺少联系表 {path}")
        image = Image.open(path).convert("RGBA")
        # 统一缩到 1× 原生格高度（每帧 256 px），便于一眼看全身。
        scale = 256 / image.height
        sheets.append(image.resize((max(1, int(image.width * scale)), 256),
                                   Image.Resampling.NEAREST))
    width = max(s.width for s in sheets)
    height = sum(s.height for s in sheets)
    canvas = Image.new("RGBA", (width, height), (238, 238, 238, 255))
    y = 0
    for sheet in sheets:
        canvas.alpha_composite(sheet, (0, y))
        y += sheet.height
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    print(out.relative_to(ROOT).as_posix(), canvas.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
