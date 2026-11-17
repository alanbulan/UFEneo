"""Create a local contact sheet of installed catalogue strips for root review.

This is a review aid, not an approval gate: it writes only a PNG in reports/.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
DISPLAY = ROOT / "content/roster/catalogue_display.json"
OUT = ROOT / "reports/catalogue-rebuild-20261113/installed-strips.png"
BATCH = "catalogue-rebuild-20261113"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", default=BATCH)
    parser.add_argument("--cols", type=int, default=3)
    args = parser.parse_args()
    data = json.loads(DISPLAY.read_text(encoding="utf-8"))["entries"]
    ids = [cid for cid, entry in data.items()
           if entry.get("rebuild_batch") == args.batch and entry.get("strip")]
    if not ids:
        raise SystemExit("no installed strips in batch")
    # Show the whole strip at a 1:2 nearest-neighbour scale, not just frame 0:
    # otherwise the contact sheet cannot expose duplicate or barely-moving frames.
    cell_w, cell_h, label_h = 576, 128, 22
    rows = math.ceil(len(ids) / args.cols)
    out = Image.new("RGB", (cell_w * args.cols, (cell_h + label_h) * rows), (235, 235, 235))
    draw = ImageDraw.Draw(out)
    for index, cid in enumerate(ids):
        entry = data[cid]
        strip = ROOT / entry["strip"].removeprefix("res://")
        with Image.open(strip) as image:
            whole = image.convert("RGBA")
            whole = whole.resize((whole.width // 2, whole.height // 2), Image.NEAREST)
        x = (index % args.cols) * cell_w
        y = (index // args.cols) * (cell_h + label_h)
        out.paste(whole, (x, y), whole)
        draw.text((x + 4, y + cell_h + 3), f"{cid}  frames={entry.get('frames')}", fill=(0, 0, 0))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h + label_h - 1), outline=(185, 185, 185))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT)
    print(json.dumps({"entries": len(ids), "contact_sheet": str(OUT.relative_to(ROOT)),
                      "size": list(out.size), "review_authority": "root_delegated_by_user",
                      "user_reviewed": False, "listening_reviewed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
