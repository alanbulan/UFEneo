"""安装杰斯提斯专属特效家族，并写出共享登记提案。

本任务不允许改共享登记文件 `content/presentation/phase3_projectiles.json` 与
`content/presentation/charge_overlay_policy.json`，因此本脚本只写：

  assets/effects/ultraman-justice/fx-family-20261112-v1/<段>/atlas.png
  assets/effects/ultraman-justice/fx-family-20261112-v1/<段>/effect.json
  assets/effects/ultraman-justice/fx-family-20261112-v1/<段>/provenance.json
  assets/effects/ultraman-justice/PIXELFX-LICENSE.txt
  tools/rebuild/ultraman-justice/fx-family-20261112/phase3_entries.json
  tools/rebuild/ultraman-justice/fx-family-20261112/charge_policy.json
  tools/rebuild/ultraman-justice/fx-family-20261112/build-report.json

并改写 `content/fighters/ultraman-justice/moves/*.json` 的弹体与命中引用。

用法：
  .venv/bin/python tools/rebuild/ultraman-justice/fx-family-20261112/install.py --dry-run
  .venv/bin/python tools/rebuild/ultraman-justice/fx-family-20261112/install.py
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
STAGING = ROOT / "reports/fx_justice_family"
DEST = ROOT / "assets/effects/ultraman-justice/fx-family-20261112-v1"
MOVES = ROOT / "content/fighters/ultraman-justice/moves"
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
POLICY = ROOT / "content/presentation/charge_overlay_policy.json"
UPSTREAM = json.loads((ROOT / "third_party/pixelfx/UPSTREAM.json").read_text(encoding="utf-8"))
LICENSE = ROOT / "third_party/pixelfx/LICENSE"

CHARACTER = "ultraman-justice"
SHORT = {
    "justice_fx_pulse_flight": "pulse_flight",
    "justice_fx_pulse_hit": "pulse_hit",
    "justice_fx_beam": "beam",
    "justice_fx_beam_hit": "beam_hit",
    "justice_fx_arrow_flight": "arrow_flight",
    "justice_fx_arrow_hit": "arrow_hit",
    "justice_fx_q_charge_start": "q_charge_start",
    "justice_fx_q_charge": "q_charge",
    "justice_fx_q_charge_stop": "q_charge_stop",
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path: Path, data, indent=2) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8", newline="\n")


def run_bake() -> dict:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    proc = subprocess.run(["node", str(BAKE), "--out", str(STAGING.relative_to(ROOT))],
                          cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"烘焙失败：\n{proc.stdout}\n{proc.stderr}")
    print(proc.stdout.strip())
    return load(STAGING / "provenance.json")


def components(alpha, want=200):
    """4 连通块；返回 (块大小降序, 最大块的 mask)。"""
    import numpy as np

    mask = alpha >= want
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    sizes = []
    best = None
    for yy in range(h):
        for xx in range(w):
            if not mask[yy, xx] or seen[yy, xx]:
                continue
            stack = [(yy, xx)]
            seen[yy, xx] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            sizes.append(len(cells))
            if best is None or len(cells) > len(best):
                best = cells
    main = np.zeros_like(mask, bool)
    for cy, cx in best or []:
        main[cy, cx] = True
    return sorted(sizes, reverse=True), main


def frame_box(alpha) -> list[int]:
    import numpy as np

    ys, xs = np.nonzero(alpha)
    return [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]


def measure_atlas(atlas: Path, entry: dict, provenance: dict) -> dict:
    import numpy as np
    from PIL import Image

    arr = np.array(Image.open(atlas).convert("RGBA"))
    ax, ay = entry["anchor"]
    frames = []
    gate_components = True
    gate_out16 = True
    gate_out200 = True
    gate_hard = True
    for i, (x, y, w, h) in enumerate(entry["rects"]):
        tile = arr[y:y + h, x:x + w]
        alpha = tile[..., 3]
        values = sorted({int(v) for v in np.unique(alpha)})
        sizes, main = components(alpha, 200)
        subject = int(sizes[0]) if sizes else 0
        outside16 = int(((alpha >= 16) & ~main).sum())
        outside200 = int(((alpha >= 200) & ~main).sum())
        gate_components &= len(sizes) == 1
        gate_out16 &= outside16 <= 100
        gate_out200 &= outside200 == 0
        gate_hard &= set(values) <= {0, 255}
        box = frame_box(alpha)
        prov = (provenance.get("frames") or [])
        prov_frame = prov[i] if i < len(prov) else {}
        frames.append({
            "index": i,
            "rect": [x, y, w, h],
            "alpha_values": values,
            "alpha_min": min(values),
            "alpha_max": max(values),
            "components": len(sizes),
            "largest_component": subject,
            "components_before_filter": int(prov_frame.get("componentsBefore", 0)),
            "outside_alpha_ge16": outside16,
            "outside_alpha_ge200": outside200,
            "dropped_before_filter": int(prov_frame.get("droppedPixels", 0)),
            "bbox_in_frame": box,
            "bbox_relative_to_anchor": [box[0] - ax, box[1] - ay, box[2], box[3]],
            "changed_pixels_vs_prev": int(prov_frame.get("changed_pixels_vs_prev", 0)),
        })
    rgb = arr[..., :3].astype(np.int64)
    packed = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    colors = int(len(np.unique(packed[arr[..., 3] > 0])))
    return {
        "frames": frames,
        "colors": colors,
        "gate": {
            "rgba_true_transparent": arr.shape[2] == 4,
            "hard_alpha": bool(gate_hard),
            "single_subject_component_each_frame": bool(gate_components),
            "outside_alpha_ge16_le_100px": bool(gate_out16),
            "outside_alpha_ge200_zero": bool(gate_out200),
        },
    }


def build_entry(export: dict, dest_atlas: Path, dest_dir: Path) -> dict:
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
        "frame_boxes": [],
        "loop": bool(export.get("loop", False)),
        "color_parameter": False,
        "alpha_binary": True,
        "orientation": "authored",
        "native_fan": False,
        "atlas_sha256": sha(dest_atlas),
        "colors": 0,
        "source_kind": "pixelfx_code_baked",
        "art_source": "pixelfx_code_baked",
        "upstream_commit": UPSTREAM["commit"],
        "license": "MIT",
        "provenance": "res://" + str((dest_dir / "provenance.json").relative_to(ROOT)),
        "dedicated_to": CHARACTER,
        "authoring_source": "res://" + str(BAKE.relative_to(ROOT)),
    }
    if state:
        entry["layer"] = "charge"
        entry["full_frame"] = True
        entry["user_approved"] = False
        entry["review_status"] = "2026-11-12 杰斯提斯 Q 蓄气自绘原创像素（PixelFX 离线烘焙，MIT），待根会话合并登记与目视终审"
    else:
        entry["layer"] = export.get("kind", "flight")
        entry["user_approved"] = False
        entry["review_status"] = "2026-11-12 杰斯提斯专属技能特效自绘原创像素（PixelFX 离线烘焙，MIT），待根会话合并登记与目视终审"
    # frame_boxes 必须以落盘图集的实际 Alpha 实测，不能沿用烘焙占位。
    from PIL import Image
    import numpy as np
    arr = np.array(Image.open(dest_atlas).convert("RGBA"))
    ax, ay = anchor
    boxes = []
    for x, y, w, h in export["rects"]:
        alpha = arr[y:y + h, x:x + w, 3]
        ys, xs = np.nonzero(alpha)
        if len(xs) == 0:
            raise SystemExit(f"空帧：{eid} rect={[x, y, w, h]}")
        boxes.append([int(xs.min()) - ax, int(ys.min()) - ay, int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)])
    entry["frame_boxes"] = boxes
    return entry


def wire_moves() -> dict:
    changes = {}

    for move_id in ("pulse", "low_pulse", "air_pulse"):
        p = MOVES / f"{move_id}.json"
        m = load(p)
        m["projectile"]["effect"] = "justice_fx_pulse_flight"
        m["feedback"]["projectile_impacts"] = {"justice_fx_pulse_flight": "justice_fx_pulse_hit"}
        save(p, m, indent=1)
        changes[move_id] = {"projectile.effect": "justice_fx_pulse_flight",
                            "feedback.projectile_impacts": {"justice_fx_pulse_flight": "justice_fx_pulse_hit"}}

    for move_id in ("special", "special2", "air_special", "special3"):
        p = MOVES / f"{move_id}.json"
        m = load(p)
        for frame in m["frames"]:
            for shot in frame.get("shots", []):
                if str(shot.get("effect", "")) == "beam_loop":
                    shot["effect"] = "justice_fx_beam"
                    shot["color"] = [1, 1, 1, 1]
        m["feedback"]["projectile_impacts"] = {"justice_fx_beam": "justice_fx_beam_hit"}
        m["feedback"]["color"] = [1, 1, 1, 1]
        if move_id in ("special", "special2", "air_special"):
            m["feedback"]["spark"] = "justice_fx_beam_hit"
        if move_id == "air_special":
            m["adaptation"] = ("游戏改编的空中闪光效应：人物整帧只画空中发射动作，光束由运行时 "
                               "justice_fx_beam 承载，不在人物帧内烘焙。不声称原剧有此空中发射镜头。")
        save(p, m, indent=1)
        changes[move_id] = {
            "shots.effect": "justice_fx_beam",
            "feedback.spark": "justice_fx_beam_hit" if move_id in ("special", "special2", "air_special") else "impact_heavy（通用接触反馈保留）",
            "feedback.projectile_impacts": {"justice_fx_beam": "justice_fx_beam_hit"},
        }

    p = MOVES / "motion_214.json"
    m = load(p)
    for frame in m["frames"]:
        for shot in frame.get("shots", []):
            if str(shot.get("effect", "")) == "special_arrow":
                shot["effect"] = "justice_fx_arrow_flight"
                shot["color"] = [1, 1, 1, 1]
    m["feedback"]["projectile_impacts"] = {"justice_fx_arrow_flight": "justice_fx_arrow_hit"}
    # 保留原防御火花染色，只把投射命中染成白色走本人固定色板。
    m["feedback"]["block_color"] = [0.55, 1.0, 0.92, 1.0]
    m["feedback"]["color"] = [1, 1, 1, 1]
    save(p, m, indent=1)
    changes["motion_214"] = {
        "shots.effect": "justice_fx_arrow_flight",
        "feedback.spark": "impact_heavy（通用接触反馈保留）",
        "feedback.block_color": [0.55, 1.0, 0.92, 1.0],
        "feedback.projectile_impacts": {"justice_fx_arrow_flight": "justice_fx_arrow_hit"},
    }
    return changes


def charge_policy() -> dict:
    placement = {}
    for state in ("charge_start", "charge", "charge_stop"):
        placement[state] = {
            "effect": f"justice_fx_q_{state}",
            "anchor": [0, 0],
            "color": [1, 1, 1, 1],
            "behind_fighter": True,
            "frames": 9 if state != "charge" else 24,
            "loop": state == "charge",
        }
    return {
        "placements": {CHARACTER: placement},
        "charge_only_effects": [f"justice_fx_q_{state}" for state in ("charge_start", "charge", "charge_stop")],
        "basis": "杰斯提斯标准型银白/冰蓝亮芯、银红外焰，与本人普通技能同一色系；Q 三态沿用本人专属环而非通用 charge_aura。",
        "activation_dependency": (
            "当前 content/fighters/ultraman-justice/state_frames.json 与运行 manifest 的 "
            "charge_start/charge/charge_stop 均无 attachments，UfeChargeEffectPolicy 只替换已有挂件，"
            "不会凭空追加。合并 placements 后仍需根会话把通用 charge_aura 挂件补进这三个 Q 状态帧"
            "（本任务允许范围不含 state_frames.json），否则这三段仍不会显示。"
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-bake", action="store_true")
    args = ap.parse_args()

    phase3_before = sha(PHASE3)
    policy_before = sha(POLICY)
    prov = load(STAGING / "provenance.json") if args.skip_bake else run_bake()
    exports = prov["exports"]
    if set(SHORT) != {e["id"] for e in exports}:
        raise SystemExit("烘焙段与预期 id 不一致")

    entries = {}
    report_effects = []
    for export in exports:
        eid = export["id"]
        atlas = STAGING / eid / "atlas.png"
        dest_dir = DEST / SHORT[eid]
        if args.dry_run:
            print(f"dry-run {eid}: {export['W']}x{export['H']} ×{export['n']} -> {dest_dir.relative_to(ROOT)}")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_atlas = dest_dir / "atlas.png"
        shutil.copyfile(atlas, dest_atlas)
        entry = build_entry(export, dest_atlas, dest_dir)
        provenance = {
            "request": "杰斯提斯专属特效家族自绘：银白亮芯/冰蓝内焰/银红外焰，按本人招式光色原创像素形状，不借他人图集",
            "character": CHARACTER,
            "family": eid,
            "kind": export.get("kind"),
            "shape_source": "原创绘制函数 tools/rebuild/ultraman-justice/fx-family-20261112/bake.mjs",
            "reused_source_atlas_shape": False,
            "source_kind": "pixelfx_code_baked",
            "route": "offline",
            "upstream": "https://github.com/patch-gg/pixelfx/tree/" + UPSTREAM["commit"],
            "upstream_commit": UPSTREAM["commit"],
            "license": "MIT",
            "license_file": "res://assets/effects/ultraman-justice/PIXELFX-LICENSE.txt",
            "license_sha256": sha(LICENSE),
            "seed": prov["seed"],
            "canvas": [export["W"] * export["cols"], export["H"] * ((export["n"] + export["cols"] - 1) // export["cols"])],
            "frame_size": [export["W"], export["H"]],
            "anchor": [export["AX"], export["AY"]],
            "rects": export["rects"],
            "frame_sha256": export["phase_png_sha256"],
            "frames": export["frames"],
            "atlas_sha256": entry["atlas_sha256"],
            "character_frames_modified": False,
            "review_status": entry["review_status"],
        }
        measure = measure_atlas(dest_atlas, entry, provenance)
        entry["colors"] = measure["colors"]
        save(dest_dir / "provenance.json", provenance)
        save(dest_dir / "effect.json", entry)
        entries[eid] = entry
        report_effects.append({
            "id": eid,
            "atlas": str(dest_atlas.relative_to(ROOT)),
            "atlas_sha256": entry["atlas_sha256"],
            "frame_size": [export["W"], export["H"]],
            "atlas_size": [export["W"] * export["cols"], export["H"] * ((export["n"] + export["cols"] - 1) // export["cols"])],
            "anchor": entry["anchor"],
            "rects": entry["rects"],
            "ticks": entry["ticks"],
            "loop": entry["loop"],
            "layer": entry["layer"],
            "colors": measure["colors"],
            "source_kind": entry["source_kind"],
            "license": "MIT",
            "license_file": "assets/effects/ultraman-justice/PIXELFX-LICENSE.txt",
            "upstream_commit": UPSTREAM["commit"],
            "provenance": entry["provenance"],
            "frames": measure["frames"],
            "gate": measure["gate"],
        })
        print(f"安装 {eid} -> {dest_dir.relative_to(ROOT)}")

    if args.dry_run:
        print(f"dry-run：{len(exports)} 段已烘焙，未写 assets/content")
        return

    license_dest = DEST.parent / "PIXELFX-LICENSE.txt"
    shutil.copyfile(LICENSE, license_dest)
    save(BATCH / "phase3_entries.json", entries)
    policy = charge_policy()
    save(BATCH / "charge_policy.json", policy)
    moves = wire_moves()

    report = {
        "schema": "ufeneo.fx-family.build-report.v1",
        "character": CHARACTER,
        "built_for": "2026-11-12 本批杰斯提斯专属运行时特效家族",
        "source_kind": "pixelfx_code_baked",
        "art_source": "pixelfx_code_baked",
        "authoring_source": "tools/rebuild/ultraman-justice/fx-family-20261112/bake.mjs",
        "installer": "tools/rebuild/ultraman-justice/fx-family-20261112/install.py",
        "upstream": {
            "repo": "https://github.com/patch-gg/pixelfx",
            "commit": UPSTREAM["commit"],
            "license": "MIT",
            "license_file": "assets/effects/ultraman-justice/PIXELFX-LICENSE.txt",
            "license_sha256": sha(LICENSE),
            "third_party_upstream_json": "third_party/pixelfx/UPSTREAM.json",
        },
        "shared_registry_policy": {
            "phase3_projectiles_sha256_before": phase3_before,
            "phase3_projectiles_sha256_after": sha(PHASE3),
            "charge_overlay_policy_sha256_before": policy_before,
            "charge_overlay_policy_sha256_after": sha(POLICY),
            "modified_by_this_batch": False,
        },
        "proposals": {
            "phase3_entries": "tools/rebuild/ultraman-justice/fx-family-20261112/phase3_entries.json",
            "charge_policy": "tools/rebuild/ultraman-justice/fx-family-20261112/charge_policy.json",
        },
        "effects": report_effects,
        "move_wiring": moves,
        "character_frames_modified": False,
        "recording": "无录屏",
        "review_status": "待根会话合并 phase3/charge 提案并目视终审；未改人物整帧 PNG",
    }
    save(BATCH / "build-report.json", report)
    if sha(PHASE3) != phase3_before or sha(POLICY) != policy_before:
        raise SystemExit("共享登记文件被意外修改")
    print(f"完成：{len(entries)} 段特效；phase3 提案 {BATCH / 'phase3_entries.json'}")


if __name__ == "__main__":
    main()
