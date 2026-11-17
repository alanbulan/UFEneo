"""用战斗里的真实待机动画烘出图鉴待机条。

可玩角色在 content/fighters/<id>/canon.json 里已经有 idle clip（多帧图集 +
每帧锚点）。这是真正画出来的待机动作，比重新生成更准，也比位移冒充动画
诚实。本工具把这些帧按图鉴标尺缩放、对齐到同一根点，拼成水平 strip。

输出：assets/fighters/<id>/catalogue/anim-strip.png
      content/roster/catalogue_display.json 里补 strip / frames / idle_source

用法：
    python tools/media/art/catalogue_idle_canon.py            # 全部有 idle 的角色
    python tools/media/art/catalogue_idle_canon.py --only ultraman gomora
    python tools/media/art/catalogue_idle_canon.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
CANVAS_WIDTH = 384
CANVAS_HEIGHT = 256
ROOT_Y = 248

sys.path.insert(0, str(ROOT / "tools/media/art"))
from catalogue_native import apply_palette, build_palette, harden_alpha, trim  # noqa: E402
import catalogue_rescale  # noqa: E402


def _usable(clip) -> dict | None:
    if not isinstance(clip, dict):
        return None
    if not clip.get("texture") or not clip.get("rects"):
        return None
    return clip


def idle_clip(catalogue_id: str) -> dict | None:
    """可玩角色已有的真实 idle：优先 canon.json，其次战斗动画 manifest。

    canon.json 只有一部分角色有；其余已装到游戏里的角色（EX 哥莫拉、
    EX 雷德王、亚刻、布莱泽、欧米伽、泰奥等）的 idle 图集与锚点写在
    assets/fighters/<id>/animations/manifest.json 的 clips.idle 里，
    同样是实机在用的真帧，直接拿来烘图鉴，不重画。
    """
    canon = ROOT / f"content/fighters/{catalogue_id}/canon.json"
    if canon.is_file():
        clip = _usable(json.loads(canon.read_text(encoding="utf-8")).get("idle"))
        if clip is not None:
            return clip
    manifest = ROOT / f"assets/fighters/{catalogue_id}/animations/manifest.json"
    if manifest.is_file():
        clips = json.loads(manifest.read_text(encoding="utf-8")).get("clips") or {}
        return _usable(clips.get("idle"))
    return None


def anchor_of(clip: dict, index: int, rect: list) -> tuple[float, float]:
    anchors = clip.get("anchors") or []
    if len(anchors) > index and len(anchors[index]) >= 2:
        return float(anchors[index][0]), float(anchors[index][1])
    cell = clip.get("cell")
    cell_width = cell if isinstance(cell, int) else int(cell[0])
    return cell_width / 2.0, float(clip.get("anchor_y", rect[3]))


def frame_subject(atlas: Image.Image, rect: list) -> tuple[Image.Image, tuple[int, int]]:
    cell = atlas.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
    cell = harden_alpha(cell)
    box = cell.getchannel("A").getbbox()
    if box is None:
        raise ValueError(f"第 {rect} 帧没有可见像素")
    return cell, box


def build_strip(catalogue_id: str, clip: dict, target_height: int,
                dry_run: bool = False) -> dict:
    atlas_path = ROOT / str(clip["texture"]).removeprefix("res://")
    with Image.open(atlas_path) as handle:
        atlas = handle.convert("RGBA")

    cells: list[Image.Image] = []
    anchors: list[tuple[float, float]] = []
    heights: list[int] = []
    for index, rect in enumerate(clip["rects"]):
        cell, box = frame_subject(atlas, rect)
        cells.append(cell)
        anchors.append(anchor_of(clip, index, rect))
        heights.append(box[3] - box[1])

    # 用中位站高定一个统一倍率：各帧的起伏是原动画自己的，不逐帧拉平。
    scale = target_height / max(1, statistics.median(heights))
    frame_width = max(1, round(cells[0].width * scale))
    frame_height = max(1, round(cells[0].height * scale))
    palette = build_palette(trim(cells[0]))

    resized_cells = [
        apply_palette(harden_alpha(cell.resize((frame_width, frame_height), Image.BOX)), palette)
        for cell in cells
    ]
    anchors_px: list[tuple[int, int]] = []
    for index in range(len(cells)):
        anchor_x, anchor_y = anchors[index]
        anchors_px.append((round(CANVAS_WIDTH / 2.0 - anchor_x * scale),
                           round(ROOT_Y - anchor_y * scale)))

    # 每帧先落在自己的 384 宽画布里，避免宽于画布的帧渗进相邻帧；再按整条
    # 可见轮廓（含尾巴/武器）统一水平居中。脚底和缩放不变，帧间相对位移保留。
    spans = []
    for resized, (left, _) in zip(resized_cells, anchors_px):
        box = resized.getchannel("A").getbbox()
        if box is None:
            raise ValueError("帧没有可见像素")
        spans.append((left + box[0], left + box[2]))
    min_x = min(span[0] for span in spans)
    max_x = max(span[1] for span in spans)
    if max_x - min_x > CANVAS_WIDTH - 4:
        raise ValueError(
            f"{catalogue_id}: 整条可见宽度 {max_x - min_x} 超过画布可用宽度 {CANVAS_WIDTH - 4}")
    shift = round(CANVAS_WIDTH / 2.0 - (min_x + max_x) / 2.0)
    shift = max(shift, 2 - min_x)
    shift = min(shift, CANVAS_WIDTH - 2 - max_x)

    strip = Image.new("RGBA", (CANVAS_WIDTH * len(cells), CANVAS_HEIGHT), (0, 0, 0, 0))
    placed: list[dict] = []
    for index, resized in enumerate(resized_cells):
        left, top = anchors_px[index]
        left += shift
        frame = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        frame.alpha_composite(resized, (left, top))
        strip.alpha_composite(frame, (CANVAS_WIDTH * index, 0))
        placed.append({"frame": index, "left": left, "top": top})

    out = ROOT / f"assets/fighters/{catalogue_id}/catalogue/anim-strip.png"
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        strip.save(out)
    return {
        "id": catalogue_id,
        "frames": len(cells),
        "target_height": target_height,
        "subject_heights": heights,
        "scale": round(scale, 4),
        "size": [strip.width, strip.height],
        "placed": placed,
        "out": out.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest() if not dry_run else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", help="只处理指定 id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    scale = catalogue_rescale.load_scale()
    index = json.loads((ROOT / "content/roster/index.json").read_text(encoding="utf-8"))
    kind_of = {row["id"]: row.get("kind", "") for row in index["entries"]}
    display = json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))

    targets = args.only or sorted(
        path.parent.name for path in (ROOT / "content/fighters").glob("*/canon.json"))
    results = []
    for catalogue_id in targets:
        if catalogue_id not in display["entries"]:
            continue
        clip = idle_clip(catalogue_id)
        if clip is None:
            results.append({"id": catalogue_id, "status": "no_idle_clip"})
            continue
        height, basis = catalogue_rescale.target_height(
            scale, catalogue_id, kind_of.get(catalogue_id, ""))
        report = build_strip(catalogue_id, clip, height, args.dry_run)
        report["status"] = "baked" if not args.dry_run else "would_bake"
        report["basis"] = basis
        results.append(report)
        if not args.dry_run:
            from catalogue_store import update_entry
            update_entry(catalogue_id, {
                "strip": "res://" + report["out"],
                "frames": report["frames"],
                "strip_sha256": report["sha256"],
                "idle_source": "battle_canon_idle",
            })

    counts: dict[str, int] = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    for row in results:
        if row["status"].startswith(("baked", "would")):
            print(f"  {row['id']:16s} {row['frames']} 帧  {row['size'][0]}×{row['size'][1]}  x{row['scale']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
