"""Audit actual published concept previews; never trust cached alpha metadata."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath

from PIL import Image
from art_pipeline import require_transparency

ROOT = _LayoutProjectPath(_layout_root)


def audit():
    data = json.loads((ROOT / "content/roster/production.json").read_text(encoding="utf-8"))
    report = {}
    for cid, row in data["by_character"].items():
        relative = row.get("preview_path", "")
        if not relative:
            continue
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT / "art/shared/legacy/concepts") or "rejected" in path.relative_to(ROOT).parts:
            raise ValueError("Concept preview path must stay in accepted candidate folders: " + cid)
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Concept preview hash changed: " + cid)
        with Image.open(path) as image:
            report[cid] = require_transparency(image)
    out = ROOT / "reports/concept-alpha.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Transparent concept previews:", len(report))
    return report


if __name__ == "__main__":
    audit()
