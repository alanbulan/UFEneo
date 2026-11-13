"""把说明文字里残留的 pending_ultimate_* 改成正式 id 前缀。"""
from __future__ import annotations

from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
ROOTS = [ROOT / "content/fighters/ultraman-zero__ultimate",
         ROOT / "tools/rebuild/ultraman-zero__ultimate"]
SKIP = {"rename_fx_ids.py", "fix_fx_prose.py", "uz_install_cells.py"}


def main() -> int:
    changed = []
    for root in ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in (".json", ".py", ".md"):
                continue
            if path.name in SKIP:
                continue
            text = path.read_text(encoding="utf-8")
            new = (text
                   .replace("运行时特效全部为 pending_ultimate_*",
                            "运行时特效全部为 zero_ultimate_fx_*（本形态专属 id）")
                   .replace("FX id 已改 pending_ultimate_*", "FX id 已改 zero_ultimate_fx_*")
                   .replace('"fx_prefix": "pending_ultimate_"', '"fx_prefix": "zero_ultimate_fx_"')
                   .replace("pending_ultimate_*", "zero_ultimate_fx_*")
                   .replace("pending_ultimate_", "zero_ultimate_fx_"))
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed.append(path.relative_to(ROOT).as_posix())
    left = []
    for root in ROOTS:
        for path in root.rglob("*"):
            if path.is_file() and path.name not in SKIP and "pending_ultimate_" in path.read_text(
                    encoding="utf-8", errors="ignore"):
                left.append(path.relative_to(ROOT).as_posix())
    print("changed", len(changed), "remaining", left)
    return 1 if left else 0


if __name__ == "__main__":
    raise SystemExit(main())
