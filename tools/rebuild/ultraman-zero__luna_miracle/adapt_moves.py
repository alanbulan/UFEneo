"""从基础赛罗复制的招式 JSON 改写为月神奇迹专属 FX id 与说明。"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MOVES = ROOT / "content/fighters/ultraman-zero__luna_miracle/moves"

REPLACEMENTS = {
    "zero_fx_wide_beam": "zero_luna_miracle_fx_wide_beam",
    "zero_fx_wide_hit": "zero_luna_miracle_fx_wide_hit",
    "zero_fx_emerium_beam": "zero_luna_miracle_fx_emerium_beam",
    "zero_fx_emerium_hit": "zero_luna_miracle_fx_emerium_hit",
    "zero_fx_slugger_flight": "zero_luna_miracle_fx_slugger_flight",
    "zero_fx_slugger_trail": "zero_luna_miracle_fx_slugger_trail",
    "zero_fx_slugger_hit": "zero_luna_miracle_fx_slugger_hit",
    "zero_fx_slugger_catch": "zero_luna_miracle_fx_slugger_catch",
    "zero_fx_pulse_flight": "zero_luna_miracle_fx_pulse_flight",
    "zero_fx_pulse_hit": "zero_luna_miracle_fx_pulse_hit",
}

NOTE = (
    "月神奇迹数据骨架：数值/tick/帧结构沿用基础赛罗；专属与飞行道具特效改用 "
    "zero_luna_miracle_fx_*；动作帧与特效资产待装机，人物帧不烘焙特效。"
)


def main() -> int:
    paths = sorted(glob.glob(str(MOVES / "*.json")))
    remaining = []
    for path_str in paths:
        path = Path(path_str)
        text = path.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS.items():
            text = text.replace(old, new)
        found = sorted(set(re.findall(r"zero_fx_[a-z0-9_]+", text)))
        if found:
            remaining.append((path.name, found))
        data = json.loads(text)
        if "production_note" in data:
            old = str(data.get("production_note", ""))
            data["production_note"] = NOTE
        else:
            data["production_note"] = NOTE
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print(json.dumps({"wrote": len(paths), "remaining_zero_fx": remaining},
                     ensure_ascii=False, indent=1))
    return 1 if remaining else 0


if __name__ == "__main__":
    raise SystemExit(main())
