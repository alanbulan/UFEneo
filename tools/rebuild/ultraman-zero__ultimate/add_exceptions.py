"""给若干 plan 追加 pose_exceptions（蹲/起跑/后跃等非直立相）。

用法：
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/add_exceptions.py dash_start:00 dash_stop:00
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
PLANS = ROOT / "tools/rebuild/ultraman-zero__ultimate/plans"


def main() -> int:
    for arg in sys.argv[1:]:
        clip, _, idxs = arg.partition(":")
        path = PLANS / f"{clip}.json"
        plan = json.loads(path.read_text(encoding="utf-8"))
        wanted = [i.strip() for i in idxs.split(",") if i.strip()]
        plan["pose_exceptions"] = sorted(set(plan.get("pose_exceptions", [])) | set(wanted))
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(clip, plan["pose_exceptions"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
