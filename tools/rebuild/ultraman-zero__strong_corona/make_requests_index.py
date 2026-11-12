"""汇总本形态逐帧请求与落格对应关系，不复制 raw 文件。

扫描 frame_plan.json、stage2 的 raw/clean/rejects、stage1/cells 的 clip 记录，
写出 art/.../stage2/requests-index.json 与 coverage.json。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIGHTER = "ultraman-zero__strong_corona"
ART = ROOT / f"art/fighters/{FIGHTER}"
PLAN = ROOT / "tools/rebuild/ultraman-zero__strong_corona/frame_plan.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    rows = []
    missing = []
    for clip, spec in plan["clips"].items():
        raw_dir = ROOT / spec["raw_dir"]
        for frame in spec["frames"]:
            i = frame["index"]
            raw = raw_dir / f"{clip}-{i:02d}-raw.png"
            cell = ROOT / f"{spec['cell_prefix']}-{i:02d}-cell.png"
            row = {
                "clip": clip,
                "group": spec["group"],
                "frame": i,
                "action": frame["action"],
                "foot_row": frame["foot_row"],
                "height_class": frame["height_class"],
                "prompt": plan["prompt_prefix"] + frame["action"] + plan["prompt_suffix"],
                "reference": plan["reference"],
            }
            if raw.is_file():
                row["raw"] = raw.relative_to(ROOT).as_posix()
                row["raw_sha256"] = sha(raw)
                row["raw_size"] = raw.stat().st_size
            elif clip == "idle":
                row["raw"] = None
                row["raw_sha256"] = None
                row["note"] = "idle 已有正式身份锚 cell，无 stage2 raw"
            else:
                missing.append(f"{clip}-{i:02d}")
            if cell.is_file():
                row["cell"] = cell.relative_to(ROOT).as_posix()
                row["cell_sha256"] = sha(cell)
            else:
                missing.append(f"{clip}-{i:02d}:cell")
            rows.append(row)
    # form_switch 六帧单独记录
    fs_rows = []
    fs_dir = ART / "stage2/form_switch/frames"
    for i in range(6):
        raw = fs_dir / f"form_switch-{i:02d}-raw-v2.png"
        cell = ART / f"stage1/cells/form_switch-{i:02d}-cell.png"
        fs_rows.append({
            "clip": "form_switch",
            "frame": i,
            "raw": raw.relative_to(ROOT).as_posix() if raw.is_file() else None,
            "raw_sha256": sha(raw) if raw.is_file() else None,
            "cell": cell.relative_to(ROOT).as_posix() if cell.is_file() else None,
            "cell_sha256": sha(cell) if cell.is_file() else None,
            "request": str(ART / "stage1/requests.json"),
        })
    out = {
        "fighter": FIGHTER,
        "source": "MCP magpie-image codex/gpt-image-2 high, 1024x1536 transparent",
        "reference": plan["reference"],
        "total_planned": plan["total_frames"] + 6,
        "rows": rows,
        "form_switch": fs_rows,
        "missing": missing,
    }
    (ART / "stage2/requests-index.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    coverage = {
        "fighter": FIGHTER,
        "clips": len(plan["clips"]) + 1,
        "planned": plan["total_frames"] + 6,
        "cells": len([r for r in rows if "cell" in r]) + len([r for r in fs_rows if r["cell"]]),
        "missing": missing,
    }
    (ART / "stage2/coverage.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
