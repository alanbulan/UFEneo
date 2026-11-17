"""只读：打印基础赛罗 special/air_special 的 shots、事件与帧内效果引用。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MOVES = ROOT / "content/fighters/ultraman-zero/moves"


def main() -> int:
    for name in ("special", "special2", "special3", "air_special", "pulse", "burst"):
        data = json.loads((MOVES / f"{name}.json").read_text(encoding="utf-8"))
        print("==", name)
        for key in ("shots", "projectile", "feedback", "data_source", "production_note"):
            if key in data:
                print(key, json.dumps(data[key], ensure_ascii=False))
        kinds = {}
        for frame in data["frames"]:
            for event in frame.get("events", []):
                kinds.setdefault(event.get("kind"), set()).add(str(event.get("id")))
            for key in ("impact_effect", "block_effect"):
                if frame.get(key):
                    kinds.setdefault(key, set()).add(str(frame[key]))
        print("frame refs", {k: sorted(v) for k, v in kinds.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
