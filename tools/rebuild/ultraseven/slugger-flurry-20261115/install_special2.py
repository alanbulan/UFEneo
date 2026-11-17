#!/usr/bin/env python3
"""安装赛文 2026-11-15 头镖战法批次的人物图集。

只更新 special2 的 atlas 与 manifest 条目；招式帧数据、伤害与返航时序在
content/fighters/ultraseven/moves/special2.json 另行维护。所有帧都必须先由
stage_cells.py 以本批统一的 0.163287 比例落成 256 格。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/art"))
from install_cells import build_atlas, sha256_file  # noqa: E402

BATCH = ROOT / "art/fighters/ultraseven/stage1/slugger-flurry-20261115"
PROCESSED = BATCH / "processed"
ANIM = ROOT / "assets/fighters/ultraseven/animations"
MANIFEST = ANIM / "manifest.json"

# 顺序即 sprite 索引：空手框住悬停头镖→合掌握紧→深蹲后拉→再握紧→拍出→跟随→控制往返→接回→收镖→装回
FRAMES = [
    "special2-hover-01",
    "special2-grip-01",
    "special2-charge-05",
    "special2-push-01",
    "special2-release-01",
    "special2-control-01",
    "special2-control-02",
    "special2-catch-01",
    "special2-receive-01",
    "special2-equip-01",
]
# 每格在招式里出现的总 tick：握掌 1 与两次控制拍复用（8+6、9+9、9+8），合计仍是 96 tick。
TICKS = [6, 14, 10, 4, 6, 18, 17, 8, 6, 7]
ROLE = "悬停头镖→合掌握紧→深蹲后拉→拍出→念力头镖来回戳刺→接回→装回头顶"


def install(*, dry_run: bool) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clip_id = "special2"
    paths = [PROCESSED / f"{name}-cell.png" for name in FRAMES]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit(f"缺少已落格帧：{missing}")
    if sum(TICKS) != 96:
        raise SystemExit(f"本批 ticks 总和 {sum(TICKS)} 与 96 tick 帧数据不符")
    atlas = build_atlas(paths, 256, 256)
    out = ANIM / clip_id / "atlas.png"
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(out)
    entry = {
        "texture": f"res://assets/fighters/ultraseven/animations/{clip_id}/atlas.png",
        "cell": 256,
        "anchor": [128, 248],
        "anchor_y": 248,
        "anchors": [[128, 248] for _ in paths],
        "rects": [[256 * i, 0, 256, 256] for i in range(len(paths))],
        "ticks": TICKS,
        "loop": False,
        "runtime_ticks": sum(TICKS),
        "frame_sources": [f"slugger-flurry-20261115:{name}" for name in FRAMES],
        "frame_role": ROLE,
        "motion_review": {
            "by": "root_delegated_by_user",
            "date": "2026-11-15",
            "batch": "art/fighters/ultraseven/stage1/slugger-flurry-20261115/manifest.json",
            "user_approved": False,
            "status": "pending_user_visual_review",
            "recording": "无录屏",
            "note": "用户已确认头镖战法方向：头镖悬停在身前，双手只在一瞬合拢紧贴再拍出；本批整帧尚未完成用户美术签收。",
        },
    }
    if not dry_run:
        entry["atlas_sha256"] = sha256_file(out)
    manifest["clips"][clip_id] = entry
    if not dry_run:
        MANIFEST.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{clip_id}: {len(paths)} frames, ticks={TICKS}, 更新 {MANIFEST.relative_to(ROOT)}")
    else:
        print(f"{clip_id}: {len(paths)} frames, ticks={TICKS}, dry-run 未改运行素材")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    install(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())