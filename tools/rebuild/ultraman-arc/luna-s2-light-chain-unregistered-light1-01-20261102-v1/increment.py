"""仅light1/01 request002的未注册整图采样及追加审图；旧12包不改。"""
from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE_TOOL = ROOT / "tools/rebuild/ultraman-arc/luna-s2-light-chain-unregistered-20261102-v1/sample_retained12.py"
BASE_REPORT = ROOT / "reports/review/2026-11-02/luna-light-chain-unregistered-retained12-v1"
SOURCE = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/light1/phase-01/request-002"
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-unregistered-20261102-v1/increment-light1-01-request002-v1"
REPORT = ROOT / "reports/review/2026-11-02/luna-light-chain-unregistered-light1-01-request002-v1"

spec = importlib.util.spec_from_file_location("luna_retained12_helpers", BASE_TOOL)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
from PIL import Image, ImageDraw
import numpy as np


def old_package():
    path = BASE_REPORT / "subagent-owned-retained12-sha256-v1.json"
    assert base.sha(path) == "5daeb115a648e1e1a892dc2ba90baca61c19a8e08322b4189ab0a9c8ffe39faf"
    manifest = base.read(path)
    frozen = {base.rel(path): base.sha(path)}
    for item in manifest["sha256_entries"]:
        checked = base.checked(item)
        frozen[base.rel(checked)] = base.sha(checked)
    assert base.rel(BASE_TOOL) in frozen
    return frozen


def recheck(frozen):
    assert all(base.sha(ROOT / name) == digest for name, digest in frozen.items())


def sample():
    assert not ART.exists() and not REPORT.exists()
    old_frozen = old_package()
    root_review = base.read(SOURCE / "root-source-review.json")
    metadata = base.read(SOURCE / "candidate.metadata.json")
    source = SOURCE / "candidate.png"
    assert root_review["reviewer"] == "root_delegated_by_user"
    assert root_review["actual_full_png_viewed"] and root_review["source_motion_accepted"]
    assert base.sha(source) == root_review["image_sha256"] == metadata["image_sha256"] == "06b58a9fe36a96178b6deb478032e3ae03c8831721039e2e04c8f22edd813b31"
    assert base.sha(SOURCE / "candidate.provider.png") == metadata["provider_image_sha256"]
    assert metadata["resized_to_requested_size"] is False and metadata["padded_to_requested_aspect"] is False
    assert base.sha(base.TIMING) == "af8d9057c3761a808123b3e6b338764b0ae8311c0a75b9459c5239a5fb15c1c8"
    assert base.sha(base.JUMP_RECIPE) == "54890830bf4fde4a1524cf282ae91ff3d33fdee941bff414c64a5e0f89d07daf"
    ticks = next(row["phase_ticks"] for row in base.read(base.TIMING)["actions"] if row["action"] == "light1")[1]
    palette = base.read(base.PALETTE)["colors"]
    assert len(palette) == 32 and ticks == 2
    frozen = {base.rel(path): base.sha(path) for path in SOURCE.iterdir() if path.is_file()}
    for path in [base.PALETTE, base.TIMING, base.JUMP_RECIPE, BASE_TOOL, Path(__file__).resolve(), ROOT / "tools/rebuild/shared/forge_backend.py"]:
        frozen[base.rel(path)] = base.sha(path)
    for item in metadata["references"]:
        path = Path(item["path"])
        path.relative_to(ROOT)
        assert base.sha(path) == item["sha256"]
        frozen[base.rel(path)] = base.sha(path)
    with Image.open(source) as image:
        assert image.format == "PNG" and image.size == (1024, 1024) and image.mode == "RGBA"
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
    colors = {tuple(map(int, pixel)) for pixel in pixels[pixels[:, :, 3] > 0, :3]}
    assert colors <= {tuple(color) for color in palette}
    ART.mkdir(parents=True)
    REPORT.mkdir(parents=True)
    for folder in [ART, REPORT]:
        (folder / ".gitattributes").write_text("*.json -text -whitespace\n*.nul -text\n", encoding="utf-8", newline="\n")
    sample_path = ART / "whole-source-159.png"
    small.save(sample_path)
    views = []
    for theme, color, ink in [("dark", "#252c38", "white"), ("light", "#e8dfcc", "#202020")]:
        page = Image.new("RGB", (636, 704), color)
        page.paste(base.solid(small.resize((636, 636), Image.Resampling.NEAREST), color), (0, 64))
        draw = ImageDraw.Draw(page)
        draw.text((8, 4), f"月亮 light1/01 request002 · 完整159方×4 · {theme}", font=base.FONT, fill=ink)
        draw.text((8, 27), "独立增量；root/grip/判定/registration=null；候选未签", font=base.SMALL, fill=ink)
        value = base.jpg(REPORT / f"light1-01-whole159-4x-{theme}.jpg", page)
        value.update(native_display_scale=4, pixel_nearest=True, source_sample=base.ref(sample_path))
        views.append(value)
    page = Image.new("RGB", (636, 255), "#364250")
    draw = ImageDraw.Draw(page)
    draw.text((8, 4), "月亮 light1/01 request002 · 159原生1:1 · 左深右浅", font=base.FONT, fill="white")
    draw.text((8, 28), "2tick仅引用；无注册/实际判定；未代填02；旧12包保持", font=base.SMALL, fill="white")
    page.paste(base.solid(small, "#252c38"), (159, 72))
    page.paste(base.solid(small, "#e8dfcc"), (318, 72))
    value = base.jpg(REPORT / "light1-01-native159-1x-complete-dark-light.jpg", page)
    value.update(native_display_scale=1, source_sample=base.ref(sample_path))
    views.append(value)
    receipt = {
        "schema": "ufeneo.arc-luna.s2.light-chain-unregistered-light1-01-increment.v1",
        "fighter": "ultraman-arc__luna", "action": "light1", "phase": 1,
        "root_instruction": "仅根已签01 request002新独立增量；159整图/Alpha128/RGB，与已冻12包相同；不碰未签02，不改原包。",
        "source": base.ref(source), "metadata": base.ref(SOURCE / "candidate.metadata.json"),
        "root_source_review": base.ref(SOURCE / "root-source-review.json"),
        "source_root_signature_scope": "根实看完整PNG接受源；本程序另绑定metadata/provider，并不伪称根原review含metadata SHA。",
        "whole_source_sample": base.ref(sample_path), "source_dimensions": [1024, 1024],
        "whole_source_raster": [159, 159], "source_scale": 159 / 1024,
        "recipe": ["binarize_alpha(original.copy())", "palette_mode('rgb')内整图_kcentroid_downscale(clean,159,159,detail_bias=True)", "本人固定32色apply_palette", "binarize_alpha(small)"],
        "palette": base.ref(base.PALETTE), "backend": backend, "shared_palette_visible_colors": len(colors),
        "jump_recipe": base.ref(base.JUMP_RECIPE), "same_processing_helpers": base.ref(BASE_TOOL),
        "source_alpha_before": base.metrics(original), "source_alpha_after_threshold": base.metrics(clean),
        "candidate_alpha": after, "source_original_transparency_accepted": metadata["transparency_accepted"],
        "alpha128_authority": "根本次仅授权完整二值派生；原低Alpha散点与metadata不回改，不删连通块。",
        "phase_ticks_reference_only": ticks, "views": views,
        "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "anchors": None, "registration": None,
        "unregistered": True, "bbox_crop": False, "component_filter_or_pixels_deleted": False,
        "per_phase_size_or_area_fitting": False, "canonical_palette_only_no_body_recoloring": True,
        "runtime_canvas": None, "no_320_frame_or_clip_or_atlas": True,
        "strict_size_accepted": False, "complete_action_accepted": False, "actual_page_review_pending": True,
        "installed": False, "playable": False, "frozen_inputs": frozen, "old12_frozen": old_frozen,
        "old12_package_bytes_unchanged": True, "new_cost_usd": "0", "new_video": False,
        "script_POST_Godot_product_Git_or_user_file_reads": False,
    }
    recheck(frozen)
    recheck(old_frozen)
    base.save(ART / "phase-receipt.json", receipt)
    result = {"phase_receipt": base.ref(ART / "phase-receipt.json"), "views": views,
              "old12_package_bytes_unchanged": True, "unregistered": True, "root_actual_review_pending": True}
    base.save(REPORT / "sampling-result.json", result)
    print(json.dumps({"result": base.ref(REPORT / "sampling-result.json"), "sample": base.ref(sample_path), "unregistered": True}, ensure_ascii=False), flush=True)


def finalize():
    result = base.read(REPORT / "sampling-result.json")
    receipt_path = base.checked(result["phase_receipt"])
    receipt = base.read(receipt_path)
    recheck(receipt["frozen_inputs"])
    recheck(receipt["old12_frozen"])
    base.checked(receipt["whole_source_sample"])
    for value in result["views"]:
        base.checked(value)
    review = {
        "schema": "ufeneo.arc-luna.s2.light1-01-increment-subagent-actual-review.v1",
        "reviewer": "/root/luna_jump_resume", "sampling_result": base.ref(REPORT / "sampling-result.json"),
        "phase_receipt": base.ref(receipt_path), "actual_views_opened_with_view_image": result["views"],
        "actual_all_three_complete_JPEG_pages_viewed": True,
        "observation": "近亮上臂由画面左肩横跨胸甲前景，圆盘腕甲与前拳向右送出，远暗拳留在颏下；双腿/双脚、头刃与腕刃完整。159下前拳指节/腕盘有像素合并；亮上臂与胸前装甲交叠仍可读，没有改画手侧或拼肢。",
        "limits": ["01已近直肘，02随势及01→02实际接续待新源；不能再拉长手臂冒充变化。", "本件未注册，未签严格骨尺、与00的比例或完整三连连续性；不凭源级手侧正确当整条动作验收。", "原低Alpha散点、metadata/provider/费用及旧错误01源保持；只新增这张二值候选。"],
        "review_scope": "新增本席实看；冻结receipt的pending字段不回写，根实际候选审图仍待。",
        "subagent_candidate_processing_accepted_only": True, "root_actual_review_pending": True,
        "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
        "unregistered": True, "strict_size_accepted": False, "complete_action_accepted": False,
        "source_bound_and_old12_bytes_rechecked_unchanged": True,
        "installed": False, "playable": False, "new_cost_usd": "0", "new_video": False,
        "script_POST_Godot_product_Git_or_user_file_reads": False,
        "session_required_readonly_git_log5_only": True, "Git_mutations": False,
        "user_settings_replay_contents_or_observe_snapshot_reads": False,
    }
    review_path = REPORT / "subagent-actual-page-review.json"
    base.save(review_path, review)
    text = """# 月亮装甲light1/01 request002：独立未注册增量

仅根已签的01完整1024源沿已冻12包/跳跃同一Forge RGB兼容配方采为159整方：Alpha128二值、整图159采样、本人固定32色、再次二值。没有裁bbox、删连通块、逐相拟合、重着色或320注册帧/clip/atlas。

本席已实际打开[完整深底4倍页](light1-01-whole159-4x-dark.jpg)、[完整浅底4倍页](light1-01-whole159-4x-light.jpg)与[159原生深浅完整页](light1-01-native159-1x-complete-dark-light.jpg)。近亮上臂跨胸向前、远暗拳护颏以及完整双足仍可读；前拳/腕盘像素合并等小差保留。[实际审图](subagent-actual-page-review.json)只签本席候选处理。

源、provider、metadata、根签及旧12包字节复核保持。root/grip/hitboxes/hurtboxes/registration全null；02新源未碰，完整三连/严尺/接续/实际命中仍待。无POST、Godot、产品/assets或用户档操作、Git变更、新费用或视频。会话git log -5仅必读，不是采样脚本动作。
"""
    with (REPORT / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    nul = REPORT / "subagent-owned-light1-01-increment-v1.nul"
    manifest_path = REPORT / "subagent-owned-light1-01-increment-sha256-v1.json"
    files = sorted([path for folder in [HERE, ART, REPORT] for path in folder.rglob("*") if path.is_file()] + [nul, manifest_path], key=base.rel)
    assert len(files) == len(set(files))
    with nul.open("xb") as stream:
        stream.write(b"".join(base.rel(path).encode("utf-8") + b"\0" for path in files))
    base.save(manifest_path, {"schema": "ufeneo.subagent-owned-files-sha256.v1", "owner": "/root/luna_jump_resume",
                             "scope": "仅light1/01独立增量工具/候选/JPEG/报告；旧12包和根生产/签收目录排除。",
                             "owned_pathspec": base.ref(nul), "total_owned_paths": len(files),
                             "sha256_entries": [base.ref(path) for path in files if path != manifest_path],
                             "self_hash_omitted": base.rel(manifest_path), "root_commit_only": True})
    print(json.dumps({"review": base.ref(review_path), "owned_nul": base.ref(nul), "owned_manifest": base.ref(manifest_path)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ["sample", "finalize"]
    {"sample": sample, "finalize": finalize}[sys.argv[1]]()
