"""赛罗基础形态 form_switch 6 帧：落格、拼 atlas、只追加 manifest 条目。

输入是本目录 frames/ 下 6 张已验收的 MCP 生成原图；唯一身份参考为
art/fighters/ultraman-zero/stage1/cells/idle-00-cell.png（256×256，根点
[128,248]，脚底 247，站高 186）。落格口径：

- 全身六帧共用一个固定源比例：186 ÷ 第 0 帧实心高；不逐帧重标定。
- 先硬化 Alpha（阈值 128）并裁实心轮廓，再用 forge_backend 的 kCentroid
  降采样、整图映射到 idle-00-cell 的 30 色锚色板。
- 每帧水平按脚底 8% 带重心对到 x=128，脚底贴第 247 行；格 256×256。
- 只新增 assets/fighters/ultraman-zero/animations/form_switch/atlas.png 与
  manifest.json 的 form_switch 条目；不改其它片段、顶层字段或 definition。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools/media/art"))
sys.path.insert(0, str(ROOT / "tools/rebuild/shared"))

from catalogue_native import apply_palette, harden_alpha, trim  # noqa: E402
from forge_backend import _kcentroid_downscale  # noqa: E402

FIGHTER = "ultraman-zero"
IDLE = ROOT / "art/fighters" / FIGHTER / "stage1/cells/idle-00-cell.png"
CELLS_DIR = ROOT / "art/fighters" / FIGHTER / "stage1/cells"
ANIM_DIR = ROOT / "assets/fighters" / FIGHTER / "animations"
CLIP = "form_switch"
CELL = 256
ANCHOR = [128, 248]
FOOT_ROW = 247
TARGET_HEIGHT = 186
HEAD_TOLERANCE = 0.08
ADJACENT_TOLERANCE = 0.10

FRAMES = [
    ("form_switch-00", HERE / "frames/form_switch-00-raw.png"),
    ("form_switch-01", HERE / "frames/form_switch-01-raw-2.png"),
    ("form_switch-02", HERE / "frames/form_switch-02-raw.png"),
    ("form_switch-03", HERE / "frames/form_switch-03-raw.png"),
    ("form_switch-04", HERE / "frames/form_switch-04-raw.png"),
    ("form_switch-05", HERE / "frames/form_switch-05-raw-2.png"),
]

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_solid(path: Path) -> Image.Image:
    return trim(harden_alpha(Image.open(path).convert("RGBA")))


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


def idle_palette() -> list[tuple[int, int, int]]:
    image = Image.open(IDLE).convert("RGBA")
    array = np.array(image)
    visible = array[:, :, 3] > 0
    return [tuple(int(c) for c in row) for row in
            np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0)]


def place(solid: Image.Image, scale: float, palette: list) -> tuple[Image.Image, dict]:
    target = (max(1, round(solid.width * scale)), max(1, round(solid.height * scale)))
    reduced = _kcentroid_downscale(solid, target[0], target[1], detail_bias=False)
    reduced = harden_alpha(trim(reduced))
    reduced = apply_palette(reduced, palette)
    mask = np.array(reduced)[:, :, 3] > 0
    center = foot_center(mask)
    left = round(ANCHOR[0] - center)
    top = ANCHOR[1] - reduced.height
    canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    canvas.alpha_composite(reduced, (left, top))
    array = np.array(canvas)
    visible = array[:, :, 3] > 0
    ys, xs = np.where(visible)
    colors = np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0)
    return canvas, {
        "target": list(target),
        "reduced_bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "height": int(ys.max() - ys.min() + 1),
        "width": int(xs.max() - xs.min() + 1),
        "foot_row": int(ys.max()),
        "foot_center": round(float(center), 3),
        "left": left,
        "top": top,
        "colors": int(len(colors)),
        "alpha_values": sorted(int(v) for v in np.unique(array[:, :, 3])),
        "components": components(visible),
        "touches_border": bool(xs.min() == 0 or ys.min() == 0
                               or xs.max() == CELL - 1 or ys.max() == CELL - 1),
    }


def build(dry_run: bool) -> int:
    palette = idle_palette()
    if len(palette) > 32:
        raise SystemExit(f"idle 色板 {len(palette)} 色，超过 32")

    solids = [load_solid(path) for _, path in FRAMES]
    scale = TARGET_HEIGHT / solids[0].height
    records = []
    failures: list[str] = []
    cells: list[Image.Image] = []
    for (name, raw), solid in zip(FRAMES, solids):
        canvas, metrics = place(solid, scale, palette)
        cells.append(canvas)
        record = {
            "frame": name,
            "raw": raw.relative_to(ROOT).as_posix(),
            "raw_sha256": sha256_file(raw),
            "raw_size": list(Image.open(raw).size),
            "source_solid": list(solid.size),
            **metrics,
            "scale": round(scale, 9),
        }
        record["cell"] = f"art/fighters/{FIGHTER}/stage1/cells/{name}-cell.png"
        records.append(record)
        drift = abs(metrics["height"] - TARGET_HEIGHT) / TARGET_HEIGHT
        record["height_drift"] = round(drift, 4)
        if drift > HEAD_TOLERANCE:
            failures.append(f"{name}: 站高 {metrics['height']} 偏离锚 {TARGET_HEIGHT} "
                            f"超过 8%")
        if metrics["height"] > 188:
            failures.append(f"{name}: 站高 {metrics['height']} 超过 188")
        if metrics["foot_row"] != FOOT_ROW:
            failures.append(f"{name}: 脚底行 {metrics['foot_row']}（应 {FOOT_ROW}）")
        if metrics["alpha_values"] != [0, 255]:
            failures.append(f"{name}: Alpha 不是二值 {metrics['alpha_values']}")
        if metrics["components"] != 1:
            failures.append(f"{name}: 连通块 {metrics['components']}（应 1）")
        if metrics["colors"] > 32:
            failures.append(f"{name}: 色数 {metrics['colors']} 超过 32")
        if metrics["touches_border"]:
            failures.append(f"{name}: 主体触及格边")
    for previous, current in zip(records, records[1:]):
        delta = abs(current["height"] - previous["height"]) / previous["height"]
        current["adjacent_delta"] = round(delta, 4)
        if delta > ADJACENT_TOLERANCE:
            failures.append(f"{current['frame']}: 与前一帧身高突变 {delta:.1%}")
    # 第 0 帧用同一比例必须落在锚站高 186。
    if records[0]["height"] != TARGET_HEIGHT:
        failures.append(f"第 0 帧站高 {records[0]['height']} 不是锚站高 {TARGET_HEIGHT}")

    report = {
        "fighter": FIGHTER,
        "clip": CLIP,
        "anchor": ANCHOR,
        "cell": CELL,
        "foot_row": FOOT_ROW,
        "idle": IDLE.relative_to(ROOT).as_posix(),
        "idle_sha256": sha256_file(IDLE),
        "idle_height": TARGET_HEIGHT,
        "palette": [list(c) for c in palette],
        "palette_size": len(palette),
        "scale": round(scale, 9),
        "scale_source": FRAMES[0][0],
        "frames": records,
        "failures": failures,
    }

    if dry_run:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 1 if failures else 0

    CELLS_DIR.mkdir(parents=True, exist_ok=True)
    for record, canvas in zip(records, cells):
        path = ROOT / record["cell"]
        canvas.save(path)
        record["cell_sha256"] = sha256_file(path)

    atlas = Image.new("RGBA", (CELL * len(cells), CELL), (0, 0, 0, 0))
    for index, canvas in enumerate(cells):
        atlas.alpha_composite(canvas, (CELL * index, 0))
    clip_dir = ANIM_DIR / CLIP
    clip_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = clip_dir / "atlas.png"
    atlas.save(atlas_path)
    atlas_sha = sha256_file(atlas_path)

    manifest_path = ANIM_DIR / "manifest.json"
    backup_dir = Path(tempfile.mkdtemp(prefix="form-switch-manifest-"))
    backup_path = backup_dir / "manifest.json"
    shutil.copy2(manifest_path, backup_path)
    before = json.loads(backup_path.read_text(encoding="utf-8"))
    if CLIP in before.get("clips", {}):
        raise SystemExit(f"manifest 已存在 {CLIP} 条目；本批只允许新增")
    after = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = {
        "texture": f"res://assets/fighters/{FIGHTER}/animations/{CLIP}/atlas.png",
        "cell": CELL,
        "anchor": list(ANCHOR),
        "anchor_y": ANCHOR[1],
        "anchors": [list(ANCHOR) for _ in cells],
        "rects": [[CELL * i, 0, CELL, CELL] for i in range(len(cells))],
        "ticks": [10 for _ in cells],
        "loop": False,
        "atlas_sha256": atlas_sha,
    }
    after["clips"][CLIP] = entry
    manifest_path.write_text(
        json.dumps(after, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 比对：其它片段条目、数量、顶层字段与备份一致。
    reloaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    other_before = {k: v for k, v in before["clips"].items() if k != CLIP}
    other_after = {k: v for k, v in reloaded["clips"].items() if k != CLIP}
    if other_before != other_after:
        raise SystemExit("manifest 其它片段被改动")
    if len(reloaded["clips"]) != len(before["clips"]) + 1:
        raise SystemExit("manifest 片段数量变化不是 +1")
    for key in before:
        if key == "clips":
            continue
        if before[key] != reloaded.get(key):
            raise SystemExit(f"manifest 顶层字段被改动：{key}")
    if set(reloaded) != set(before) | {"clips"} and set(reloaded) != set(before):
        raise SystemExit("manifest 顶层键集合被改动")
    for clip, clip_entry in other_after.items():
        atlas_file = ROOT / "assets/fighters" / FIGHTER / "animations" / clip / "atlas.png"
        if not atlas_file.is_file():
            raise SystemExit(f"{clip}: atlas 缺失 {atlas_file}")
        if sha256_file(atlas_file) != clip_entry.get("atlas_sha256"):
            raise SystemExit(f"{clip}: atlas SHA 与 manifest 不一致")

    report["atlas"] = {
        "path": atlas_path.relative_to(ROOT).as_posix(),
        "size": list(atlas.size),
        "sha256": atlas_sha,
    }
    report["manifest"] = {
        "path": manifest_path.relative_to(ROOT).as_posix(),
        "backup": str(backup_path),
        "clip_count_before": len(before["clips"]),
        "clip_count_after": len(reloaded["clips"]),
        "other_clips_unchanged": True,
        "top_level_unchanged": True,
        "form_switch": entry,
    }
    (HERE / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return build(args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
