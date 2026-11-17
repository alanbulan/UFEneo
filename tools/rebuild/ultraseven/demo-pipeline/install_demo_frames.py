#!/usr/bin/env python3
"""把赛文示范批（art/fighters/ultraseven/stage1/demo-missing-20261114）的 21 帧装进赛文。

为什么不直接用 tools/art/install_cells.py：它要求 stage1/cells 目录、把 ticks 统一成 10、
并按第一组格宽改写 definition.json 的 presentation。这里只动 6 个 clip，其余 manifest 条目、
definition 和 selection 一律不碰；拼图集和 SHA 复用 install_cells 的 build_atlas / sha256_file。

- 受击 4 个 clip：现有 3 张 + 新 3 张按动作连贯排成 6 张，ticks 合计 26（= 状态帧条数，
  盖住站立打击最大硬直 26）。state_frames 的 sprite 按新 ticks 展开；受击框取该图对应的
  已有姿势（新姿势借相邻已有姿势的框），不新增框。
- crush_charge：3 张，ticks [20,12,8]，表现层按 crush_hold 取帧（0–19 起势、20–39 二档、32+ 满档前最后一拍
  为 32–39；40 自动出手）。
- crush_charged：6 张，ticks [6,6,4,4,7,8]=35，与 crush 招式帧数相同；第 3 张（命中帧）从 tick 12
  开始，正好是第一个出招帧。表现层按 move_tick 取帧（timeline_driven）。
用法：.venv/bin/python tools/rebuild/ultraseven/demo-pipeline/install_demo_frames.py [--dry-run] [--base REV]

重生某几帧后重装：加 `--base f00dfde6a`（装入前的 main）。受击 4 个 clip 的 3 张原图、旧时间轴和受击框
从该提交读出，再按同样顺序重拼；manifest 与 state_frames 的其余部分取工作区现状。
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/art"))
from install_cells import build_atlas, sha256_file  # noqa: E402
from PIL import Image  # noqa: E402

BATCH = ROOT / "art/fighters/ultraseven/stage1/demo-missing-20261114"
ANIM = ROOT / "assets/fighters/ultraseven/animations"
STATE = ROOT / "content/fighters/ultraseven/state_frames.json"
MISSING = ROOT / "tools/rebuild/ultraseven/demo-pipeline/missing_frames.json"

# 每个受击 clip 的播放顺序：("e", i) = 现有图集第 i 张；("n", k) = 新生成第 k 帧。
# 第三项是这一张用哪张现有图的受击框。
HIT_ORDER = {
    # 现有1 最大后仰 → 现有2 → 新5 回到一半 → 新4 前臂护脸 → 现有3 架势 → 新6 收势
    "hit_high": ([("e", 0, 0), ("e", 1, 1), ("n", 5, 1), ("n", 4, 2), ("e", 2, 2), ("n", 6, 2)], [4, 5, 5, 4, 4, 4]),
    # 现有1 挨打 → 新4 低头护腹 → 现有2 弯腰 → 现有3 折腹顶点 → 新5 抬起一半 → 新6 收势
    "hit_mid": ([("e", 0, 0), ("n", 4, 0), ("e", 1, 1), ("e", 2, 2), ("n", 5, 1), ("n", 6, 0)], [4, 4, 5, 5, 4, 4]),
    # 现有1 → 现有2 → 新4 最低点 → 新5 回升 → 现有3 拳回前 → 新6 蹲防
    "hit_crouch": ([("e", 0, 0), ("e", 1, 1), ("n", 4, 1), ("n", 5, 1), ("e", 2, 2), ("n", 6, 2)], [4, 4, 5, 5, 4, 4]),
    # 新4 开始后仰 → 现有1 → 现有2 → 现有3 展体 → 新5 蜷缩 → 新6 半展开斜落
    "hit_air": ([("n", 4, 0), ("e", 0, 0), ("e", 1, 1), ("e", 2, 2), ("n", 5, 1), ("n", 6, 1)], [4, 4, 5, 5, 4, 4]),
}
NEW_CLIPS = {
    "crush_charge": ([1, 2, 3], [20, 12, 8], {"driven_by": "crush_hold"}),
    "crush_charged": ([1, 2, 3, 4, 5, 6], [6, 6, 4, 4, 7, 8], {"timeline_driven": True}),
}


def cell(name: str) -> Path:
    sub = "hit" if name.startswith("hit_") else "crush"
    path = BATCH / "processed" / sub / f"{name}-cell.png"
    with Image.open(path) as im:
        if im.size != (256, 256):
            raise SystemExit(f"{path} 不是 256 格")
    return path


def git_show(rev: str, path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT, check=True,
                          capture_output=True).stdout


def lfs_smudge(data: bytes) -> bytes:
    if data.startswith(b"version https://git-lfs"):
        return subprocess.run(["git", "lfs", "smudge"], cwd=ROOT, input=data, check=True,
                              capture_output=True).stdout
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--base", default="", help="重装时读受击原图和旧时间轴的提交（装入前的 main）")
    args = ap.parse_args()
    manifest = json.loads((ANIM / "manifest.json").read_text(encoding="utf-8"))
    clips = manifest["clips"]
    state = json.loads(STATE.read_text(encoding="utf-8"))
    base_atlas = {}
    if args.base:
        base_manifest = json.loads(git_show(args.base, ANIM / "manifest.json"))
        base_state = json.loads(git_show(args.base, STATE))
        for clip in HIT_ORDER:
            clips[clip] = base_manifest["clips"][clip]
            state[clip] = base_state[clip]
            base_atlas[clip] = Image.open(io.BytesIO(lfs_smudge(git_show(args.base, ANIM / clip / "atlas.png"))))
    tmp = BATCH / "install-tmp"
    tmp.mkdir(exist_ok=True)
    review = {"by": "root_delegated_by_user", "date": "2026-11-14",
              "batch": "art/fighters/ultraseven/stage1/demo-missing-20261114/manifest.json",
              "user_approved": False}
    for clip, (order, ticks) in HIT_ORDER.items():
        entry = clips[clip]
        if len(entry["rects"]) != 3:
            raise SystemExit(f"{clip} 已不是 3 张原图（{len(entry['rects'])}），拒绝重复安装")
        old = (base_atlas.get(clip) or Image.open(ANIM / clip / "atlas.png")).convert("RGBA")
        frames = []
        for kind, index, _ in order:
            if kind == "e":
                r = entry["rects"][index]
                path = tmp / f"{clip}-existing-{index}.png"
                old.crop((r[0], r[1], r[0] + r[2], r[1] + r[3])).save(path)
                frames.append(path)
            else:
                frames.append(cell(f"{clip}-{index:02d}"))
        poses = state[clip]
        if len(poses) != sum(ticks):
            raise SystemExit(f"{clip} 状态帧 {len(poses)} ≠ ticks {sum(ticks)}")
        # 现有姿势 i 的受击框：取旧时间轴里 sprite==i 的第一条。
        hurt = {}
        for pose in poses:
            hurt.setdefault(int(pose["sprite"]), pose["hurtboxes"])
        expanded = [i for i, t in enumerate(ticks) for _ in range(t)]
        for tick, sprite in enumerate(expanded):
            poses[tick]["sprite"] = sprite
            poses[tick]["hurtboxes"] = json.loads(json.dumps(hurt[order[sprite][2]]))
        atlas = build_atlas(frames, 256, 256)
        if not args.dry_run:
            atlas.save(ANIM / clip / "atlas.png")
        entry["rects"] = [[256 * i, 0, 256, 256] for i in range(len(frames))]
        entry["anchors"] = [[128, 248] for _ in frames]
        entry["ticks"] = ticks
        entry["frame_sources"] = [f"existing:{i}" if k == "e" else f"demo-missing-20261114:{clip}-{i:02d}" for k, i, _ in order]
        entry["demo_frames_review"] = review
        if not args.dry_run:
            entry["atlas_sha256"] = sha256_file(ANIM / clip / "atlas.png")
    for clip, (orders, ticks, extra) in NEW_CLIPS.items():
        frames = [cell(f"{clip}-{i:02d}") for i in orders]
        atlas = build_atlas(frames, 256, 256)
        if not args.dry_run:
            (ANIM / clip).mkdir(exist_ok=True)
            atlas.save(ANIM / clip / "atlas.png")
        entry = {"texture": f"res://assets/fighters/ultraseven/animations/{clip}/atlas.png", "cell": 256,
                 "anchor": [128, 248], "anchor_y": 248, "anchors": [[128, 248] for _ in frames],
                 "rects": [[256 * i, 0, 256, 256] for i in range(len(frames))], "ticks": ticks, "loop": False,
                 **extra, "frame_sources": [f"demo-missing-20261114:{clip}-{i:02d}" for i in orders],
                 "demo_frames_review": review}
        if not args.dry_run:
            entry["atlas_sha256"] = sha256_file(ANIM / clip / "atlas.png")
        clips[clip] = entry
    manifest["clips"] = clips
    for path in tmp.iterdir():
        path.unlink()
    tmp.rmdir()
    if args.dry_run:
        print("dry-run ok")
        return 0
    (ANIM / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("installed hit_high/hit_mid/hit_crouch/hit_air (6 张) + crush_charge (3) + crush_charged (6)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
