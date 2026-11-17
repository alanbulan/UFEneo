"""Install accepted catalogue-rebuild receipts, one root writer only.

Do not run while generation subagents are writing shared assets. This script
reads each receipt, validates its declared source/frame SHA256 values, installs
the still and animation strip, then records the batch tag through the flock
protected catalogue_store. Godot import and full verification remain separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
VENV = ROOT / ".venv/bin/python"
sys.path.insert(0, str(ROOT / "tools/media/art"))
import catalogue_store  # noqa: E402

RECEIPTS = ROOT / "reports/catalogue-rebuild-20261113/receipts"
ART = ROOT / "art/catalogue-rebuild-20261113"
BATCH = "catalogue-rebuild-20261113"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt_problems(receipt: dict) -> list[str]:
    problems: list[str] = []
    if receipt.get("schema") != "ufeneo.catalogue-rebuild-receipt.v1":
        problems.append("schema")
    if receipt.get("status") != "accepted":
        problems.append("status not accepted")
    if receipt.get("source_gate") != "passed":
        problems.append("source gate not passed")
    if not receipt.get("glow_gate_pass"):
        problems.append("glow gate")
    if not receipt.get("clean_alpha_binary"):
        problems.append("clean alpha not binary")
    if not receipt.get("visual_review"):
        problems.append("visual review missing")
    for name in ("reference_sha256", "model", "quality", "prompts", "generation_ids"):
        if not receipt.get(name):
            problems.append(f"missing {name}")
    if receipt.get("model") not in {"codex/gpt-image-2", "cpa/gpt-image-2.6-sunburst"}:
        problems.append("model")
    files = receipt.get("files", {})
    expected = ("still-00", "still-00-clean", "idle-01", "idle-01-clean", "idle-02", "idle-02-clean")
    for name in expected:
        item = files.get(name)
        if not item:
            problems.append(f"missing file record {name}")
            continue
        path = ROOT / item["path"]
        if not path.is_file():
            problems.append(f"missing file {name}")
            continue
        if digest(path) != item["sha256"]:
            problems.append(f"sha changed {name}")
        with Image.open(path) as image:
            if list(image.size) != [item["width"], item["height"]]:
                problems.append(f"size changed {name}")
            if image.mode != "RGBA":
                problems.append(f"mode changed {name}")
        if name.endswith("-clean"):
            if item["alpha_value_count"] != 2:
                problems.append(f"alpha not binary {name}")
            gate = item.get("glow_gate", {})
            if gate.get("alpha_ge_128_components") != 1:
                problems.append(f"clean frame not one component {name}")
    reference = ROOT / receipt["reference_file"]
    if not reference.is_file() or digest(reference) != receipt["reference_sha256"]:
        problems.append("reference sha changed")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalogue_ids", nargs="+")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results = []
    accepted: list[tuple[str, dict]] = []
    for cid in args.catalogue_ids:
        path = RECEIPTS / f"{cid}.json"
        if not path.is_file():
            results.append({"id": cid, "status": "missing_receipt"})
            continue
        receipt = json.loads(path.read_text(encoding="utf-8"))
        problems = receipt_problems(receipt)
        if problems:
            results.append({"id": cid, "status": "rejected", "problems": problems})
            continue
        accepted.append((cid, receipt))
        results.append({"id": cid, "status": "receipt_validated" if args.dry_run else "install_queued"})

    if not args.dry_run:
        for cid, receipt in accepted:
            still = ART / cid / "still-00-clean.png"
            raw = ROOT / f"reports/catalogue-ref/{cid}/raw.png"
            raw.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(still, raw)
            subprocess.run([str(VENV), str(ROOT / "tools/media/art/catalogue_install.py"),
                            cid, str(still), "--art-source", "mcp_image_to_image_from_official_reference"],
                           check=True, cwd=ROOT)
            # Re-pack all three generated sources at one common scale and one
            # fixed 384x256 UI cell, rather than using the old foot-centre
            # alignment that cropped long tails and dorsal fins.
            subprocess.run([str(VENV), str(ROOT / "tools/rebuild/catalogue-rebuild-20261113/catalogue_rebuild_repack.py"),
                            cid], check=True, cwd=ROOT)
            display_entry = catalogue_store.load()["entries"][cid]
            still_sha = digest(ROOT / display_entry["image"].removeprefix("res://"))
            strip_sha = digest(ROOT / display_entry["strip"].removeprefix("res://"))
            if still_sha != display_entry["image_sha256"] or strip_sha != display_entry["strip_sha256"]:
                raise SystemExit(f"installed SHA mismatch: {cid}")
            catalogue_store.update_entry(cid, {
                "rebuild_batch": BATCH,
                "rebuild_receipt": f"reports/catalogue-rebuild-20261113/receipts/{cid}.json",
                "reference_file": receipt["reference_file"],
                "review_authority": "root_delegated_by_user",
                "user_reviewed": False,
                "listening_reviewed": False,
            })
            item = next(x for x in results if x["id"] == cid)
            item.update({
                "status": "installed",
                "frames": display_entry["frames"],
                "image_sha256": still_sha,
                "strip_sha256": strip_sha,
            })
    print(json.dumps({"batch": BATCH, "dry_run": args.dry_run, "results": results},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
