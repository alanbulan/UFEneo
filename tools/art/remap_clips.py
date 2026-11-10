"""重命名 / 别名 / 删除已安装 clip，不改像素内容。

美术组名与运行时 `animation_key()` 不一定同名：赛罗的 `light1` 美术组实际是
1 格必杀 `special`，真正的一段普攻在 `light_combo1` 组。安装时若按美术组名
直接落格，必杀会取不到片段（side_view 直接返回空），人物在招式期间不可见。

本工具只操作 `assets/fighters/<id>/animations/manifest.json` 与 clip 目录，
不生成、不缩放、不改色；atlas.png 原样移动或复用。

用法：
    .venv/bin/python tools/art/remap_clips.py --fighter ultraman-zero \
        --rename light1=special --rename light2=special2 --rename light3=special3 \
        --rename light_combo1=light1 --rename light_combo2=light2 --rename light_combo3=light3
    .venv/bin/python tools/art/remap_clips.py --fighter zoffy \
        --alias walk=walk_forward --alias jump=takeoff --alias run=walk_back
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def clip_dir(fighter: str, clip: str) -> Path:
    return ROOT / f"assets/fighters/{fighter}/animations/{clip}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", required=True)
    ap.add_argument("--rename", action="append", default=[], help="旧名=新名，移动 atlas 目录")
    ap.add_argument("--alias", action="append", default=[], help="已存在clip=新名，共用 atlas")
    ap.add_argument("--drop", action="append", default=[], help="删除 clip 条目与目录")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    man_path = ROOT / f"assets/fighters/{args.fighter}/animations/manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    clips: dict = manifest["clips"]

    plan: list[tuple[str, str, str]] = []
    # 重命名允许链式（light1→special 后 light_combo1→light1），按声明顺序模拟占位。
    live: set[str] = set(clips)
    for text in args.rename:
        old, _, new = text.partition("=")
        if not old or not new:
            raise SystemExit(f"--rename 需要 旧名=新名：{text}")
        if old not in live:
            raise SystemExit(f"clip 不存在：{old}")
        if new in live:
            raise SystemExit(f"目标 clip 已存在，拒绝覆盖：{new}")
        live.discard(old)
        live.add(new)
        plan.append(("rename", old, new))
    for text in args.alias:
        src, _, new = text.partition("=")
        if src not in live:
            raise SystemExit(f"源 clip 不存在：{src}")
        if new in live:
            raise SystemExit(f"目标 clip 已存在，拒绝覆盖：{new}")
        live.add(new)
        plan.append(("alias", src, new))
    for name in args.drop:
        if name not in live:
            raise SystemExit(f"clip 不存在：{name}")
        live.discard(name)
        plan.append(("drop", name, ""))

    for kind, src, new in plan:
        if kind == "drop":
            if not args.dry_run:
                d = clip_dir(args.fighter, src)
                if d.is_dir():
                    shutil.rmtree(d)
                clips.pop(src, None)
            print(f"drop {src}")
            continue
        entry = json.loads(json.dumps(clips[src]))
        if kind == "rename":
            if not args.dry_run:
                old_dir = clip_dir(args.fighter, src)
                new_dir = clip_dir(args.fighter, new)
                if old_dir.is_dir():
                    old_dir.rename(new_dir)
                atlas = new_dir / "atlas.png"
                entry["texture"] = f"res://assets/fighters/{args.fighter}/animations/{new}/atlas.png"
                if atlas.is_file():
                    entry["atlas_sha256"] = sha256_file(atlas)
                clips.pop(src)
                clips[new] = entry
            print(f"rename {src} -> {new}")
        else:
            if not args.dry_run:
                clips[new] = entry
            print(f"alias {src} -> {new}")

    if not args.dry_run:
        manifest["clips"] = dict(sorted(clips.items()))
        man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{args.fighter}: manifest 已更新，共 {len(clips)} clips")
    else:
        print(f"{args.fighter}: dry-run，共 {len(plan)} 项")


if __name__ == "__main__":
    main()
