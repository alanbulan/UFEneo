"""按已装机基准角色列出新角色的完整度缺口（只读，不生成素材）。

基准：ultraman-taro（102 clip / 49 本地招式 / 53 状态音效）。护甲形态专用的
super_transform、super_special3 不计入通用完整度；空中必杀 air_special 属
通用战斗能力，必须存在。招式以模板清单 47 项为通用要求（含 special2/3、
air_special、taunt），本地招式文件缺失而靠模板回退的也算缺口：模板帧数常与
本角色 clip 帧数不一致，会取错 sprite。

用法：
    .venv/bin/python tools/art/parity_matrix.py
    .venv/bin/python tools/art/parity_matrix.py --fighter ultraman-zero --json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "ultraman-taro"
NEW = [
    "ultraman-justice", "ultraman-zero", "zoffy", "mother-of-ultra",
    "ultraman-gaia", "ultraman-king", "father-of-ultra",
]
FORM_ONLY = {"super_transform", "super_special3"}


def read(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def clips_of(fighter: str) -> dict:
    man = read(ROOT / f"assets/fighters/{fighter}/animations/manifest.json", {})
    return man.get("clips", {})


def frames_of(clip: dict | None) -> int:
    return len(clip.get("rects", [])) if clip else 0


def move_ids_required() -> list[str]:
    return list(read(ROOT / "content/templates/humanoid/move_manifest.json", []))


def local_moves(fighter: str) -> dict:
    d = ROOT / f"content/fighters/{fighter}/moves"
    if not d.is_dir():
        return {}
    return {p.stem: read(p) for p in d.glob("*.json")}


def audio_coverage(fighter: str) -> dict:
    state_events = read(ROOT / "content/audio/state_events.json", {}).get(fighter, {})
    runtime = read(ROOT / "content/audio/runtime.json", {})
    return {
        "state_events": len(state_events),
        "voices": fighter in runtime.get("voices", {}),
        "footsteps": fighter in runtime.get("footsteps", {}),
        "frame_sounds": fighter in runtime.get("frame_sounds", {}),
    }


def report(fighter: str, base_clips: dict, required_clips: list[str], required_moves: list[str]) -> dict:
    clips = clips_of(fighter)
    moves = local_moves(fighter)
    unsupported = set(read(ROOT / f"content/fighters/{fighter}/definition.json", {}).get("unsupported_moves", []))
    missing_clips = [{"clip": c, "frames": frames_of(base_clips.get(c))} for c in required_clips if c not in clips]
    missing_moves = []
    for move_id in required_moves:
        if move_id in unsupported:
            continue
        if move_id not in moves:
            missing_moves.append({"move": move_id, "clip": move_id in clips})
            continue
        data = moves[move_id]
        clip = clips.get(move_id)
        n = frames_of(clip)
        if n:
            bad = [f["sprite"] for f in data.get("frames", []) if not 0 <= int(f.get("sprite", 0)) < n]
            if bad:
                missing_moves.append({"move": move_id, "clip": True, "sprite_overflow": len(bad), "clip_frames": n, "move_frames": len(data.get("frames", []))})
    states = read(ROOT / f"content/fighters/{fighter}/state_frames.json", {})
    # 附加招式（如 crouch_sweep/bounce_*）不在模板 47 项里，但有本地招式文件，
    # 属招式而非状态，不应要求 state_frames 条目。
    state_missing = [c for c in clips if c not in required_moves and c not in moves and c not in states]
    supers = read(ROOT / "content/presentation/supers.json", {})
    return {
        "fighter": fighter,
        "clips": len(clips),
        "required_clips": len(required_clips),
        "missing_clips": missing_clips,
        "local_moves": len(moves),
        "required_moves": len(required_moves),
        "missing_moves": missing_moves,
        "unsupported_moves": sorted(unsupported),
        "state_frames_missing": state_missing,
        "audio": audio_coverage(fighter),
        "supers": fighter in supers,
        "portrait": (ROOT / f"assets/effects/{fighter}/super_portrait/atlas.png").is_file(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    base_clips = clips_of(BASE)
    required_clips = sorted(c for c in base_clips if c not in FORM_ONLY)
    required_moves = move_ids_required()
    fighters = args.fighter or NEW
    rows = [report(f, base_clips, required_clips, required_moves) for f in fighters]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    base_states = read(ROOT / "content/audio/state_events.json", {}).get(BASE, {})
    print(f"基准 {BASE}: {len(base_clips)} clips / {len(required_clips)} 通用 clips / "
          f"{len(required_moves)} 招 / {len(base_states)} 状态音效")
    for r in rows:
        print(f"\n== {r['fighter']}  clips {r['clips']}/{r['required_clips']}  moves {r['local_moves']}/{r['required_moves']}"
              f"  supers {'有' if r['supers'] else '缺'}  portrait {'有' if r['portrait'] else '缺'}")
        if r["missing_clips"]:
            print("  缺 clip: " + "、".join(f"{m['clip']}({m['frames']})" for m in r["missing_clips"]))
        if r["missing_moves"]:
            print("  缺/错 move: " + "、".join(
                m["move"] + ("[sprite %d]" % m["sprite_overflow"] if "sprite_overflow" in m else "") for m in r["missing_moves"]))
        if r["state_frames_missing"]:
            print("  state_frames 缺: " + "、".join(r["state_frames_missing"]))
        a = r["audio"]
        print(f"  音效: state_events {a['state_events']}/{len(base_states)}  voices {'有' if a['voices'] else '缺'}"
              f"  footsteps {'有' if a['footsteps'] else '缺'}  frame_sounds {'有' if a['frame_sounds'] else '缺'}")


if __name__ == "__main__":
    main()
