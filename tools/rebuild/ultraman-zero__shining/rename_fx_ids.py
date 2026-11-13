"""把本形态特效 id 从临时 pending_shining_* 统一改为正式 zero_shining_fx_*。

只改本形态自己的内容与提案记录；共享 phase3/charge 仍由根登记。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGETS = [
    ROOT / "content/fighters/ultraman-zero__shining",
    ROOT / "tools/rebuild/ultraman-zero__shining/fx-proposal.json",
    ROOT / "tools/rebuild/ultraman-zero__shining/charge_policy.json",
    ROOT / "tools/rebuild/ultraman-zero__shining/fx-report.json",
    ROOT / "art/fighters/ultraman-zero__shining/stage1/requests.json",
    ROOT / "assets/effects/ultraman-zero__shining",
    ROOT / "tools/rebuild/ultraman-zero__shining/README.md",
]
SKIP = {"build_content.py", "rename_fx_ids.py"}
OLD = "pending_shining_"
NEW = "zero_shining_fx_"


def main() -> int:
    changed = {}
    for target in TARGETS:
        files = [target] if target.is_file() else sorted(target.rglob("*"))
        for path in files:
            if not path.is_file() or path.suffix not in {".json", ".md", ".py", ".mjs"}:
                continue
            if path.name in SKIP:
                continue
            text = path.read_text(encoding="utf-8")
            if OLD not in text:
                continue
            count = text.count(OLD)
            path.write_text(text.replace(OLD, NEW), encoding="utf-8", newline="\n")
            changed[path.relative_to(ROOT).as_posix()] = count
    for name, count in changed.items():
        print(f"{count:4d}  {name}")
    print(f"files={len(changed)} replacements={sum(changed.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
