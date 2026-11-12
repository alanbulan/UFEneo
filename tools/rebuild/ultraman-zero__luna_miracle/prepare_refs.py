"""从官方来源准备待机照参考：白底抠透明、统一留白画布、侧脸结构裁切。

只处理参考图，不改造型。输出到
art/fighters/ultraman-zero__luna_miracle/stage1/idle/references/。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ROOT / "art/fighters/ultraman-zero__luna_miracle/sources"
REFS = ROOT / "art/fighters/ultraman-zero__luna_miracle/stage1/idle/references"
CANVAS = (1024, 1536)
SUBJECT_HEIGHT = 1100
BASELINE = 1410
HEAD_CROP = (200, 150, 580, 470)
HEAD_SCALE = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def largest_component(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    seen = np.zeros_like(mask, bool)
    best = np.zeros_like(mask, bool)
    best_size = 0
    from collections import deque

    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            queue = deque([(y, x)])
            seen[y, x] = True
            cells = [(y, x)]
            while queue:
                cy, cx = queue.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < height and 0 <= nx < width \
                            and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
                        cells.append((ny, nx))
            if len(cells) > best_size:
                best_size = len(cells)
                best = np.zeros_like(mask, bool)
                for cy, cx in cells:
                    best[cy, cx] = True
    return best


def cutout(path: Path, threshold: int) -> Image.Image:
    original = Image.open(path).convert("RGBA")
    # 顶部左侧有日文标题条，连主体外留白一起裁到本人范围，不进入参考。
    original = original.crop((170, 75, 540, 1000))
    image = original.convert("RGB")
    sentinel = (255, 0, 255)
    ImageDraw.floodfill(image, (5, 5), sentinel, thresh=threshold)
    array = np.array(image)
    background = np.all(array == np.array(sentinel), axis=2)
    rgba = np.array(original)
    rgba[background, 3] = 0
    rgba[background, :3] = 0
    alpha = rgba[:, :, 3] > 0
    keep = largest_component(alpha)
    rgba[~keep] = 0
    return Image.fromarray(rgba, "RGBA")


def main() -> int:
    REFS.mkdir(parents=True, exist_ok=True)
    result = {}

    for threshold in (8, 12, 16, 24):
        cut = cutout(SOURCES / "ref-03-suit-official.jpg", threshold)
        alpha = np.array(cut)[:, :, 3]
        ys, xs = np.nonzero(alpha)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        preview = Image.new("RGBA", cut.size, (40, 40, 40, 255))
        preview.alpha_composite(cut)
        preview.convert("RGB").save(REFS / f"cutout-threshold-{threshold}.png")
        result[str(threshold)] = {"bbox": bbox, "visible_pixels": int(alpha.astype(bool).sum())}
        print(threshold, bbox, int(alpha.astype(bool).sum()))

    # 正式待机参考：白底分离、单一主体、统一缩放到站高 1100、透明留白画布。
    cut = cutout(SOURCES / "ref-03-suit-official.jpg", 16)
    alpha = np.array(cut)[:, :, 3]
    ys, xs = np.nonzero(alpha)
    cut = cut.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    scale = SUBJECT_HEIGHT / cut.height
    cut = cut.resize((max(1, round(cut.width * scale)), SUBJECT_HEIGHT), Image.LANCZOS)
    array = np.array(cut)
    hard = np.where(array[:, :, 3] >= 128, 255, 0).astype(np.uint8)
    array[:, :, 3] = hard
    array[hard == 0, :3] = 0
    cut = Image.fromarray(array, "RGBA")
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.alpha_composite(cut, ((CANVAS[0] - cut.width) // 2, BASELINE - cut.height))
    wide_path = REFS / "suit-wide-canvas.png"
    canvas.save(wide_path)
    print("wide", cut.size, canvas.size, sha256(wide_path))

    head = Image.open(SOURCES / "ref-02-side-official.png").convert("RGB").crop(HEAD_CROP)
    head = head.resize((head.width * HEAD_SCALE, head.height * HEAD_SCALE), Image.LANCZOS)
    head_path = REFS / "luna-side-head-official.png"
    head.save(head_path)
    print("head", head.size, sha256(head_path))

    (REFS / "prepare-check.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
