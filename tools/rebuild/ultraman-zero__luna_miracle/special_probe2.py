"""只读：打印 special* 的 manual_projectiles、adaptation 与帧事件。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MOVES = ROOT / "content/fighters/ultraman-zero/moves"


def main() -> int:
    for name in ("special", "special2", "special3", "air_special"):
        data = json.loads((MOVES / f"{name}.json").read_text(encoding="utf-8"))
        print("==", name)
        print("manual_projectiles", json.dumps(data.get("manual_projectiles"), ensure_ascii=False))
        print("adaptation", json.dumps(data.get("adaptation"), ensure_ascii=False))
        events = []
        for index, frame in enumerate(data["frames"]):
            for event in frame.get("events", []):
                events.append((index, event))
        print("events", json.dumps(events, ensure_ascii=False)[:4000])
        hitboxes = [(i, f["hitboxes"]) for i, f in enumerate(data["frames"]) if f.get("hitboxes")]
        print("hitbox frames", json.dumps(hitboxes, ensure_ascii=False)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
