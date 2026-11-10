"""把 stage1 已落格的 *-cell.png 安装进 assets/fighters/<id>/animations/。

生成每个 clip 的 atlas.png（水平拼接）与 manifest.json（schema 1），复制
catalogue/model-native.png，并更新 content/definition.json 与 selection.json 登记。

用法：
    .venv/bin/python tools/art/install_cells.py --fighter ultraman-king
    .venv/bin/python tools/art/install_cells.py --fighter ultraman-zero --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from collections import defaultdict, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FIGHTER_ASSETS = ROOT / "assets" / "fighters"
CONTENT = ROOT / "content" / "fighters"
SELECTION = ROOT / "content" / "roster" / "selection.json"

LOOP_CLIPS = {"idle", "walk_forward", "walk_back", "crouch", "dash", "charge", "guard", "block"}
TICKS = 10

DISPLAY_NAMES = {
    "ultraman-king": "奥特之王",
    "ultraman-zero": "赛罗奥特曼",
    "zoffy": "佐菲",
    "mother-of-ultra": "奥特之母",
    "ultraman-gaia": "盖亚奥特曼",
    "ultraman-justice": "杰斯提斯奥特曼",
    "astra": "阿斯特拉",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def cell_size(path: Path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def collect_cells(fighter: str):
    cells_dir = ROOT / "art" / "fighters" / fighter / "stage1" / "cells"
    if not cells_dir.is_dir():
        raise SystemExit(f"缺少 cells 目录：{cells_dir}")
    groups = defaultdict(list)
    candidates = defaultdict(list)
    for p in sorted(cells_dir.glob("*-cell.png")):
        stem = p.name[: -len("-cell.png")]
        if "candidate" in stem:
            # 候选锚定帧：作为该 clip 的后备（仅在无编号帧时使用）
            base = stem.replace("idle-candidate", "idle").split("-")[0]
            # normalize: candidate frames are idle
            candidates["idle"].append(("99-cand", p))
            continue
        if "review" in stem:
            continue
        # 从右往左找序号段：`motion-22-00` 的 clip 是 motion-22，不能被
        # 非贪婪正则吃成 `motion` + 序号 22。序号后允许跟备注段（run-00-v5）。
        parts = stem.split("-")
        index_at = -1
        for pos in range(len(parts) - 1, 0, -1):
            if len(parts[pos]) == 2 and parts[pos].isdigit():
                index_at = pos
                break
        if index_at < 0:
            continue
        clip = "-".join(parts[:index_at]).replace("-", "_")
        idx = parts[index_at]
        groups[clip].append((idx, p))
    # fallback: use candidates where no numbered frames exist
    for clip, frames in candidates.items():
        if clip not in groups or not groups[clip]:
            groups[clip] = frames
    for clip in groups:
        groups[clip].sort(key=lambda t: t[0])
        seen = set()
        deduped = []
        for idx, path in groups[clip]:
            if idx in seen:
                continue
            seen.add(idx)
            deduped.append((idx, path))
        groups[clip] = deduped
    return groups, cells_dir


def load_cells_json(fighter: str):
    p = ROOT / "art" / "fighters" / fighter / "stage1" / "cells" / "cells.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def anchor_for(fighter, cell_w, cell_h, cells_json):
    if isinstance(cells_json, dict):
        a = cells_json.get("anchor")
        if isinstance(a, (list, tuple)) and len(a) == 2 and all(x is not None for x in a):
            return [int(a[0]), int(a[1])]
    return [cell_w // 2, cell_h - 8]


def build_atlas(frames, cell_w, cell_h):
    from PIL import Image
    atlas = Image.new("RGBA", (cell_w * len(frames), cell_h))
    for i, p in enumerate(frames):
        with Image.open(p) as im:
            im = im.convert("RGBA")
            if im.size != (cell_w, cell_h):
                im = im.resize((cell_w, cell_h))
            atlas.alpha_composite(im, (cell_w * i, 0))
    return atlas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--only", default="", help="逗号分隔的 clip 名；只装这些")
    ap.add_argument("--merge", action="store_true",
                    help="保留 manifest 里未重装的 clip（合成/改名过的帧不被清掉）")
    args = ap.parse_args()

    fighter = args.fighter
    groups, cells_dir = collect_cells(fighter)
    if not groups:
        raise SystemExit(f"{fighter}: 没有可安装的 cell 帧")
    only = {c.strip() for c in args.only.split(",") if c.strip()}
    if only:
        groups = {c: v for c, v in groups.items() if c in only}
        if not groups:
            raise SystemExit(f"{fighter}: --only 没有匹配到任何 cell 组")

    first_cell = next(iter(groups.values()))[0][1]
    cw, ch = cell_size(first_cell)
    cells_json = load_cells_json(fighter)
    anchor = anchor_for(fighter, cw, ch, cells_json)

    anim_root = FIGHTER_ASSETS / fighter / "animations"
    print(f"{fighter}: {len(groups)} clips, cell {cw}x{ch}, anchor {anchor}")

    clips = OrderedDict()
    total_frames = 0
    for clip in sorted(groups):
        frames = [p for (_, p) in groups[clip]]
        total_frames += len(frames)
        atlas = build_atlas(frames, cw, ch)
        clip_dir = anim_root / clip
        atlas_path = clip_dir / "atlas.png"
        rects = [[cw * i, 0, cw, ch] for i in range(len(frames))]
        anchors = [list(anchor) for _ in frames]
        entry = {
            "texture": f"res://assets/fighters/{fighter}/animations/{clip}/atlas.png",
            "cell": cw if cw == ch else [cw, ch],
            "anchor": list(anchor),
            "anchor_y": anchor[1],
            "anchors": anchors,
            "rects": rects,
            "ticks": [args.ticks] * len(frames),
            "loop": clip in LOOP_CLIPS,
        }
        clips[clip] = entry
        if not args.dry_run:
            clip_dir.mkdir(parents=True, exist_ok=True)
            atlas.save(atlas_path)

    identity_revision = "root_delegated_by_user_2026-11-10"

    if args.merge and (anim_root / "manifest.json").is_file():
        existing = json.loads((anim_root / "manifest.json").read_text(encoding="utf-8"))
        merged = OrderedDict(sorted(existing.get("clips", {}).items()))
        merged.update(clips)
        clips = merged

    manifest = {
        "schema": 1,
        "cell": [cw, ch],
        "anchor": list(anchor),
        "reviewed": False,
        "identity_revision": identity_revision,
        "clips": clips,
    }

    if not args.dry_run:
        for clip, entry in clips.items():
            p = FIGHTER_ASSETS / fighter / "animations" / clip / "atlas.png"
            entry["atlas_sha256"] = sha256_file(p)

    manifest_path = anim_root / "manifest.json"
    if not args.dry_run:
        anim_root.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # copy model-native.png
    src_model = FIGHTER_ASSETS / fighter / "catalogue" / "model-native.png"
    dst_model = FIGHTER_ASSETS / fighter / "model-native.png"
    if src_model.is_file() and not args.dry_run and not dst_model.is_file():
        shutil.copy2(src_model, dst_model)

    # definition.json
    def_path = CONTENT / fighter / "definition.json"
    if not def_path.is_file():
        d = {
            "id": fighter,
            "display_name": DISPLAY_NAMES.get(fighter, fighter),
            "template": "humanoid",
            "production_status": "stage1_action_frames_installed",
            "playable": True,
            "max_health": 1000,
            "walk_speed": 2,
            "jump_speed": 16,
            "numeric_status": "stage1 动作帧已落格并安装；数值为占位，待实机校准。",
            "presentation": {
                "model": f"res://assets/fighters/{fighter}/model-native.png",
                "manifest": f"res://assets/fighters/{fighter}/animations/manifest.json",
                "native": True,
                "cell": cw if cw == ch else [cw, ch],
                "anchor": list(anchor),
                "target_height": ch - 8,
                "height_policy": "stage1 待机像素整帧；数值待校准。",
                "anchor_y": anchor[1],
            },
            "forms": ["default"],
            "identity_notes": "stage1 待机像素整帧身份锚；动作帧按同一比例落格。",
            "reference_file": f"content/fighters/{fighter}/catalogue_profile.json",
            "model_review_pending": False,
            "pilot_playable": True,
            "walks_installed": True,
            "selection_authorization": "root_delegated_by_user：stage1 动作帧已安装。",
            "pilot_manual_ready": True,
            "pilot_lock_reason": "",
            "unsupported_moves": [],
        }
    else:
        d = json.loads(def_path.read_text(encoding="utf-8"))
        d["playable"] = True
        d["select_visible"] = True
        d["selection_visible"] = True
        d["pilot_playable"] = True
        d["pilot_manual_ready"] = True
        d["walks_installed"] = True
        d["production_status"] = "stage1_action_frames_installed"
        d["pilot_lock_reason"] = ""
        if "stage2_status" in d:
            d["stage2_status"] = "stage1_action_frames_installed"
        if "presentation" in d and isinstance(d["presentation"], dict):
            d["presentation"]["manifest"] = f"res://assets/fighters/{fighter}/animations/manifest.json"
            d["presentation"]["model"] = f"res://assets/fighters/{fighter}/model-native.png"
            d["presentation"]["cell"] = cw if cw == ch else [cw, ch]
            d["presentation"]["anchor"] = list(anchor)
            d["presentation"]["anchor_y"] = anchor[1]
    if not args.dry_run:
        (CONTENT / fighter).mkdir(parents=True, exist_ok=True)
        def_path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # command_table.json 必须存在（空表继承模板指令）
    ct_path = CONTENT / fighter / "command_table.json"
    if not ct_path.is_file() and not args.dry_run:
        (CONTENT / fighter).mkdir(parents=True, exist_ok=True)
        ct_path.write_text("[]\n", encoding="utf-8")

    # generate minimal state_frames.json if missing (don't overwrite zero's good one)
    sf_path = CONTENT / fighter / "state_frames.json"
    if not sf_path.is_file():
        generic = {}
        for clip in clips:
            generic[clip] = [{
                "sprite": 0,
                "dx": 0,
                "dy": 0,
                "hitboxes": [],
                "hurtboxes": [[-cw // 4, 0, cw // 2, ch]],
                "cancel": [],
                "events": [],
            }]
        if not args.dry_run:
            sf_path.write_text(json.dumps(generic, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # update selection.json forms implemented：只认有 definition 且可玩、有清单的形态。
    if SELECTION.is_file():
        sel = json.loads(SELECTION.read_text(encoding="utf-8"))
        for e in sel.get("entries", []):
            if e.get("id") != fighter:
                continue
            for form in e.get("forms", []):
                fid = str(form.get("id", ""))
                base = fighter if fid == "default" else fid
                def_path = CONTENT / base / "definition.json"
                man_path = FIGHTER_ASSETS / base / "animations/manifest.json"
                ready = def_path.is_file() and man_path.is_file()
                if ready:
                    d = json.loads(def_path.read_text(encoding="utf-8"))
                    ready = bool(d.get("playable", True)) or bool(d.get("pilot_playable", False))
                form["implemented"] = ready
        if not args.dry_run:
            SELECTION.write_text(json.dumps(sel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"{fighter}: installed {len(clips)} clips / {total_frames} frames" + (" (dry-run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()

