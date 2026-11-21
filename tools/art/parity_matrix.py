"""核对角色的具体动作、状态、资源和声音引用；存在缺口时退出码为 1。

通用要求来自 ultraman-taro 与 humanoid 招式清单；本地招式不能靠模板回退
冒充完成。unsupported_moves 必须逐项附有 unsupported_reasons，包含有依据
不制作的 air_special。已登记变身使用自己的时间轴，不要求伪造状态帧。
只核对数据与本机资源完整度，不代表美术或听感通过。

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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clips_of(fighter: str) -> dict:
    man = read(ROOT / f"assets/fighters/{fighter}/animations/manifest.json", {})
    return man.get("clips", {})


def frames_of(clip: dict | None) -> int:
    rects = clip.get("rects", []) if isinstance(clip, dict) else []
    return len(rects) if isinstance(rects, list) else 0


def move_ids_required() -> list[str]:
    return list(read(ROOT / "content/templates/humanoid/move_manifest.json", []))


def local_moves(fighter: str) -> dict:
    directory = ROOT / f"content/fighters/{fighter}/moves"
    if not directory.is_dir():
        return {}
    return {path.stem: read(path) for path in sorted(directory.glob("*.json"))}


def resource_exists(reference: str) -> bool:
    if not isinstance(reference, str) or not reference.startswith("res://"):
        return False
    path = (ROOT / reference.removeprefix("res://")).resolve()
    return path.is_relative_to(ROOT.resolve()) and path.is_file()


def resource_references(value) -> set[str]:
    if isinstance(value, str):
        return {value} if value.startswith("res://") else set()
    if isinstance(value, dict):
        children = [child for key, child in value.items() if key != "authoring_source" or not isinstance(child, str)]
    else:
        children = value if isinstance(value, list) else []
    return set().union(*(resource_references(child) for child in children))


def sound_references(value) -> set[str]:
    found = set()
    if isinstance(value, dict):
        if value.get("kind") == "sound":
            found.add(str(value.get("id", "")))
        for key, child in value.items():
            if key in {"audio_loop", "guard_sound", "return_sound", "sound"} and isinstance(child, str) and child:
                found.add(child)
            elif key == "audio" and isinstance(child, dict):
                found.update(sound for sound in child.values() if isinstance(sound, str) and sound)
            elif key == "sounds" and isinstance(child, list):
                found.update(sound for sound in child if isinstance(sound, str))
            found.update(sound_references(child))
    elif isinstance(value, list):
        for child in value:
            found.update(sound_references(child))
    return found


def effect_references(value) -> set[str]:
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"effect", "impact_effect", "block_effect", "guard_effect", "launch_effect", "return_effect", "trail_effect", "pair_trail_effect", "spark", "block_spark"} and isinstance(child, str) and child:
                found.add(child)
            found.update(effect_references(child))
    elif isinstance(value, list):
        for child in value:
            found.update(effect_references(child))
    return found


def form_bindings(fighter: str) -> list[dict]:
    bindings = {}
    for owner, source in read(ROOT / "content/catalogs/battle_forms.json", {}).get("forms", {}).items():
        if not source.get("enabled", False):
            continue
        for form in [source, *source.get("choices", [])]:
            if not form.get("enabled", False) or not form.get("implemented", True):
                continue
            displayed = form.get("target") if form.get("mode") == "definition" else owner
            if displayed != fighter:
                continue
            path = form.get("transform", "")
            timeline = read(ROOT / path.removeprefix("res://"), {}) if resource_exists(path) else {}
            for field, sequence in [("transform_animation", "frames"), ("entry_animation", "entry_frames")]:
                if form.get(field):
                    bindings[(form[field], path, sequence)] = {"clip": form[field], "path": path, "frames": timeline.get(sequence, [])}
            if form.get("mode") == "palette" and form.get("super_move"):
                path = form["super_move"]
                move = read(ROOT / path.removeprefix("res://"), {}) if resource_exists(path) else {}
                clip = move.get("id", Path(path).stem)
                bindings[(clip, path, "frames")] = {"clip": clip, "path": path, "frames": move.get("frames", [])}
    return list(bindings.values())


def sprite_overflow(frames, ranges: list[tuple[int, int]]) -> int:
    if not isinstance(frames, list) or not frames:
        return 1
    invalid = 0
    for frame in frames:
        sprite = frame.get("sprite") if isinstance(frame, dict) else None
        if type(sprite) not in (int, float) or not float(sprite).is_integer() or not any(start <= sprite < end for start, end in ranges):
            invalid += 1
    return invalid


def clip_range(clip: dict) -> tuple[int, int]:
    offset = int(clip.get("simulation_sprite_offset", 0))
    return offset, offset + frames_of(clip)


def audio_coverage(fighter: str, moves: dict, states: dict, unsupported: set[str]) -> dict:
    all_states = read(ROOT / "content/audio/state_events.json", {})
    state_events = all_states.get(fighter, {})
    runtime = read(ROOT / "content/audio/runtime.json", {})
    voices = runtime.get("voices", {}).get(fighter, {})
    footsteps = runtime.get("footsteps", {}).get(fighter, {})
    frame_sounds = runtime.get("frame_sounds", {}).get(fighter, {})
    missing = []
    valid_footsteps = set()
    for name in ["walk_forward", "walk_back"]:
        step = footsteps.get(name, {})
        cycle = step.get("cycle_ticks", 0)
        contacts = step.get("contacts", [])
        sounds = step.get("sounds", [])
        if (type(cycle) is int and cycle > 0
                and isinstance(contacts, list) and contacts
                and all(type(contact) is int and 0 <= contact < cycle for contact in contacts)
                and contacts == sorted(set(contacts))
                and isinstance(sounds, list) and sounds
                and all(isinstance(sound, str) and sound for sound in sounds)):
            valid_footsteps.add(name)
        else:
            missing.append("footsteps." + name)
    for name in set(all_states.get(BASE, {})) - unsupported - FORM_ONLY:
        if not state_events.get(name) and name not in valid_footsteps:
            missing.append("state_events." + name)
    for name in set(runtime.get("voices", {}).get(BASE, {})) - unsupported:
        if not isinstance(voices.get(name), str) or not voices[name]:
            missing.append("voices." + name)
    for name in set(runtime.get("frame_sounds", {}).get(BASE, {})) - unsupported - FORM_ONLY:
        cues = frame_sounds.get(name, {})
        emitted = any(event.get("kind") == "sound" and event.get("id") for frame in moves.get(name, {}).get("frames", []) for event in frame.get("events", []))
        if not any(cues.values()) and not emitted:
            missing.append("frame_sounds." + name)
    for name, mapping in [("state_events", state_events), ("voices", voices), ("footsteps", footsteps), ("frame_sounds", frame_sounds)]:
        if not mapping:
            missing.append(name)
    references = sound_references([state_events, footsteps, frame_sounds, moves, states]) | set(voices.values())
    unknown = []
    missing_resources = []
    sounds = runtime.get("sounds", {})
    for sound in sorted(references):
        resolved = sound if sound in sounds else runtime.get("aliases", {}).get(sound, sound)
        if resolved not in sounds:
            unknown.append(sound)
        else:
            path = sounds[resolved].get("path", "")
            if not resource_exists(path):
                missing_resources.append(path or "sounds." + resolved + ".path")
    return {
        "state_events": len(state_events),
        "voices": bool(voices),
        "footsteps": bool(footsteps),
        "frame_sounds": bool(frame_sounds),
        "missing_mappings": sorted(set(missing)),
        "unknown_sounds": unknown,
        "missing_resources": sorted(set(missing_resources)),
    }


def report(fighter: str, base_clips: dict, required_clips: list[str], required_moves: list[str]) -> dict:
    clips = clips_of(fighter)
    moves = local_moves(fighter)
    definition = read(ROOT / f"content/fighters/{fighter}/definition.json", {})
    declared_unsupported = set(definition.get("unsupported_moves", []))
    reasons = definition.get("unsupported_reasons", {})
    declared_moves = set(read(ROOT / f"content/fighters/{fighter}/move_manifest.json", []))
    known_moves = set(required_moves) | declared_moves | set(moves)
    justified = {move for move in declared_unsupported if isinstance(reasons.get(move), str) and reasons[move].strip()}
    unsupported_errors = sorted(declared_unsupported - justified)
    unsupported_unknown = sorted(declared_unsupported - known_moves)
    unsupported = justified & known_moves
    bindings = form_bindings(fighter)
    form_clips = {binding["clip"] for binding in bindings}
    expected_moves = known_moves - unsupported
    expected_clips = (set(required_clips) | expected_moves | form_clips) - unsupported
    missing_clips = [{"clip": clip, "frames": frames_of(base_clips.get(clip))} for clip in sorted(expected_clips - set(clips))]
    invalid_clips = sorted(clip for clip, data in clips.items() if not frames_of(data) or not isinstance(data.get("texture"), str) or not data["texture"].startswith("res://"))
    missing_moves = []
    for move_id in sorted(expected_moves):
        if not isinstance(moves.get(move_id), dict) or not moves[move_id].get("frames"):
            missing_moves.append({"move": move_id, "clip": move_id in clips})
            continue
        data = moves[move_id]
        count = frames_of(clips.get(move_id))
        overflow = sprite_overflow(data["frames"], [(0, count)])
        if overflow:
            missing_moves.append({"move": move_id, "clip": move_id in clips, "sprite_overflow": overflow, "clip_frames": count, "move_frames": len(data["frames"])})
    states = read(ROOT / f"content/fighters/{fighter}/state_frames.json", {})
    state_clips = (set(required_clips) | set(clips)) - set(required_moves) - declared_moves - set(moves) - form_clips - unsupported
    air_aliases = {"vertical_air": "vertical_jump", "diagonal_air": "flip_forward", "backward_air": "flip_back", "chase_air": "chase_takeoff"}
    required_states = state_clips | {key for key, clip in air_aliases.items() if clip in expected_clips}
    state_missing = sorted(key for key in required_states if not states.get(key))
    invalid_states = []
    for state, frames in states.items():
        clip = air_aliases.get(state, state)
        if clip not in clips:
            continue
        ranges = [clip_range(clips[clip])]
        if state == "dash" and all("simulation_sprite_offset" in clips.get(key, {}) for key in ["dash_start", "dash", "dash_stop"]):
            ranges = [clip_range(clips[key]) for key in ["dash_start", "dash", "dash_stop"]]
        overflow = sprite_overflow(frames, ranges)
        if overflow:
            invalid_states.append({"state": state, "clip": clip, "sprite_overflow": overflow})
    invalid_forms = []
    for binding in bindings:
        overflow = sprite_overflow(binding["frames"], [(0, frames_of(clips.get(binding["clip"])))])
        if overflow:
            invalid_forms.append({"clip": binding["clip"], "path": binding["path"], "sprite_overflow": overflow})
    supers = read(ROOT / "content/presentation/supers.json", {}).get(fighter, {})
    audio = audio_coverage(fighter, {key: move for key, move in moves.items() if key not in unsupported and isinstance(move, dict)}, states, unsupported)
    resources = resource_references([clips, moves, states, definition.get("presentation", {}), supers, bindings])
    effect_ids = effect_references([clips, moves, states, bindings])
    effects = read(ROOT / "content/presentation/phase3_projectiles.json", {})
    for effect in effect_ids & effects.keys():
        source = effects[effect]
        resources.update(resource_references({key: value for key, value in source.items() if key != "beam_fighter_variants"}))
        resources.update(resource_references(source.get("beam_fighter_variants", {}).get(fighter, {})))
    resources.update("res://" + path for path in [f"content/fighters/{fighter}/definition.json", f"content/fighters/{fighter}/state_frames.json", f"assets/fighters/{fighter}/animations/manifest.json", "content/audio/runtime.json", "content/audio/state_events.json", "content/templates/humanoid/move_manifest.json", "content/catalogs/battle_forms.json", "content/presentation/phase3_projectiles.json"])
    missing_resources = sorted({path for path in resources if not resource_exists(path)} | set(audio["missing_resources"]))
    result = {
        "fighter": fighter,
        "clips": len(clips),
        "required_clips": len(expected_clips),
        "missing_clips": missing_clips,
        "invalid_clips": invalid_clips,
        "local_moves": len(moves),
        "required_moves": len(expected_moves),
        "missing_moves": missing_moves,
        "unsupported_moves": sorted(declared_unsupported),
        "unsupported_without_reason": unsupported_errors,
        "unsupported_unknown_moves": unsupported_unknown,
        "state_frames_missing": state_missing,
        "state_frames_invalid": invalid_states,
        "form_clips": sorted(form_clips),
        "form_frames_invalid": invalid_forms,
        "unknown_effects": sorted(effect_ids - effects.keys()),
        "missing_resources": missing_resources,
        "audio": audio,
        "supers": bool(supers.get("background")) and resource_exists(supers["background"]),
        "portrait": resource_exists(supers.get("portrait", "")),
    }
    result["passed"] = not any(result[key] for key in ["missing_clips", "invalid_clips", "missing_moves", "unsupported_without_reason", "unsupported_unknown_moves", "state_frames_missing", "state_frames_invalid", "form_frames_invalid", "unknown_effects", "missing_resources"]) and not audio["missing_mappings"] and not audio["unknown_sounds"] and result["supers"] and result["portrait"]
    return result


def main() -> int:
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
        return 0 if all(row["passed"] for row in rows) else 1
    base_states = read(ROOT / "content/audio/state_events.json", {}).get(BASE, {})
    print(f"基准 {BASE}: {len(base_clips)} clips / {len(required_clips)} 通用 clips / "
          f"{len(required_moves)} 招 / {len(base_states)} 状态音效")
    for row in rows:
        print(f"\n== {row['fighter']}  {'PASS' if row['passed'] else 'FAIL'}  clips {row['clips']}/{row['required_clips']}  moves {row['local_moves']}/{row['required_moves']}"
              f"  supers {'有' if row['supers'] else '缺'}  portrait {'有' if row['portrait'] else '缺'}")
        if row["missing_clips"]:
            print("  缺 clip: " + "、".join(f"{missing['clip']}({missing['frames']})" for missing in row["missing_clips"]))
        if row["missing_moves"]:
            print("  缺/错 move: " + "、".join(
                missing["move"] + ("[sprite %d]" % missing["sprite_overflow"] if "sprite_overflow" in missing else "") for missing in row["missing_moves"]))
        for key in ["invalid_clips", "unsupported_without_reason", "unsupported_unknown_moves", "state_frames_missing", "state_frames_invalid", "form_frames_invalid", "unknown_effects", "missing_resources"]:
            if row[key]:
                print("  " + key + ": " + json.dumps(row[key], ensure_ascii=False))
        audio = row["audio"]
        print(f"  音效: state_events {audio['state_events']}/{len(base_states)}  voices {'有' if audio['voices'] else '缺'}"
              f"  footsteps {'有' if audio['footsteps'] else '缺'}  frame_sounds {'有' if audio['frame_sounds'] else '缺'}")
        for key in ["missing_mappings", "unknown_sounds"]:
            if audio[key]:
                print("  音效 " + key + ": " + "、".join(audio[key]))
    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
