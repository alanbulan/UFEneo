"""将已落格 cell 安装为 luna_miracle 动画 atlas/manifest，不改 definition/selection。"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
FIGHTER = "ultraman-zero__luna_miracle"
CELLS_DIR = ROOT / "art/fighters" / FIGHTER / "stage1/cells"
ANIM_ROOT = ROOT / "assets/fighters" / FIGHTER / "animations"
MANIFEST_PATH = ANIM_ROOT / "manifest.json"
LOOP_CLIPS = {"idle", "walk_forward", "walk_back", "crouch", "dash", "charge", "guard", "block"}
TICKS = 10


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_cells() -> dict[str, list[Path]]:
    groups: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for p in sorted(CELLS_DIR.glob("*-cell.png")):
        stem = p.name[: -len("-cell.png")]
        parts = stem.split("-")
        index_at = -1
        for pos in range(len(parts) - 1, 0, -1):
            if len(parts[pos]) == 2 and parts[pos].isdigit():
                index_at = pos
                break
        if index_at < 0:
            continue
        clip = "_".join("-".join(parts[:index_at]).split("-"))
        idx = parts[index_at]
        groups[clip].append((idx, p))
    out: dict[str, list[Path]] = {}
    for clip, items in groups.items():
        items.sort(key=lambda t: t[0])
        seen = set()
        frames = []
        for idx, path in items:
            if idx in seen:
                continue
            seen.add(idx)
            frames.append(path)
        out[clip] = frames
    return out


def main() -> int:
    groups = collect_cells()
    if not groups:
        raise SystemExit("no cells found")
    cells_json = json.loads((CELLS_DIR / "cells.json").read_text(encoding="utf-8"))

    if MANIFEST_PATH.is_file():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        manifest = {
            "schema": 1,
            "cell": [256, 256],
            "anchor": [128, 248],
            "reviewed": False,
            "identity_revision": "root_delegated_by_user_2026-11-10",
            "clips": {},
        }

    clips = OrderedDict(sorted(manifest.get("clips", {}).items()))
    installed = []

    for clip in sorted(groups):
        frames = groups[clip]
        with Image.open(frames[0]) as im:
            cw, ch = im.size
        atlas = Image.new("RGBA", (cw * len(frames), ch))
        for i, fp in enumerate(frames):
            with Image.open(fp) as im:
                im = im.convert("RGBA")
                if im.size != (cw, ch):
                    im = im.resize((cw, ch))
                atlas.alpha_composite(im, (cw * i, 0))
        clip_dir = ANIM_ROOT / clip
        clip_dir.mkdir(parents=True, exist_ok=True)
        atlas_path = clip_dir / "atlas.png"
        atlas.save(atlas_path)

        # anchor: prefer standing foot_row from cells records
        foot_rows = []
        for rec in cells_json.get("frames", []):
            name = str(rec.get("frame", ""))
            if name.startswith(clip + "-") and rec.get("standing") is True and isinstance(rec.get("foot_row"), int):
                foot_rows.append(int(rec["foot_row"]))
        if foot_rows:
            clip_anchor = [cw // 2, max(foot_rows) + 1]
        else:
            prior = clips.get(clip) or {}
            pa = prior.get("anchor")
            pc = prior.get("cell")
            if isinstance(pc, int):
                pc = [pc, pc]
            if isinstance(pa, list) and len(pa) == 2 and pc in ([cw, ch], cw if cw == ch else None):
                clip_anchor = [int(pa[0]), int(pa[1])]
            else:
                clip_anchor = [cw // 2, ch - 8]

        rects = [[cw * i, 0, cw, ch] for i in range(len(frames))]
        entry = {
            "texture": f"res://assets/fighters/{FIGHTER}/animations/{clip}/atlas.png",
            "cell": cw if cw == ch else [cw, ch],
            "anchor": list(clip_anchor),
            "anchor_y": int(clip_anchor[1]),
            "anchors": [list(clip_anchor) for _ in frames],
            "rects": rects,
            "ticks": [TICKS] * len(frames),
            "loop": clip in LOOP_CLIPS,
            "atlas_sha256": sha256_file(atlas_path),
        }
        clips[clip] = entry
        installed.append((clip, len(frames), [cw, ch], clip_anchor))

    manifest["clips"] = OrderedDict(sorted(clips.items()))
    # keep top-level cell/anchor as 256-grid defaults for this fighter
    manifest.setdefault("schema", 1)
    manifest.setdefault("cell", [256, 256])
    manifest.setdefault("anchor", [128, 248])
    ANIM_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"installed": installed, "total_clips": len(clips)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
