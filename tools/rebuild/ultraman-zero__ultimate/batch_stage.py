"""批量落格：对 plans/ 下所有 raw 已齐的 clip 依次调用 stage_clip 逻辑。

用法：
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/batch_stage.py
    .venv/bin/python tools/rebuild/ultraman-zero__ultimate/batch_stage.py --clips dash,dash_stop
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
HERE = Path(__file__).resolve().parent
PLANS = HERE / "plans"


def ready(plan: dict) -> bool:
    return all((ROOT / frame["source"]).is_file() for frame in plan["frames"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", default="")
    args = ap.parse_args()
    wanted = {c.strip() for c in args.clips.split(",") if c.strip()}
    results = []
    for path in sorted(PLANS.glob("*.json")):
        plan = json.loads(path.read_text(encoding="utf-8"))
        clip = plan["clip"]
        if wanted and clip not in wanted:
            continue
        if not ready(plan):
            results.append({"clip": clip, "status": "raw_missing"})
            continue
        proc = subprocess.run(
            [sys.executable, str(HERE / "stage_clip.py"), "--plan",
             path.relative_to(ROOT).as_posix()],
            cwd=ROOT, capture_output=True, text=True)
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            report = {"raw_stdout": proc.stdout[-500:], "stderr": proc.stderr[-500:]}
        results.append({
            "clip": clip,
            "status": "ok" if proc.returncode == 0 else "fail",
            "frames": report.get("frames"),
            "failures": report.get("failures"),
        })
    print(json.dumps(results, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
