"""根已签light3/04、05各自独立159整图增量；不出注册帧。"""
from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE2 = ROOT / "tools/rebuild/ultraman-arc/luna-s2-light-chain-unregistered-light1-02-20261102-v1/sample_increment.py"
spec = importlib.util.spec_from_file_location("luna_light1_02_sample_helpers", BASE2)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
base = prior.base
from PIL import Image, ImageDraw
import numpy as np

ROOT_REVIEW_SHA = {
    4: "61b567c6b7e20a611fb4c94387b45ea844cf290b09b77e0c980236e3ffeab399",
    5: "4e02a8100b2cfd92412f3797903a527325e6372f63e288d98430d481cc10172d",
}
OLD02 = ROOT / "reports/review/2026-11-02/luna-light-chain-unregistered-light1-02-request002-v1/subagent-owned-light1-02-increment-sha256-v1.json"


def old_frozen():
    frozen = prior.freeze_old()
    assert base.sha(OLD02) == "756d67dfaa722c30ef20c64d8f0f925f601a2ae4ea1e0376ac813a4375cf2d90"
    frozen[base.rel(OLD02)] = base.sha(OLD02)
    for value in base.read(OLD02)["sha256_entries"]:
        path = base.checked(value)
        frozen[base.rel(path)] = base.sha(path)
    return frozen


def locations(phase):
    source = ROOT / f"art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/light3/phase-{phase:02}/request-001"
    art = ROOT / f"art/fighters/ultraman-arc__luna/stage2/light-chain-unregistered-20261102-v1/increment-light3-{phase:02}-request001-v1"
    report = ROOT / f"reports/review/2026-11-02/luna-light-chain-unregistered-light3-{phase:02}-request001-v1"
    return source, art, report


def main(phase):
    assert phase in [4, 5]
    source_dir, art, report = locations(phase)
    assert not art.exists() and not report.exists()
    old = old_frozen()
    source = source_dir / "candidate.png"
    metadata_path, review_path = source_dir / "candidate.metadata.json", source_dir / "root-source-review.json"
    assert base.sha(review_path) == ROOT_REVIEW_SHA[phase]
    metadata, review = base.read(metadata_path), base.read(review_path)
    assert review["reviewer"] == "root_delegated_by_user" and review["actual_full_png_viewed"] is True and review["source_motion_accepted"] is True
    assert base.sha(source) == metadata["image_sha256"] == review["image_sha256"]
    assert base.sha(metadata_path) == review["metadata_sha256"]
    assert base.sha(source_dir / "candidate.provider.png") == metadata["provider_image_sha256"]
    assert metadata["resized_to_requested_size"] is False and metadata["padded_to_requested_aspect"] is False
    assert base.sha(base.TIMING) == "af8d9057c3761a808123b3e6b338764b0ae8311c0a75b9459c5239a5fb15c1c8"
    assert base.sha(base.JUMP_RECIPE) == "54890830bf4fde4a1524cf282ae91ff3d33fdee941bff414c64a5e0f89d07daf"
    ticks = next(row["phase_ticks"] for row in base.read(base.TIMING)["actions"] if row["action"] == "light3")[phase]
    palette = base.read(base.PALETTE)["colors"]
    assert len(palette) == 32
    frozen = {base.rel(path): base.sha(path) for path in source_dir.rglob("*") if path.is_file()}
    for path in [base.PALETTE, base.TIMING, base.JUMP_RECIPE, prior.BASE_TOOL, BASE2, Path(__file__).resolve(), ROOT / "tools/rebuild/shared/forge_backend.py"]:
        frozen[base.rel(path)] = base.sha(path)
    for value in metadata["references"]:
        path = Path(value["path"])
        path.relative_to(ROOT)
        assert base.sha(path) == value["sha256"]
        frozen[base.rel(path)] = base.sha(path)
    with Image.open(source) as image:
        assert image.mode == "RGBA" and image.format == "PNG" and image.size == (1024, 1024)
        original = image.copy()
    assert base.metrics(original)["alpha128_edge_pixels"] == 0
    clean = base.binarize_alpha(original.copy())
    with base.palette_mode("rgb"):
        small = base._kcentroid_downscale(clean, 159, 159, detail_bias=True)
        base.apply_palette(small, palette)
        base.binarize_alpha(small)
        backend = base.backend_info()
    after = base.metrics(small)
    assert after["alpha_values"] == [0, 255] and after["nonzero_alpha_edge_pixels"] == 0
    pixels = np.asarray(small)
    assert not pixels[pixels[:, :, 3] == 0].any()
    colors = {tuple(map(int, value)) for value in pixels[pixels[:, :, 3] > 0, :3]}
    assert colors <= {tuple(value) for value in palette}
    art.mkdir(parents=True)
    report.mkdir(parents=True)
    for folder in [art, report]:
        (folder / ".gitattributes").write_text("*.json -text -whitespace\n*.nul -text\n", encoding="utf-8", newline="\n")
    output = art / "whole-source-159.png"
    small.save(output)
    views = []
    for kind in ["source1024", "whole159"]:
        for theme, color, ink in [("dark", "#252c38", "white"), ("light", "#e8dfcc", "#202020")]:
            page = Image.new("RGB", (636, 704), color)
            shown = (base.solid(original, color).resize((636, 636), Image.Resampling.LANCZOS) if kind == "source1024"
                     else base.solid(small.resize((636, 636), Image.Resampling.NEAREST), color))
            page.paste(shown, (0, 64))
            draw = ImageDraw.Draw(page)
            caption = "原1024完整源显示636" if kind == "source1024" else "完整159方×4"
            draw.text((8, 4), f"月亮 light3/{phase:02} request001 · {caption} · {theme}", font=base.FONT, fill=ink)
            draw.text((8, 27), "独立增量；整图同倍率；root/grip/判定/registration=null", font=base.SMALL, fill=ink)
            value = base.jpg(report / f"light3-{phase:02}-{kind}-complete-{theme}.jpg", page)
            value.update(image_kind=kind, native_display_scale=636 / 1024 if kind == "source1024" else 4,
                         bound_image=base.ref(source if kind == "source1024" else output))
            if kind == "source1024":
                value.update(whole_unregistered159_canvas_shown=False, whole_original1024_canvas_shown=True,
                             display_resize_only_not_sampling_or_measurement=True)
            views.append(value)
    page = Image.new("RGB", (636, 255), "#364250")
    draw = ImageDraw.Draw(page)
    draw.text((8, 4), f"月亮 light3/{phase:02} request001 · 159原生1:1 · 左深右浅", font=base.FONT, fill="white")
    draw.text((8, 28), f"{ticks}tick仅引用；候选未注册；冻12/01/02保持", font=base.SMALL, fill="white")
    page.paste(base.solid(small, "#252c38"), (159, 72))
    page.paste(base.solid(small, "#e8dfcc"), (318, 72))
    value = base.jpg(report / f"light3-{phase:02}-native159-1x-complete-dark-light.jpg", page)
    value.update(image_kind="whole159", native_display_scale=1, bound_image=base.ref(output))
    views.append(value)
    receipt = {
        "schema": "ufeneo.arc-luna.s2.light3-return-unregistered-increment.v1", "fighter": "ultraman-arc__luna",
        "action": "light3", "phase": phase, "phase_ticks_reference_only": ticks,
        "source": base.ref(source), "metadata": base.ref(metadata_path), "root_source_review": base.ref(review_path),
        "original_native_transparency_accepted": metadata["transparency_accepted"], "whole_source_sample": base.ref(output),
        "source_dimensions": [1024, 1024], "whole_source_raster": [159, 159], "source_scale": 159 / 1024,
        "recipe": ["binarize_alpha(original.copy())", "palette_mode('rgb')内整张_kcentroid_downscale(clean,159,159,detail_bias=True)", "本人固定32色apply_palette", "binarize_alpha(small)"],
        "palette": base.ref(base.PALETTE), "backend": backend, "shared_palette_visible_colors": len(colors),
        "source_alpha_before": base.metrics(original), "source_alpha_after_threshold": base.metrics(clean), "candidate_alpha": after,
        "views": views, "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
        "runtime_canvas": None, "unregistered": True, "bbox_crop": False, "component_filter_or_extra_pixel_deletion": False,
        "per_phase_size_or_area_fitting": False, "canonical_palette_only_no_body_recoloring": True,
        "no_320_frame_or_clip_or_atlas": True, "strict_size_accepted": False, "complete_action_accepted": False,
        "installed": False, "playable": False, "actual_page_review_pending": True,
        "frozen_inputs": frozen, "old12_01_02_frozen": old, "old12_01_02_package_bytes_unchanged": True,
        "script_POST_Godot_product_Git_or_user_file_reads": False, "new_cost_usd": "0", "new_video": False,
    }
    prior.recheck(frozen)
    prior.recheck(old)
    base.save(art / "phase-receipt.json", receipt)
    base.save(report / "sampling-result.json", {"phase_receipt": base.ref(art / "phase-receipt.json"), "views": views,
                                              "unregistered": True, "old12_01_02_package_bytes_unchanged": True,
                                              "actual_page_review_pending": True})
    print(json.dumps({"phase": phase, "result": base.ref(report / "sampling-result.json"), "sample": base.ref(output)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    main(int(sys.argv[1]))
