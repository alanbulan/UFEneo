"""02本人可见表面测点建议和本席审图；建议不写入root/判定。"""
from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("luna_light1_02_sample_helpers", HERE / "sample_increment.py")
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)
base, ROOT, ART, REPORT = sample.base, sample.ROOT, sample.ART, sample.REPORT
from PIL import Image, ImageDraw
import numpy as np


def binding():
    result = base.read(REPORT / "sampling-result.json")
    receipt_path = base.checked(result["phase_receipt"])
    receipt = base.read(receipt_path)
    sample.recheck(receipt["frozen_inputs"])
    sample.recheck(receipt["old12_and_01_frozen"])
    for value in result["views"]:
        base.checked(value)
    image_path = base.checked(receipt["whole_source_sample"])
    with Image.open(image_path) as image:
        small = image.copy()
    return result, receipt_path, receipt, small


def propose():
    result, receipt_path, receipt, small = binding()
    rows = [
        ("C", "头刃尖可见外缘", [68, 14], 1, "仅完整轮廓观察，不当作不含刃头高的端点。"),
        ("T", "头盔顶部实体代理（不含刃）", [78, 23], 2, "头盔与头刃相接处有遮挡，非严格头尺起点。"),
        ("H", "头盔可见侧部代理", [83, 31], 2, "可见侧部/颞部，非推定骨骼头心。"),
        ("J", "下颏可见表面", [87, 40], 1, "仅头盔下颏轮廓；不沿头刃估计头长。"),
        ("S", "近侧肩表面代理", [73, 48], 3, "靠肩甲下缘与亮上臂出发处；真实肩关节被甲遮挡。"),
        ("P", "骨盆红色表面中心代理", [79, 83], 3, "可见腰胯/两大腿之间红面；非根、髋关节或严格骨尺。"),
        ("F", "出击近拳可见实体中心", [140, 52], 1, "拳面量化约1px，不给实际攻击框或握持点。"),
        ("G", "护颏远拳可见实体中心", [94, 43], 1, "远拳在颏下，部分与甲/近臂重叠，不补隐藏骨点。"),
        ("B", "画面左后足最低可见鞋底代表", [39, 151], 1, "最低占用像素行151，几何外边界152；非已签地面接触。"),
        ("A", "画面右前足最低可见鞋底代表", [121, 148], 1, "最低占用像素行148，几何外边界149；不强行拉平左右鞋底。"),
    ]
    pixels = np.asarray(small)
    points = []
    for code, name, point, uncertainty, note in rows:
        x, y = point
        assert pixels[y, x, 3] == 255
        points.append({"code": code, "name": name, "point_native159": point,
                       "manual_visual_uncertainty_px": uncertainty, "sample_pixel_rgba": pixels[y, x].tolist(),
                       "kind": "本人可见表面建议，未签骨点/注册", "note": note})
    feet = []
    for name, xr in [("画面左后足", (20, 60)), ("画面右前足", (95, 140))]:
        mask = pixels[130:, xr[0]:xr[1], 3] > 0
        yy, xx = np.where(mask)
        y = int(yy.max()) + 130
        xs = (xx[yy == yy.max()] + xr[0]).astype(int).tolist()
        feet.append({"name": name, "diagnostic_scan_region_native159": [xr[0], 130, xr[1], 159],
                     "lowest_occupied_pixel_row": y, "occupied_xs_on_lowest_row": xs,
                     "outer_pixel_boundary_y": y + 1, "not_used_for_crop_or_scale_or_registration": True})
    assert [row["lowest_occupied_pixel_row"] for row in feet] == [151, 148]
    page_refs = []
    for theme, color, ink in [("dark", "#252c38", "white"), ("light", "#e8dfcc", "#202020")]:
        page = Image.new("RGB", (636, 704), color)
        page.paste(base.solid(small.resize((636, 636), Image.Resampling.NEAREST), color), (0, 64))
        draw = ImageDraw.Draw(page)
        draw.text((8, 4), f"月亮 light1/02 · 本人可见表面测点建议 · {theme}", font=base.FONT, fill=ink)
        draw.text((8, 27), "完整159方×4；测点未签；root/grip/判定/registration仍null", font=base.SMALL, fill=ink)
        for point in points:
            x, y = point["point_native159"]
            px, py = x * 4 + 2, y * 4 + 66
            draw.line((px - 5, py, px + 5, py), fill="#ffdc52", width=1)
            draw.line((px, py - 5, px, py + 5), fill="#ffdc52", width=1)
            # 字母仅测量说明层，不改变候选PNG。密集头部标签按方向错开。
            dx = -17 if point["code"] in ["C", "T", "H", "S", "B"] else 7
            dy = -16 if point["code"] in ["C", "T", "F", "G", "A"] else 3
            draw.text((px + dx, py + dy), point["code"], font=base.SMALL, fill="#ffdc52", stroke_width=1, stroke_fill="#202020")
        path = REPORT / f"light1-02-point-proposals-complete-{theme}.jpg"
        value = base.jpg(path, page)
        value.update(native_display_scale=4, pixel_nearest=True, bound_image=receipt["whole_source_sample"],
                     diagnostic_overlay_only=True, candidate_PNG_not_changed=True)
        page_refs.append(value)
    proposal = {
        "schema": "ufeneo.arc-luna.s2.light1-02-visible-surface-point-proposal.v1",
        "reviewer": "/root/luna_jump_resume", "phase_receipt": base.ref(receipt_path),
        "coordinate_system": "未注册159整方，左上(0,0)，x向右/y向下，整数表示该像素索引；外边界与占用行单列。",
        "method": "本席实看完整源深浅及159原生/4倍深浅后人工建议，再查该159像素Alpha；不以bbox中心或别人的骨点推定。",
        "source_display_preview_not_measurement_input": True, "points": points,
        "far_shoulder_point": None, "far_shoulder_reason": "远肩被胸甲/近臂及护颏臂遮挡，不捏造可见关节坐标。",
        "visible_sole_diagnostics": feet, "left_right_lowest_occupied_row_difference_px": 3,
        "shoe_floor_note": "3px为本候选真实可见鞋底行差，不能自动认定漂移/离地；不逐脚平移或改鞋底，地面root未签。",
        "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
        "runtime_ground_y": None, "suggestions_only": True, "strict_bone_size_accepted": False,
        "root_acceptance_pending": True, "overlay_views": page_refs,
        "candidate_png_unchanged": receipt["whole_source_sample"],
    }
    base.save(REPORT / "landmark-proposal.json", proposal)
    print(json.dumps({"proposal": base.ref(REPORT / "landmark-proposal.json"), "overlay_views": page_refs}, ensure_ascii=False), flush=True)


def finalize():
    result, receipt_path, receipt, _ = binding()
    proposal_path = REPORT / "landmark-proposal.json"
    proposal = base.read(proposal_path)
    for item in proposal["overlay_views"]:
        base.checked(item)
    review = {
        "schema": "ufeneo.arc-luna.s2.light1-02-subagent-actual-page-review.v1",
        "reviewer": "/root/luna_jump_resume", "sampling_result": base.ref(REPORT / "sampling-result.json"),
        "phase_receipt": base.ref(receipt_path), "landmark_proposal": base.ref(proposal_path),
        "actual_views_opened_with_view_image": result["views"] + proposal["overlay_views"],
        "actual_all_complete_JPEG_pages_viewed": True,
        "observation": "完整1024源显示深浅、159原生深浅及精确4倍深浅均实看：近亮臂跨胸、腕盘/拳前送，远暗拳在颏下，头刃及两靴完整；缩采后前拳指节、腕盘环与脸部有像素合并。两测点页再实看，建议点落本人所述可见表面，无注册含义。",
        "visible_sole_observation": "后足最低占用行151、前足148，差3native；这与本相原姿态/量化相关，未逐脚拉平，未从鞋底直接指定root。",
        "limits": ["02前拳较01继续前送，但两相手臂长度/肩髋/前膝接续仍待根合看，不以单相手侧正确当完整招式验收。", "近肩/骨盆建议是遮挡下的可见表面代理，远肩不明则null；不签严格骨尺。", "原四角Alpha1和客户端拒收保持原位/原字节，只按根明确例外生成整图Alpha128候选。", "root/grip/攻击框/受击框/registration全null，没有320帧/clip/atlas、正式main或回放。"],
        "subagent_candidate_processing_accepted_only": True, "root_actual_candidate_review_pending": True,
        "old12_01_and_source_bound_bytes_rechecked_unchanged": True,
        "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
        "unregistered": True, "strict_size_accepted": False, "complete_action_accepted": False,
        "installed": False, "playable": False, "new_cost_usd": "0", "new_video": False,
        "script_POST_Godot_product_Git_or_user_file_reads": False, "session_required_readonly_git_log5_only": True,
        "Git_mutations": False, "user_settings_replay_contents_or_observe_snapshot_reads": False,
        "pending_fields_in_frozen_sampling_receipts_not_rewritten": True,
    }
    review_path = REPORT / "subagent-actual-page-review.json"
    base.save(review_path, review)
    text = """# 月亮装甲light1/02 request002：未注册增量与测点建议

原source和metadata继续留在request002/rejected，原四角Alpha1/客户端透明拒收结论不改。本次按根明确例外，仅把完整1024源经同跳跃/冻12包的Forge RGB兼容配方做159整方及Alpha128候选，不裁框、删分量、逐相拟合或重着色；冻12/01字节复核保持。

本席已实际打开完整[源深底](light1-02-source1024-complete-dark.jpg)/[源浅底](light1-02-source1024-complete-light.jpg)、[159原生深浅](light1-02-native159-1x-complete-dark-light.jpg)、精确4倍[深底](light1-02-whole159-complete-dark.jpg)/[浅底](light1-02-whole159-complete-light.jpg)，及建议测点[深底](light1-02-point-proposals-complete-dark.jpg)/[浅底](light1-02-point-proposals-complete-light.jpg)。源页为完整1024只显示缩到636宽；候选实际只采一次1024→159，源显示页不用于采样或测点。

[landmark-proposal.json](landmark-proposal.json)给本人头盔、近肩、骨盆、前拳/护颏拳及可见鞋底建议；近肩/髋均为遮挡下表面代理，远肩未知则null，不作严格骨点。后足最低占用行151、前足148，相差3native；不强行拉平鞋底或借此指定地面root。候选前拳/腕盘/脸部像素合并保留，01→02长度/接续须根合看。

root、grip、hitboxes、hurtboxes、registration全部null，没有320注册帧、clip、atlas或实际命中验收。本项无POST、Godot、产品/assets/用户档操作、Git变更、新费用或视频。会话git log -5只执行必读。完整观察见[subagent-actual-page-review.json](subagent-actual-page-review.json)，冻结pending字段不回改。
"""
    with (REPORT / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    nul = REPORT / "subagent-owned-light1-02-increment-v1.nul"
    manifest_path = REPORT / "subagent-owned-light1-02-increment-sha256-v1.json"
    files = sorted([path for folder in [HERE, ART, REPORT] for path in folder.rglob("*") if path.is_file()] + [nul, manifest_path], key=base.rel)
    assert len(files) == len(set(files))
    with nul.open("xb") as stream:
        stream.write(b"".join(base.rel(path).encode("utf-8") + b"\0" for path in files))
    base.save(manifest_path, {"schema": "ufeneo.subagent-owned-files-sha256.v1", "owner": "/root/luna_jump_resume",
                             "scope": "仅02独立增量工具/159候选/完整JPEG/测点建议及报告；冻12/01、原拒收/根生产目录排除。",
                             "owned_pathspec": base.ref(nul), "total_owned_paths": len(files),
                             "sha256_entries": [base.ref(path) for path in files if path != manifest_path],
                             "self_hash_omitted": base.rel(manifest_path), "root_commit_only": True})
    print(json.dumps({"review": base.ref(review_path), "proposal": base.ref(proposal_path),
                      "owned_nul": base.ref(nul), "owned_manifest": base.ref(manifest_path)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ["propose", "finalize"]
    {"propose": propose, "finalize": finalize}[sys.argv[1]]()
