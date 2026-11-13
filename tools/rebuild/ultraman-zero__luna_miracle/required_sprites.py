"""计算月神奇迹需要的 clip sprite 索引（按基础赛罗 state_frames/moves 骨架）。"""
from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "content/fighters/ultraman-zero__luna_miracle"


def uniq_indices(frames):
    return sorted({int(f.get("sprite", 0)) for f in frames if isinstance(f, dict)})


def main() -> int:
    states = json.loads((BASE / "state_frames.json").read_text(encoding="utf-8"))
    state_req = {}
    for clip, frames in sorted(states.items()):
        idx = uniq_indices(frames)
        state_req[clip] = {"count": len(idx), "indices": idx}
    move_req = {}
    for path in sorted(glob.glob(str(BASE / "moves/*.json"))):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        clip = data["id"]
        idx = uniq_indices(data.get("frames", []))
        move_req[clip] = {"count": len(idx), "indices": idx, "frame_count": len(data.get("frames", []))}
    total = sum(v["count"] for v in state_req.values()) + sum(v["count"] for v in move_req.values())
    out = {
        "states": {"clips": len(state_req), "sprites": sum(v["count"] for v in state_req.values()), "detail": state_req},
        "moves": {"clips": len(move_req), "sprites": sum(v["count"] for v in move_req.values()), "detail": move_req},
        "total_sprites": total,
    }
    out_path = ROOT / "tools/rebuild/ultraman-zero__luna_miracle/required-sprites.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"states_clips": out["states"]["clips"], "state_sprites": out["states"]["sprites"],
                      "move_clips": out["moves"]["clips"], "move_sprites": out["moves"]["sprites"],
                      "total": total, "out": str(out_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
