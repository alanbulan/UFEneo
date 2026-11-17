"""把各角色已烘焙的 Q 蓄气贴图登记进 phase3_projectiles.json。

背景：gaia/king/zoffy/mother 的 q-outline 批次把 atlas 与 provenance 写进
assets/effects/<角色>/q-outline-*，charge_overlay_policy.json 也已换成各自的
effect id，但 phase3 里没有对应条目。side_view 查不到 clip 就跳过，Q 起势/
保持/收势的蓄气光效因此整体不可见。

本工具只补登记，不重烘焙、不改像素：
  - 从 charge_overlay_policy.json 取每个角色 charge_start/charge/charge_stop 的 effect id
  - 在 assets/effects/<角色>/q-outline-*/<effect id>/atlas.png 找已核 atlas
  - 用批次 provenance.json 的 W/H/AX/AY/count 生成逐帧 rects 与条目
  - SHA 与 provenance 记录不符则拒绝登记

用法：
  .venv/bin/python tools/rebuild/shared/q_charge_registry.py --dry-run
  .venv/bin/python tools/rebuild/shared/q_charge_registry.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
POLICY = ROOT / "content/presentation/charge_overlay_policy.json"
UPSTREAM = json.loads((ROOT / "third_party/pixelfx/UPSTREAM.json").read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def find_clip(fighter: str, effect: str):
    """在角色目录的 q-outline 批次里找该 effect 的 atlas、provenance 与 bake 源。"""
    base = ROOT / "assets/effects" / fighter
    hits = sorted(base.glob(f"q-outline-*/{effect}/atlas.png"))
    if not hits:
        return None
    atlas = hits[0]
    prov = atlas.parent.parent / "provenance.json"
    if not prov.is_file():
        raise SystemExit(f"{effect}: 缺批次 provenance {prov}")
    return atlas, prov


def build_entry(fighter: str, effect: str, state: str, atlas: Path, prov: Path) -> dict:
    from PIL import Image

    data = load_json(prov)
    export = next((e for e in data.get("exports", []) if e.get("state") == state), None)
    if export is None:
        raise SystemExit(f"{effect}: provenance 缺 state={state}")
    w, h = int(export["W"]), int(export["H"])
    count = int(export["count"])
    ax, ay = int(export["AX"]), int(export["AY"])
    atlas_sha = sha(atlas)
    if atlas_sha != export.get("atlas_sha256"):
        raise SystemExit(f"{effect}: atlas SHA 与 provenance 不符（{atlas_sha[:12]}）")
    with Image.open(atlas) as im:
        aw, ah = im.size
    cols = aw // w
    if cols <= 0 or aw % w or ah % h or cols * (ah // h) < count:
        raise SystemExit(f"{effect}: atlas 尺寸 {aw}x{ah} 与 {w}x{h}×{count} 不符")
    rects = [[(i % cols) * w, (i // cols) * h, w, h] for i in range(count)]
    rel_prov = "res://" + str(prov.relative_to(ROOT))
    bake = atlas.parent.parent / "bake.mjs"
    return {
        "texture": "res://" + str(atlas.relative_to(ROOT)),
        "rects": rects,
        "anchor": [ax, ay],
        "ticks": 1,
        "display_scale": [1, 1],
        "behind_fighter": True,
        "full_frame": True,
        "loop": state == "charge",
        "color_parameter": False,
        # 蓄气轮廓是半透明流带，不是人物帧式二值 Alpha。
        "alpha_binary": False,
        "source_kind": "pixelfx_code_baked",
        "upstream_commit": data.get("upstream_commit", UPSTREAM["commit"]),
        "license": "MIT",
        "atlas_sha256": atlas_sha,
        "provenance": rel_prov,
        "dedicated_to": fighter,
        "authoring_source": "res://" + str(bake.relative_to(ROOT)),
        "review_status": "2026-11-12 补登记已烘焙 Q 蓄气贴图；像素未改，待指挥目视终审",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw = PHASE3.read_text(encoding="utf-8")
    projectiles = json.loads(raw)
    if json.dumps(projectiles, ensure_ascii=False, indent=2) + "\n" != raw:
        raise SystemExit("phase3 往返格式不一致")
    policy = load_json(POLICY)
    added = 0
    missing = []
    for fighter, states in policy.get("placements", {}).items():
        for state, placement in states.items():
            effect = str(placement.get("effect", ""))
            if not effect:
                continue
            if effect in projectiles:
                continue
            found = find_clip(fighter, effect)
            if found is None:
                missing.append((fighter, state, effect))
                continue
            atlas, prov = found
            projectiles[effect] = build_entry(fighter, effect, state, atlas, prov)
            added += 1
            print(f"登记 {effect} <- {atlas.relative_to(ROOT)}")
    for fighter, state, effect in missing:
        print(f"缺贴图，未登记：{fighter}/{state} {effect}")
    if not args.dry_run and added:
        save_json(PHASE3, projectiles)
    print(f"{'dry-run：' if args.dry_run else ''}新增 {added} 条，phase3 现有 {len(projectiles)} 条")
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
