"""月亮S2跳跃整源离线采样/注册；不调用网络、Godot、产品安装或Git。"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
FID = "ultraman-arc__luna"
OWN = ROOT / "art/fighters" / FID
GROUND = OWN / "stage2/jump-ground-guides-20261102-v2"
AIR = OWN / "stage2/jump-air-guides-resume-20261102-v2"
PALETTE = OWN / "model/palette.json"
IDLE = OWN / "stage2/goal-closeout-20261101-v1/idle/frames.json"
ART_TOP = OWN / "stage2/jump-whole-offline-resume-20261102-v1"
REPORT_TOP = ROOT / "reports/review/2026-11-02/luna-jump-offline-resume-v1"
TICKS = {"takeoff": [1, 1], "vertical_jump": [8, 7, 3, 8, 7],
         "flip_forward": [8, 8, 8, 9], "flip_back": [8, 8, 8, 9], "land": [2, 2]}
SIZE, CELL, RUNTIME_ROOT, GUIDE_ROOT = 159, 320, [160, 280], [512, 960]
SCALE = SIZE / 1024
FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
SMALL_FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 12)
sys.path.insert(0, str(ROOT / "tools/rebuild/shared"))
from forge_backend import _kcentroid_downscale, apply_palette, binarize_alpha, palette_mode, backend_info


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text("utf-8-sig"))


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def ref(path):
    return {"path": rel(path), "sha256": sha(path)}


def check_ref(value):
    path = (ROOT / value["path"]).resolve()
    path.relative_to(ROOT)
    assert path.is_file() and sha(path) == value["sha256"], value
    return path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def safe_new(path, top):
    path = path.resolve()
    path.relative_to(top)
    assert not path.exists(), f"输出必须是新目录：{path}"
    return path


def valid_phase(action, phase):
    assert action in TICKS and 0 <= phase < len(TICKS[action]), (action, phase)


def guide_files(action, phase):
    valid_phase(action, phase)
    base = (GROUND if action in {"takeoff", "land"} else AIR) / action / f"phase-{phase:02d}"
    return {name: base / filename for name, filename in
            {"guide": "pose-guide.png", "pose_target": "pose-target.json", "brief": "brief.json"}.items()}


def guide_audit(action, phase):
    paths = guide_files(action, phase)
    data = read(paths["pose_target"])
    assert data["action"] == action and data["phase"] == phase
    assert data["virtual_root_client1024"] == GUIDE_ROOT and data["runtime_root_candidate"] == RUNTIME_ROOT
    native, client = data["native_planned_points"], data["client1024_planned_points"]
    for key, point in native.items():
        projected = [round(512 + (point[0] - 128) / SCALE), round(960 + (point[1] - 248) / SCALE)]
        assert projected == client[key], (action, phase, key, projected, client[key])
    # client1024点是实际guide的已舍入像素位置，只描述guide，不冒充返回源landmark。
    target_points = {key: [RUNTIME_ROOT[i] + (point[i] - GUIDE_ROOT[i]) * SCALE for i in range(2)]
                     for key, point in client.items()}
    return {"action": action, "phase": phase, "ticks": TICKS[action][phase],
            "guide_inputs": {key: ref(path) for key, path in paths.items()},
            "guide_virtual_root": GUIDE_ROOT, "guide_client1024_planned_points": client,
            "runtime_planned_points_before_integer_offset": target_points,
            "client_rounding_bound_native": SCALE / 2,
            "source_landmarks_measured": False,
            "planning_points_are_not_returned_source_measurements": True}


def alpha_metrics(image):
    a = np.asarray(image.convert("RGBA"))[:, :, 3]
    mask = a >= 128
    labels, _ = ndimage.label(mask, np.ones((3, 3), dtype=int))
    counts = sorted(map(int, np.bincount(labels.ravel())[1:]), reverse=True)
    ys, xs = np.where(mask)
    return {"size": list(image.size), "mode": image.mode, "alpha_values": np.unique(a).tolist(),
            "alpha128_bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None,
            "alpha_nonzero_bbox": list(image.getchannel("A").getbbox()) if image.mode == "RGBA" and image.getchannel("A").getbbox() else None,
            "opaque_area": int(mask.sum()), "partial_alpha_pixels": int(((a > 0) & (a < 255)).sum()),
            "alpha_nonzero_edge_pixels": int(np.count_nonzero(a[0]) + np.count_nonzero(a[-1]) + np.count_nonzero(a[1:-1, 0]) + np.count_nonzero(a[1:-1, -1])),
            "alpha128_edge_pixels": int(mask[0].sum() + mask[-1].sum() + mask[1:-1, 0].sum() + mask[1:-1, -1].sum()),
            "component_areas": counts, "component_pixels_deleted": False}


def root_source_review(path, action, phase):
    review = read(path)
    assert review["reviewer"] == "root_delegated_by_user"
    assert review["actual_source_reviewed"] is True and review["accepted_for_offline_candidate"] is True
    assert review["allow_forge_binary_alpha"] is True and review["whole_body_only"] is True
    source = (ROOT / review["source"]).resolve()
    source.relative_to(OWN)
    assert sha(source) == review["source_sha256"]
    # 路径中的action/phase只做防误绑；实际相号仍由明确CLI及guide绑定。
    assert source.parent.parent.name == f"{phase:02d}" and source.parent.parent.parent.name == action
    authority = review.get("registration_authority")
    if authority is None:
        return review, source, None
    assert authority["common_source_sample"] == SIZE and authority["output_root"] == RUNTIME_ROOT
    root = authority["source_virtual_root"]
    assert len(root) == 2 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in root)
    method = authority["method"]
    if method == "root_accepts_original_guide_virtual_root_for_offline_candidate":
        assert root == GUIDE_ROOT, "沿guide注册须明确保持原虚拟根，不取最低靴/Alpha底边"
    elif method == "root_accepts_actual_landmark_derived_virtual_root_for_offline_candidate":
        audit = guide_audit(action, phase)
        key = authority["anchor_landmark"]
        actual = authority["actual_source_landmarks"][key]
        planned = audit["guide_client1024_planned_points"][key]
        derived = [actual[i] - planned[i] + GUIDE_ROOT[i] for i in range(2)]
        assert max(abs(derived[i] - root[i]) for i in range(2)) < 1e-8
        assert authority["actual_source_landmarks_reviewed"] is True
    else:
        raise AssertionError(f"未知根授权方法：{method}；拒绝猜根")
    return review, source, authority


def picture_on_background(picture, background):
    out = Image.new("RGB", picture.size, background)
    out.paste(picture, (0, 0), picture)
    return out


def jpeg(path, image):
    assert image.width <= 768 and not path.exists()
    image.convert("RGB").save(path, format="JPEG", quality=80, optimize=True)
    assert path.stat().st_size <= 150000, (path, path.stat().st_size)
    return {**ref(path), "dimensions": list(image.size), "bytes": path.stat().st_size, "quality": 80,
            "complete_canvas": True, "actual_opened_by_this_script": False}


def pair_page(path, frames, labels, note, multiplier=1):
    assert len(frames) == len(labels) == 2 and multiplier in {1, 2}
    size = frames[0].width * multiplier
    assert all(frame.size == frames[0].size for frame in frames) and size * 2 <= 768
    page = Image.new("RGB", (size * 2, size + 94), "#364250")
    draw = ImageDraw.Draw(page)
    draw.text((10, 5), note, font=FONT, fill="white")
    for index, (frame, label) in enumerate(zip(frames, labels)):
        draw.text((index * size + 8, 34), label, font=SMALL_FONT, fill="#ffe780")
        background = "#252c38" if index == 0 else "#e8dfcc"
        full = frame if multiplier == 1 else frame.resize((size, size), Image.Resampling.NEAREST)
        page.paste(picture_on_background(full, background), (index * size, 64))
    draw.text((10, size + 69), "整幅同倍率；无裁切/单相拟合/拼肢；候选尚未签收正式main", font=SMALL_FONT, fill="white")
    return jpeg(path, page)


def source_page(path, picture, background, label):
    small = picture.resize((640, 640), Image.Resampling.LANCZOS)
    page = Image.new("RGB", (640, 704), background)
    page.paste(picture_on_background(small, background), (0, 64))
    ImageDraw.Draw(page).text((10, 10), label + " / 完整原件1024→640；未作Alpha修改", font=FONT,
                              fill="white" if background == "#252c38" else "#202020")
    return jpeg(path, page)


def freeze_paths(paths):
    return {rel(path): sha(path) for path in sorted(set(paths), key=rel)}


def assert_frozen(frozen):
    for name, digest in frozen.items():
        assert sha(ROOT / name) == digest, name


def prepare(out):
    out = safe_new(out, REPORT_TOP)
    audits = [guide_audit(action, phase) for action, ticks in TICKS.items() for phase in range(len(ticks))]
    assert len(audits) == 17
    bound = [PALETTE, IDLE, HERE / "offline_jump.py"]
    bound += [check_ref(item) for audit in audits for item in audit["guide_inputs"].values()]
    with palette_mode("rgb"):
        backend = backend_info()
    data = {"schema": "ufeneo.arc-luna.s2.jump-offline-preparation.v1", "fighter": FID,
            "common_full_source_raster": [SIZE, SIZE], "required_source_dimensions": [1024, 1024],
            "source_scale": SCALE, "runtime_canvas": [CELL, CELL], "runtime_root": RUNTIME_ROOT,
            "guide_native_origin": [128, 248], "guide_client_origin": GUIDE_ROOT,
            "guide_native_to_runtime_translation": [32, 32],
            "guide_only_shared_source_offset_if_root_explicitly_accepts": [round(RUNTIME_ROOT[i] - GUIDE_ROOT[i] * SCALE) for i in range(2)],
            "per_phase_scale_or_area_fitting": False, "air_lowest_boot_is_not_ground": True,
            "no_extra_simulation_jump_height_baked_into_registration": True,
            "source_root_rule": "仅接受根逐源review中的原guide虚拟根，或根实看真实landmark推导的同guide根；缺根时只采159整源、不产生320注册帧/clip/最终manifest。",
            "frozen_inputs": freeze_paths(bound), "backend": backend, "guide_audits": audits,
            "actual_person_sources_processed": [], "POST_count": 0, "Godot_started": False,
            "product_written": False, "git_written": False, "final_registered_manifest_emitted": False,
            "known_pending": ["逐源root-source-review、源SHA及Alpha二值许可", "每相可靠的根授权", "17源终态与整套处理权限根确认", "完整源/320候选与接续页根实看", "正式main及原输入回放仍由根执行"]}
    save(out / "preparation.json", data)
    print(json.dumps({"preparation": ref(out / "preparation.json"), "person_images_written": False}, ensure_ascii=False))


def sample(action, phase, review_path, art_out, report_out):
    valid_phase(action, phase)
    art_out, report_out = safe_new(art_out, ART_TOP), safe_new(report_out, REPORT_TOP)
    review_path = review_path.resolve()
    review, source, authority = root_source_review(review_path, action, phase)
    guide = guide_audit(action, phase)
    paths = guide_files(action, phase)
    # 仅读取根已接受的真实原件，RGBA以外不伪造透明支持。
    with Image.open(source) as loaded:
        assert loaded.format == "PNG" and loaded.mode == "RGBA" and loaded.size == (1024, 1024)
        original = loaded.copy()
    before_alpha = alpha_metrics(original)
    assert before_alpha["alpha128_edge_pixels"] == 0 and before_alpha["opaque_area"] > 0
    if not review["native_alpha_gate_passed"]:
        assert review.get("native_alpha_exception"), "原Alpha拒收必须保留明确例外，不改写为原生过门"
    palette = read(PALETTE)["colors"]
    assert len(palette) == 32
    frozen = freeze_paths([review_path, source, PALETTE, HERE / "offline_jump.py", *paths.values()])
    clean = binarize_alpha(original.copy())
    with palette_mode("rgb"):
        small = _kcentroid_downscale(clean, SIZE, SIZE, detail_bias=True)
        apply_palette(small, palette)
        binarize_alpha(small)
        backend = backend_info()
    # 不按bbox裁图，也不删除连通块；159格完全来自1024完整源。
    art_out.mkdir(parents=True)
    report_out.mkdir(parents=True)
    small_path = art_out / "whole-source-159.png"
    small.save(small_path)
    previews = [source_page(report_out / f"whole-source-{label}.jpg", original, bg, label)
                for label, bg in [("dark", "#252c38"), ("light", "#e8dfcc")]]
    previews.append(pair_page(report_out / "whole-sample-dark-light-2x.jpg", [small, small],
                              ["159整源深底×2", "159整源浅底×2"], f"{action} {phase:02d} / 未裁整源像素采样", 2))
    row = {"schema": "ufeneo.arc-luna.s2.jump-offline-phase.v1", "fighter": FID,
           "action": action, "phase": phase, "ticks": TICKS[action][phase],
           "source": rel(source), "source_sha256": sha(source), "root_source_review": ref(review_path),
           "guide_inputs": guide["guide_inputs"], "palette": ref(PALETTE), "backend": backend,
           "source_dimensions": [1024, 1024], "common_full_source_raster": [SIZE, SIZE], "source_scale": SCALE,
           "whole_source_sample": ref(small_path), "source_alpha_before": before_alpha,
           "source_alpha_after_threshold": alpha_metrics(clean), "sample_alpha": alpha_metrics(small),
           "native_alpha_gate_passed": review["native_alpha_gate_passed"],
           "native_alpha_exception": review.get("native_alpha_exception"),
           "binary_threshold": 128, "binary_alpha_operation": "whole_source_threshold_only_no_component_deletion",
           "root_registration_authority": authority,
           "whole_image_only": True, "per_phase_scale_or_area_fitting": False,
           "source_original_untouched": True, "component_pixels_deleted": False,
           "air_lowest_boot_is_not_ground": True, "extra_simulation_height_baked_in": False,
           "guide_points_used_as_actual_source_measurements": False,
           "frozen_inputs": frozen, "complete_JPEG_views": previews,
           "registered": authority is not None, "strict_size_accepted": False,
           "accepted_for_formal_main_candidate": False, "installed": False, "playable": False,
           "POST_count": 0, "Godot_started": False, "product_written": False, "git_written": False,
           "root_known_issues": review.get("known_issues", [])}
    if authority is not None:
        virtual = authority["source_virtual_root"]
        offset = [round(RUNTIME_ROOT[i] - virtual[i] * SCALE) for i in range(2)]
        assert all(0 <= v and v + SIZE <= CELL for v in offset), "完整159画布不允许被320画布裁掉；根需复核虚拟根"
        native = Image.new("RGBA", (CELL, CELL))
        native.alpha_composite(small, tuple(offset))
        metrics = alpha_metrics(native)
        assert metrics["alpha_values"] == [0, 255] and metrics["alpha128_edge_pixels"] == 0
        image_path = art_out / "frame.png"
        native.save(image_path)
        actual_root = [offset[i] + virtual[i] * SCALE for i in range(2)]
        row.update(image=rel(image_path), image_sha256=sha(image_path), runtime_canvas=[CELL, CELL],
                   runtime_root=RUNTIME_ROOT, whole_source_destination_offset=offset,
                   resulting_virtual_root_float=actual_root,
                   root_quantization_error=[actual_root[i] - RUNTIME_ROOT[i] for i in range(2)],
                   image_alpha=metrics)
        previews.append(pair_page(report_out / "registered-complete-dark-light-1x.jpg", [native, native],
                                  ["完整320深底/1:1", "完整320浅底/1:1"], f"{action} {phase:02d} / 根授权虚拟根候选"))
        # idle是同一320/根，完整原帧并列；不重新配准、裁切或缩放idle来掩盖体量差。
        idle_data = read(IDLE)
        idle_row = idle_data["frames"][0]
        idle_path = check_ref({"path": idle_row["image"], "sha256": idle_row["image_sha256"]})
        with Image.open(idle_path) as idle_loaded:
            assert idle_loaded.size == (CELL, CELL) and idle_loaded.mode == "RGBA"
            idle = idle_loaded.copy()
        previews.append(pair_page(report_out / "idle-to-candidate-complete-1x.jpg", [idle, native],
                                  ["既有idle00深底/完整320", f"新{action}{phase:02d}浅底/完整320"], "同根[160,280] / 原生1:1接续对比"))
        frozen.update(freeze_paths([IDLE, idle_path]))
        row["same_native_idle_reference"] = ref(idle_path)
        row["same_native_idle_alpha"] = alpha_metrics(idle)
    else:
        row["registration_pending"] = "根review缺registration_authority；未猜根/未产生320运行帧。请根确认原guide[512,960]，或实测hip_center等对应点后写明确导出虚拟根。"
    assert_frozen(frozen)
    save(art_out / "phase-receipt.json", row)
    save(report_out / "sampling-result.json", {"phase_receipt": ref(art_out / "phase-receipt.json"),
                                                "complete_JPEG_views": previews,
                                                "original_and_bound_inputs_unchanged": True,
                                                "actual_visual_review": "pending actual opening; script metrics are not anatomy acceptance"})
    print(json.dumps({"phase_receipt": ref(art_out / "phase-receipt.json"), "registered": authority is not None,
                      "review_pages": [item["path"] for item in previews], "formal_main_accepted": False}, ensure_ascii=False))


def assemble(receipts, root_set_review, art_out, report_out):
    art_out, report_out = safe_new(art_out, ART_TOP), safe_new(report_out, REPORT_TOP)
    assert len(receipts) == 17, "缺真实17源时禁止发最终registered schema"
    rows = [read(path) for path in receipts]
    lookup = {(row["action"], row["phase"]): (path, row) for path, row in zip(receipts, rows)}
    wanted = [(action, phase) for action, ticks in TICKS.items() for phase in range(len(ticks))]
    assert set(lookup) == set(wanted) and len(lookup) == 17
    assert len({row["source_sha256"] for row in rows}) == len({row["image_sha256"] for row in rows}) == 17
    source_set = read(root_set_review)
    assert source_set["reviewer"] == "root_delegated_by_user"
    assert source_set["root_all_sources_terminal_and_processing_permission_received"] is True
    assert source_set["common_full_source_raster"] == [SIZE, SIZE] and source_set["runtime_root"] == RUNTIME_ROOT
    assert source_set["per_phase_scale_or_area_fitting"] is False
    expected_refs = {rel(path): sha(path) for path in receipts}
    assert {item["path"]: item["sha256"] for item in source_set["phase_receipts"]} == expected_refs
    frozen = freeze_paths([root_set_review, HERE / "offline_jump.py", *receipts])
    for path, row in lookup.values():
        assert row["schema"] == "ufeneo.arc-luna.s2.jump-offline-phase.v1" and row["fighter"] == FID and row["registered"] is True
        assert row["source_dimensions"] == [1024, 1024] and row["common_full_source_raster"] == [SIZE, SIZE]
        assert row["runtime_root"] == RUNTIME_ROOT and row["per_phase_scale_or_area_fitting"] is False
        assert row["extra_simulation_height_baked_in"] is False and row["air_lowest_boot_is_not_ground"] is True
        assert_frozen(row["frozen_inputs"])
        frozen.update(row["frozen_inputs"])
        frozen.update(freeze_paths([check_ref(row["whole_source_sample"]),
                                   check_ref({"path": row["image"], "sha256": row["image_sha256"]})]))
        for viewed in row["complete_JPEG_views"]:
            check_ref(viewed)
        with Image.open(ROOT / row["image"]) as image:
            assert image.size == (CELL, CELL) and image.mode == "RGBA"
            metrics = alpha_metrics(image)
            assert metrics["alpha_values"] == [0, 255] and metrics["alpha128_edge_pixels"] == 0
    art_out.mkdir(parents=True)
    report_out.mkdir(parents=True)
    manifest = {"schema": "ufeneo.arc-luna.s2.jump-whole-registered.v1", "fighter": FID, "actions": {},
                "strict_size_accepted": False, "accepted_for_formal_main_candidate": False,
                "installed": False, "playable": False, "transform_enabled": False}
    views = []
    for action, ticks in TICKS.items():
        folder = art_out / action
        folder.mkdir()
        frames = [lookup[(action, phase)][1] for phase in range(len(ticks))]
        images = []
        atlas = Image.new("RGBA", (CELL * len(frames), CELL))
        for phase, row in enumerate(frames):
            with Image.open(ROOT / row["image"]) as image:
                images.append(image.copy())
                atlas.alpha_composite(image, (phase * CELL, 0))
        atlas_path = folder / "atlas.png"
        atlas.save(atlas_path)
        clip = {"fighter": FID, "source_fighter": FID, "action": action, "texture": atlas_path.as_posix(),
                "atlas_sha256": sha(atlas_path), "cell": CELL, "anchor": RUNTIME_ROOT,
                "anchors": [RUNTIME_ROOT] * len(frames), "rects": [[i * CELL, 0, CELL, CELL] for i in range(len(frames))],
                "ticks": ticks, "loop": False, "simulation_sprite_offset": 0,
                "trajectory_driven": action not in {"takeoff", "land"},
                "art_passed": False, "root_approved": False, "installed": False, "playable": False}
        clip_path = folder / "candidate-clip.json"
        save(clip_path, clip)
        manifest["actions"][action] = {"frames": frames, "clip": ref(clip_path)}
        for pair_start in range(0, len(frames), 2):
            pair_ids = [pair_start, min(pair_start + 1, len(frames) - 1)]
            views.append(pair_page(report_out / f"{action}-complete-{pair_start:02d}.jpg", [images[i] for i in pair_ids],
                                   [f"{action}{i:02d} / 完整320原生1:1" for i in pair_ids], "相邻完整姿态；深浅底仅为审图"))
    assert_frozen(frozen)
    registration = {"schema": "ufeneo.arc-luna.s2.jump-registration-contract.v1", "fighter": FID,
                    "root_all_sources_terminal_and_processing_permission_received": True,
                    "root_source_set_review": ref(root_set_review), "common_full_source_raster": [SIZE, SIZE],
                    "source_dimensions": [1024, 1024], "source_scale": SCALE,
                    "runtime_root": RUNTIME_ROOT, "runtime_canvas": [CELL, CELL],
                    "per_phase_scale_or_area_fitting": False, "air_lowest_boot_is_not_ground": True,
                    "extra_simulation_height_baked_in": False, "frozen_inputs": frozen,
                    "root_complete_visual_and_runtime_acceptance_still_required": True}
    reg_path = art_out / "registration-contract.json"
    save(reg_path, registration)
    manifest["registration_contract"] = ref(reg_path)
    save(art_out / "registered-manifest.json", manifest)
    save(report_out / "assembly-result.json", {"manifest": ref(art_out / "registered-manifest.json"),
                                                "complete_JPEG_views": views,
                                                "actual_visual_review": "pending root actual opening",
                                                "runtime_bundle_contract_structurally_ready": True,
                                                "Godot_started": False, "product_written": False, "git_written": False,
                                                "strict_size_accepted": False, "formal_main_accepted": False})
    print(json.dumps({"manifest": ref(art_out / "registered-manifest.json"), "root_visual_acceptance_still_required": True}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("sample")
    p.add_argument("--action", choices=list(TICKS), required=True)
    p.add_argument("--phase", type=int, required=True)
    p.add_argument("--root-source-review", type=Path, required=True)
    p.add_argument("--art-out", type=Path, required=True)
    p.add_argument("--report-out", type=Path, required=True)
    p = commands.add_parser("assemble")
    p.add_argument("--phase-receipts", type=Path, nargs="+", required=True)
    p.add_argument("--root-source-set-review", type=Path, required=True)
    p.add_argument("--art-out", type=Path, required=True)
    p.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.out)
    elif args.command == "sample":
        sample(args.action, args.phase, args.root_source_review, args.art_out, args.report_out)
    else:
        assemble(args.phase_receipts, args.root_source_set_review, args.art_out, args.report_out)


if __name__ == "__main__":
    main()
