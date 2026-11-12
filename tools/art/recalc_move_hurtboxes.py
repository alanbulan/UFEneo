"""按已装招式图集重算 moves/*.json 每帧 hurtboxes。

整帧重做后 sprite 数量、身形与落格比例都变了：旧 hurtboxes 来自旧图或
旧 sprite，未映射的新帧甚至没有该键（UfeMoveData.validate 会直接拒收整
招）。本工具按 manifest 的 rects 装载最大连通块，用 band_boxes 三等分
重算，再按 frame["sprite"] 写回全部帧；其它字段（sprite/dx/dy/hitboxes/
cancel/events/shots/target/电影化键）一律原样保留。

不改伤害、判定、节奏，也不碰 state_frames.json（那是
tools/rebuild/body-rescale/recalc_hurtboxes.py 的职责）。

用法：
    .venv/bin/python tools/art/recalc_move_hurtboxes.py --fighter ultraman-zero \
        --move special --move special2 --move special3 --move air_special --write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/art"))
from derive_fighter_data import band_boxes, largest_component, load_mask  # noqa: E402


def boxes_for_clip(manifest: dict, clip_id: str,
                   cache: dict[str, Image.Image]) -> list[list[list[int]]]:
    clip = manifest["clips"][clip_id]
    texture = clip["texture"].replace("res://", "")
    atlas = cache.get(texture)
    if atlas is None:
        atlas = Image.open(ROOT / texture).convert("RGBA")
        cache[texture] = atlas
    ax, ay = clip.get("anchor", manifest.get("anchor", [96, 184]))
    boxes = []
    for rect in clip["rects"]:
        mask = largest_component(load_mask(atlas, rect))
        boxes.append(band_boxes(mask, ax, ay))
    return boxes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", required=True)
    ap.add_argument("--move", action="append", required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    manifest = json.loads(
        (ROOT / f"assets/fighters/{args.fighter}/animations/manifest.json")
        .read_text(encoding="utf-8"))
    cache: dict[str, Image.Image] = {}
    for move_id in args.move:
        path = ROOT / f"content/fighters/{args.fighter}/moves/{move_id}.json"
        move = json.loads(path.read_text(encoding="utf-8"))
        if move_id not in manifest["clips"]:
            raise SystemExit(f"manifest 无 clip：{move_id}")
        boxes = boxes_for_clip(manifest, move_id, cache)
        changed = missing = 0
        for frame in move["frames"]:
            sprite = int(frame["sprite"])
            if sprite >= len(boxes):
                missing += 1
                continue
            if frame.get("hurtboxes") != boxes[sprite]:
                changed += 1
            if args.write:
                frame["hurtboxes"] = boxes[sprite]
                # 重映射后的首 tick 帧可能缺空键，校验会拒收整招。
                for key in ("hitboxes", "cancel", "events"):
                    frame.setdefault(key, [])
                frame.setdefault("dx", 0)
                frame.setdefault("dy", 0)
        print(f"{args.fighter}/{move_id}: {len(move['frames'])} 帧，"
              f"hurtboxes 变更 {changed}，越界 {missing}，图集 sprite {len(boxes)}")
        if missing:
            raise SystemExit(f"{move_id} 有帧 sprite 超出图集 rect 数，先重装图集")
        if args.write:
            path.write_text(json.dumps(move, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
    if not args.write:
        print("未写入（加 --write 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
