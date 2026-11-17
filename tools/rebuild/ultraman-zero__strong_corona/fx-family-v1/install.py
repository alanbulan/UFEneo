"""安装强壮日冕赛罗专属特效家族并接线招式与蓄气登记提案。

步骤：
  1. node bake.mjs --out reports/fx_zero_strong_corona_family
  2. 复制 atlas 与 provenance 到 assets/effects/ultraman-zero__strong_corona/fx-family-v1/
  3. 生成 phase3_entries.json（frame_boxes 按 Alpha 实测）
  4. 生成 charge_policy.json（placements + charge_only_effects）
  5. 改本形态 special/special2/special3/air_special 的特效 id 与文本
  6. 写 build-report.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
BATCH = Path(__file__).resolve().parent
BAKE = BATCH / "bake.mjs"
STAGING = ROOT / "reports/fx_zero_strong_corona_family"
DEST = ROOT / "assets/effects/ultraman-zero__strong_corona/fx-family-v1"
MOVES = ROOT / "content/fighters/ultraman-zero__strong_corona/moves"
UPSTREAM = json.loads((ROOT / "third_party/pixelfx/UPSTREAM.json").read_text(encoding="utf-8"))
LICENSE = ROOT / "third_party/pixelfx/LICENSE"
REPORT = BATCH / "build-report.json"
PHASE3_PROPOSAL = BATCH / "phase3_entries.json"
CHARGE_PROPOSAL = BATCH / "charge_policy.json"

FIGHTER = "ultraman-zero__strong_corona"
DATE = "2026-11-12"
REVIEW = f"{DATE} 强壮日冕赛罗专属技能特效自绘原创像素（PixelFX 离线烘焙），待指挥目视终审"
CHARGE_REVIEW = f"{DATE} 强壮日冕赛罗 Q 蓄气自绘原创像素（PixelFX 离线烘焙），待指挥目视终审"

SHORT = {
    "zero_strong_corona_fx_wide_beam": "wide_beam",
    "zero_strong_corona_fx_wide_hit": "wide_hit",
    "zero_strong_corona_fx_emerium_beam": "emerium_beam",
    "zero_strong_corona_fx_emerium_hit": "emerium_hit",
    "zero_strong_corona_fx_slugger_flight": "slugger_flight",
    "zero_strong_corona_fx_slugger_trail": "slugger_trail",
    "zero_strong_corona_fx_slugger_hit": "slugger_hit",
    "zero_strong_corona_fx_slugger_catch": "slugger_catch",
    "zero_strong_corona_fx_q_charge_start": "q_charge_start",
    "zero_strong_corona_fx_q_charge": "q_charge",
    "zero_strong_corona_fx_q_charge_stop": "q_charge_stop",
}
TICKS = {
    "zero_strong_corona_fx_wide_beam": 4,
    "zero_strong_corona_fx_wide_hit": 4,
    "zero_strong_corona_fx_emerium_beam": 4,
    "zero_strong_corona_fx_emerium_hit": 4,
    "zero_strong_corona_fx_slugger_flight": 4,
    "zero_strong_corona_fx_slugger_trail": 4,
    "zero_strong_corona_fx_slugger_hit": 4,
    "zero_strong_corona_fx_slugger_catch": 4,
    "zero_strong_corona_fx_q_charge_start": 1,
    "zero_strong_corona_fx_q_charge": 1,
    "zero_strong_corona_fx_q_charge_stop": 1,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data, indent=2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8", newline="\n")


def frame_boxes(atlas: Path, rects, anchor) -> list:
    import numpy as np
    from PIL import Image
    arr = np.array(Image.open(atlas).convert("RGBA"))
    ax, ay = anchor
    boxes = []
    for x, y, w, h in rects:
        alpha = arr[y:y + h, x:x + w, 3]
        ys, xs = np.nonzero(alpha)
        if len(xs) == 0:
            raise SystemExit(f"空帧：{atlas} rect={[x, y, w, h]}")
        boxes.append([int(xs.min()) - ax, int(ys.min()) - ay, int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)])
    return boxes


def color_count(path: Path) -> int:
    import numpy as np
    from PIL import Image
    arr = np.array(Image.open(path).convert("RGBA"))
    visible = arr[arr[..., 3] > 0][:, :3]
    return int(len({tuple(int(v) for v in c) for c in visible}))


def run_bake() -> dict:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    proc = subprocess.run(["node", str(BAKE), "--out", str(STAGING.relative_to(ROOT))],
                          cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"烘焙失败：\n{proc.stdout}\n{proc.stderr}")
    print(proc.stdout.strip())
    return load(STAGING / "provenance.json")


def build_entry(export: dict, dest_atlas: Path, dest_dir: Path) -> dict:
    eid = export["id"]
    state = export.get("state")
    anchor = [int(export["AX"]), int(export["AY"])]
    entry = {
        "texture": "res://" + str(dest_atlas.relative_to(ROOT)).replace("\\", "/"),
        "rects": export["rects"],
        "anchor": anchor,
        "ticks": TICKS[eid],
        "display_scale": [1, 1],
        "behind_fighter": bool(export.get("behind", False)),
        "frame_boxes": frame_boxes(dest_atlas, export["rects"], anchor),
        "loop": bool(export.get("loop", False)),
        "color_parameter": export.get("kind") == "beam",
        "alpha_binary": not state,
        "orientation": "authored",
        "native_fan": False,
        "atlas_sha256": sha(dest_atlas),
        "colors": color_count(dest_atlas),
        "source_kind": "pixelfx_code_baked",
        "art_source": "pixelfx_code_baked",
        "upstream_commit": UPSTREAM["commit"],
        "license": "MIT",
        "provenance": "res://" + str((dest_dir / "provenance.json").relative_to(ROOT)).replace("\\", "/"),
        "dedicated_to": FIGHTER,
        "authoring_source": "res://" + str(BAKE.relative_to(ROOT)).replace("\\", "/"),
        "layer": export.get("kind", "flight"),
        "user_approved": False,
        "review_status": CHARGE_REVIEW if state else REVIEW,
    }
    if state:
        entry["full_frame"] = True
    return entry


REPLACEMENTS = {
    "pending_corona_wide_beam": "zero_strong_corona_fx_wide_beam",
    "pending_corona_wide_hit": "zero_strong_corona_fx_wide_hit",
    "pending_corona_emerium_beam": "zero_strong_corona_fx_emerium_beam",
    "pending_corona_emerium_hit": "zero_strong_corona_fx_emerium_hit",
    "pending_corona_slugger_flight": "zero_strong_corona_fx_slugger_flight",
    "pending_corona_slugger_trail": "zero_strong_corona_fx_slugger_trail",
    "pending_corona_slugger_hit": "zero_strong_corona_fx_slugger_hit",
    "pending_corona_slugger_catch": "zero_strong_corona_fx_slugger_catch",
    "pending_corona_q_charge_start": "zero_strong_corona_fx_q_charge_start",
    "pending_corona_q_charge_charge": "zero_strong_corona_fx_q_charge",
    "pending_corona_q_charge_stop": "zero_strong_corona_fx_q_charge_stop",
}


def wire_moves() -> list[str]:
    changed = []
    for mv in ["special", "special2", "special3", "air_special"]:
        path = MOVES / f"{mv}.json"
        text = path.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS.items():
            text = text.replace(old, new)
        m = json.loads(text)
        m["production_note"] = "已安装：stage2 动作帧与强壮日冕专属特效已接线；实机 720/1080 双朝向与听审未做，无录屏。"
        if mv == "special":
            m["display_name"] = "强壮日冕·赛罗集束射线"
            m["adaptation"] = "游戏改编的赛罗集束射线（Wide Zero Shot）：强壮日冕赛罗双臂前伸聚能后发射宽幅金红光束；人物帧不含光束，束体由运行时 zero_strong_corona_fx_wide_beam 承载。"
            m["data_source"] = "伤害/消耗/硬直与起止帧沿用基础赛罗同招；发射根点沿用手部中心，束体与命中为强壮日冕赛罗专属 PixelFX 自绘段。"
            m["feedback"]["color"] = [1, 1, 1, 1]
        elif mv == "special2":
            m["display_name"] = "强壮日冕·艾梅利姆切割"
            m["adaptation"] = "游戏改编的艾梅利姆切割（Emerium Slash）：强壮日冕赛罗额灯蓄光后射出橙金细束，新月刃波沿束推进；人物帧不含光束，束体由运行时 zero_strong_corona_fx_emerium_beam 承载。"
            m["data_source"] = "伤害/消耗/硬直与起止帧沿用基础赛罗同招；发射根点沿用手部中心，束体与命中为强壮日冕赛罗专属 PixelFX 自绘段。"
            m["feedback"]["color"] = [1, 1, 1, 1]
        elif mv == "special3":
            m["display_name"] = "强壮日冕·赛罗头镖"
            m["adaptation"] = "游戏改编的赛罗头镖（Zero Slugger）：强壮日冕赛罗取下双头镖掷出、回旋回收；人物帧只画取镖与投掷动作，飞行刃、拖尾与接刃闪光由运行时承载。"
            m["data_source"] = "伤害/消耗/硬直与起止帧沿用基础赛罗同招；双镖发射点沿用手部位置，飞行与回收为强壮日冕赛罗专属 PixelFX 自绘段。"
            m["feedback"]["color"] = [1, 1, 1, 1]
        elif mv == "air_special":
            m["display_name"] = "强壮日冕·空中集束射线"
            m["adaptation"] = "游戏改编的空中集束射线：强壮日冕赛罗空中发射金红集束光；人物帧只画发射动作，光束由运行时 zero_strong_corona_fx_wide_beam 承载。不声称原剧有此空中发射镜头。"
            m["data_source"] = "伤害/消耗/硬直与起止帧沿用基础赛罗同招；发射根点沿用手部中心，束体与命中为强壮日冕赛罗专属 PixelFX 自绘段。"
            m["feedback"]["color"] = [1, 1, 1, 1]
        path.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        changed.append(mv)
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    prov = run_bake()
    exports = prov["exports"]
    entries = {}
    for export in exports:
        eid = export["id"]
        short = SHORT[eid]
        atlas = STAGING / eid / "atlas.png"
        dest_dir = DEST / short
        if not args.dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(atlas, dest_dir / "atlas.png")
            provenance = {
                "request": "强壮日冕赛罗专属特效家族自绘：日冕红金配色原创像素形状，不借他人角色图集",
                "character": FIGHTER,
                "family": eid,
                "kind": export.get("kind"),
                "shape_source": "原创绘制函数 tools/rebuild/ultraman-zero__strong_corona/fx-family-v1/bake.mjs",
                "reused_source_atlas_shape": False,
                "source_kind": "pixelfx_code_baked",
                "route": "offline",
                "upstream": prov["upstream"],
                "upstream_commit": prov["upstream_commit"],
                "seed": prov["seed"],
                "license_sha256": prov["license_sha256"],
                "source_sha256": prov["source_sha256"],
                "phase_png_sha256": export["phase_png_sha256"],
                "atlas_sha256": sha(dest_dir / "atlas.png"),
                "user_approved": False,
                "review_status": CHARGE_REVIEW if export.get("state") else REVIEW,
            }
            save(dest_dir / "provenance.json", provenance)
            entries[eid] = build_entry(export, dest_dir / "atlas.png", dest_dir)
        else:
            entries[eid] = {"dry_run": True, "id": eid}
    save(PHASE3_PROPOSAL, {"fighter": FIGHTER, "status": "ready_for_merge", "entries": {k: v for k, v in entries.items() if "q_charge" not in k}})
    save(CHARGE_PROPOSAL, {
        "schema": 1,
        "status": "ready_for_merge",
        "character": FIGHTER,
        "merge_into": "content/presentation/charge_overlay_policy.json",
        "placements": {
            FIGHTER: {
                "charge_start": {"effect": "zero_strong_corona_fx_q_charge_start", "anchor": [0, 0], "color": [1, 1, 1, 1], "behind_fighter": True, "frames": 9, "loop": False},
                "charge": {"effect": "zero_strong_corona_fx_q_charge", "anchor": [0, 0], "color": [1, 1, 1, 1], "behind_fighter": True, "frames": 24, "loop": True},
                "charge_stop": {"effect": "zero_strong_corona_fx_q_charge_stop", "anchor": [0, 0], "color": [1, 1, 1, 1], "behind_fighter": True, "frames": 9, "loop": False},
            }
        },
        "charge_only_effects": ["zero_strong_corona_fx_q_charge_start", "zero_strong_corona_fx_q_charge", "zero_strong_corona_fx_q_charge_stop"],
    })
    wired = wire_moves() if not args.dry_run else []
    report = {
        "batch": "tools/rebuild/ultraman-zero__strong_corona/fx-family-v1",
        "date": DATE,
        "source_kind": "pixelfx_code_baked",
        "staging": str(STAGING.relative_to(ROOT)).replace("\\", "/"),
        "dest": str(DEST.relative_to(ROOT)).replace("\\", "/"),
        "wired_moves": wired,
        "entries": sorted(entries.keys()),
        "dry_run": args.dry_run,
    }
    save(REPORT, report)
    print(json.dumps({"effects": len(entries), "wired": wired, "dest": report["dest"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
