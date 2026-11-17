#!/usr/bin/env python3
"""安装赛文 2026-11-15 宽幅光线八帧动作，替换 motion_41236 的近身投技动作。

只更新 motion_41236 的 atlas 与 manifest 条目；招式数值、命中框和状态模拟
由 content/fighters/ultraseven/moves/motion_41236.json 决定，本脚本不改。
旧投技帧的头部/头镖质检记录随旧图一并失效，历史签收写进 review.superceded。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/art"))
from install_cells import build_atlas, sha256_file  # noqa: E402

BATCH = ROOT / "art/fighters/ultraseven/stage1/wide-shot-20261115"
PROCESSED = BATCH / "processed"
ANIM = ROOT / "assets/fighters/ultraseven/animations"
MANIFEST = ANIM / "manifest.json"

CLIP = "motion_41236"
FRAMES = [f"wideshot-{i:02d}" for i in range(1, 9)]
TICKS = [4, 4, 4, 4, 6, 6, 6, 6]
ROLE = "起手→胸前 L 形结印→压低蓄力→峰值→双臂前抖发射→发射保持→收势→回位"

SUPERSEDED = {
    "art": "过肩强投（游戏编排）",
    "user_approved": True,
    "date": "2026-10-22",
    "verdict": "旧投技动作已由用户审过；2026-11-15 因组合键全部改为远程，重绘为宽幅光线。",
}


def install(*, dry_run: bool) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clips = manifest["clips"]
    paths = [PROCESSED / f"{name}-cell.png" for name in FRAMES]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise SystemExit(f"缺少已落格帧：{missing}")
    atlas = build_atlas(paths, 256, 256)
    out = ANIM / CLIP / "atlas.png"
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(out)
    old = clips.get(CLIP, {})
    entry = {
        "texture": f"res://assets/fighters/ultraseven/animations/{CLIP}/atlas.png",
        "cell": 256,
        "anchor": [128, 248],
        "anchor_y": 248,
        "anchors": [[128, 248] for _ in FRAMES],
        "rects": [[256 * i, 0, 256, 256] for i in range(len(FRAMES))],
        "ticks": TICKS,
        "loop": False,
        "runtime_ticks": sum(TICKS),
        "frame_sources": [f"wide-shot-20261115:{name}" for name in FRAMES],
        "frame_role": ROLE,
        "review_status": "2026-11-15 宽幅光线重绘，待用户美术签收",
        "approved": False,
        "motion_review": {
            "user_approved": False,
            "date": "2026-11-15",
            "verdict": "组合键改为远程后的重绘帧，待用户审片",
            "superseded": SUPERSEDED,
        },
        "audio_events": [
            {"kind": "sound", "id": "seven_wide_charge", "source": "content/fighters/ultraseven/moves/motion_41236.json"},
            {"kind": "sound", "id": "seven_wide_cast1", "source": "content/fighters/ultraseven/moves/motion_41236.json"},
        ],
    }
    if not dry_run:
        entry["atlas_sha256"] = sha256_file(out)
    elif old.get("atlas_sha256"):
        entry["atlas_sha256"] = old["atlas_sha256"]
    clips[CLIP] = entry
    print(f"{CLIP}: {len(paths)} frames, ticks={TICKS}, dry_run={dry_run}")
    if not dry_run:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
