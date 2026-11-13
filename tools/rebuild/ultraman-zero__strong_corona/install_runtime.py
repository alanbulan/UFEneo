"""安装强壮日冕赛罗运行时资产：atlas、manifest、state_frames、model、定义与登记。

规则：只写本形态目录与本形态专属条目；保持 playable=false，implemented 不打开。
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
FIGHTER = "ultraman-zero__strong_corona"
CELLS = ROOT / f"art/fighters/{FIGHTER}/stage1/cells"
ASSET_ANIM = ROOT / f"assets/fighters/{FIGHTER}/animations"
ASSET_CAT = ROOT / f"assets/fighters/{FIGHTER}/catalogue"
CONTENT = ROOT / f"content/fighters/{FIGHTER}"
BASE_CONTENT = ROOT / "content/fighters/ultraman-zero"
BASE_MANIFEST = ROOT / "assets/fighters/ultraman-zero/animations/manifest.json"
PLAN = ROOT / "tools/rebuild/ultraman-zero__strong_corona/frame_plan.json"
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
CHARGE = ROOT / "content/presentation/charge_overlay_policy.json"

CELL = 256
ANCHOR = [128, 248]
TICK = 10
LOOP_CLIPS = {
    "idle", "walk_forward", "walk_back", "crouch", "crouch_guard", "guard",
    "block", "dash", "charge", "air_apex", "air_fall", "air_rise",
    "stun", "down",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def make_atlas(paths: list[Path]) -> Image.Image:
    atlas = Image.new("RGBA", (CELL * len(paths), CELL), (0, 0, 0, 0))
    for i, path in enumerate(paths):
        im = Image.open(path).convert("RGBA")
        if im.size != (CELL, CELL):
            im = im.resize((CELL, CELL), Image.NEAREST)
        atlas.alpha_composite(im, (i * CELL, 0))
    return atlas


def main() -> int:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    base_manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    clips = {}
    manifest_clips = {}
    state_frames = {}
    fx_refs = {}
    for move_path in sorted((CONTENT / "moves").glob("*.json")):
        move = json.loads(move_path.read_text(encoding="utf-8"))
        ids = set()
        def walk(v):
            if isinstance(v, dict):
                for k in ("effect", "spark", "trail_effect", "return_effect"):
                    if isinstance(v.get(k), str):
                        ids.add(v[k])
                for vv in v.values():
                    walk(vv)
            elif isinstance(v, list):
                for vv in v:
                    walk(vv)
        walk(move)
        fx_refs[move_path.stem] = sorted(ids)
    for clip, spec in plan["clips"].items():
        n = len(spec["frames"])
        cells = [CELLS / f"{clip}-{i:02d}-cell.png" for i in range(n)]
        if not all(p.is_file() for p in cells):
            raise SystemExit(f"{clip}: 缺 cell")
        out_dir = ASSET_ANIM / clip
        ensure_dir(out_dir)
        atlas_path = out_dir / "atlas.png"
        atlas = make_atlas(cells)
        atlas.save(atlas_path)
        entry = {
            "texture": f"res://assets/fighters/{FIGHTER}/animations/{clip}/atlas.png",
            "cell": CELL,
            "anchor": ANCHOR[:],
            "anchor_y": ANCHOR[1],
            "anchors": [ANCHOR[:] for _ in range(n)],
            "rects": [[i * CELL, 0, CELL, CELL] for i in range(n)],
            "ticks": spec["ticks"][:],
            "loop": bool(spec.get("loop", clip in LOOP_CLIPS)),
            "atlas_sha256": sha(atlas_path),
            "source_cells": [str(p.relative_to(ROOT)).replace("\\", "/") for p in cells],
            "user_approved": False,
        }
        manifest_clips[clip] = entry
        base_frames = base_manifest["clips"][clip]["ticks"]
        if base_frames != spec["ticks"]:
            raise SystemExit(f"{clip}: ticks 与基础赛罗不一致")
        state_frames[clip] = [{
            "sprite": 0,
            "dx": 0,
            "dy": 0,
            "hitboxes": [],
            "hurtboxes": [[-64, 0, 128, 248]],
            "cancel": [],
            "events": [],
        }]
    # form_switch
    form_cells = [CELLS / f"form_switch-{i:02d}-cell.png" for i in range(6)]
    if not all(p.is_file() for p in form_cells):
        raise SystemExit("form_switch: 缺 cell")
    form_dir = ASSET_ANIM / "form_switch"
    ensure_dir(form_dir)
    form_atlas = make_atlas(form_cells)
    form_atlas.save(form_dir / "atlas.png")
    manifest_clips["form_switch"] = {
        "texture": f"res://assets/fighters/{FIGHTER}/animations/form_switch/atlas.png",
        "cell": CELL,
        "anchor": ANCHOR[:],
        "anchor_y": ANCHOR[1],
        "anchors": [ANCHOR[:] for _ in range(6)],
        "rects": [[i * CELL, 0, CELL, CELL] for i in range(6)],
        "ticks": [10, 10, 10, 10, 10, 10],
        "loop": False,
        "atlas_sha256": sha(form_dir / "atlas.png"),
        "source_cells": [str(p.relative_to(ROOT)).replace("\\", "/") for p in form_cells],
        "user_approved": False,
    }
    manifest = {
        "schema": 1,
        "fighter": FIGHTER,
        "cell": [CELL, CELL],
        "anchor": ANCHOR,
        "reviewed": False,
        "identity_revision": "root_delegated_by_user_2026-11-12",
        "clips": manifest_clips,
    }
    ensure_dir(ASSET_ANIM)
    (ASSET_ANIM / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (CONTENT / "state_frames.json").write_text(
        json.dumps(state_frames, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # model-native: use identity anchor as runtime sprite sheet reference for now
    ensure_dir(ASSET_CAT)
    src_model = ROOT / f"art/fighters/{FIGHTER}/model/identity-anchor.png"
    if not src_model.is_file():
        src_model = ASSET_CAT / "model-native.png"
    shutil.copy2(src_model, ASSET_CAT / "model-native.png")

    # definition: playable false until effects and review complete
    definition = json.loads((CONTENT / "definition.json").read_text(encoding="utf-8"))
    presentation = definition.setdefault("presentation", {})
    presentation.update({
        "model": f"res://assets/fighters/{FIGHTER}/animations/idle/atlas.png",
        "manifest": f"res://assets/fighters/{FIGHTER}/animations/manifest.json",
        "native": True,
        "cell": CELL,
        "anchor": ANCHOR,
        "target_height": 188,
        "height_basis": "冠顶/头冠顶至鞋底；本形态身份锚实测站高188，脚底247",
        "anchor_y": ANCHOR[1],
    })
    definition["playable"] = False
    definition["select_visible"] = False
    definition["selection_visible"] = False
    definition["production_status"] = "stage2_frames_installed_fx_pending"
    definition["pilot_playable"] = False
    definition["pilot_manual_ready"] = False
    definition["pilot_lock_reason"] = "动作帧与 form_switch 已落格，专属运行时特效与最终装机待完成。"
    definition["model_review_pending"] = True
    definition["reference_file"] = f"content/fighters/{FIGHTER}/profile.json"
    (CONTENT / "definition.json").write_text(
        json.dumps(definition, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"clips": len(manifest_clips), "manifest_sha256": sha(ASSET_ANIM / "manifest.json")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
