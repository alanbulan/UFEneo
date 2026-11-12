"""把新角色的状态音效键补齐到已装机基准覆盖。

背景：side_audio 按 `state_events[角色][进入状态]` 播放声音；新角色只登记了
13 个键，而已装机基准（ultraman-taro）覆盖 53 个键。缺键不会报错，只是那
些状态静默。本工具只补“缺的键”，不覆盖已有条目、不改 runtime.json 资源，
并把每个键映射到 runtime.json 已存在且已登记的通用音效 id。

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
    "walk_back": "step",
    "walk_forward": "step",
}


FOOTSTEP = {
    "walk_forward": {"cycle_ticks": 40, "contacts": [0, 20], "sounds": ["step"]},
    "walk_back": {"cycle_ticks": 40, "contacts": [0, 20], "sounds": ["step"]},
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
    missing_base = [k for k in base_keys if k not in GENERIC]
    if missing_base:
        raise SystemExit(f"基准键没有通用映射：{missing_base}")
    for fighter in (args.fighter or NEW):
        table = events.setdefault(fighter, {})
        added = []
        for key in base_keys:
            if key in table:
                continue
            sound = GENERIC[key]
            if sound not in known:
                raise SystemExit(f"{sound} 不在 runtime.json，拒绝写空引用")
            table[key] = [{"kind": "sound", "id": sound}]
            added.append(key)
        events[fighter] = {k: table[k] for k in sorted(table)}
        print(f"{fighter}: 补 {len(added)} 键，现有 {len(events[fighter])}/{len(base_keys)}")
    bad = []
    for fighter in (args.fighter or NEW):
        for key, cues in events[fighter].items():
            for cue in cues:
                if str(cue.get("id", "")) not in known:
                    bad.append((fighter, key, cue.get("id")))
    if bad:
        raise SystemExit(f"仍有无主引用：{bad[:10]}")
    if args.dry_run:
        print("dry-run：未写文件 footsteps")
        return
    path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {path}")
    # 脚步声：runtime.json 里部分新角色只有一个方向，补齐两个方向。
    footsteps = runtime.setdefault("footsteps", {})
    changed = False
    for fighter in (args.fighter or NEW):
        table = footsteps.setdefault(fighter, {})
        added = []
        for key, row in FOOTSTEP.items():
            if key not in table:
                table[key] = json.loads(json.dumps(row))
                added.append(key)
        if added:
            changed = True
            print(f"{fighter}: 补脚步声 {added}")
    if changed:
        runtime_path.write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入 {runtime_path}")


if __name__ == "__main__":
    main()
