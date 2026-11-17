"""Re-pack installed catalogue strips in the fixed 384x256 UI cell.

Long tails, wings and dorsal fins must stay complete. The catalogue UI and
`tools/check/catalogue_idle.py` use one 384x256 cell, so the approved wide-body
treatment uses one uniform body-area scale relative to `still-00` for the still
and every animation frame, shrunk uniformly if the widest frame exceeds the
372px inner width and registered in `strip_width_fit`. Horizontal placement
aligns the opaque-pixel median X to `ROOT_X` (clamped inside the cell) so
swinging tails/arms do not shift the character's torso or feet horizontally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/media/art"))
from catalogue_native import (  # noqa: E402
    apply_palette, build_palette, downsample, harden_alpha, load_raw, trim,
)
import catalogue_store  # noqa: E402

ART = ROOT / "art/catalogue-rebuild-20261113"
CANVAS_WIDTH = 384
CANVAS_HEIGHT = 256
ROOT_X = 192
ROOT_Y = 248
MARGIN_X = 6
AVAILABLE_WIDTH = CANVAS_WIDTH - 2 * MARGIN_X
FRAME_NAMES = ("still-00-clean.png", "idle-01-clean.png", "idle-02-clean.png")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_frame_ratios(cid: str, nominal_height: int) -> tuple[float, float]:
    """Compute constant-body-area height ratios for idle-01 and idle-02 vs still-00."""
    raw_hs: list[int] = []
    raw_areas: list[int] = []
    for name in FRAME_NAMES:
        raw = trim(load_raw(ART / cid / name))
        arr = np.asarray(raw)
        raw_hs.append(raw.height)
        raw_areas.append(max(1, int((arr[:, :, 3] >= 128).sum())))
    s1 = (raw_hs[1] / raw_hs[0]) * ((raw_areas[0] / raw_areas[1]) ** 0.5)
    s2 = (raw_hs[2] / raw_hs[0]) * ((raw_areas[0] / raw_areas[2]) ** 0.5)
    r1 = max(0.78, min(1.03, s1))
    r2 = max(0.78, min(1.03, s2))
    med_r = sorted([1.0, r1, r2])[1]
    if nominal_height > 0 and abs(med_r - 1.0) * nominal_height > 4.0:
        target_med = (1.0 - 4.0 / nominal_height) if med_r < 1.0 else (1.0 + 4.0 / nominal_height)
        if abs(r1 - 1.0) <= abs(r2 - 1.0):
            r1 = target_med
        else:
            r2 = target_med
    return r1, r2


def compose(cid: str, palette: list, heights: list[int]) -> list[Image.Image]:
    frames = []
    for name, height in zip(FRAME_NAMES, heights):
        reduced = trim(downsample(trim(load_raw(ART / cid / name)), height))
        # Region averaging can lose one edge row. Normalise that tiny round-off
        # back to the frame's target height, then use nearest neighbour.
        if reduced.height != height:
            width = max(1, round(reduced.width * height / reduced.height))
            reduced = harden_alpha(reduced.resize((width, height), Image.NEAREST))
        coloured = apply_palette(reduced, palette)
        padded = Image.new("RGBA", (coloured.width, height), (0, 0, 0, 0))
        padded.alpha_composite(coloured, (0, 0))
        frames.append(padded)
    return frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalogue_ids", nargs="+")
    args = parser.parse_args()
    display = catalogue_store.load()["entries"]
    results = []
    for cid in args.catalogue_ids:
        entry = display[cid]
        native = ROOT / entry["image"].removeprefix("res://")
        with Image.open(native) as handle:
            base = harden_alpha(handle.convert("RGBA"))
        palette = build_palette(trim(base))
        nominal_height = int(entry.get("scale_target") or trim(base).height)
        r1, r2 = relative_frame_ratios(cid, nominal_height)

        height = nominal_height
        for _ in range(12):
            target_heights = [
                height,
                max(1, round(height * r1)),
                max(1, round(height * r2)),
            ]
            med_t = sorted(target_heights)[1]
            if abs(med_t - target_heights[0]) > 4:
                clamped_med = target_heights[0] - 4 if med_t < target_heights[0] else target_heights[0] + 4
                if abs(target_heights[1] - target_heights[0]) <= abs(target_heights[2] - target_heights[0]):
                    target_heights[1] = max(1, clamped_med)
                else:
                    target_heights[2] = max(1, clamped_med)
            frames = compose(cid, palette, target_heights)
            widest = max(frame.width for frame in frames)
            if widest <= AVAILABLE_WIDTH:
                break
            next_height = max(1, int(height * AVAILABLE_WIDTH / widest))
            if next_height >= height:
                next_height = height - 1
            if next_height < 1:
                raise SystemExit(f"{cid}: cannot fit wide silhouette at height {height}")
            height = next_height
        else:
            raise SystemExit(f"{cid}: width fit did not converge")

        actual_heights = [frame.height for frame in frames]
        med_height = int(np.median(actual_heights))
        declared = round((actual_heights[0] + med_height) / 2)
        placements = []
        lefts: list[int] = []
        for frame in frames:
            arr = np.asarray(frame)
            _, xs = np.nonzero(arr[:, :, 3] > 0)
            cx = float(np.median(xs))
            left = int(round(ROOT_X - cx))
            left = max(MARGIN_X, min(CANVAS_WIDTH - MARGIN_X - frame.width, left))
            lefts.append(left)
        # First frame is also the rewritten static display image, so the still
        # and animation strip share one scale, palette, root and colour table.
        static = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        static.alpha_composite(frames[0], (lefts[0], ROOT_Y - frames[0].height))
        static.save(native)
        strip = Image.new("RGBA", (CANVAS_WIDTH * len(frames), CANVAS_HEIGHT), (0, 0, 0, 0))
        for index, (frame, left) in enumerate(zip(frames, lefts)):
            if left < MARGIN_X or left + frame.width > CANVAS_WIDTH - MARGIN_X:
                raise SystemExit(f"{cid}: frame {index} exceeds cell after common scale")
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            canvas.alpha_composite(frame, (left, ROOT_Y - frame.height))
            strip.alpha_composite(canvas, (CANVAS_WIDTH * index, 0))
            placements.append({"index": index, "left": left, "width": frame.width,
                               "height": frame.height, "alignment": "alpha_median_x_centroid"})
        out = ROOT / f"assets/fighters/{cid}/catalogue/anim-strip.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        strip.save(out)
        uniform_scale_applied = actual_heights[0] != nominal_height
        width_fit = {
            "nominal_height": nominal_height,
            "height": declared,
            "frame_heights": actual_heights,
            "max_width": widest,
            "available_width": AVAILABLE_WIDTH,
            "uniform_scale_applied": uniform_scale_applied,
            "basis": "catalogue_wide_silhouette_uniform_scale" if uniform_scale_applied else "catalogue_fixed_cell",
        }
        catalogue_store.update_entry(cid, {
            "image_sha256": digest(native),
            "native_canvas": [CANVAS_WIDTH, CANVAS_HEIGHT],
            "native_root": [ROOT_X, ROOT_Y],
            "visible_height_including_ornaments": declared,
            "strip": "res://" + out.relative_to(ROOT).as_posix(),
            "frames": len(frames),
            "strip_sha256": digest(out),
            "strip_cell": [CANVAS_WIDTH, CANVAS_HEIGHT],
            "strip_root": [ROOT_X, ROOT_Y],
            "strip_alignment": "alpha_median_x_wide_silhouette_uniform_scale" if uniform_scale_applied
                               else "alpha_median_x_body_area_fit",
            "strip_width_fit": width_fit,
            "idle_source": "mcp_image_to_image_idle_frames",
        })
        results.append({"id": cid, "strip_sha256": digest(out), "frames": len(frames),
                        "height": declared, "cell": [CANVAS_WIDTH, CANVAS_HEIGHT],
                        "root": [ROOT_X, ROOT_Y], "width_fit": width_fit,
                        "placements": placements})
    print(json.dumps({"check": "catalogue_rebuild_repack", "results": results},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
