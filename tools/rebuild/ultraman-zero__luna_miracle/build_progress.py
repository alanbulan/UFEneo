"""读取已落格 cell，汇总月神奇迹帧完成度。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CELLS = ROOT / "art/fighters/ultraman-zero__luna_miracle/stage1/cells"
REQ = ROOT / "tools/rebuild/ultraman-zero__luna_miracle/required-sprites.json"


def main() -> int:
    req = json.loads(REQ.read_text(encoding="utf-8"))
    have = {}
    if CELLS.is_dir():
        for path in CELLS.glob("*-cell.png"):
            m = re.match(r"(.+)-(\d\d)-cell\.png$", path.name)
            if not m:
                continue
            clip, idx = m.group(1), int(m.group(2))
            have.setdefault(clip, set()).add(idx)
    out = {"states": {}, "moves": {}, "form_switch": sorted(have.get("form_switch", []))}
    for kind in ("states", "moves"):
        done_clips = 0
        done_sprites = 0
        total = 0
        for clip, info in req[kind]["detail"].items():
            need = set(info["indices"])
            got = have.get(clip, set()) & need
            missing = sorted(need - got)
            complete = not missing
            if complete:
                done_clips += 1
            done_sprites += len(got)
            total += len(need)
            out[kind][clip] = {
                "need": info["indices"],
                "have": sorted(got),
                "missing": missing,
                "complete": complete,
            }
        out[kind + "_summary"] = {
            "clips_total": req[kind]["clips"],
            "clips_complete": done_clips,
            "sprites_total": total,
            "sprites_have": done_sprites,
        }
    out_path = ROOT / "tools/rebuild/ultraman-zero__luna_miracle/build-progress.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({
        "states": out["states_summary"],
        "moves": out["moves_summary"],
        "form_switch_have": out["form_switch"],
        "out": str(out_path),
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
