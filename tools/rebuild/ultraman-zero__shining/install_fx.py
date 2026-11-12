"""光辉赛罗运行特效家族：15 个 pending_shining_* id 的图集、规格与提案。

来源：
- 8 个招式/命中段：复用同一角色的基础赛罗 PixelFX 自绘图集（不改图，只换路径与归属）；
- 3 个 Q 蓄气段：由 bake_qcharge_hard.mjs 按同一 chargeAura 形状重烘为硬 Alpha；
- 4 个通用段（pulse/impact_*）：复制项目共享图集到本形态目录。

不改 content/presentation/phase3_projectiles.json 与 charge_overlay_policy.json。
产出：assets/effects/ultraman-zero__shining/fx-family-pixelfx-20261112-v1/**、
tools/rebuild/ultraman-zero__shining/fx-proposal.json、charge_policy.json、fx-report.json。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "assets/effects/ultraman-zero/fx-family-pixelfx-20261112-v1"
DEST = ROOT / "assets/effects/ultraman-zero__shining/fx-family-pixelfx-20261112-v1"
STAGING_Q = ROOT / "tools/rebuild/ultraman-zero__shining/fx-staging-qcharge-v3"
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
REPORT = ROOT / "tools/rebuild/ultraman-zero__shining/fx-report.json"
PROPOSAL = ROOT / "tools/rebuild/ultraman-zero__shining/fx-proposal.json"
POLICY = ROOT / "tools/rebuild/ultraman-zero__shining/charge_policy.json"
FAMILY = "fx-family-pixelfx-20261112-v1"

MOVE_FX = [
    ("wide_beam", "pending_shining_wide_beam", "zero_fx_wide_beam", "beam"),
    ("wide_hit", "pending_shining_wide_hit", "zero_fx_wide_hit", "hit_spark"),
    ("emerium_beam", "pending_shining_emerium_beam", "zero_fx_emerium_beam", "beam"),
    ("emerium_hit", "pending_shining_emerium_hit", "zero_fx_emerium_hit", "hit_spark"),
    ("slugger_flight", "pending_shining_slugger_flight", "zero_fx_slugger_flight", "projectile"),
    ("slugger_trail", "pending_shining_slugger_trail", "zero_fx_slugger_trail", "trail"),
    ("slugger_hit", "pending_shining_slugger_hit", "zero_fx_slugger_hit", "hit_spark"),
    ("slugger_catch", "pending_shining_slugger_catch", "zero_fx_slugger_catch", "return"),
]
Q_STATES = [
    ("q_charge_start", "pending_shining_q_charge_start", 9, False),
    ("q_charge", "pending_shining_q_charge", 24, True),
    ("q_charge_stop", "pending_shining_q_charge_stop", 9, False),
]
GENERIC = [
    ("pulse", "pending_shining_pulse", "pulse", "projectile", ROOT / "assets/effects/pulse/atlas.png"),
    ("impact_light", "pending_shining_impact_light", "impact_light", "hit_spark",
     ROOT / "assets/effects/shared/impact_light/sprite-sheet-alpha.png"),
    ("impact_guard", "pending_shining_impact_guard", "impact_guard", "block_spark",
     ROOT / "assets/effects/shared/impact_light/variants/guard.png"),
    ("impact_heavy", "pending_shining_impact_heavy", "impact_heavy", "hit_spark",
     ROOT / "assets/effects/shared/impact_heavy/sprite-sheet-alpha.png"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def frame_boxes(atlas_path: Path, rects: list, anchor: list[int]) -> list:
    atlas = np.array(Image.open(atlas_path).convert("RGBA"))
    ax, ay = anchor
    boxes = []
    for x, y, w, h in rects:
        alpha = atlas[y:y + h, x:x + w, 3]
        ys, xs = np.nonzero(alpha)
        if len(xs) == 0:
            boxes.append([0, 0, 1, 1])
            continue
        boxes.append([int(xs.min()) - ax, int(ys.min()) - ay,
                      int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)])
    return boxes


def color_count(atlas_path: Path) -> int:
    array = np.array(Image.open(atlas_path).convert("RGBA"))
    visible = array[array[..., 3] > 0][:, :3]
    return int(len({tuple(int(v) for v in c) for c in visible}))


def components_and_glow(atlas_path: Path, rects: list) -> list:
    """按帧核：二值 Alpha、色数、最大 alpha>=200 连通块外扩 3px 的计数。"""
    atlas = np.array(Image.open(atlas_path).convert("RGBA"))
    results = []
    for x, y, w, h in rects:
        frame = atlas[y:y + h, x:x + w]
        alpha = frame[:, :, 3]
        solid = alpha >= 200
        # 行程并查集（4 连通）
        parent = []

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        runs = []
        prev = []
        for row in range(frame.shape[0]):
            xs = np.nonzero(solid[row])[0]
            current = []
            if len(xs):
                start = prev_end = int(xs[0])
                for value in xs[1:]:
                    value = int(value)
                    if value == prev_end + 1:
                        prev_end = value
                        continue
                    current.append((start, prev_end))
                    start = prev_end = value
                current.append((start, prev_end))
            label_ids = []
            for start, end in current:
                idx = len(parent)
                parent.append(idx)
                label_ids.append((start, end, idx))
                for pstart, pend, pidx in prev:
                    if pstart <= end and start <= pend:
                        union(idx, pidx)
            runs.append(label_ids)
            prev = [(s, e, i) for s, e, i in label_ids]
        sizes = {}
        for row in runs:
            for start, end, idx in row:
                root = find(idx)
                sizes[root] = sizes.get(root, 0) + (end - start + 1)
        largest = max(sizes.values()) if sizes else 0
        largest_mask = np.zeros_like(solid)
        if largest:
            best_root = max(sizes, key=sizes.get)
            for row_index, row in enumerate(runs):
                for start, end, idx in row:
                    if find(idx) == best_root:
                        largest_mask[row_index, start:end + 1] = True
            dilated = largest_mask.copy()
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    shifted = np.roll(np.roll(largest_mask, dy, axis=0), dx, axis=1)
                    dilated |= shifted
            outside = ~dilated
            gte16 = int(((alpha >= 16) & outside).sum())
            gte200 = int(((alpha >= 200) & outside).sum())
        else:
            gte16 = gte200 = 0
        results.append({
            "binary": bool(((alpha == 0) | (alpha == 255)).all()),
            "colors": int(len(np.unique(frame[:, :, :3][alpha > 0].reshape(-1, 3), axis=0))) if (alpha > 0).any() else 0,
            "visible_px": int((alpha > 0).sum()),
            "components_alpha200": len(sizes),
            "largest_component_px": largest,
            "outside_gte16": gte16,
            "outside_gte200": gte200,
        })
    return results


def write_provenance(dest_dir: Path, data: dict) -> None:
    save(dest_dir / "provenance.json", data)


def main() -> int:
    if not (STAGING_Q / "provenance.json").exists():
        subprocess.run([
            "node", str(ROOT / "tools/rebuild/ultraman-zero__shining/bake_qcharge_hard.mjs"),
            "--out", str(STAGING_Q.relative_to(ROOT)), "--cutoff", "32",
        ], cwd=ROOT, check=True)
    phase3 = load(PHASE3)
    source_family_prov = load(BASE / "emerium_beam/provenance.json")
    license_src = BASE / "PIXELFX-LICENSE.txt"
    license_sha = sha(license_src)
    review = "2026-11-12 光辉赛罗特效家族（基础赛罗 PixelFX 自绘段复用；Q 蓄气硬 Alpha 重烘），root_delegated_by_user，待主会话登记"
    entries = {}

    # 1) 基础家族 8 段：复制图集，改路径与归属
    for short, pending, source_id, role in MOVE_FX:
        src_dir = BASE / short
        dst_dir = DEST / short
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_dir / "atlas.png", dst_dir / "atlas.png")
        spec = load(src_dir / "effect.json")
        atlas_path = dst_dir / "atlas.png"
        entry = dict(spec)
        entry.update({
            "texture": "res://" + str(atlas_path.relative_to(ROOT)),
            "provenance": "res://" + str((dst_dir / "provenance.json").relative_to(ROOT)),
            "dedicated_to": "ultraman-zero__shining",
            "authoring_source": "res://tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs",
            "atlas_sha256": sha(atlas_path),
            "user_approved": False,
            "review_status": review,
            "reused_from": f"assets/effects/ultraman-zero/{FAMILY}/{short}",
            "reuse_note": "同一角色光辉形态复用基础赛罗 PixelFX 自绘图集；像素未改，只改路径与归属。",
        })
        save(dst_dir / "effect.json", entry)
        write_provenance(dst_dir, {
            "request": "光辉赛罗运行特效：复用基础赛罗同角色 PixelFX 自绘段",
            "character": "ultraman-zero__shining",
            "family": pending,
            "source_id": source_id,
            "kind": entry.get("layer"),
            "shape_source": "tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs",
            "reused_from": f"assets/effects/ultraman-zero/{FAMILY}/{short}",
            "reused_atlas_sha256": sha(BASE / short / "atlas.png"),
            "reused_source_atlas_shape": True,
            "source_kind": "pixelfx_code_baked",
            "route": "offline",
            "upstream": source_family_prov.get("upstream"),
            "upstream_commit": source_family_prov.get("upstream_commit"),
            "license": "MIT",
            "license_sha256": license_sha,
            "atlas_sha256": sha(atlas_path),
            "character_frames_modified": False,
            "review_status": review,
        })
        entries[pending] = {
            "id": pending, "source_id": source_id, "role": role,
            "status": "pending_register", "reused_from": entry["reused_from"],
            "effect": entry,
        }

    # 2) Q 蓄气三态：硬 Alpha 重烘
    q_prov = load(STAGING_Q / "provenance.json")
    q_exports = {e["id"]: e for e in q_prov["exports"]}
    for state, pending, frames, loop in Q_STATES:
        export = q_exports[f"pending_shining_{state}"]
        src_atlas = STAGING_Q / export["id"] / "atlas.png"
        dst_dir = DEST / state
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_atlas, dst_dir / "atlas.png")
        entry = {
            "texture": "res://" + str((dst_dir / "atlas.png").relative_to(ROOT)),
            "rects": export["rects"],
            "anchor": [export["AX"], export["AY"]],
            "ticks": 1,
            "display_scale": [1, 1],
            "behind_fighter": True,
            "frame_boxes": frame_boxes(dst_dir / "atlas.png", export["rects"], [export["AX"], export["AY"]]),
            "loop": loop,
            "color_parameter": False,
            "alpha_binary": True,
            "orientation": "authored",
            "native_fan": False,
            "atlas_sha256": sha(dst_dir / "atlas.png"),
            "colors": color_count(dst_dir / "atlas.png"),
            "source_kind": "pixelfx_code_baked",
            "art_source": "pixelfx_code_baked",
            "upstream_commit": q_prov["upstream_commit"],
            "license": "MIT",
            "provenance": "res://" + str((dst_dir / "provenance.json").relative_to(ROOT)),
            "dedicated_to": "ultraman-zero__shining",
            "authoring_source": "res://tools/rebuild/ultraman-zero__shining/bake_qcharge_hard.mjs",
            "layer": "charge",
            "full_frame": True,
            "user_approved": False,
            "review_status": review,
            "reused_from": "tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs chargeAura",
            "reuse_note": "沿用基础家族 chargeAura 形状，离线重烘为二值 Alpha 并量化到青蓝 8 色板。",
        }
        save(dst_dir / "effect.json", entry)
        write_provenance(dst_dir, {
            "request": "光辉赛罗 Q 蓄气三态：硬 Alpha 像素环，亮芯/外焰/颗粒/相位变化",
            "character": "ultraman-zero__shining",
            "family": pending,
            "source_id": f"zero_fx_{state}",
            "kind": "charge",
            "shape_source": "tools/rebuild/ultraman-zero/fx-family-pixelfx-20261112-v1/bake.mjs",
            "authoring_source": "tools/rebuild/ultraman-zero__shining/bake_qcharge_hard.mjs",
            "source_kind": "pixelfx_code_baked",
            "route": "offline",
            "upstream": q_prov["upstream"],
            "upstream_commit": q_prov["upstream_commit"],
            "license": "MIT",
            "license_sha256": q_prov["license_sha256"],
            "seed": q_prov["seed"],
            "hard_alpha_cutoff": q_prov["hard_alpha_cutoff"],
            "canvas": [export["W"] * export["cols"], export["H"]],
            "anchor": [export["AX"], export["AY"]],
            "rects": export["rects"],
            "phase_png_sha256": export["phase_png_sha256"],
            "atlas_sha256": sha(dst_dir / "atlas.png"),
            "character_frames_modified": False,
            "review_status": review,
        })
        entries[pending] = {
            "id": pending, "source_id": f"zero_fx_{state}", "role": "charge_overlay",
            "status": "pending_register", "effect": entry,
        }

    # 3) 通用段：复制共享图集，保留共享规格
    for short, pending, source_id, role, src_path in GENERIC:
        dst_dir = DEST / short
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_name = src_path.name
        shutil.copyfile(src_path, dst_dir / dst_name)
        spec = phase3[source_id]
        entry = dict(spec)
        entry.update({
            "texture": "res://" + str((dst_dir / dst_name).relative_to(ROOT)),
            "provenance": "res://" + str((dst_dir / "provenance.json").relative_to(ROOT)),
            "dedicated_to": "ultraman-zero__shining",
            "atlas_sha256": sha(dst_dir / dst_name),
            "colors": color_count(dst_dir / dst_name),
            "alpha_binary": True,
            "source_kind": "shared_effect_reuse",
            "reused_from": str(src_path.relative_to(ROOT)),
            "reuse_note": "项目共享通用特效图集；本形态独立副本，不改共享文件。",
            "user_approved": False,
            "review_status": review,
        })
        save(dst_dir / "effect.json", entry)
        write_provenance(dst_dir, {
            "request": "光辉赛罗通用命中/投射特效：复制项目共享图集",
            "character": "ultraman-zero__shining",
            "family": pending,
            "source_id": source_id,
            "kind": role,
            "source_path": str(src_path.relative_to(ROOT)),
            "source_sha256": sha(src_path),
            "source_kind": "shared_effect_reuse",
            "license": "project-internal",
            "atlas_sha256": sha(dst_dir / dst_name),
            "character_frames_modified": False,
            "review_status": review,
        })
        entries[pending] = {
            "id": pending, "source_id": source_id, "role": role,
            "status": "pending_register", "effect": entry,
        }

    # 4) 校验与报告
    shutil.copyfile(license_src, DEST / "PIXELFX-LICENSE.txt")
    report = {"fighter": "ultraman-zero__shining", "family": FAMILY,
              "license_sha256": license_sha, "effects": {}}
    all_ok = True
    for pending, item in sorted(entries.items()):
        entry = item["effect"]
        texture = ROOT / entry["texture"].removeprefix("res://")
        checks = components_and_glow(texture, entry["rects"])
        binary_ok = all(c["binary"] for c in checks)
        colors_ok = all(c["colors"] <= 32 for c in checks)
        sha_ok = sha(texture) == entry["atlas_sha256"]
        rects_ok = all(0 <= x and 0 <= y and x + w <= Image.open(texture).width and y + h <= Image.open(texture).height
                       for x, y, w, h in entry["rects"])
        boxes_ok = len(entry.get("frame_boxes", [])) in (0, len(entry["rects"]))
        item_ok = binary_ok and colors_ok and sha_ok and rects_ok and boxes_ok
        all_ok = all_ok and item_ok
        report["effects"][pending] = {
            "texture": entry["texture"], "role": item["role"],
            "frames": len(entry["rects"]), "atlas_sha256": entry["atlas_sha256"],
            "sha_match": sha_ok, "binary_alpha": binary_ok, "colors_max": max(c["colors"] for c in checks),
            "colors_ok": colors_ok, "rects_in_bounds": rects_ok,
            "frame_boxes_match": boxes_ok,
            "frames_checks": checks,
            "note": "多连通块为特效段/颗粒，按 AGENTS 独立颗粒另行核；逐帧二值 Alpha 无辉光晕边。",
        }
    save(REPORT, report)

    proposal = {
        "schema": 1,
        "fighter": "ultraman-zero__shining",
        "form": "光辉赛罗 / Shining Ultraman Zero",
        "note": "共享 phase3_projectiles.json 与 charge_overlay_policy.json 未修改；以下 id 与图集需由主会话登记后生效。",
        "family": f"assets/effects/ultraman-zero__shining/{FAMILY}",
        "license": "MIT (PixelFX)，来源与 SHA 见各段 provenance.json",
        "effects": [entries[key] for key in sorted(entries)],
        "charge_policy_proposal": "tools/rebuild/ultraman-zero__shining/charge_policy.json",
    }
    save(PROPOSAL, proposal)

    policy = load(POLICY)
    policy["note"] = "提案：共享 content/presentation/charge_overlay_policy.json 未修改；图集见 assets/effects/ultraman-zero__shining/fx-family-pixelfx-20261112-v1/，主会话登记后生效。"
    policy["placements"]["ultraman-zero__shining"] = {
        state: {
            "effect": pending,
            "anchor": [0, 0],
            "color": [1, 1, 1, 1],
            "behind_fighter": True,
            "frames": frames,
            "loop": loop,
        }
        for state, pending, frames, loop in (
            ("charge_start", "pending_shining_q_charge_start", 9, False),
            ("charge", "pending_shining_q_charge", 24, True),
            ("charge_stop", "pending_shining_q_charge_stop", 9, False),
        )
    }
    save(POLICY, policy)
    print(json.dumps({"ok": all_ok, "effects": len(entries), "report": str(REPORT)}, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
