"""安装赛罗专属特效家族并接线三招 + Q 蓄气。

步骤：
  1. node bake.mjs --out reports/fx_zero_family（冻结烘焙，不覆盖）
  2. 复制 atlas 到 assets/effects/ultraman-zero/fx-family-pixelfx-20261112-v1/<id>/
  3. 生成 phase3_projectiles.json 条目（frame_boxes 按 Alpha 实测）
  4. 改 special / special2 / special3 / air_special 的 shots 与反馈
  5. 在 charge_overlay_policy.json 登记 zero 的 Q 蓄气三态

用法：
  .venv/bin/python tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/install.py --dry-run
  .venv/bin/python tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/install.py
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
STAGING = ROOT / "reports/fx_zero_family"
DEST = ROOT / "assets/effects/ultraman-zero/fx-family-pixelfx-20261112-v1"
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
POLICY = ROOT / "content/presentation/charge_overlay_policy.json"
MOVES = ROOT / "content/fighters/ultraman-zero/moves"
UPSTREAM = json.loads((ROOT / "third_party/pixelfx/UPSTREAM.json").read_text(encoding="utf-8"))
LICENSE = ROOT / "third_party/pixelfx/LICENSE"

SHORT = {
    "zero_fx_wide_beam": "wide_beam",
    "zero_fx_wide_hit": "wide_hit",
    "zero_fx_emerium_beam": "emerium_beam",
    "zero_fx_emerium_hit": "emerium_hit",
    "zero_fx_slugger_flight": "slugger_flight",
    "zero_fx_slugger_trail": "slugger_trail",
    "zero_fx_slugger_hit": "slugger_hit",
    "zero_fx_slugger_catch": "slugger_catch",
    "zero_fx_q_charge_start": "q_charge_start",
    "zero_fx_q_charge": "q_charge",
    "zero_fx_q_charge_stop": "q_charge_stop",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data, indent=2) -> None:
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


def build_entry(fighter: str, export: dict, dest_atlas: Path, dest_dir: Path) -> dict:
    eid = export["id"]
    state = export.get("state")
    anchor = [int(export["AX"]), int(export["AY"])]
    entry = {
        "texture": "res://" + str(dest_atlas.relative_to(ROOT)),
        "rects": export["rects"],
        "anchor": anchor,
        "ticks": 1 if state else 4,
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
        "provenance": "res://" + str((dest_dir / "provenance.json").relative_to(ROOT)),
        "dedicated_to": fighter,
        "authoring_source": "res://" + str(BAKE.relative_to(ROOT)),
    }
    if state:
        entry["layer"] = "charge"
        entry["full_frame"] = True
        entry["user_approved"] = False
        entry["review_status"] = "2026-11-12 赛罗 Q 蓄气自绘原创像素（PixelFX 离线烘焙），待指挥目视终审"
    else:
        entry["layer"] = export.get("kind", "flight")
        entry["user_approved"] = False
        entry["review_status"] = "2026-11-12 赛罗专属技能特效自绘原创像素（PixelFX 离线烘焙），待指挥目视终审"
    return entry


def wire_moves() -> None:
    # special 赛罗集束射线
    p = MOVES / "special.json"
    m = load(p)
    m["display_name"] = "赛罗集束射线"
    m["production_note"] = "赛罗专属特效 zero_fx_wide_beam 已接线；人物帧只画身体，束体由运行时承载。"
    shot = m["frames"][24]["shots"][0]
    shot["effect"] = "zero_fx_wide_beam"
    shot["color"] = [1, 1, 1, 1]
    m["feedback"]["spark"] = "zero_fx_wide_hit"
    m["feedback"]["color"] = [1, 1, 1, 1]
    m["adaptation"] = "游戏改编的赛罗集束射线（Wide Zero Shot）：双臂前伸聚能后发射宽幅青蓝光束；人物帧不含光束，束体由运行时 zero_fx_wide_beam 承载。"
    m["data_source"] = "伤害/消耗/硬直沿用已装机同体型必杀规则；发射根点取 special-11 手部中心，命中与光束为赛罗专属 PixelFX 自绘段。"
    save(p, m, indent=1)

    # special2 艾梅利姆切割
    p = MOVES / "special2.json"
    m = load(p)
    m["display_name"] = "艾梅利姆切割"
    m["production_note"] = "赛罗专属特效 zero_fx_emerium_beam 已接线；人物帧只画身体，束体由运行时承载。"
    shot = m["frames"][32]["shots"][0]
    shot["effect"] = "zero_fx_emerium_beam"
    shot["color"] = [1, 1, 1, 1]
    m["feedback"]["spark"] = "zero_fx_emerium_hit"
    m["feedback"]["color"] = [1, 1, 1, 1]
    m["adaptation"] = "游戏改编的艾梅利姆切割（Emerium Slash）：额灯蓄光后射出青绿细束，新月刃波沿束推进；人物帧不含光束，束体由运行时 zero_fx_emerium_beam 承载。"
    m["data_source"] = "伤害/消耗/硬直沿用已装机同体型必杀规则；发射根点取 special2-10 手部中心，命中与束体为赛罗专属 PixelFX 自绘段。"
    save(p, m, indent=1)

    # special3 赛罗头镖
    p = MOVES / "special3.json"
    m = load(p)
    m["display_name"] = "赛罗头镖"
    m["production_note"] = "赛罗专属特效 zero_fx_slugger_flight/trail/catch 已接线；头镖实体飞行与回收由运行时承载。"
    for frame in m["frames"]:
        for shot in frame.get("shots", []):
            if shot.get("weapon_id", "").startswith("zero_slugger"):
                shot["effect"] = "zero_fx_slugger_flight"
                shot["trail_effect"] = "zero_fx_slugger_trail"
                shot["return_effect"] = "zero_fx_slugger_catch"
                shot["color"] = [1, 1, 1, 1]
    m["feedback"]["spark"] = "zero_fx_slugger_hit"
    m["feedback"]["color"] = [1, 1, 1, 1]
    m["feedback"]["projectile_impacts"] = {"zero_fx_slugger_flight": "zero_fx_slugger_hit"}
    m["adaptation"] = "游戏改编的赛罗头镖（Zero Slugger）：取下双头镖掷出、回旋回收；人物帧只画取镖与投掷动作，飞行刃、拖尾与接刃闪光由运行时承载。"
    m["data_source"] = "伤害/消耗/硬直沿用已装机同体型必杀规则；双镖发射点按 special3-8 双手位置分别量取，飞行与回收为赛罗专属 PixelFX 自绘段。"
    save(p, m, indent=1)

    # air_special 空中集束射线：strike 的不可见判定改为运行时束体
    p = MOVES / "air_special.json"
    m = load(p)
    m["kind"] = "projectile"
    m["production_note"] = "游戏改编的空中集束射线；人物帧只画身体，束体由运行时 zero_fx_wide_beam 承载。"
    frame = m["frames"][10]
    frame["hitboxes"] = []
    frame["shots"] = [{
        "effect": "zero_fx_wide_beam",
        "spawn": [126, 162],
        "anchor": [126, 162],
        "speed": 0,
        "life": 8,
        "beam": True,
        "length": 420,
        "thickness": 44,
        "level": 1,
        "box": [0, -22, 420, 44],
        "color": [1, 1, 1, 1],
    }]
    m["feedback"]["spark"] = "zero_fx_wide_hit"
    m["feedback"]["color"] = [1, 1, 1, 1]
    m["adaptation"] = "游戏改编的空中集束射线：人物帧只画空中发射动作，光束由运行时 zero_fx_wide_beam 承载，不在人物帧内烘焙。不声称原剧有此空中发射镜头。"
    m["data_source"] = "伤害/消耗/硬直沿用已装机同体型空中必杀规则；发射根点按 air_special-03 手部中心（格内 254,86）量取，束体与命中为赛罗专属 PixelFX 自绘段。"
    save(p, m, indent=1)


def wire_charge_policy() -> None:
    policy = load(POLICY)
    placements = policy.setdefault("placements", {})
    placements["ultraman-zero"] = {
        state: {
            "effect": f"zero_fx_q_{state}",
            "anchor": [0, 0],
            "color": [1, 1, 1, 1],
            "behind_fighter": True,
            "frames": 9 if state != "charge" else 24,
            "loop": state == "charge",
        }
        for state in ("charge_start", "charge", "charge_stop")
    }
    charge_only = policy.setdefault("charge_only_effects", [])
    for state in ("charge_start", "charge", "charge_stop"):
        eid = f"zero_fx_q_{state}"
        if eid not in charge_only:
            charge_only.append(eid)
    save(POLICY, policy)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    prov = run_bake()
    exports = prov["exports"]
    projectiles = load(PHASE3)
    entries = {}
    for export in exports:
        eid = export["id"]
        short = SHORT[eid]
        atlas = STAGING / eid / "atlas.png"
        dest_dir = DEST / short
        entries[eid] = (export, atlas, dest_dir)
        if not args.dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(atlas, dest_dir / "atlas.png")
            entry = build_entry("ultraman-zero", export, dest_dir / "atlas.png", dest_dir)
            provenance = {
                "request": "赛罗专属特效家族自绘：按本人招式光色原创像素形状，不借他人图集",
                "character": "ultraman-zero",
                "family": eid,
                "kind": export.get("kind"),
                "shape_source": "原创绘制函数 tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs",
                "reused_source_atlas_shape": False,
                "source_kind": "pixelfx_code_baked",
                "route": "offline",
                "upstream": prov["upstream"],
                "upstream_commit": prov["upstream_commit"],
                "license": "MIT",
                "seed": prov["seed"],
                "canvas": [export["W"] * (export.get("cols") or 4), export["H"]],
                "anchor": [export["AX"], export["AY"]],
                "rects": export["rects"],
                "phase_png_sha256": export["phase_png_sha256"],
                "atlas_sha256": export["atlas_sha256"],
                "character_frames_modified": False,
                "review_status": entry["review_status"],
            }
            save(dest_dir / "provenance.json", provenance)
            save(dest_dir / "effect.json", entry)
            projectiles[eid] = entry
            print(f"安装 {eid} -> {dest_dir.relative_to(ROOT)}")
    if args.dry_run:
        print(f"dry-run：{len(exports)} 段已烘焙，未写 assets/content")
        return
    shutil.copyfile(LICENSE, DEST / "PIXELFX-LICENSE.txt")
    save(PHASE3, projectiles)
    wire_moves()
    wire_charge_policy()
    print(f"完成：{len(exports)} 段特效，phase3 共 {len(projectiles)} 条")


if __name__ == "__main__":
    main()
