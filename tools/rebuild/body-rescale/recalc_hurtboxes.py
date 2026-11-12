"""按重落格后的图集重算 state_frames hurtboxes，保留节奏条目结构。

2026-11-11 体型重落格任务配套：重落改变像素几何，受击框须按新图集重算；
state_frames 节奏展开（74f99d6f5）的条目数、sprite 序列、dx/dy、cancel、
events 等节奏字段一律原样保留。已核对七角色节奏版满足：
- 同 sprite 重复条目的 hurtboxes 完全一致（逐 sprite 重算再复用安全）；
- 状态帧 hitboxes 全空、events 全空（derive 原生成口径本就如此）。

每 clip：按 manifest rects 装载最大连通块，band_boxes 三等分重算 hurtboxes，
按 sprite 写回全部条目（entries[i]["hurtboxes"] = boxes[sprite]）。

用法：
    .venv/bin/python tools/rebuild/body-rescale/recalc_hurtboxes.py --fighter ultraman-king --write
    .venv/bin/python tools/rebuild/body-rescale/recalc_hurtboxes.py --fighter ultraman-king  # 干跑对比
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/art"))
from derive_fighter_data import band_boxes, largest_component, load_mask  # noqa: E402

FIGHTERS = [
    "ultraman-king", "father-of-ultra", "ultraman-zero", "ultraman-justice",
    "zoffy", "ultraman-gaia", "mother-of-ultra",
]


def recalc(fighter: str, write: bool) -> None:
    manifest = json.loads(
        (REPO / f"assets/fighters/{fighter}/animations/manifest.json")
        .read_text(encoding="utf-8"))
    sf_path = REPO / f"content/fighters/{fighter}/state_frames.json"
    sf = json.loads(sf_path.read_text(encoding="utf-8"))
    clips = manifest["clips"]
    tex_cache: dict[str, Image.Image] = {}
    changed = same = missing_clips = 0

    for clip_id, entries in sf.items():
        clip = clips.get(clip_id)
        if clip is None:
            missing_clips += 1
            print(f"  跳过（manifest 无 clip）：{clip_id}")
            continue
        tex = clip["texture"].replace("res://", "")
        im = tex_cache.get(tex)
        if im is None:
            im = Image.open(REPO / tex).convert("RGBA")
            tex_cache[tex] = im
        rects = clip["rects"]
        cax, cay = clip.get("anchor", manifest.get("anchor", [96, 184]))
        boxes: dict[int, list] = {}
        for i, r in enumerate(rects):
            mask = largest_component(load_mask(im, r))
            boxes[i] = band_boxes(mask, cax, cay)
        for e in entries:
            s = e.get("sprite", 0)
            if s >= len(rects):
                continue
            new = boxes[s]
            if e.get("hurtboxes") != new:
                changed += 1
            else:
                same += 1
            if write:
                e["hurtboxes"] = new

    print(f"{fighter}: 条目 hurtboxes 变更 {changed} 不变 {same} "
          f"缺clip {missing_clips}")
    if write:
        sf_path.write_text(json.dumps(sf, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        print(f"已写回 {sf_path.relative_to(REPO)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", default="")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    fighters = [args.fighter] if args.fighter else FIGHTERS
    for f in fighters:
        recalc(f, args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
