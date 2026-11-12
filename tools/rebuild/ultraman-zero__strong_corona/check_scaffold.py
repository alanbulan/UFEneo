"""核对本形态内容骨架：机制字段与原招一致，仅形态表述/特效 id 改写。

用法：.venv/bin/python tools/rebuild/ultraman-zero__strong_corona/check_scaffold.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "content/fighters/ultraman-zero"
OUT = ROOT / "content/fighters/ultraman-zero__strong_corona"
FX_RE = re.compile(r"zero_fx_[a-z0-9_]+")
PENDING_RE = re.compile(r"pending_corona_[a-z0-9_]+")
IGNORE_MOVE = {"display_name", "data_source", "production_note", "adaptation"}


def normalize(value):
    if isinstance(value, str):
        value = FX_RE.sub(lambda m: "pending_corona_" + m.group(0)[len("zero_fx_"):], value)
        return value
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {normalize(k): normalize(v) for k, v in value.items()}
    return value


def strip_meta(obj):
    return {k: v for k, v in obj.items() if k not in IGNORE_MOVE}


def main() -> int:
    errors = []
    move_ids = json.loads((BASE / "move_manifest.json").read_text(encoding="utf-8"))
    out_ids = json.loads((OUT / "move_manifest.json").read_text(encoding="utf-8"))
    if move_ids != out_ids:
        errors.append("move_manifest 顺序或内容不同")
    for move_id in move_ids:
        base = json.loads((BASE / "moves" / f"{move_id}.json").read_text(encoding="utf-8"))
        cand = json.loads((OUT / "moves" / f"{move_id}.json").read_text(encoding="utf-8"))
        if strip_meta(normalize(base)) != strip_meta(cand):
            errors.append(f"{move_id}: 机制字段变化")
        if "zero_fx_" in json.dumps(cand, ensure_ascii=False):
            errors.append(f"{move_id}: 仍引用 zero_fx_")
        if not str(cand.get("display_name", "")).startswith("强壮日冕·"):
            errors.append(f"{move_id}: display_name 未加形态前缀")

    base_states = json.loads((BASE / "state_frames.json").read_text(encoding="utf-8"))
    cand_states = json.loads((OUT / "state_frames.json").read_text(encoding="utf-8"))
    if set(cand_states) != set(base_states) | {"form_switch"}:
        errors.append("state_frames 键集不符")
    for key, value in base_states.items():
        if cand_states.get(key) != value:
            errors.append(f"state_frames[{key}] 被改动")
    if len(cand_states.get("form_switch", [])) != 6:
        errors.append("form_switch 不是 6 帧")

    base_cmd = json.loads((BASE / "command_table.json").read_text(encoding="utf-8"))
    cand_cmd = json.loads((OUT / "command_table.json").read_text(encoding="utf-8"))
    for b, c in zip(base_cmd, cand_cmd):
        b2 = dict(b)
        c2 = dict(c)
        b2.pop("display_name", None)
        c2.pop("display_name", None)
        if b2 != c2:
            errors.append(f"command_table {b.get('move')}: 字段变化")
    if len(base_cmd) != len(cand_cmd):
        errors.append("command_table 行数不同")

    definition = json.loads((OUT / "definition.json").read_text(encoding="utf-8"))
    if definition.get("playable") is not True:
        errors.append("definition.playable 不是 true")
    if definition.get("id") != "ultraman-zero__strong_corona":
        errors.append("definition.id 不符")

    print(json.dumps({
        "moves": len(move_ids),
        "states": len(cand_states),
        "form_switch": len(cand_states.get("form_switch", [])),
        "errors": errors,
    }, ensure_ascii=False, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
