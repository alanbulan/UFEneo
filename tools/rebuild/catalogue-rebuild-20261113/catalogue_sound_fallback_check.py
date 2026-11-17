"""Read-only audit of the catalogue UI's per-entry sound selection.

It mirrors the static lookup order in `ui/kit/catalogue_sound.gd`: fixed own-voice
resources, then the installed `voices[base].intro` record, then the generic pick
sound. It does not generate or play audio and is not a listening review.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VOICE_CANDIDATES = (
    "assets/audio/characters/{base}/roars-v3/intro.wav",
    "assets/audio/characters/{base}/roar_threat.wav",
    "assets/audio/characters/{base}/c-type/preview-v001/call-1/sound.wav",
)
NON_SELF_INTRO = {"ultraman-arc", "ultraman-omega"}
INSTALLED = {"installed", "installed_pending_user_listening"}
OTHER_VOICE_KEYS = ("victory", "attack", "taunt", "timeout", "down", "heavy", "super")


def sound_path(root: Path, sounds: dict, sound_id: str) -> Path:
    record = sounds.get(sound_id, {})
    path = str(record.get("path", "")) if isinstance(record, dict) else ""
    if not path.startswith("res://"):
        return Path()
    return root / path.removeprefix("res://")


def main() -> None:
    display = json.loads((ROOT / "content/roster/catalogue_display.json").read_text(encoding="utf-8"))["entries"]
    runtime = json.loads((ROOT / "content/audio/runtime.json").read_text(encoding="utf-8"))
    sources = json.loads((ROOT / "content/audio/sources.json").read_text(encoding="utf-8"))
    sounds = runtime.get("sounds", {})
    voice_map = runtime.get("voices", {})
    statuses = {
        str(record.get("id", "")): str(record.get("runtime_status", "installed"))
        for record in sources.get("records", [])
        if isinstance(record, dict)
    }
    counts: Counter[str] = Counter()
    fixed_voice_ids: list[str] = []
    intro_voice_ids: list[str] = []
    other_voice_ids: list[str] = []
    missing_runtime_paths: list[str] = []
    for cid, entry in display.items():
        base = str(entry.get("base_character") or cid)
        found = ""
        for candidate in VOICE_CANDIDATES:
            relative = candidate.format(base=base)
            if (ROOT / relative).is_file():
                found = relative
                break
        if found:
            counts["own_voice_fixed_resource"] += 1
            fixed_voice_ids.append(cid)
            continue
        intro_id = ""
        intro_file = Path()
        if base not in NON_SELF_INTRO:
            voice = voice_map.get(base, {})
            intro_id = str(voice.get("intro", "")) if isinstance(voice, dict) else ""
            if intro_id and statuses.get(intro_id) in INSTALLED:
                intro_file = sound_path(ROOT, sounds, intro_id)
                if not intro_file.name or not intro_file.is_file():
                    missing_runtime_paths.append(f"{cid}:{intro_id}:{intro_file.relative_to(ROOT) if intro_file.is_relative_to(ROOT) else intro_file}")
                    intro_id = ""
        if intro_id:
            counts["own_voice_runtime_intro"] += 1
            intro_voice_ids.append(cid)
            continue
        voice = voice_map.get(base, {})
        other_found = False
        if isinstance(voice, dict):
            for key in OTHER_VOICE_KEYS:
                sound_id = str(voice.get(key, ""))
                if not sound_id or sound_id not in sounds:
                    continue
                path = sound_path(ROOT, sounds, sound_id)
                if path.name and path.is_file():
                    counts["runtime_voice_available_but_not_selected"] += 1
                    other_voice_ids.append(cid)
                    other_found = True
                    break
        if not other_found:
            counts["generic_fallback"] += 1
        if base in NON_SELF_INTRO:
            counts["non_self_intro_excluded"] += 1
    print(json.dumps({
        "check": "catalogue_sound_fallback",
        "total_entries": len(display),
        "counts": dict(counts),
        "own_voice_fixed_ids": sorted(fixed_voice_ids),
        "own_voice_runtime_intro_ids": sorted(intro_voice_ids),
        "runtime_voice_ids_not_selected_sample": sorted(other_voice_ids)[:30],
        "missing_runtime_paths": missing_runtime_paths[:30],
        "music_model_generated": False,
        "listening_reviewed": False,
        "note": "按 display 条目静态推演 ui/kit/catalogue_sound.gd 的固定候选→runtime intro→通用 pick 选路；UI 实际还会归并 aliases，且静态资源存在不等于实机播放或听审通过。",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
