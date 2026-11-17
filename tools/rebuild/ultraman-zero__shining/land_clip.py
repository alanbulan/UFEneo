"""按 clip 落格：同一固定源比例、同一色板、256 格、root [128,248]、脚底 247。

用法：
    .venv/bin/python -I tools/rebuild/ultraman-zero__shining/land_clip.py \
        --clip form_switch --scale 0.170909091 --out-dir art/fighters/.../stage1/form_switch/cells \
        --frame 00=path/switch-00-raw.png --frame 01=path/switch-01-raw.png ...

只做确定性后处理；逐帧核连通块、二值 Alpha、色数，并输出站高与联系表。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/art"))
import stage_cells  # noqa: E402

CELL = 256
ANCHOR_X = 128
FOOT_ROW = 247
CELLS_JSON = ROOT / "art/fighters/ultraman-zero__shining/stage1/cells/cells.json"


def checker(size: tuple[int, int], square: int = 12) -> Image.Image:
    board = Image.new("RGB", size, (205, 205, 210))
    draw = ImageDraw.Draw(board)
    for y in range(0, size[1], square):
        for x in range(0, size[0], square):
            if (x // square + y // square) % 2:
                draw.rectangle([x, y, x + square - 1, y + square - 1], fill=(158, 158, 164))
    return board


def sheet(cells: list[Path], out: Path, scale: int = 2) -> None:
    tiles = []
    for path in cells:
        image = Image.open(path).convert("RGBA")
        image = image.resize((image.width * scale, image.height * scale), Image.NEAREST)
        plate = checker(image.size)
        plate.paste(image, (0, 0), image)
        tiles.append((path, plate))
    width = sum(t.width for _, t in tiles) + 8 * (len(tiles) - 1)
    height = tiles[0][1].height + 24
    board = Image.new("RGB", (width, height), (28, 28, 32))
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 14)
    x = 0
    for path, tile in tiles:
        board.paste(tile, (x, 24))
        draw.text((x + 3, 4), path.stem, fill=(238, 238, 238), font=font)
        x += tile.width + 8
    out.parent.mkdir(parents=True, exist_ok=True)
    board.save(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clip", required=True)
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--frame", action="append", required=True, help="索引=原始图")
    parser.add_argument("--foot-row", type=int, default=FOOT_ROW)
    parser.add_argument("--foot-band", type=float, default=0.08)
    parser.add_argument("--stand-check", type=float, default=8.0,
                        help="直立帧站高偏差门（百分比），默认 8")
    parser.add_argument("--sheet", default="", help="联系表输出；默认 <out-dir>/contact.png")
    args = parser.parse_args(argv)

    anchor = json.loads(CELLS_JSON.read_text(encoding="utf-8"))
    palette = [tuple(color) for color in anchor["palette"]]
    target = anchor["target_standing_height"]
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, flags, cells = [], [], []
    for text in args.frame:
        index, _, path_text = text.partition("=")
        source = Path(path_text)
        if not source.is_absolute():
            source = ROOT / source
        if not source.exists():
            raise SystemExit(f"缺帧：{source}")
        out = out_dir / f"{args.clip}-{index}-cell.png"
        row = stage_cells.build(source, out, palette, args.scale, args.foot_row,
                                anchor_x=ANCHOR_X, cell=CELL, foot_band=args.foot_band)
        solid = stage_cells.solid_source(source)
        row.update({
            "clip": args.clip,
            "index": index,
            "source_standing_solid": solid.height,
            "projected_standing": round(solid.height * args.scale, 1),
            "standing_drift_percent": round(
                (solid.height * args.scale - target) / target * 100, 1),
        })
        if row["components"] != 1:
            flags.append(f"{index}: 连通块 {row['components']}")
        if row["alpha"] != [0, 255]:
            flags.append(f"{index}: Alpha 非二值 {row['alpha']}")
        if row["colors"] > 32:
            flags.append(f"{index}: 色数 {row['colors']}")
        rows.append(row)
        cells.append(out)

    report = {
        "clip": args.clip,
        "cell": CELL,
        "root": [ANCHOR_X, args.foot_row + 1],
        "foot_row": args.foot_row,
        "scale": args.scale,
        "scale_status": "fixed_from_identity_anchor_source",
        "target_standing_height": target,
        "palette_source": anchor["palette_source"],
        "frames": rows,
        "flags": flags,
    }
    (out_dir / "cells.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sheet_path = Path(args.sheet) if args.sheet else out_dir / "contact.png"
    sheet(cells, sheet_path)
    for row in rows:
        print(json.dumps({k: row[k] for k in (
            "index", "source_standing_solid", "projected_standing",
            "standing_drift_percent", "height", "width", "bbox", "head_height",
            "head_ratio", "colors", "components", "foot_row", "alpha")}, ensure_ascii=False))
    print("flags", flags)
    return 0 if not flags else 1


if __name__ == "__main__":
    raise SystemExit(main())
