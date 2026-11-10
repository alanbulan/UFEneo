"""由 catalogue_profile.json 生成运行时角色档案 profile.json。

已装机角色都有 profile.json：UI 读称号/简介，side_audio 读 audio_timer 决定
残血彩色计时器提示音。stage1 新装角色缺该文件时，界面与低血量提示音都会
静默回退。本工具只复用已核实的角色资料，不新增设定，不覆盖已有档案。

用法：
    .venv/bin/python tools/art/sync_fighter_profiles.py ultraman-justice ultraman-zero
    .venv/bin/python tools/art/sync_fighter_profiles.py --all-missing
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEW = [
    "ultraman-justice", "ultraman-zero", "zoffy", "mother-of-ultra",
    "ultraman-gaia", "ultraman-king", "father-of-ultra",
]


def build(fighter: str) -> dict | None:
    src = ROOT / f"content/fighters/{fighter}/catalogue_profile.json"
    if not src.is_file():
        return None
    c = json.loads(src.read_text(encoding="utf-8"))
    model = f"res://assets/fighters/{fighter}/model-native.png"
    return {
        "name": c.get("name", fighter),
        "title": c.get("title", ""),
        "text": c.get("text", ""),
        "source_label": c.get("source_label", ""),
        "source_url": c.get("source_url", ""),
        "license": c.get("license", ""),
        "model": model,
        "audio_timer": {"enabled": True, "sound": "timer"},
        "profile_source": "catalogue_profile.json；称号/简介沿用图鉴已核资料，不新增设定。",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("fighters", nargs="*")
    ap.add_argument("--all-missing", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    targets = NEW if args.all_missing else args.fighters
    for fighter in targets:
        out = ROOT / f"content/fighters/{fighter}/profile.json"
        if out.is_file() and not args.force:
            print(f"{fighter}: profile.json 已存在，跳过")
            continue
        data = build(fighter)
        if data is None:
            print(f"{fighter}: 缺 catalogue_profile.json，跳过")
            continue
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{fighter}: 写入 profile.json")


if __name__ == "__main__":
    main()
