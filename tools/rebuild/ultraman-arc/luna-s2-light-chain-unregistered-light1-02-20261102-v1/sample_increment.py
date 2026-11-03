"""仅02拒收原位源的获准159整图派生；不改变冻12/01或原生Alpha结论。"""
from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE_TOOL = ROOT / "tools/rebuild/ultraman-arc/luna-s2-light-chain-unregistered-20261102-v1/sample_retained12.py"
SOURCE_DIR = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/light1/phase-02/request-002"
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-unregistered-20261102-v1/increment-light1-02-request002-v1"
REPORT = ROOT / "reports/review/2026-11-02/luna-light-chain-unregistered-light1-02-request002-v1"
OLD_BUNDLES = [
    ("reports/review/2026-11-02/luna-light-chain-unregistered-retained12-v1/subagent-owned-retained12-sha256-v1.json", "5daeb115a648e1e1a892dc2ba90baca61c19a8e08322b4189ab0a9c8ffe39faf"),
    ("reports/review/2026-11-02/luna-light-chain-unregistered-light1-01-request002-v1/subagent-owned-light1-01-increment-sha256-v1.json", "b01031c7393e04e766e74e5d97faa6b5fee5768666fb3eb405e8d058b8821448"),
]
spec = importlib.util.spec_from_file_location("luna_retained12_helpers", BASE_TOOL)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
from PIL import Image, ImageDraw
import numpy as np


def freeze_old():
    frozen = {}
    for name, digest in OLD_BUNDLES:
        path = ROOT / name
        assert base.sha(path) == digest
        frozen[name] = digest
        for item in base.read(path)["sha256_entries"]:
            checked = base.checked(item)
            frozen[base.rel(checked)] = base.sha(checked)
    assert base.rel(BASE_TOOL) in frozen
    return frozen


def recheck(frozen):
    for name, digest in frozen.items():
        assert base.sha(ROOT / name) == digest, name


def main():
    assert not ART.exists() and not REPORT.exists()
    old_frozen = freeze_old()
    source = SOURCE_DIR / "rejected/candidate.png"
    metadata_path = SOURCE_DIR / "rejected/candidate.metadata.json"
    review_path = SOURCE_DIR / "root-source-review.json"
    assert base.sha(review_path) == "e387fcbcfcfffe4753153ee20c3895b92dd50d7dd8af42ea93c3b3622d900acb"
    review, metadata = base.read(review_path), base.read(metadata_path)
    assert review["reviewer"] == "root_delegated_by_user" and review["actual_full_png_viewed"] is True and review["source_motion_accepted"] is True
    assert base.sha(source) == review["image_sha256"] == metadata["image_sha256"] == "b2946fd0212e015e2515367c56e75b65d795b8a7463b0f12b34f4bbf6bd9d690"
    assert base.sha(metadata_path) == review["metadata_sha256"]
    assert metadata["transparency_accepted"] is False and review["native_transparency_accepted"] is False
    assert metadata["resized_to_requested_size"] is False and metadata["padded_to_requested_aspect"] is False
    assert base.sha(SOURCE_DIR / "candidate.provider.png") == metadata["provider_image_sha256"]
    assert base.sha(base.TIMING) == "af8d9057c3761a808123b3e6b338764b0ae8311c0a75b9459c5239a5fb15c1c8"
    assert base.sha(base.JUMP_RECIPE) == "54890830bf4fde4a1524cf282ae91ff3d33fdee941bff414c64a5e0f89d07daf"
    phase_ticks = next(row["phase_ticks"] for row in base.read(base.TIMING)["actions"] if row["action"] == "light1")[2]
    palette = base.read(base.PALETTE)["colors"]
    assert len(palette) == 32 and phase_ticks == 4
    frozen = {base.rel(path): base.sha(path) for path in SOURCE_DIR.rglob("*") if path.is_file()}
    for path in [base.PALETTE, base.TIMING, base.JUMP_RECIPE, BASE_TOOL, Path(__file__).resolve(), ROOT / "tools/rebuild/shared/forge_backend.py"]:
        frozen[base.rel(path)] = base.sha(path)
    for item in metadata["references"]:
        path = Path(item["path"])
        path.relative_to(ROOT)
        assert base.sha(path) == item["sha256"]
        frozen[base.rel(path)] = base.sha(path)
    with Image.open(source) as image:
        assert image.format == "PNG" and image.mode == "RGBA" and image.size == (1024, 1024)
        original = image.copy()
    before = base.metrics(original)
    assert before["alpha128_edge_pixels"] == 0
    corners = [list(original.getpixel(point)) for point in [(0, 0), (1023, 0), (0, 1023), (1023, 1023)]]
    assert corners == review["corners_rgba"] and any(point[3] > 0 for point in corners)
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
    colors = {tuple(map(int, pixel)) for pixel in pixels[pixels[:, :, 3] > 0, :3]}
    assert colors <= {tuple(color) for color in palette}
    ART.mkdir(parents=True)
    REPORT.mkdir(parents=True)
    for folder in [ART, REPORT]:
        (folder / ".gitattributes").write_text("*.json -text -whitespace\n*.nul -text\n", encoding="utf-8", newline="\n")
    output = ART / "whole-source-159.png"
    small.save(output)
    views = []
    for kind in ["source1024", "whole159"]:
        for theme, color, ink in [("dark", "#252c38", "white"), ("light", "#e8dfcc", "#202020")]:
            page = Image.new("RGB", (636, 704), color)
            if kind == "source1024":
                # 仅完整源审图显示缩为636宽；不供人物采样或测点推导使用。
                shown = base.solid(original, color).resize((636, 636), Image.Resampling.LANCZOS)
                caption = f"月亮 light1/02 request002 · 原1024完整源显示636 · {theme}"
            else:
                shown = base.solid(small.resize((636, 636), Image.Resampling.NEAREST), color)
                caption = f"月亮 light1/02 request002 · 未注册159整方×4 · {theme}"
            page.paste(shown, (0, 64))
            draw = ImageDraw.Draw(page)
            draw.text((8, 4), caption, font=base.FONT, fill=ink)
            draw.text((8, 27), "原生Alpha拒收原位保持；只准整图Alpha128派生；注册/判定=null", font=base.SMALL, fill=ink)
            value = base.jpg(REPORT / f"light1-02-{kind}-complete-{theme}.jpg", page)
            value["image_kind"] = kind
            value["bound_image"] = base.ref(source if kind == "source1024" else output)
            value["native_display_scale"] = 636 / 1024 if kind == "source1024" else 4
            value["source_bbox_not_cropped"] = True
            if kind == "source1024":
                value["whole_unregistered159_canvas_shown"] = False
                value["whole_original1024_canvas_shown"] = True
                value["display_resize_only_not_sampling_or_measurement"] = True
            views.append(value)
    page = Image.new("RGB", (636, 255), "#364250")
    draw = ImageDraw.Draw(page)
    draw.text((8, 4), "月亮 light1/02 request002 · 159原生1:1 · 左深右浅", font=base.FONT, fill="white")
    draw.text((8, 28), "4tick仅引用；root/grip/判定/registration=null；冻12/01不改", font=base.SMALL, fill="white")
    page.paste(base.solid(small, "#252c38"), (159, 72))
    page.paste(base.solid(small, "#e8dfcc"), (318, 72))
    value = base.jpg(REPORT / "light1-02-native159-1x-complete-dark-light.jpg", page)
    value.update(image_kind="whole159", native_display_scale=1, bound_image=base.ref(output))
    views.append(value)
    receipt = {
        "schema": "ufeneo.arc-luna.s2.light1-02-unregistered-increment.v1", "fighter": "ultraman-arc__luna",
        "action": "light1", "phase": 2, "phase_ticks_reference_only": phase_ticks,
        "source": base.ref(source), "metadata": base.ref(metadata_path), "root_source_review": base.ref(review_path),
        "original_quarantine_path_unchanged": True, "original_native_transparency_accepted": False,
        "original_corners_rgba": corners, "alpha128_only_exception": review["limitations"][1],
        "whole_source_sample": base.ref(output), "source_dimensions": [1024, 1024], "whole_source_raster": [159, 159],
        "source_scale": 159 / 1024, "palette": base.ref(base.PALETTE), "backend": backend,
        "same_sampling_helpers": base.ref(BASE_TOOL), "jump_recipe": base.ref(base.JUMP_RECIPE),
        "recipe": ["binarize_alpha(original.copy())，128二值", "palette_mode('rgb')内整张_kcentroid_downscale(clean,159,159,detail_bias=True)", "本人固定32色apply_palette", "binarize_alpha(small)，128二值"],
        "source_alpha_before": before, "source_alpha_after_threshold": base.metrics(clean), "candidate_alpha": after,
        "shared_palette_visible_colors": len(colors), "views": views,
        "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None, "runtime_canvas": None,
        "unregistered": True, "bbox_crop": False, "component_filter_or_extra_pixel_deletion": False,
        "per_phase_size_or_area_fitting": False, "canonical_palette_only_no_body_recoloring": True,
        "no_320_frame_or_clip_or_atlas": True, "strict_size_accepted": False, "complete_action_accepted": False,
        "installed": False, "playable": False, "actual_page_review_pending": True,
        "frozen_inputs": frozen, "old12_and_01_frozen": old_frozen,
        "old12_and_01_package_bytes_unchanged": True, "script_POST_Godot_product_Git_or_user_file_reads": False,
        "new_cost_usd": "0", "new_video": False,
    }
    recheck(frozen)
    recheck(old_frozen)
    base.save(ART / "phase-receipt.json", receipt)
    base.save(REPORT / "sampling-result.json", {"phase_receipt": base.ref(ART / "phase-receipt.json"), "views": views,
                                               "old12_and_01_package_bytes_unchanged": True, "unregistered": True,
                                               "actual_page_review_pending": True, "measurement_proposal_pending": True})
    print(json.dumps({"result": base.ref(REPORT / "sampling-result.json"), "sample": base.ref(output)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
