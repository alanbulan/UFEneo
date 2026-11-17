"""动作帧批次核验：尺寸、Alpha、连通块、辉光门、固定比例换算站高、联系表。

只报数值，不作造型验收。辉光门口径按 AGENTS.md：
主体=alpha>=200 最大连通块，外扩 3 px 后统计；
主体外 alpha>=16 <=100 px、主体外 alpha>=200 必须为 0；
alpha 1–15 的尘点只登记。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CELL = 256
SOURCE_SCALE = 188 / 1100
GLOW_DILATE = 3
GLOW_MAX_GTE16 = 100


def components(mask: np.ndarray, min_alpha: int = 128) -> list[int]:
    seen = np.zeros_like(mask, bool)
    sizes = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                size = 0
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    size += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                sizes.append(size)
    return sorted(sizes, reverse=True)


def largest_component(mask: np.ndarray) -> np.ndarray:
    seen = np.zeros_like(mask, bool)
    best: list[tuple[int, int]] = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                cells = []
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                if len(cells) > len(best):
                    best = cells
    out = np.zeros_like(mask, bool)
    for cy, cx in best:
        out[cy, cx] = True
    return out


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    out = mask.copy()
    h, w = mask.shape
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        y0, y1 = max(0, y - radius), min(h, y + radius + 1)
        x0, x1 = max(0, x - radius), min(w, x + radius + 1)
        out[y0:y1, x0:x1] = True
    return out


def measure(path: Path) -> dict:
    image = Image.open(path).convert("RGBA")
    array = np.array(image)
    alpha = array[:, :, 3]
    visible = alpha > 0
    ys, xs = np.where(visible)
    if len(ys) == 0:
        return {"path": str(path), "error": "全透明"}
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    height = int(ys.max() - ys.min() + 1)
    subject = largest_component(alpha >= 200)
    outside = ~dilate(subject, GLOW_DILATE)
    a16 = int(((alpha >= 16) & outside).sum())
    a200 = int(((alpha >= 200) & outside).sum())
    dust = int(((alpha >= 1) & (alpha <= 15)).sum())
    comps = components(alpha >= 128)
    return {
        "path": path.relative_to(path.parents[0]).as_posix() if False else str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": list(image.size),
        "bbox": bbox,
        "height": height,
        "width": bbox[2] - bbox[0] + 1,
        "projected_cell_standing": round(height * SOURCE_SCALE, 1),
        "alpha_categories": {
            "zero": int((alpha == 0).sum()),
            "dust_1_15": dust,
            "mid_16_199": int(((alpha >= 16) & (alpha <= 199)).sum()),
            "solid_200_255": int((alpha >= 200).sum()),
        },
        "glow_outside_dilate3": {"gte16": a16, "gte200": a200},
        "glow_pass": a16 <= GLOW_MAX_GTE16 and a200 == 0,
        "components_alpha128": len(comps),
        "largest_component": comps[0] if comps else 0,
    }


def checker(size: tuple[int, int], square: int = 16) -> Image.Image:
    width, height = size
    board = Image.new("RGB", size, (210, 210, 214))
    draw = ImageDraw.Draw(board)
    for y in range(0, height, square):
        for x in range(0, width, square):
            if (x // square + y // square) % 2:
                draw.rectangle([x, y, x + square - 1, y + square - 1], fill=(164, 164, 170))
    return board


def contact_sheet(paths: list[Path], out: Path, columns: int = 3) -> None:
    tile_w, tile_h = 360, 540
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (tile_w * columns, tile_h * rows), (32, 32, 36))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 20)
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGBA")
        image.thumbnail((tile_w - 20, tile_h - 44), Image.NEAREST)
        plate = checker(image.size, 12)
        plate.paste(image, (0, 0), image)
        col, row = index % columns, index // columns
        x = col * tile_w + (tile_w - image.width) // 2
        y = row * tile_h + 28
        sheet.paste(plate, (x, y))
        draw.text((col * tile_w + 10, row * tile_h + 4), path.stem, fill=(240, 240, 240), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", nargs="+", required=True)
    parser.add_argument("--out", required=True, help="报告 JSON")
    parser.add_argument("--sheet", default="", help="联系表 PNG")
    args = parser.parse_args(argv)
    paths = [Path(p) for p in args.paths]
    rows = [measure(p) for p in paths]
    report = {"scale": SOURCE_SCALE, "frames": rows}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))
    if args.sheet:
        contact_sheet(paths, Path(args.sheet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
