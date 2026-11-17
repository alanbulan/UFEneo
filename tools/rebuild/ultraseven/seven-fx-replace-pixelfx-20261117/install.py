"""把赛文替换批装进运行素材并登记到特效名册。

这批不是新增特效，而是把已有 id 的画面换成同尺寸、同时序的 PixelFX 成品：
- seven_fx_wide1 / seven_fx_wide2：原 AI 候选（rejected）换为手绘像素宽幅扇；
- seven_pixelfx_emerium_hit / _guard：原正圆+等距射线碎爆换为不规则碎核；
- seven_slugger：放大到可读的旋转月牙刃，seven_slugger_edge 共用同一图集。

只做确定性复制与登记，不改招式判定、帧数、时长或根点。
用法：
  .venv/bin/python tools/rebuild/ultraseven/seven-fx-replace-pixelfx-20261117/install.py \
      --candidate art/fighters/ultraseven/stage1/fx-replace-20261117 [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEST = ROOT / "assets/effects/ultraseven"
REGISTRY = ROOT / "content/presentation/phase3_projectiles.json"
# 候选 id → 运行目录名（沿用旧目录，保持 texture 路径稳定）。
LAYOUT = {
    "seven_fx_wide1": "fx_wide1",
    "seven_fx_wide2": "fx_wide2",
    "seven_pixelfx_emerium_hit": "seven_pixelfx_emerium_hit",
    "seven_pixelfx_emerium_guard": "seven_pixelfx_emerium_guard",
    "seven_slugger": "slugger",
    "seven_fx_emerium_start": "fx_emerium_start",
    "seven_fx_wide_start": "fx_wide_start",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    candidate = (ROOT / args.candidate).resolve()
    bundle = json.loads((candidate / "bundle.json").read_text(encoding="utf-8"))
    catalog = json.loads((candidate / "catalog-candidate.json").read_text(encoding="utf-8"))
    exports = {item["id"]: item for item in bundle["exports"]}
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    problems: list[str] = []

    for effect_id, clip in catalog.items():
        source = candidate / effect_id / "atlas.png"
        expect = exports[effect_id]["atlas_sha256"]
        if sha(source) != expect:
            problems.append(f"{effect_id}: 候选 atlas 与 bundle SHA 不一致")
            continue
        folder = LAYOUT.get(effect_id)
        if folder is None:
            problems.append(f"{effect_id}: 未登记运行目录")
            continue
        entry = dict(clip)
        entry["atlas_sha256"] = expect
        entry["source"] = source.relative_to(ROOT).as_posix()
        entry["source_sha256"] = expect
        entry["texture"] = f"res://assets/effects/ultraseven/{folder}/atlas.png"
        if effect_id not in registry:
            problems.append(f"{effect_id}: 名册里没有同名条目，拒绝新增")
            continue
        registry[effect_id] = entry
        if effect_id == "seven_slugger":
            edge = dict(registry["seven_slugger_edge"])
            edge["atlas_sha256"] = expect
            edge["source"] = entry["source"]
            edge["source_sha256"] = expect
            edge["note"] = "与 seven_slugger 同一图集，只取竖立刃身那一格（rect 96,0）：头镖战法里镖身长条竖立，割线朝正前方。"
            registry["seven_slugger_edge"] = edge
        target = DEST / folder / "atlas.png"
        if args.check:
            if not target.exists() or sha(target) != expect:
                problems.append(f"{effect_id}: 运行素材缺失或 SHA 不符 {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        for phase in sorted((candidate / effect_id).glob("[0-9][0-9].png")):
            shutil.copyfile(phase, target.parent / phase.name)
        if sha(target) != expect:
            problems.append(f"{effect_id}: 复制后 SHA 不符")
    if problems:
        for line in problems:
            print("FAIL", line)
        return 1
    if not args.check:
        REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "effects": sorted(catalog), "check": args.check}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())