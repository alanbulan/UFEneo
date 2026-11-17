"""把本形态临时 pending_ultimate_* 特效 id 改为正式专属 id zero_ultimate_fx_*。

只改 content/fighters/ultraman-zero__ultimate 与
tools/rebuild/ultraman-zero__ultimate 内的文本；共享 phase3/charge 不动。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
MAP = {
    "pending_ultimate_wide_beam": "zero_ultimate_fx_wide_beam",
    "pending_ultimate_wide_hit": "zero_ultimate_fx_wide_hit",
    "pending_ultimate_emerium_beam": "zero_ultimate_fx_emerium_beam",
    "pending_ultimate_emerium_hit": "zero_ultimate_fx_emerium_hit",
    "pending_ultimate_slugger_flight": "zero_ultimate_fx_slugger_flight",
    "pending_ultimate_slugger_trail": "zero_ultimate_fx_slugger_trail",
    "pending_ultimate_slugger_hit": "zero_ultimate_fx_slugger_hit",
    "pending_ultimate_slugger_catch": "zero_ultimate_fx_slugger_catch",
    "pending_ultimate_q_charge_start": "zero_ultimate_fx_q_charge_start",
    "pending_ultimate_q_charge": "zero_ultimate_fx_q_charge",
    "pending_ultimate_q_charge_stop": "zero_ultimate_fx_q_charge_stop",
    "pending_ultimate_impact_light": "zero_ultimate_fx_impact_light",
    "pending_ultimate_impact_heavy": "zero_ultimate_fx_impact_heavy",
    "pending_ultimate_impact_guard": "zero_ultimate_fx_impact_guard",
    "pending_ultimate_pulse": "zero_ultimate_fx_pulse",
}


def main() -> int:
    targets = [ROOT / "content/fighters/ultraman-zero__ultimate",
               ROOT / "tools/rebuild/ultraman-zero__ultimate"]
    changed = []
    for target in targets:
        files = [target] if target.is_file() else [
            p for p in target.rglob("*") if p.suffix in (".json", ".py", ".md")]
        for path in files:
            if not path.is_file() or path.name in ("rename_fx_ids.py", "uz_install_cells.py"):
                continue
            text = path.read_text(encoding="utf-8")
            new = text
            for old, final in MAP.items():
                new = new.replace(old, final)
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed.append(path.relative_to(ROOT).as_posix())
    # 清单核对：不再有 pending_ultimate_，正式 id 覆盖 15 段。
    remaining = []
    ids = set()
    for target in targets:
        files = [target] if target.is_file() else [
            p for p in target.rglob("*") if p.suffix in (".json", ".py", ".md")]
        for path in files:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if "pending_ultimate_" in text:
                remaining.append(path.relative_to(ROOT).as_posix())
            for final in MAP.values():
                if final in text:
                    ids.add(final)
    print(json.dumps({"changed": changed, "remaining_pending": remaining,
                      "final_ids": sorted(ids), "final_id_count": len(ids)},
                     ensure_ascii=False, indent=1))
    return 1 if remaining else 0


if __name__ == "__main__":
    raise SystemExit(main())
