"""把新角色的状态音效键补齐到已装机基准覆盖。

背景：side_audio 按 `state_events[角色][进入状态]` 播放声音；新角色只登记了
13 个键，而已装机基准（ultraman-taro）覆盖 53 个键。缺键不会报错，只是那
些状态静默。本工具补“缺的键”，保留已有声音；移除与脚步表重复的 walk
入态 step，缺失脚步绑定按本人行走 clip 的帧时长补齐，不改音频资源。

用法：
    .venv/bin/python tools/audio/fill_state_events.py
    .venv/bin/python tools/audio/fill_state_events.py --fighter ultraman-king --dry-run
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

# 语义对齐 taro 的 id：shift→step、skid→step、recover→step、voice_hit→hit_light、
# voice_down→down、entry→entry。只用 runtime.json 已登记的资源，避免新增空引用。
GENERIC = {
    "air_apex": "jump",
    "air_fall": "jump",
    "air_rise": "jump",
    "air_tech": "step",
    "backstep": "step",
    "blockstun": "guard",
    "bounce": "down",
    "charge": "charge",
    "charge_start": "charge",
    "charge_stop": "charge",
    "chase_takeoff": "jump",
    "crouch": "step",
    "crouch_blockstun": "guard",
    "crouch_guard": "guard",
    "crouch_rise": "step",
    "crouch_start": "step",
    "crouch_turn": "step",
    "dash": "dash",
    "dash_start": "dash",
    "dash_stop": "step",
    "defeat": "down",
    "dodge": "dodge",
    "down": "down",
    "flip_back": "jump",
    "flip_forward": "jump",
    "grabbed": "step",
    "guard": "guard",
    "guardbreak": "hit_heavy",
    "hit_air": "hit_light",
    "hit_crouch": "hit_light",
    "hit_high": "hit_light",
    "hit_mid": "hit_light",
    "idle": "step",
    "intro": "entry",
    "land": "land",
    "launch_fall": "hit_light",
    "launch_rise": "hit_light",
    "roll_back": "dodge",
    "roll_forward": "dodge",
    "stun": "hit_light",
    "takeoff": "jump",
    "throw_tech": "guard",
    "thrown_air": "down",
    "thrown_back": "down",
    "thrown_dash": "down",
    "thrown_forward": "down",
    "timeout": "entry",
    "turn": "step",
    "vertical_jump": "jump",
    "victory": "entry",
    "wake": "step",
}


WALK_STATES = ("walk_forward", "walk_back")


def build_footstep(fighter: str, key: str) -> dict:
    definition_path = ROOT / "content/fighters" / fighter / "definition.json"
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    manifest_ref = definition.get("presentation", {}).get("manifest", "")
    if not isinstance(manifest_ref, str) or not manifest_ref.startswith("res://"):
        raise SystemExit(f"{fighter}: 缺少本人图集 manifest，拒绝猜测脚步周期")
    manifest_path = ROOT / manifest_ref.removeprefix("res://")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clip = manifest.get("clips", {}).get(key, {})
    ticks = clip.get("ticks", [])
    if (
        not isinstance(ticks, list)
        or len(ticks) < 2
        or len(ticks) != len(clip.get("rects", []))
        or any(type(duration) is not int or duration <= 0 for duration in ticks)
        or not clip.get("loop", False)
    ):
        raise SystemExit(f"{fighter}/{key}: 行走 clip 缺失或帧时长无效，拒绝猜测脚步周期")
    return {
        "cycle_ticks": sum(ticks),
        "contacts": [0, sum(ticks[:len(ticks) // 2])],
        "sounds": ["step"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = ROOT / "content/audio/state_events.json"
    events = json.loads(path.read_text(encoding="utf-8"))
    runtime_path = ROOT / "content/audio/runtime.json"
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    known = set(runtime.get("sounds", {})) | set(runtime.get("aliases", {}))
    base_keys = sorted(events[BASE])
    missing_base = [k for k in base_keys if k not in GENERIC and k not in WALK_STATES]
    if missing_base:
        raise SystemExit(f"基准键没有通用映射：{missing_base}")
    for fighter in (args.fighter or NEW):
        table = events.setdefault(fighter, {})
        added = []
        removed = 0
        for key in base_keys:
            if key in WALK_STATES:
                cues = table.get(key, [])
                table[key] = [cue for cue in cues if not (cue.get("kind") == "sound" and cue.get("id") == "step")]
                removed += len(cues) - len(table[key])
                continue
            if key in table:
                continue
            sound = GENERIC[key]
            if sound not in known:
                raise SystemExit(f"{sound} 不在 runtime.json，拒绝写空引用")
            table[key] = [{"kind": "sound", "id": sound}]
            added.append(key)
        events[fighter] = {k: table[k] for k in sorted(table)}
        print(f"{fighter}: 补 {len(added)} 键，移除 {removed} 条重复步声，现有 {len(events[fighter])}/{len(base_keys)}")
    bad = []
    for fighter in (args.fighter or NEW):
        for key, cues in events[fighter].items():
            for cue in cues:
                if str(cue.get("id", "")) not in known:
                    bad.append((fighter, key, cue.get("id")))
    if bad:
        raise SystemExit(f"仍有无主引用：{bad[:10]}")
    footsteps = runtime.setdefault("footsteps", {})
    changed = False
    for fighter in (args.fighter or NEW):
        table = footsteps.setdefault(fighter, {})
        added = []
        for key in WALK_STATES:
            if key not in table:
                if "step" not in known:
                    raise SystemExit("step 不在 runtime.json，拒绝写空引用")
                table[key] = build_footstep(fighter, key)
                added.append(key)
        if added:
            changed = True
            print(f"{fighter}: 补脚步声 {added}")
    if args.dry_run:
        print("dry-run：未写状态音效或脚步表")
        return
    path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {path}")
    if changed:
        runtime_path.write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入 {runtime_path}")


if __name__ == "__main__":
    main()
