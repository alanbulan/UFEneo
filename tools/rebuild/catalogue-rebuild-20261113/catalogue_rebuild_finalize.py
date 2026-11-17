"""Aggregate one catalogue-rebuild ID's generated frames into a receipt.

Read side-effect: writes only reports/catalogue-rebuild-20261113/receipts/<id>.json.
Generated images must already exist in art/catalogue-rebuild-20261113/<id>/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Unified layout bootstrap: tools/ and each tools/ subdirectory on sys.path.
import sys as _layout_sys
from pathlib import Path as _LayoutPath

_layout_root = _LayoutPath(__file__).resolve().parents[3]
_layout_sys.path[:0] = [str(_layout_root / "tools"),
    *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]

FRAME_NAMES = ("still-00", "idle-01", "idle-02")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_metrics(path: Path) -> dict:
    with Image.open(path) as im:
        image = im.convert("RGBA")
    array = np.asarray(image)
    alpha = array[:, :, 3]
    levels = sorted(int(v) for v in np.unique(alpha).tolist())
    ys, xs = np.where(alpha >= 128)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None
    main_binary = (alpha >= 200).astype(np.uint8)
    # OpenCV 4/5 return (count, labels, stats, centroids); tolerate an extra
    # trailing value without mistaking centroids for the per-label area stats.
    components = cv2.connectedComponentsWithStats(main_binary, connectivity=8)
    count, labels, stats, _centroids = components[:4]
    sizes = np.asarray(stats)[:, cv2.CC_STAT_AREA]
    largest = 1 + int(np.argmax(sizes[1:])) if count > 1 else 0
    main = (labels == largest).astype(np.uint8) if largest else np.zeros_like(main_binary)
    expanded = cv2.dilate(main, np.ones((3, 3), np.uint8), iterations=3) if largest else main
    outside = ((expanded == 0) & (main == 0))
    outside_16 = int(np.count_nonzero(outside & (alpha >= 16)))
    outside_200 = int(np.count_nonzero(outside & (alpha >= 200)))
    dust = int(np.count_nonzero((alpha >= 1) & (alpha <= 15)))
    solid_components = int(cv2.connectedComponents((alpha >= 128).astype(np.uint8), connectivity=8)[0] - 1)
    visible = alpha >= 128
    xs_all = np.nonzero(visible.any(axis=0))[0]
    ys_all = np.nonzero(visible.any(axis=1))[0]
    bbox_ge128 = [int(xs_all.min()), int(ys_all.min()), int(xs_all.max()) + 1, int(ys_all.max()) + 1] if len(xs_all) and len(ys_all) else None
    body_height = int(ys_all.max() - ys_all.min() + 1) if len(ys_all) else 0
    body_width = int(xs_all.max() - xs_all.min() + 1) if len(xs_all) else 0
    # Report the aspect after a nominal 192 px standing-height downsample.
    # The catalogue UI keeps its 384x256 cell; a wide quadruped is fitted once,
    # at install time, by one uniform scale shared by all three frames. The
    # width report must never reject a valid long tail or dorsal fin.
    scaled_width_at_192 = round(body_width * 192 / body_height) if body_height else 0
    fits_catalogue = bool(scaled_width_at_192 <= 384 - 8)
    gate = {
        "main_component_pixels": int(main.sum()),
        "outside_expanded_alpha_ge_16": outside_16,
        "outside_expanded_alpha_ge_200": outside_200,
        "alpha_1_to_15_dust_registered": dust,
        "alpha_ge_128_components": solid_components,
        "body_bbox_ge_128": bbox_ge128,
        "body_width_ge_128": body_width,
        "body_height_ge_128": body_height,
        "scaled_width_at_192": scaled_width_at_192,
        "fits_catalogue_cell": fits_catalogue,
        "pass": bool(largest and outside_16 <= 100 and outside_200 == 0
                     and solid_components == 1),
    }
    return {
        "path": str(path.relative_to(_layout_root)),
        "sha256": digest(path),
        "bytes": path.stat().st_size,
        "width": image.width,
        "height": image.height,
        "mode": "RGBA",
        "alpha_value_count": len(levels),
        "alpha_values": levels if len(levels) <= 8 else f"{len(levels)} levels",
        "alpha_ge_128_bbox": bbox,
        "glow_gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalogue_id")
    parser.add_argument("--prompts", required=True, type=Path)
    parser.add_argument("--generation-ids", required=True, type=Path)
    parser.add_argument("--visual-review", required=True, type=Path)
    parser.add_argument("--status", choices=("accepted", "rejected"), required=True)
    parser.add_argument("--source-gate-only", action="store_true",
                        help="reject an unusable reference before spending image generations")
    parser.add_argument("--notes", default="")
    parser.add_argument("--model", default="cpa/gpt-image-2.6-sunburst")
    args = parser.parse_args()

    directory = _layout_root / "art/catalogue-rebuild-20261113" / args.catalogue_id
    source = json.loads((directory / "source.json").read_text(encoding="utf-8"))
    reference = _layout_root / source["reference_files"][0]
    with Image.open(reference) as im:
        reference_size = list(im.size)
        reference_mode = im.mode

    files = {}
    clean_alpha_ok = True
    gates_ok = True
    if not args.source_gate_only:
        for name in FRAME_NAMES:
            raw = directory / f"{name}.png"
            clean = directory / f"{name}-clean.png"
            if not raw.exists() or not clean.exists():
                raise SystemExit(f"missing frame for {name}: {raw} / {clean}")
            files[name] = frame_metrics(raw)
            files[f"{name}-clean"] = frame_metrics(clean)
            clean_levels = files[f"{name}-clean"]["alpha_value_count"]
            if clean_levels != 2:
                clean_alpha_ok = False
            if not files[name]["glow_gate"]["pass"]:
                gates_ok = False

    visual_review = args.visual_review.read_text(encoding="utf-8").strip()
    if not visual_review:
        raise SystemExit("visual review text is empty")
    prompts = json.loads(args.prompts.read_text(encoding="utf-8")) if args.prompts.exists() else {}
    generation_ids = json.loads(args.generation_ids.read_text(encoding="utf-8")) if args.generation_ids.exists() else []
    if args.source_gate_only and args.status != "rejected":
        raise SystemExit("--source-gate-only requires --status rejected")
    receipt = {
        "schema": "ufeneo.catalogue-rebuild-receipt.v1",
        "catalogue_id": args.catalogue_id,
        "name": source.get("name"),
        "kind": source.get("kind"),
        "catalog_year": source.get("catalog_year"),
        "reference_file": source["reference_files"][0],
        "reference_sha256": digest(reference),
        "reference_size": reference_size,
        "reference_mode": reference_mode,
        "model": args.model,
        "quality": "high",
        "source_gate": "rejected_before_generation" if args.source_gate_only else "passed",
        "prompts": prompts,
        "generation_ids": generation_ids,
        "files": files,
        "glow_gate_pass": False if args.source_gate_only else gates_ok,
        "clean_alpha_binary": False if args.source_gate_only else clean_alpha_ok,
        "visual_review": visual_review,
        "notes": args.notes,
        "status": args.status,
        "review_authority": "root_delegated_by_user" if args.status == "accepted" else "",
        "user_reviewed": False,
        "listening_reviewed": False,
    }
    target = _layout_root / "reports/catalogue-rebuild-20261113/receipts" / f"{args.catalogue_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(target.relative_to(_layout_root)),
        "status": args.status,
        "glow_gate_pass": receipt["glow_gate_pass"],
        "clean_alpha_binary": receipt["clean_alpha_binary"],
        "gates_executed": not args.source_gate_only,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
