"""生成特效审阅接触表（只读 staging，不写 assets/content）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
STAGING = ROOT / "reports/fx_father_family"


def main() -> None:
    provenance = json.loads((STAGING / "provenance.json").read_text(encoding="utf-8"))
    exports = {item["id"]: item for item in provenance["exports"]}
    for effect_id, export in exports.items():
        atlas = Image.open(STAGING / effect_id / "atlas.png").convert("RGBA")
        frames = []
        for x, y, w, h in export["rects"]:
            frames.append(atlas.crop((x, y, x + w, y + h)))
        scale = max(1, min(4, 1024 // max(1, sum(frame.width for frame in frames))))
        sheet = Image.new(
            "RGBA",
            (sum(frame.width for frame in frames) * scale + 8 * (len(frames) + 1), max(frame.height for frame in frames) * scale + 28),
            (18, 18, 22, 255),
        )
        draw = ImageDraw.Draw(sheet)
        x = 8
        for index, frame in enumerate(frames):
            big = frame.resize((frame.width * scale, frame.height * scale), Image.NEAREST)
            sheet.alpha_composite(big, (x, 24))
            draw.text((x, 4), str(index), fill=(230, 230, 230, 255))
            x += big.width + 8
        sheet.save(STAGING / f"contact-{effect_id}.png")
        print(f"wrote {STAGING.name}/contact-{effect_id}.png")


if __name__ == "__main__":
    sys.exit(main())
