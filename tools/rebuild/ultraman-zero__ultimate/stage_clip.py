"""究极赛罗逐 clip 落格：固定比例、整图色板、硬门与报告。

按基础赛罗 2026-11-12 的纯人物整帧落格口径：
- 全套动作帧共用一个固定源比例（189 / 基准站立帧实心高）；不逐帧重标定。
- harden_alpha(128) → trim → forge_backend._kcentroid_downscale → 再硬化裁切
  → 整图映射到待机锚的 32 色硬色板。
- 格、根点、脚底行逐 clip 由 plan 指定；水平按脚底 8% 带重心对到根点 x，
  垂直按脚底贴 foot_row。
- 站姿帧核：整帧高相对 189、头部列带站高相对 172；蹲/腾空等在 plan 的
  pose_exceptions 登记，不因此免掉 Alpha/连通/色数/脚底硬门。

用法：
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/stage_clip.py \
        --plan tools/rebuild/ultraman-zero__ultimate/plans/form_switch.json
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
sys.path.insert(0, str(ROOT / "tools/rebuild/shared"))
from catalogue_native import apply_palette, harden_alpha, trim  # noqa: E402
from forge_backend import _kcentroid_downscale  # noqa: E402

FIGHTER = "ultraman-zero__ultimate"
CELLS_DIR = ROOT / "art/fighters" / FIGHTER / "stage1/cells"
CELLS_JSON = CELLS_DIR / "cells.json"
IDLE = CELLS_DIR / "idle-00-cell.png"
REPORT_DIR = ROOT / "tools/rebuild" / FIGHTER / "reports"
TARGET_FULL = 189
TARGET_STANDING = 172
HEAD_BAND = 26
FULL_TOL = 0.08
STAND_TOL = 0.08
ADJ_TOL = 0.10
DIFF_MIN = 0.03


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_solid(path: Path) -> Image.Image:
    return trim(harden_alpha(Image.open(path).convert("RGBA")))


def palette_from_idle() -> list[tuple[int, int, int]]:
    array = np.array(Image.open(IDLE).convert("RGBA"))
    visible = array[:, :, 3] > 0
    colors = np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0)
    return [tuple(int(c) for c in row) for row in colors]


def foot_center(mask: np.ndarray, fraction: float = 0.08) -> float:
    ys = np.nonzero(mask.any(axis=1))[0]
    bottom = int(ys.max())
    top = max(int(ys.min()), bottom - max(1, int((bottom - int(ys.min()) + 1) * fraction)))
    band = mask[top:bottom + 1]
    total = band.sum()
    if not total:
        return mask.shape[1] / 2.0
    return float((band.sum(axis=0) * np.arange(band.shape[1])).sum() / total)


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


def eye_center_x(array: np.ndarray) -> int | None:
    r = array[:, :, 0].astype(int)
    g = array[:, :, 1].astype(int)
    b = array[:, :, 2].astype(int)
    eye = (r > 180) & (g > 140) & (b < 110) & (array[:, :, 3] > 0)
    xs = np.nonzero(eye)[1]
    return int(round(xs.mean())) if xs.size else None


def foot_runs(mask: np.ndarray, foot_row: int) -> dict:
    sub = mask[max(0, foot_row - 4):foot_row + 1]
    col = sub.any(axis=0)
    runs, start = [], None
    for x, v in enumerate(col):
        if v and start is None:
            start = x
        elif not v and start is not None:
            runs.append((start, x - 1))
            start = None
    if start is not None:
        runs.append((start, len(col) - 1))
    runs = [(s, e) for s, e in runs if e - s >= 3]
    return {
        "feet": [{"span": [int(s), int(e)],
                  "bottom": int(np.nonzero(mask[:, s:e + 1].any(axis=1))[0].max())}
                 for s, e in runs],
        "outer_span": (max(e for _, e in runs) - min(s for s, _ in runs) + 1) if runs else 0,
    }


def diff_ratio(prev: np.ndarray, cur: np.ndarray) -> float:
    a = prev[:, :, 3] > 0
    b = cur[:, :, 3] > 0
    union = np.logical_or(a, b).sum()
    return float(np.logical_xor(a, b).sum() / union) if union else 0.0


def stage_frame(source: Path, scale: float, cell: int, root: list[int],
                foot_row: int, palette: list) -> tuple[Image.Image, dict]:
    solid = load_solid(source)
    target = (max(1, round(solid.width * scale)), max(1, round(solid.height * scale)))
    reduced = _kcentroid_downscale(solid, target[0], target[1], detail_bias=False)
    reduced = harden_alpha(trim(reduced))
    reduced = apply_palette(reduced, palette)
    mask = np.array(reduced)[:, :, 3] > 0
    center = foot_center(mask)
    raw_left = round(root[0] - center)
    left = min(max(raw_left, 4), cell - 4 - reduced.width)
    clamped = left != raw_left
    top = foot_row + 1 - reduced.height
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    canvas.alpha_composite(reduced, (left, top))
    array = np.array(canvas)
    visible = array[:, :, 3] > 0
    center_final = foot_center(visible)
    ys, xs = np.where(visible)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    eye_x = eye_center_x(array)
    standing = None
    head_top = None
    if eye_x is not None:
        band = visible[:, max(0, eye_x - HEAD_BAND):eye_x + HEAD_BAND + 1]
        head_top = int(np.nonzero(band.any(axis=1))[0].min())
        standing = foot_row - head_top + 1
    feet = foot_runs(visible, int(ys.max()))
    colors = np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0)
    margins = {
        "left": bbox[0], "top": bbox[1],
        "right": cell - 1 - bbox[2], "bottom": cell - 1 - bbox[3],
    }
    return canvas, {
        "source_solid": [solid.width, solid.height],
        "target": list(target),
        "bbox": bbox,
        "full_height": int(ys.max() - ys.min() + 1),
        "width": int(xs.max() - xs.min() + 1),
        "foot_row": int(ys.max()),
        "foot_center": round(float(center_final), 3),
        "foot_center_offset": round(float(center_final) - root[0], 3),
        "horizontal_clamped": bool(clamped),
        "feet": feet["feet"],
        "foot_outer_span": feet["outer_span"],
        "stance_ratio": round(feet["outer_span"] / standing, 4) if standing else None,
        "eye_x": eye_x,
        "head_top_y": head_top,
        "standing_height": standing,
        "colors": int(len(colors)),
        "alpha": sorted(int(v) for v in np.unique(array[:, :, 3])),
        "components": components(visible),
        "margins": margins,
        "touches_border": bool(bbox[0] == 0 or bbox[1] == 0
                               or bbox[2] == cell - 1 or bbox[3] == cell - 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    args = ap.parse_args()
    plan = json.loads((ROOT / args.plan).read_text(encoding="utf-8"))
    clip = plan["clip"]
    cell = int(plan.get("cell", 256))
    root = [int(v) for v in plan.get("root", [128, 248])]
    foot_row = int(plan.get("foot_row", 247))
    scale = float(plan["scale"])
    pose_exceptions = set(plan.get("pose_exceptions", []))
    adjacent_exceptions = {tuple(pair) for pair in plan.get("adjacent_exceptions", [])}
    palette = palette_from_idle()
    failures: list[str] = []
    records = []
    cells = []

    for item in plan["frames"]:
        idx = str(item["idx"])
        source = ROOT / item["source"]
        frame_foot_row = int(item.get("foot_row", foot_row))
        canvas, metrics = stage_frame(source, scale, cell, root, frame_foot_row, palette)
        cells.append(canvas)
        record = {
            "clip": clip,
            "frame": f"{clip}-{idx}",
            "idx": idx,
            "raw": rel(source),
            "raw_sha256": sha256(source),
            "raw_size": list(Image.open(source).size),
            "raw_alpha_range": list(Image.open(source).getchannel("A").getextrema()),
            "pose": item.get("pose", "standing"),
            "scale": round(scale, 9),
            **metrics,
            "cell": rel(CELLS_DIR / f"{clip}-{idx}-cell.png"),
        }
        drift_full = abs(record["full_height"] - TARGET_FULL) / TARGET_FULL
        record["full_height_drift"] = round(drift_full, 4)
        if idx in pose_exceptions:
            record["pose_exception"] = item.get("pose", "standing")
        else:
            if drift_full > FULL_TOL:
                failures.append(f"{clip}-{idx}: 整帧高 {record['full_height']} 偏离 {TARGET_FULL} 超 8%")
            if record["standing_height"] is not None:
                drift_stand = abs(record["standing_height"] - TARGET_STANDING) / TARGET_STANDING
                record["standing_drift"] = round(drift_stand, 4)
                if drift_stand > STAND_TOL:
                    failures.append(f"{clip}-{idx}: 站高 {record['standing_height']} 偏离 {TARGET_STANDING} 超 8%")
        if record["foot_row"] != frame_foot_row:
            failures.append(f"{clip}-{idx}: 脚底行 {record['foot_row']}（应 {frame_foot_row}）")
        if record["alpha"] != [0, 255]:
            failures.append(f"{clip}-{idx}: Alpha 非二值 {record['alpha']}")
        if record["components"] != 1:
            failures.append(f"{clip}-{idx}: 连通块 {record['components']}（应 1）")
        if record["colors"] > 32:
            failures.append(f"{clip}-{idx}: 色数 {record['colors']} 超 32")
        if record["touches_border"]:
            failures.append(f"{clip}-{idx}: 主体触及格边")
        if abs(record["foot_center"] - root[0]) > 2 and not record["horizontal_clamped"]:
            failures.append(f"{clip}-{idx}: 脚底重心 {record['foot_center']} 偏离根点 x {root[0]} 超 2 px")
        records.append(record)

    for prev, cur in zip(records, records[1:]):
        if "pose_exception" in prev or "pose_exception" in cur:
            if (prev["idx"], cur["idx"]) not in adjacent_exceptions:
                cur["adjacent_height_delta"] = None
                continue
        delta = abs(cur["full_height"] - prev["full_height"]) / prev["full_height"]
        cur["adjacent_height_delta"] = round(delta, 4)
        if delta > ADJ_TOL and (prev["idx"], cur["idx"]) not in adjacent_exceptions:
            failures.append(f"{clip}-{cur['idx']}: 与前一帧整帧高突变 {delta:.1%}")

    arrays = [np.array(c) for c in cells]
    for (prev, cur), a, b in zip(zip(records, records[1:]), arrays, arrays[1:]):
        ratio = diff_ratio(a, b)
        cur["adjacent_pixel_diff"] = round(ratio, 4)
        if ratio < DIFF_MIN and (prev["idx"], cur["idx"]) not in adjacent_exceptions:
            failures.append(f"{clip}-{cur['idx']}: 与前一帧仅 {ratio:.1%} 像素差，疑似复制姿势")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "fighter": FIGHTER,
        "clip": clip,
        "plan": args.plan,
        "cell": cell,
        "root": root,
        "foot_row": foot_row,
        "idle": rel(IDLE),
        "idle_sha256": sha256(IDLE),
        "palette_size": len(palette),
        "palette": [list(c) for c in palette],
        "scale": round(scale, 9),
        "scale_rule": "固定源比例；本形态动作帧共用，不逐帧重标定",
        "target_full_height": TARGET_FULL,
        "target_standing_height": TARGET_STANDING,
        "frames": records,
        "failures": failures,
    }

    if plan.get("dry_run", False):
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 1 if failures else 0

    CELLS_DIR.mkdir(parents=True, exist_ok=True)
    for record, canvas in zip(records, cells):
        path = ROOT / record["cell"]
        canvas.save(path)
        record["cell_sha256"] = sha256(path)

    # contact sheet: 2× nearest-neighbour per frame, wrap after 8 columns.
    cols = min(8, len(cells))
    rows = (len(cells) + cols - 1) // cols
    preview = Image.new("RGBA", (cols * cell * 2, rows * cell * 2), (238, 238, 238, 255))
    for i, canvas in enumerate(cells):
        big = canvas.resize((cell * 2, cell * 2), Image.Resampling.NEAREST)
        preview.alpha_composite(big, ((i % cols) * cell * 2, (i // cols) * cell * 2))
    contact = REPORT_DIR / f"{clip}-contact.png"
    preview.save(contact)
    report["contact_sheet"] = rel(contact)
    report["contact_sheet_sha256"] = sha256(contact)

    existing = json.loads(CELLS_JSON.read_text(encoding="utf-8")) if CELLS_JSON.is_file() else {}
    frames = [f for f in existing.get("frames", [])
              if not (isinstance(f, dict) and f.get("clip") == clip)]
    frames.extend(records)
    existing["frames"] = frames
    existing.setdefault("fighter", FIGHTER)
    existing.setdefault("canvas", [cell, cell])
    existing.setdefault("root", root)
    existing.setdefault("baseline", foot_row + 1)
    existing.setdefault("foot_row", foot_row)
    existing.setdefault("target_standing_height", TARGET_STANDING)
    existing["action_scale"] = round(scale, 9)
    existing["action_scale_status"] = "冻结：本形态动作帧共用此比例；不逐帧重标定"
    existing["anchor"] = root
    existing["cell"] = [cell, cell]
    CELLS_JSON.write_text(
        json.dumps(existing, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    report_path = REPORT_DIR / f"{clip}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({
        "clip": clip,
        "frames": len(records),
        "scale": report["scale"],
        "heights": [r["full_height"] for r in records],
        "standing": [r["standing_height"] for r in records],
        "colors": [r["colors"] for r in records],
        "components": [r["components"] for r in records],
        "diff": [r.get("adjacent_pixel_diff") for r in records],
        "failures": failures,
        "report": rel(report_path),
        "contact": report["contact_sheet"],
    }, ensure_ascii=False, indent=1))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
