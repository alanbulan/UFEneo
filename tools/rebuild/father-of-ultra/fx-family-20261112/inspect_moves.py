"""只读检查：打印奥父相关招式的特效引用、事件与反馈。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
BASE = ROOT / "content/fighters/father-of-ultra/moves"

NAMES = sys.argv[1:] or [
    "pulse", "low_pulse", "air_pulse", "special", "special2", "air_special",
    "motion_236", "ranged_forward", "motion_623", "motion_22", "motion_214",
]


def main() -> None:
    for name in NAMES:
        move = json.loads((BASE / f"{name}.json").read_text(encoding="utf-8"))
        print("=" * 24, name, "=")
        meta = {k: v for k, v in move.items() if k != "frames"}
        print(json.dumps(meta, ensure_ascii=False, indent=1))
        for i, frame in enumerate(move["frames"]):
            extra = {
                k: v for k, v in frame.items()
                if k not in ("hurtboxes", "hitboxes", "cancel", "sprite", "dx", "dy")
            }
            if extra:
                print("frame", i, json.dumps(extra, ensure_ascii=False))


if __name__ == "__main__":
    main()
