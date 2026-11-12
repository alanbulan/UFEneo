"""把一个 clip 的全部 raw 帧落进 256 格：固定源比例、统一色板、逐帧脚底行。

用法：
  .venv/bin/python tools/rebuild/ultraman-zero__strong_corona/promote_clip.py light1
  .venv/bin/python tools/rebuild/ultraman-zero__strong_corona/promote_clip.py walk_forward
只写本形态 stage1/cells/ 与 clip 记录；不安装、不改共享文件。
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/art"))
sys.path.insert(0, str(ROOT / "tools/media/art"))
import stage_cells  # noqa: E402
from catalogue_native import harden_alpha, trim  # noqa: E402

FIGHTER = "ultraman-zero__strong_corona"
CELLS = ROOT / f"art/fighters/{FIGHTER}/stage1/cells"
PLAN = ROOT / "tools/rebuild/ultraman-zero__strong_corona/frame_plan.json"
MIN_COMPONENT = 32
TARGET = 188
HEIGHT_TOL = 0.08


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remove_specks(image: Image.Image, minimum: int) -> tuple[Image.Image, list]:
    array = np.array(image)
    mask = array[:, :, 3] > 0
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = np.zeros_like(mask, dtype=bool)
    sizes = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            points = []
            while q:
                cy, cx = q.popleft()
                points.append((cy, cx))
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            sizes.append(len(points))
            if len(points) >= minimum:
                for py, px in points:
                    out[py, px] = True
    array[:, :, 3] = np.where(out, array[:, :, 3], 0)
    return Image.fromarray(array, "RGBA"), sizes


def largest_component_bbox(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = None
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            n = 0
            x0 = x1 = x
            y0 = y1 = y
            while q:
                cy, cx = q.popleft()
                n += 1
                x0 = min(x0, cx); x1 = max(x1, cx)
                y0 = min(y0, cy); y1 = max(y1, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if best is None or n > best[0]:
                best = (n, x0, y0, x1, y1)
    return best


def foot_span(mask, fraction=0.08):
    ys = np.nonzero(mask.any(axis=1))[0]
    bottom = int(ys.max())
    top = max(int(ys.min()), bottom - max(1, int((bottom - int(ys.min()) + 1) * fraction)))
    by, bx = np.nonzero(mask[top:bottom + 1])
    return int(bx.min()), int(bx.max()), int(bx.max() - bx.min() + 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("用法：promote_clip.py <clip>")
    clip = sys.argv[1]
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if clip not in plan["clips"]:
        raise SystemExit(f"计划中没有 clip：{clip}")
    spec = plan["clips"][clip]
    raw_dir = ROOT / spec["raw_dir"]
    anchor = json.loads((CELLS / "cells.json").read_text(encoding="utf-8"))
    palette = [tuple(c) for c in anchor["palette"]]
    scale = float(anchor["scale"])
    records = []
    for frame in spec["frames"]:
        i = frame["index"]
        raw = raw_dir / f"{clip}-{i:02d}-raw.png"
        if not raw.is_file():
            records.append({"index": i, "missing": raw.relative_to(ROOT).as_posix()})
            continue
        cleaned, sizes = remove_specks(harden_alpha(Image.open(raw).convert("RGBA")), MIN_COMPONENT)
        cleaned = trim(cleaned)
        clean_path = raw_dir / f"{clip}-{i:02d}-clean.png"
        cleaned.save(clean_path)
        out = CELLS / f"{clip}-{i:02d}-cell.png"
        row = stage_cells.build(
            clean_path, out, palette, scale, int(frame["foot_row"]),
            anchor_x=128, cell=256, foot_band=0.08,
        )
        cell = np.array(Image.open(out).convert("RGBA"))
        mask = cell[:, :, 3] > 0
        main = largest_component_bbox(mask)
        body = np.zeros_like(mask)
        if main:
            body[main[2]:main[4] + 1, main[1]:main[3] + 1] = mask[main[2]:main[4] + 1, main[1]:main[3] + 1]
        x0, x1, span = foot_span(body) if main else (0, 0, 0)
        height = main[4] - main[2] + 1 if main else 0
        drift = abs(height - TARGET) / TARGET
        row.update({
            "index": i,
            "raw": raw.relative_to(ROOT).as_posix(),
            "raw_sha256": sha(raw),
            "clean_sha256": sha(clean_path),
            "raw_size": list(Image.open(raw).size),
            "specks_removed": len([s for s in sizes if s < MIN_COMPONENT]),
            "specks_px_removed": sum(s for s in sizes if s < MIN_COMPONENT),
            "height_class": frame["height_class"],
            "stance_gate": frame["stance_gate"],
            "main_height": height,
            "main_width": main[3] - main[1] + 1 if main else 0,
            "stance_08": round(span / height, 4) if height else 0,
            "height_drift": round(drift, 4),
            "height_exception": drift > HEIGHT_TOL,
            "stance_exception": bool(frame["stance_gate"] and height and not (0.65 <= span / height <= 0.80)),
            "top_margin": int(main[2]) if main else None,
            "bottom_margin": 255 - int(main[4]) if main else None,
        })
        records.append(row)
    flags = []
    for row in records:
        if "missing" in row:
            flags.append(f"{row['index']:02d}: 缺 raw")
            continue
        if row["components"] != 1:
            flags.append(f"{row['index']:02d}: 连通块 {row['components']}")
        if row["alpha"] != [0, 255]:
            flags.append(f"{row['index']:02d}: Alpha {row['alpha']}")
        if row["colors"] > 32:
            flags.append(f"{row['index']:02d}: 色数 {row['colors']}")
        if row["height_exception"] and row["height_class"] == "ground":
            flags.append(f"{row['index']:02d}: 站高 {row['main_height']} 偏离 188 超过 8%")
        if row["stance_exception"]:
            flags.append(f"{row['index']:02d}: 站距 {row['stance_08']} 不在 0.65–0.80")
    summary = {
        "clip": clip,
        "group": spec["group"],
        "scale": scale,
        "palette_size": len(palette),
        "frames": records,
        "flags": flags,
        "authority": "root_delegated_by_user",
        "user_approved": False,
    }
    (CELLS / f"{clip}-cells.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({
        "clip": clip,
        "frames": len(records),
        "heights": [r.get("main_height") for r in records],
        "stance": [r.get("stance_08") for r in records],
        "height_exceptions": [r["index"] for r in records if r.get("height_exception")],
        "stance_exceptions": [r["index"] for r in records if r.get("stance_exception")],
        "flags": flags,
    }, ensure_ascii=False, indent=1))
    return 1 if flags else 0


if __name__ == "__main__":
    raise SystemExit(main())
