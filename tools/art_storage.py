"""Audit categorized art; optionally prune obsolete generated drafts and caches."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
Path = _LayoutProjectPath
import argparse
import hashlib
import json; json = _LayoutJson
import re

from art_paths import LEGACY_KEYART, PIXEL_PORTRAITS, asset_id, brief_path, pixel_portrait_path

ROOT = _LayoutProjectPath(_layout_root)
MAINTENANCE = "reports/maintenance"


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def bounded(path):
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()) or resolved == ROOT.resolve() or path.is_symlink():
        raise ValueError("Refusing a maintenance path outside the project: " + str(path))
    return resolved


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def obsolete_drafts():
    """Only recognized generator output absent from the current catalog is eligible."""
    ids = {row["id"] for row in load("content/roster/catalog.json")["entries"]}
    legacy_audit = ROOT / "reports/unused-generated-drafts.json"
    legacy_packs = set(load(legacy_audit).get("files", [])) if legacy_audit.exists() else set()
    candidates = {}
    for path in (ROOT / "content/roster/packs").glob("*.json"):
        if path.stem in ids:
            continue
        data = json.loads(path.read_text("utf-8"))
        if (data.get("schema") == 1 and data.get("character_id") == path.stem
                and data.get("catalog") == "content/roster/catalog.json"
                and "production_stages" in data
                and ("asset_layer_contract" in data or path.relative_to(ROOT).as_posix() in legacy_packs)):
            candidates[path] = "旧自动生成内容包；角色ID不在当前目录"
    for path in (ROOT / "art/shared/briefs").rglob("*.json"):
        data = json.loads(path.read_text("utf-8"))
        if (data.get("managed_by") == "tools/build_roster.py" and data.get("character_id") not in ids
                and data.get("ready_for_generation") is False):
            candidates[path] = "旧自动生成美术草稿；未获生成资格且角色ID已失效"
    if not candidates:
        return {}
    # Documentation/reports may retain a historical receipt. Active source or
    # content references prevent deletion, even for an otherwise stale draft.
    references = {}
    for top in ["app", "art", "assets", "content", "core", "data", "input", "presentation", "app/scenes", "tests", "tools", "ui"]:
        for path in (ROOT / top).rglob("*"):
            if path.is_file() and path not in candidates and path.suffix in {".json", ".jsonl", ".py", ".gd", ".tres", ".tscn"}:
                text = path.read_text("utf-8").replace("\\\\", "/").replace("\\", "/")
                for match in re.findall(r"(?:art/briefs|content/roster/packs)/[A-Za-z0-9_./-]+\.json", text):
                    references.setdefault(match, []).append(path.relative_to(ROOT).as_posix())
    return {path: reason for path, reason in candidates.items() if path.relative_to(ROOT).as_posix() not in references}


def cleanup_candidates():
    candidates = obsolete_drafts()
    for top in ["tools", "tests"]:
        for path in (ROOT / top).rglob("*.pyc"):
            if "__pycache__" in path.parts:
                candidates[path] = "Python可重建字节码缓存"
    gallery_log = ROOT / "reports/capture-gallery-pages.log"
    if gallery_log.is_file():
        verified_pages = re.findall(r"GALLERY_CAPTURE_OK pages=(\d+)", gallery_log.read_text("utf-8"))
        if verified_pages:
            for path in (ROOT / "reports").glob("gallery-page-*.png"):
                match = re.fullmatch(r"gallery-page-(\d+)\.png", path.name)
                if (match and int(match.group(1)) > int(verified_pages[-1])
                        and path.stat().st_mtime < gallery_log.stat().st_mtime):
                    candidates[path] = "最新成功画廊捕获已确认不存在该页；删除旧版派生预览"
    # These roots are deliberately excluded from the Godot importer.
    for top in ["art", "reports"]:
        if not (ROOT / top / ".gdignore").is_file():
            raise ValueError("Missing importer exclusion for " + top)
        for path in (ROOT / top).rglob("*.import"):
            candidates[path] = "已排除导入目录内的过期Godot导入侧文件"
    # Only remove source sidecars when the migration receipt proves the source
    # was moved. Never guess based on an image name or remove the entire cache.
    receipt = ROOT / MAINTENANCE / "art-storage-migration.json"
    old_images = {row["old"] for row in load(receipt)["moves"] if row["old"].endswith(".png")} if receipt.exists() else set()
    for old in old_images:
        sidecar = ROOT / (old + ".import")
        if (ROOT / old).exists() or not sidecar.is_file():
            continue
        candidates[sidecar] = "素材已迁移；原路径的Godot导入侧文件"
    for path in list(candidates):
        if path.suffix != ".import":
            continue
        text = path.read_text("utf-8")
        for relative in re.findall(r'res://(/.godot/imported/[^"\r\n]+\.ctex)', text):
            cached = bounded(ROOT / relative)
            for cache in [cached, cached.with_suffix(".md5")]:
                if cache.is_file():
                    candidates[cache] = "已迁移或排除素材的可重建Godot导入缓存"
    return candidates


def clean():
    planned = cleanup_candidates()
    records = []
    # Validate the entire deletion set before touching the first file.
    for path, reason in sorted(planned.items()):
        bounded(path)
        records.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
                        "sha256": digest(path), "reason": reason})
    report = ROOT / MAINTENANCE / "art-storage-cleanup.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    history = load(report) if report.exists() else {"schema": 1, "runs": []}
    run = {"created_utc": datetime.now(timezone.utc).isoformat(), "status": "planned",
           "deleted_files": len(records), "deleted_bytes": sum(row["bytes"] for row in records), "files": records}
    history["runs"].append(run)
    report.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for row in records:
        path = bounded(ROOT / row["path"])
        if digest(path) != row["sha256"]:
            raise ValueError("File changed after cleanup planning: " + row["path"])
        path.unlink()
    for top in ["art/shared/briefs", "art/shared/legacy/concepts", "art/shared/reviews", "assets/ui/keyart", "tools/__pycache__", "tests/__pycache__"]:
        parent = bounded(ROOT / top)
        if parent.is_dir():
            for directory in sorted((p for p in parent.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                bounded(directory)
                if not any(directory.iterdir()):
                    directory.rmdir()
            if not any(parent.iterdir()):
                parent.rmdir()
    run["status"] = "completed"
    report.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {k: v for k, v in run.items() if k != "files"}


def verify_file(relative, expected_hash=None):
    path = bounded(ROOT / relative)
    if not path.is_file():
        raise ValueError("Missing art reference: " + relative)
    if expected_hash and digest(path) != expected_hash:
        raise ValueError("Art hash mismatch: " + relative)
    return path


def run_owner(request_path):
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("source_character_id"):
        return asset_id(request["source_character_id"])
    packet = request.get("source_visual_packet")
    if packet:
        reference = bounded(ROOT / packet)
        source = json.loads(reference.read_text(encoding="utf-8"))
        if source.get("character_id"):
            return asset_id(source["character_id"])
    for legacy in ["ultraman", "zetton"]:
        if request_path.parent.name.startswith(legacy + "_"):
            return legacy
    return "shared_effects" if request.get("subject") == "effect" else "unassigned"


def audit(write_index=False):
    rows = load("content/roster/catalog.json")["entries"]
    portraits = load(PIXEL_PORTRAITS + "/catalog.json")["characters"]
    indexed = []
    for row in rows:
        expected = brief_path(row["id"], row["kind"])
        if row["brief"] != expected:
            raise ValueError("Uncategorized character brief: " + row["id"])
        verify_file(expected)
        indexed.append({"id": row["id"], "name": row["name"], "kind": row["kind"], "brief": expected,
                        "portrait": portraits.get(row["id"], {}).get("path", "")})
    for cid, row in portraits.items():
        if row["path"] != str(pixel_portrait_path(cid)):
            raise ValueError("Uncategorized runtime portrait: " + cid)
        verify_file(row["path"], row["sha256"])
        verify_file(row["source"], row["source_sha256"])
    legacy = load(LEGACY_KEYART + "/catalog.json")["characters"]
    for row in legacy.values():
        verify_file(row["path"], row["sha256"])
        verify_file(row["source"], row["source_sha256"])
        verify_file(row["review"])
        verify_file(row["reference"]["local_path"], row["reference"]["sha256"])
    if any((ROOT / "art/shared/briefs").glob("*.json")):
        raise ValueError("Flat briefs remain; classify drafts or prune obsolete generated ones")
    if any((ROOT / "assets/ui/keyart").glob("*.png")):
        raise ValueError("Legacy HD art remains in runtime assets")
    for top in ["art/shared/legacy/concepts", "assets/ui/pixel_portraits"]:
        if any((ROOT / top).glob("*.png")):
            raise ValueError("Flat images remain under " + top)
    # Each diagnostic run already owns its raw/frames/curated/layers and evidence.
    # Keeping these immutable avoids breaking their byte-bound review records.
    runs = []
    for path in sorted((ROOT / "art/runs").glob("*/sprite-request.json")):
        owner = run_owner(path)
        runs.append({"id": path.parent.name, "owner": owner, "folder": path.parent.relative_to(ROOT).as_posix()})
    result = {"ok": True, "character_briefs": len(rows), "by_kind": dict(Counter(row["kind"] for row in rows)),
              "runtime_pixel_portraits": len(portraits), "archived_hd_portraits": len(legacy), "preserved_runs": len(runs),
              "obsolete_drafts": len(obsolete_drafts())}
    if write_index:
        index = {"schema": 1, "generated_by": "tools/art_storage.py --index", "characters": indexed, "runs": runs,
                 "backgrounds": "art/shared/legacy/concepts/backgrounds", "shared_effects": "art/shared/legacy/concepts/effects",
                 "legacy_hd_archive": LEGACY_KEYART, "storage_guide": "docs/ASSET_STORAGE.md"}
        (ROOT / "art/catalog.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = ROOT / MAINTENANCE / "art-storage-audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="Delete only confirmed obsolete generator output and rebuildable caches")
    parser.add_argument("--index", action="store_true")
    args = parser.parse_args()
    if args.clean:
        print(json.dumps(clean(), ensure_ascii=False))
    print(json.dumps(audit(args.index), ensure_ascii=False))
