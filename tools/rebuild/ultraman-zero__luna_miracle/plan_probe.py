"""只读：统计基础赛罗各 clip 的唯一帧数与按 8 帧条带的生成批次数。"""
from __future__ import annotations

import glob
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "content/fighters/ultraman-zero"


def main() -> int:
    moves = {}
    for path in sorted(glob.glob(str(BASE / "moves/*.json"))):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        moves[data["id"]] = len({frame["sprite"] for frame in data["frames"]})
    states = {}
    data = json.loads((BASE / "state_frames.json").read_text(encoding="utf-8"))
    for key, frames in data.items():
        states[key] = len({frame.get("sprite") for frame in frames if isinstance(frame, dict)})
    move_strips = sum(math.ceil(v / 8) for v in moves.values())
    state_strips = sum(math.ceil(v / 8) for v in states.values())
    print("moves", len(moves), sum(moves.values()), "strips", move_strips)
    print("states", len(states), sum(states.values()), "strips", state_strips)
    print("total", sum(moves.values()) + sum(states.values()),
          "strips", move_strips + state_strips)
    print(json.dumps({"moves": moves, "states": states}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
