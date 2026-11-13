"""检查已生成动作原图：实收尺寸、Alpha、SHA、站立高度、眼宽、单连通。

只读；把结果写 reports/raw-check.json，供选帧与记录使用。
用法：
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/verify_frames.py --clip idle
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path.insert(0, str(ROOT / "tools/media/art"))
from catalogue_native import harden_alpha, trim  # noqa: E402

FIGHTER = "ultraman-zero__ultimate"
STAGE = ROOT / "art/fighters" / FIGHTER / "stage1"
REPORTS = ROOT / "tools/rebuild" / FIGHTER / "reports"


def components(mask: np.ndarray) -> int:
    seen = np.zeros_like(mask, bool)
    count = 0
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        count += 1
        queue = deque([(y, x)])
        seen[y, x] = True
        while queue:
            cy, cx = queue.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                        and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
    return count


def inspect(path: Path) -> dict:
    raw = Image.open(path)
    alpha = np.array(raw.convert("RGBA"))[:, :, 3]
    solid_image = trim(harden_alpha(raw.convert("RGBA")))
    array = np.array(solid_image)
    mask = array[:, :, 3] > 0
    r, g, b = array[:, :, 0].astype(int), array[:, :, 1].astype(int), array[:, :, 2].astype(int)
    eye = (r > 180) & (g > 140) & (b < 110) & mask
    eye_xs = np.nonzero(eye)[1]
    eye_ys = np.nonzero(eye)[0]
    result = {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "actual_size": list(raw.size),
        "mode": raw.mode,
        "alpha_range": [int(alpha.min()), int(alpha.max())],
        "solid_size": list(solid_image.size),
        "components": components(mask),
    }
    if eye_xs.size:
        eye_y = int(round(eye_ys.mean()))
        eye_x = int(round(eye_xs.mean()))
        band = mask[:, max(0, eye_x - 134):eye_x + 135]
        top = int(np.nonzero(band.any(axis=1))[0].min())
        sole = int(np.nonzero(mask.any(axis=1))[0].max())
        row = mask[eye_y]
        runs, start = [], None
        for x, v in enumerate(row):
            if v and start is None:
                start = x
            elif not v and start is not None:
                runs.append((start, x - 1))
                start = None
        if start is not None:
            runs.append((start, len(row) - 1))
        face = [run for run in runs if run[0] <= eye_x <= run[1]]
        result.update({
            "eye_y": eye_y,
            "eye_x": eye_x,
            "eye_width": int(eye_xs.max() - eye_xs.min() + 1),
            "face_width": int(face[0][1] - face[0][0] + 1) if face else None,
            "standing": sole - top + 1,
            "scale_for_172": round(172 / (sole - top + 1), 6),
        })
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", required=True)
    args = ap.parse_args()
    frame_dir = STAGE / args.clip / "frames"
    paths = sorted(p for p in frame_dir.glob("*.png"))
    if not paths:
        raise SystemExit(f"{args.clip}: frames 目录没有 PNG")
    rows = [inspect(p) for p in paths]
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"{args.clip}-raw-check.json"
    out.write_text(json.dumps({"clip": args.clip, "frames": rows},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(row["path"].split("/")[-1], row["actual_size"], row["alpha_range"],
              "components", row["components"], "standing", row.get("standing"),
              "eye_w", row.get("eye_width"), "face_w", row.get("face_width"))
    print("report", out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
