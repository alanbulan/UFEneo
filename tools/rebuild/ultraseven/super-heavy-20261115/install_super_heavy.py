#!/usr/bin/env python3
"""安装赛文 2026-11-15 头标超重击重做批次的两段人物图集。

只更新 crush_charge / crush_charged 的 atlas 与 manifest 条目；不改招式数值、
命中框、状态模拟或旧赛文示范批次。所有帧都必须先由 stage_cells.py 落成 256 格。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/art"))
from install_cells import build_atlas, sha256_file  # noqa: E402

BATCH = ROOT / "art/fighters/ultraseven/stage1/rework-20261115"
PROCESSED = BATCH / "processed/crush"
ANIM = ROOT / "assets/fighters/ultraseven/animations"
MANIFEST = ANIM / "manifest.json"

CLIPS = {
    "crush_charge": {
        "frames": ["crush_charge-01", "crush_charge-02", "crush_charge-03"],
        "ticks": [20, 12, 8],
        "extra": {"driven_by": "crush_hold"},
        "role": "摸冠→摘下→持镖压低蓄力",
    },
    "crush_charged": {
        "frames": [
            "crush_charged-01", "crush_charged-02", "crush_charged-03",
            "crush_charged-04", "crush_charged-05", "crush_charged-06",
        ],
        "ticks": [6, 6, 4, 4, 7, 8],
        "extra": {"timeline_driven": True},
        "role": "持镖后拉→送髋→头标命中→贯切→收镖→装回复位",
    },
}


def install(*, dry_run: bool) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clips = manifest["clips"]
    review = {
        "by": "root_delegated_by_user",
        "date": "2026-11-15",
        "batch": "art/fighters/ultraseven/stage1/rework-20261115/manifest.json",
        "user_approved": False,
        "status": "pending_user_visual_review",
        "note": "用户已确认摘头标、手持蓄力、头标挥出的动作方向；本批图像尚未完成用户美术签收。",
    }
    for clip, spec in CLIPS.items():
        paths = [PROCESSED / f"{name}-cell.png" for name in spec["frames"]]
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            raise SystemExit(f"缺少已落格帧：{missing}")
        atlas = build_atlas(paths, 256, 256)
        out = ANIM / clip / "atlas.png"
        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            atlas.save(out)
        entry = dict(clips.get(clip, {}))
        entry.update({
            "texture": f"res://assets/fighters/ultraseven/animations/{clip}/atlas.png",
            "cell": 256,
            "anchor": [128, 248],
            "anchor_y": 248,
            "anchors": [[128, 248] for _ in paths],
            "rects": [[256 * i, 0, 256, 256] for i in range(len(paths))],
            "ticks": spec["ticks"],
            "loop": False,
            **spec["extra"],
            "frame_sources": [
                f"rework-super-heavy-20261115:{name}" for name in spec["frames"]
            ],
            "frame_role": spec["role"],
            "demo_frames_review": review,
        })
        if not dry_run:
            entry["atlas_sha256"] = sha256_file(out)
        clips[clip] = entry
        print(f"{clip}: {len(paths)} frames, ticks={spec['ticks']}, dry_run={dry_run}")
    if not dry_run:
        MANIFEST.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"updated {MANIFEST.relative_to(ROOT)}")
    else:
        print("dry-run ok; no runtime assets changed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    install(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
