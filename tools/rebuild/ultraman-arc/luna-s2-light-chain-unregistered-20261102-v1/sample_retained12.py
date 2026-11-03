"""12张已授权整源统一159方候选：无注册、无运行帧/判定、无网络或产品操作。"""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-unregistered-20261102-v1/retained12-v1"
REPORT = ROOT / "reports/review/2026-11-02/luna-light-chain-unregistered-retained12-v1"
SOURCE_CONTRACT = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/source-reference-contract.json"
TIMING = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/timing-contract.json"
PALETTE = ROOT / "art/fighters/ultraman-arc__luna/model/palette.json"
NEW00 = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/light1/phase-00/request-002"
JUMP_RECIPE = ROOT / "tools/rebuild/ultraman-arc/luna-jump-offline-resume-20261102-v1/offline_jump.py"
FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
SMALL = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 12)
SIZE = 159
sys.path.insert(0, str(ROOT / "tools/rebuild/shared"))
from forge_backend import _kcentroid_downscale, apply_palette, binarize_alpha, palette_mode, backend_info


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def ref(path):
    return {"path": rel(path), "sha256": sha(path)}


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def checked(value):
    path = (ROOT / value["path"]).resolve()
    path.relative_to(ROOT)
    assert sha(path) == value["sha256"], value["path"]
    return path


def metrics(image):
    alpha = np.asarray(image.getchannel("A"))
    mask = alpha >= 128
    yy, xx = np.where(mask)
    labels, _ = ndimage.label(mask, np.ones((3, 3), dtype=int))
    areas = sorted(map(int, np.bincount(labels.ravel())[1:]), reverse=True)
    return {"size": list(image.size), "mode": image.mode, "alpha_values": np.unique(alpha).tolist(),
            "alpha128_bbox_safety_only": [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1] if len(xx) else None,
            "alpha128_area": int(mask.sum()), "nonzero_alpha_bbox": list(image.getbbox()) if image.getbbox() else None,
            "partial_alpha_pixels": int(((alpha > 0) & (alpha < 255)).sum()),
            "nonzero_alpha_edge_pixels": int(np.count_nonzero(alpha[0]) + np.count_nonzero(alpha[-1]) + np.count_nonzero(alpha[1:-1, 0]) + np.count_nonzero(alpha[1:-1, -1])),
            "alpha128_edge_pixels": int(mask[0].sum() + mask[-1].sum() + mask[1:-1, 0].sum() + mask[1:-1, -1].sum()),
            "component_areas_diagnostic_only": areas, "component_filter_or_pixels_deleted": False}


def jpg(path, image):
    assert image.width <= 768 and not path.exists()
    image.convert("RGB").save(path, "JPEG", quality=80, optimize=True)
    assert path.stat().st_size <= 150000
    return {**ref(path), "size": list(image.size), "quality": 80, "bytes": path.stat().st_size,
            "whole_unregistered159_canvas_shown": True, "source_bbox_not_cropped": True,
            "actual_visual_review_pending": True}


def solid(image, background):
    output = Image.new("RGB", image.size, background)
    output.paste(image, (0, 0), image)
    return output


def main():
    assert not ART.exists() and not REPORT.exists()
    assert sha(SOURCE_CONTRACT) == "8c22511ae3d20036445f589dc9ddf0b934b040fee5a625dd015b7a377525a2d9"
    assert sha(TIMING) == "af8d9057c3761a808123b3e6b338764b0ae8311c0a75b9459c5239a5fb15c1c8"
    assert sha(JUMP_RECIPE) == "54890830bf4fde4a1524cf282ae91ff3d33fdee941bff414c64a5e0f89d07daf"
    source_contract = read(SOURCE_CONTRACT)
    root_gap_review = checked(source_contract["root_source_gap_review"])
    timing = read(TIMING)
    phase_ticks = {row["action"]: row["phase_ticks"] for row in timing["actions"]}
    palette = read(PALETTE)["colors"]
    assert len(palette) == 32
    old = {(row["action"], row["phase"]): row for row in source_contract["current_existing_sources"]}
    selections = []
    source00, metadata00, review00 = [NEW00 / name for name in ["candidate.png", "candidate.metadata.json", "root-source-review.json"]]
    new_review, new_metadata = read(review00), read(metadata00)
    assert new_review["reviewer"] == "root_delegated_by_user" and new_review["actual_full_png_viewed"] is True
    assert new_review["source_motion_accepted"] is True
    assert sha(source00) == new_review["image_sha256"] == new_metadata["image_sha256"]
    assert sha(metadata00) == new_review["metadata_sha256"]
    selections.append({"action": "light1", "phase": 0, "source": ref(source00), "metadata": ref(metadata00),
                       "review": ref(review00), "provider": ref(NEW00 / "candidate.provider.png"),
                       "prior_attempt_disposition": "仅取根已签request002；request001错手源不处理",
                       "source_kind": "new_root_accepted_request002", "original_client_transparency_accepted": new_metadata["transparency_accepted"],
                       "original_quarantine_preserved": False})
    for action, phases in [("light1", [3, 4]), ("light2", [0, 1, 2, 3, 4]), ("light3", [0, 1, 2, 3])]:
        for phase in phases:
            item = old[(action, phase)]
            for key in ["client1024", "metadata", "saved_provider1254", "request_state"]:
                checked(item[key])
            selections.append({"action": action, "phase": phase, "source": item["client1024"], "metadata": item["metadata"],
                               "provider": item["saved_provider1254"], "request_state": item["request_state"],
                               "review": ref(root_gap_review), "source_kind": "old_retained_whole_candidate",
                               "original_client_transparency_accepted": item["metadata_transparency_accepted"],
                               "original_quarantine_preserved": item["historical_quarantine"],
                               "historical_request_state": item["historical_state"]})
    assert len(selections) == 12 and len({row["source"]["sha256"] for row in selections}) == 12
    images, frozen = {}, {}
    for row in selections:
        for key in ["source", "metadata", "review", "provider", "request_state"]:
            if key in row:
                path = checked(row[key])
                frozen[rel(path)] = sha(path)
        source = checked(row["source"])
        with Image.open(source) as image:
            assert image.format == "PNG" and image.mode == "RGBA" and image.size == (1024, 1024)
            images[(row["action"], row["phase"])] = image.copy()
        before = metrics(images[(row["action"], row["phase"])])
        assert before["alpha128_edge_pixels"] == 0 and before["alpha128_area"] > 0
    for path in [SOURCE_CONTRACT, TIMING, PALETTE, JUMP_RECIPE, ROOT / "tools/rebuild/shared/forge_backend.py", Path(__file__).resolve()]:
        frozen[rel(path)] = sha(path)
    ART.mkdir(parents=True)
    REPORT.mkdir(parents=True)
    for folder in [ART, REPORT]:
        (folder / ".gitattributes").write_text("*.json -text -whitespace\n*.nul -text\n", encoding="utf-8", newline="\n")
    with palette_mode("rgb"):
        backend = backend_info()
    contract = {"schema": "ufeneo.arc-luna.s2.light-chain-unregistered-processing.v1", "fighter": "ultraman-arc__luna",
                "root_delegated_instruction": "仅11保留旧源及已签00 request002，沿跳跃RGB兼容159整图+128二值；不裁bbox/删分量/逐相缩放/重着色，root/grip/判定先null。",
                "source_dimensions": [1024, 1024], "whole_source_raster": [159, 159], "source_scale": SIZE / 1024,
                "recipe": ["binarize_alpha(original.copy())，阈值128", "palette_mode('rgb')内整张_kcentroid_downscale(clean,159,159,detail_bias=True)", "同本人固定32色apply_palette", "binarize_alpha(small)，阈值128"],
                "jump_recipe_source": ref(JUMP_RECIPE), "palette": ref(PALETTE), "backend": backend,
                "canonical_palette_only_no_body_recoloring": True, "bbox_crop_or_component_filter": False,
                "per_phase_scale_or_area_fitting": False, "whole_source_only": True,
                "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "anchors": None,
                "registration": None, "runtime_canvas": None,
                "unregistered": True, "clip_or_atlas_written": False, "selections": selections, "frozen_inputs": frozen,
                "sampling_script_POST_Godot_product_Git_or_user_file_reads": False}
    save(ART / "processing-contract.json", contract)
    receipts, samples, previews = [], {}, []
    for row in selections:
        action, phase = row["action"], row["phase"]
        original = images[(action, phase)]
        clean = binarize_alpha(original.copy())
        with palette_mode("rgb"):
            small = _kcentroid_downscale(clean, SIZE, SIZE, detail_bias=True)
            apply_palette(small, palette)
            binarize_alpha(small)
        assert small.mode == "RGBA" and small.size == (159, 159)
        after = metrics(small)
        assert after["alpha_values"] == [0, 255] and after["alpha128_area"] > 0
        assert after["nonzero_alpha_edge_pixels"] == 0
        rgba = np.asarray(small)
        colors = {tuple(int(value) for value in pixel) for pixel in rgba[rgba[:, :, 3] > 0, :3]}
        assert colors <= {tuple(color) for color in palette}
        assert not rgba[rgba[:, :, 3] == 0].any()
        folder = ART / action / f"phase-{phase:02}"
        folder.mkdir(parents=True)
        output = folder / "whole-source-159.png"
        small.save(output)
        samples[(action, phase)] = small
        views = []
        for theme, color, ink in [("dark", "#252c38", "white"), ("light", "#e8dfcc", "#202020")]:
            # 仅审片显示为精确4倍NEAREST，159整幅始终完整；不保存新的放大人物PNG。
            page = Image.new("RGB", (636, 704), color)
            enlarged = small.resize((636, 636), Image.Resampling.NEAREST)
            page.paste(solid(enlarged, color), (0, 64))
            draw = ImageDraw.Draw(page)
            draw.text((8, 4), f"月亮 {action}/{phase:02} · 未注册159整方×4 · {theme}", font=FONT, fill=ink)
            draw.text((8, 27), "root/grip/判定=null；不裁框/不删分量/不按相拟合；候选未签", font=SMALL, fill=ink)
            path = REPORT / f"{action}-{phase:02}-whole159-4x-{theme}.jpg"
            value = jpg(path, page)
            value.update(native_display_scale=4, pixel_nearest=True, source_sample=ref(output))
            views.append(value)
        receipt = {"schema": "ufeneo.arc-luna.s2.light-chain-unregistered-phase.v1", "fighter": "ultraman-arc__luna",
                   "action": action, "phase": phase, "phase_ticks_reference_only": phase_ticks[action][phase],
                   "selection": row, "processing_contract": ref(ART / "processing-contract.json"),
                   "source": row["source"], "source_dimensions": [1024, 1024], "whole_source_raster": [159, 159],
                   "source_scale": SIZE / 1024, "palette": ref(PALETTE), "backend": backend,
                   "source_alpha_before": metrics(original), "source_alpha_after_threshold": metrics(clean), "candidate_alpha": after,
                   "shared_palette_visible_colors": len(colors), "whole_source_sample": ref(output),
                   "source_client_original_transparency_accepted": row["original_client_transparency_accepted"],
                   "source_historical_quarantine_preserved": row["original_quarantine_preserved"],
                   "alpha_exception_authority": "根本次仅授权整图Alpha128派生候选；旧metadata与rejected位置保持，不称原生Alpha门被改成通过。",
                   "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "anchors": None,
                   "registration": None, "unregistered": True, "no_320_frame_or_clip_or_atlas": True,
                   "component_filter_or_pixels_deleted": False, "bbox_crop": False,
                   "per_phase_scale_or_area_fitting": False, "canonical_palette_only_no_body_recoloring": True,
                   "deep_light_complete_views": views, "strict_size_accepted": False, "action_or_main_accepted": False,
                   "installed": False, "playable": False, "sampling_script_POST_Godot_product_Git_or_user_file_reads": False}
        path = folder / "phase-receipt.json"
        save(path, receipt)
        receipts.append(ref(path))
        previews.extend(views)
    for action in ["light1", "light2", "light3"]:
        selected = [row for row in selections if row["action"] == action]
        page = Image.new("RGB", (636, 64 + 207 * ((len(selected) + 1) // 2)), "#364250")
        draw = ImageDraw.Draw(page)
        draw.text((8, 4), f"月亮 {action} 保留相 · 159原生1:1 · 每相左深右浅", font=FONT, fill="white")
        draw.text((8, 28), "相号照列；缺相未代填，不是完整动作或接续验收；未注册", font=SMALL, fill="white")
        binding = []
        for index, row in enumerate(selected):
            phase = row["phase"]
            small = samples[(action, phase)]
            x, y = (index % 2) * 318, 64 + (index // 2) * 207
            draw.text((x + 6, y), f"{phase:02} / {phase_ticks[action][phase]}tick / root=null", font=SMALL, fill="#ffe780")
            page.paste(solid(small, "#252c38"), (x, y + 24))
            page.paste(solid(small, "#e8dfcc"), (x + 159, y + 24))
            binding.append({"action": action, "phase": phase, "source_sample": ref(ART / action / f"phase-{phase:02}/whole-source-159.png"), "native_display_scale": 1})
        path = REPORT / f"{action}-native159-1x-complete-dark-light.jpg"
        value = jpg(path, page)
        value.update(native_display_scale=1, sample_bindings=binding)
        previews.append(value)
    assert all(sha(ROOT / name) == digest for name, digest in frozen.items())
    result = {"schema": "ufeneo.arc-luna.s2.light-chain-unregistered-retained12-result.v1",
              "processing_contract": ref(ART / "processing-contract.json"), "receipts": receipts, "views": previews,
              "processed": [{"action": row["action"], "phase": row["phase"]} for row in selections],
              "remaining_new_sources_not_processed": [{"action": "light1", "phases": [1, 2]}, {"action": "light3", "phases": [4, 5]}],
              "all_original_and_bound_bytes_unchanged": True, "old_quarantine_not_released": True,
              "all_root_grip_hit_hurt_registration_null": True, "unregistered": True,
              "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
              "strict_size_or_complete_action_accepted": False, "actual_page_review_pending": True,
              "sampling_script_POST_Godot_product_Git_or_user_file_reads": False}
    save(REPORT / "sampling-result.json", result)
    print(json.dumps({"result": ref(REPORT / "sampling-result.json"), "phase_receipts": len(receipts), "complete_JPEG_pages": len(previews), "registered": False, "no_product_or_POST": True}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
