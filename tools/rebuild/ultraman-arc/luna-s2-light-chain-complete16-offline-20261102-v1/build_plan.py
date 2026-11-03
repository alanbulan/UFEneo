"""完整16相本人可见骨盆/承重足与实体拳足提案；只出JSON和完整诊断JPEG。"""
from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("luna_returns_helpers", HERE / "produce_returns.py")
returns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(returns)
base, ROOT = returns.base, returns.ROOT
from PIL import Image, ImageDraw
import numpy as np

REPORT = ROOT / "reports/review/2026-11-02/luna-light-chain-complete16-offline-proposal-v1"
SEEDS = HERE / "measurement-seeds-v1.json"
ROOT_REVIEW = ROOT / "reports/review/2026-11-02/luna-light-chain-native159-root-review-v1/root-candidate-processing-review.json"
IDLE_METADATA = ROOT / "art/fighters/ultraman-arc__luna/stage2/goal-closeout-20261101-v1/idle/frames.json"
SIM_GEOMETRY = ROOT / "core/combat/hit_resolver.gd"
SOURCE_X_REFERENCE = 80
RUNTIME_ROOT_PROPOSAL = [160, 280]


def selected():
    old = base.read(ROOT / "reports/review/2026-11-02/luna-light-chain-unregistered-retained12-v1/sampling-result.json")
    result = {}
    for value in old["receipts"]:
        path = base.checked(value)
        data = base.read(path)
        result[(data["action"], data["phase"])] = (path, data)
    for phase in [1, 2]:
        path = ROOT / f"art/fighters/ultraman-arc__luna/stage2/light-chain-unregistered-20261102-v1/increment-light1-{phase:02}-request002-v1/phase-receipt.json"
        result[("light1", phase)] = (path, base.read(path))
    for phase in [4, 5]:
        _, art, _ = returns.locations(phase)
        path = art / "phase-receipt.json"
        result[("light3", phase)] = (path, base.read(path))
    assert len(result) == 16
    return result


def feet_measure(image, seeds):
    pixels = np.asarray(image)
    measured = {}
    for name, roi in seeds["feet"].items():
        x0, y0, x1, y1 = roi
        mask = pixels[y0:y1, x0:x1, 3] > 0
        yy, xx = np.where(mask)
        assert len(xx), (seeds["action"], seeds["phase"], name)
        low = int(yy.max()) + y0
        xs = (xx[yy == yy.max()] + x0).astype(int).tolist()
        measured[name] = {"manual_selected_visible_foot_roi": roi, "lowest_occupied_row": low,
                          "occupied_xs_on_lowest_row": xs, "sole_outer_pixel_boundary_y": low + 1,
                          "visible_foot_area_in_roi": int(mask.sum()),
                          "diagnostic_only_not_bbox_fit": True}
    return measured


def measurements():
    sources = selected()
    timing = {row["action"]: row for row in base.read(base.TIMING)["actions"]}
    entries = []
    for seeds in base.read(SEEDS)["phases"]:
        action, phase = seeds["action"], seeds["phase"]
        path, receipt = sources[(action, phase)]
        image_path = base.checked(receipt["whole_source_sample"])
        with Image.open(image_path) as image:
            small = image.copy()
        rgba = np.asarray(small)
        assert small.mode == "RGBA" and small.size == (159, 159)
        points = {code: {"point_native159": point, "sample_pixel_rgba": rgba[point[1], point[0]].tolist(),
                         "visible_opaque_at_suggestion": bool(rgba[point[1], point[0], 3] == 255),
                         "manual_visual_uncertainty_px": 3 if code in ["S", "P"] else 2}
                  for code, point in seeds["points"].items()}
        feet = feet_measure(small, seeds)
        ground = feet[seeds["support"]]["sole_outer_pixel_boundary_y"]
        run = next(row for row in timing[action]["frame_runs"] if row["sprite"] == phase)
        rule_boxes = run["hitboxes"]
        contact = None
        if seeds["contact_roi"]:
            x0, y0, x1, y1 = seeds["contact_roi"]
            contact_mask = np.zeros((159, 159), dtype=bool)
            contact_mask[y0:y1, x0:x1] = rgba[y0:y1, x0:x1, 3] == 255
            projected_rule_boxes = []
            rule_mask = np.zeros((159, 159), dtype=bool)
            for x, y, w, h in rule_boxes:
                native = [SOURCE_X_REFERENCE + x, ground - y - h, SOURCE_X_REFERENCE + x + w, ground - y]
                projected_rule_boxes.append(native)
                rx0, ry0, rx1, ry1 = native
                rule_mask[max(0, ry0):min(159, ry1), max(0, rx0):min(159, rx1)] = True
            contact = {"visible_entity": "近拳" if action == "light1" else "远拳" if action == "light2" else "远侧踢出靴",
                       "manual_visible_contact_roi_native159": seeds["contact_roi"],
                       "opaque_pixels_in_roi": int(contact_mask.sum()),
                       "projected_original_rule_boxes_native159": projected_rule_boxes,
                       "opaque_entity_pixels_inside_original_rule_boxes": int((contact_mask & rule_mask).sum()),
                       "roi_proposed_root_relative_box_reference_only": [x0 - SOURCE_X_REFERENCE, ground - y1, x1 - x0, y1 - y0],
                       "not_a_simulation_hitbox_change": True, "actual_combat_contact_not_yet_tested": True}
        assert run["active"] == (contact is not None)
        row = {"action": action, "phase": phase, "phase_receipt": base.ref(path), "sample": base.ref(image_path),
               "source": receipt["source"], "whole_source_scale": 159 / 1024,
               "phase_ticks_reference_only": run["ticks"], "first_tick0": run["first_tick0"], "last_tick0_inclusive": run["last_tick0_inclusive"],
               "visible_surface_points": points, "true_far_shoulder_joint": None,
               "point_semantics": "H为头盔可见侧面；S为甲遮挡下近肩表面；P为本人实际可见骨盆红面，不是真关节/根；F/G为两拳表面。",
               "visible_feet_separate": feet, "selected_weight_bearing_foot": seeds["support"],
               "proposed_ground_support_boundary_native159": ground,
               "other_foot_boundary_minus_support_y": {name: value["sole_outer_pixel_boundary_y"] - ground for name, value in feet.items()},
               "proposed_source_horizontal_reference_x": SOURCE_X_REFERENCE,
               "proposed_whole_frame_translation_to_320": [160 - SOURCE_X_REFERENCE, 280 - ground],
               "pelvis_surface_x_from_common_reference": seeds["points"]["P"][0] - SOURCE_X_REFERENCE,
               "pelvis_surface_height_above_support_boundary": ground - seeds["points"]["P"][1],
               "active_reference_only": run["active"], "cancel_reference_only": run["cancel"],
               "original_rule_boxes_reference_only": rule_boxes, "visible_contact_proposal": contact,
               "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
               "registered_frame_written": False}
        entries.append((row, small))
    return entries


def inspect():
    entries = measurements()
    print(json.dumps([{"action": row["action"], "phase": row["phase"],
                       "nonopaque_suggested_points": {code: value["point_native159"] for code, value in row["visible_surface_points"].items() if not value["visible_opaque_at_suggestion"]},
                       "sole_rows": {name: value["lowest_occupied_row"] for name, value in row["visible_feet_separate"].items()},
                       "ground_proposal": row["proposed_ground_support_boundary_native159"],
                       "visible_contact": row["visible_contact_proposal"]} for row, _ in entries], ensure_ascii=False), flush=True)


def prepare():
    assert not REPORT.exists()
    old = returns.old_frozen()
    assert base.sha(ROOT_REVIEW) == "3ace6e79b3042d110bd9584932ddc2b326abe8f2fef40f84d35954563ea743c5"
    entries = measurements()
    assert all(value["visible_opaque_at_suggestion"] for row, _ in entries for value in row["visible_surface_points"].values())
    frozen = dict(old)
    bound = [ROOT_REVIEW, SEEDS, Path(__file__).resolve(), HERE / "produce_returns.py", base.TIMING, IDLE_METADATA, SIM_GEOMETRY]
    for row, _ in entries:
        bound += [base.checked(row["phase_receipt"]), base.checked(row["sample"]), base.checked(row["source"])]
        receipt = base.read(base.checked(row["phase_receipt"]))
        frozen.update(receipt.get("frozen_inputs", {}))
    for path in bound:
        frozen[base.rel(path)] = base.sha(path)
    REPORT.mkdir(parents=True)
    (REPORT / ".gitattributes").write_text("*.json -text -whitespace\n*.nul -text\n", encoding="utf-8", newline="\n")
    views = []
    for row, small in entries:
        page = Image.new("RGB", (636, 704), "#252c38")
        page.paste(base.solid(small.resize((636, 636), Image.Resampling.NEAREST), "#252c38"), (0, 64))
        draw = ImageDraw.Draw(page)
        draw.text((8, 4), f"月亮 {row['action']}/{row['phase']:02} · 本人测点/支撑/拳足区建议", font=base.FONT, fill="white")
        draw.text((8, 27), "完整159×4；黄=表面点 橙=拳靴实体区 红=旧规则框；均未签注册", font=base.SMALL, fill="white")
        ground = row["proposed_ground_support_boundary_native159"]
        draw.line((0, 64 + ground * 4, 635, 64 + ground * 4), fill="#82dd9c", width=1)
        draw.text((8, 64 + ground * 4 - 18), f"支撑外边界 y={ground}", font=base.SMALL, fill="#82dd9c")
        for name, foot in row["visible_feet_separate"].items():
            x0, y0, x1, y1 = foot["manual_selected_visible_foot_roi"]
            draw.rectangle((x0 * 4, 64 + y0 * 4, x1 * 4 - 1, 64 + y1 * 4 - 1), outline="#a99adc", width=1)
            low = foot["lowest_occupied_row"]
            draw.text((x0 * 4, 64 + y0 * 4 - 15), f"{name} {low}", font=base.SMALL, fill="#c9baff", stroke_width=1, stroke_fill="#202020")
        for code, point in row["visible_surface_points"].items():
            x, y = point["point_native159"]
            px, py = x * 4 + 2, 64 + y * 4 + 2
            draw.line((px - 5, py, px + 5, py), fill="#ffde50", width=1)
            draw.line((px, py - 5, px, py + 5), fill="#ffde50", width=1)
            draw.text((px + 6, py - 16), code, font=base.SMALL, fill="#ffde50", stroke_width=1, stroke_fill="#202020")
        contact = row["visible_contact_proposal"]
        if contact:
            for roi in contact["projected_original_rule_boxes_native159"]:
                x0, y0, x1, y1 = roi
                draw.rectangle((x0 * 4, 64 + y0 * 4, x1 * 4 - 1, 64 + y1 * 4 - 1), outline="#eb7680", width=1)
            x0, y0, x1, y1 = contact["manual_visible_contact_roi_native159"]
            draw.rectangle((x0 * 4, 64 + y0 * 4, x1 * 4 - 1, 64 + y1 * 4 - 1), outline="#ffc66a", width=2)
        path = REPORT / f"{row['action']}-{row['phase']:02}-whole159-point-support-contact-proposal.jpg"
        value = base.jpg(path, page)
        value.update(native_display_scale=4, pixel_nearest=True, diagnostic_overlay_only=True,
                     source_sample=row["sample"], no_registered_raster=True)
        row["complete_diagnostic_view"] = value
        views.append(value)
    for action in ["light1", "light2", "light3"]:
        action_entries = [(row, small) for row, small in entries if row["action"] == action]
        page = Image.new("RGB", (636, 64 + 207 * ((len(action_entries) + 1) // 2)), "#364250")
        draw = ImageDraw.Draw(page)
        draw.text((8, 4), f"月亮 {action} 全相 · 159原生1:1 · 每相左深右浅", font=base.FONT, fill="white")
        draw.text((8, 28), "严格保持159整方；没有先做注册/拉平鞋底/改动人物像素", font=base.SMALL, fill="white")
        for index, (row, small) in enumerate(action_entries):
            x, y = index % 2 * 318, 64 + index // 2 * 207
            draw.text((x + 6, y), f"{row['phase']:02}/{row['phase_ticks_reference_only']}t  P={row['visible_surface_points']['P']['point_native159']} ground?{row['proposed_ground_support_boundary_native159']}", font=base.SMALL, fill="#ffe780")
            page.paste(base.solid(small, "#252c38"), (x, y + 24))
            page.paste(base.solid(small, "#e8dfcc"), (x + 159, y + 24))
        value = base.jpg(REPORT / f"{action}-complete-native159-dark-light.jpg", page)
        value.update(native_display_scale=1, sample_bindings=[row["sample"] for row, _ in action_entries])
        views.append(value)
    plan = {
        "schema": "ufeneo.arc-luna.s2.complete16-offline-registration-and-visible-contact-proposal.v1",
        "reviewer": "/root/luna_jump_resume", "root_accepted_unregistered_processing": base.ref(ROOT_REVIEW),
        "timing_contract_reference_only": base.ref(base.TIMING), "coordinate_convention_source": base.ref(SIM_GEOMETRY),
        "same_character_layout_reference_only": base.ref(IDLE_METADATA), "measurement_seeds": base.ref(SEEDS),
        "whole_source_common_scale": 159 / 1024, "registered_raster_or_clip_atlas_written": False,
        "proposed_runtime_canvas": [320, 320], "proposed_runtime_root_layout_reference": RUNTIME_ROOT_PROPOSAL,
        "horizontal_policy": "先建议所有16相共同source x=80（完整1024中央512乘159/1024后取最近整数），仅共同平移x=80；不逐相把骨盆/头或出拳手强拉到同一x。本人实测骨盆表面P与其偏差逐相另列，保留踢击后仰/出拳随势；该参考不冒称实测根。",
        "vertical_policy": "逐相人工选可见承重脚的完整鞋底ROI，只以该实际鞋底最末占用行的外边界提出地面支撑y；另一脚鞋底/悬空靴单列，不能拿全图bbox最底或踢出脚当根，也不逐脚平移。建议整帧dy=280-支撑外边界；是待根目视的初案，非已安装注册。",
        "pelvis_policy": "P逐相来自本人红色骨盆可见表面，带遮挡/投影不确定；头盔H/近肩S也单列，不拿甲外轮廓当真实关节，不按这些点拟合缩放。",
        "visible_contact_policy": "只在原时序active相圈出本人实际拳面/踢出靴的可见实体ROI，统计真Alpha实体与原规则框投影相交作离线诊断；不把整片腕盘/脚路径/技能FX当拳脚本体，不改任何规则框、命中/取消/费用。实战需真正受方接触后另签。",
        "simulation_y_note": "core world_box以height+box[1]为高度下界；159坐标转根相对参考为[x0-80,ground-y1,w,h]。只用于比较，不装入模拟。",
        "no_bone_size_signoff": "H/S/P是可见表面，不是隐藏骨点；严格头身、肩髋投影及手臂长度均未签。",
        "phases": [row for row, _ in entries], "views": views,
        "required_root_decisions": ["逐相复核本人H/S/P与选定承重脚是否读对。", "核00→01→02与03/04回护、light3 00→01换承重及03→04→05→既有idle，保留两靴不共线。", "确认共同x参考与每相整体dy，再允许输出320整帧；不把本JSON提案当root通过。", "原规则框与本人实体相交只说明几何可供主游戏候选，最终须真J单击/三连及双向命中、防御、落空、独立原输入回放。"],
        "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
        "proposal_only": True, "actual_complete_page_review_pending": True, "root_geometry_acceptance_pending": True,
        "strict_size_accepted": False, "complete_action_accepted": False, "installed": False, "playable": False,
        "frozen_inputs": frozen, "old12_01_02_and_all_source_bytes_unchanged": True,
        "script_POST_Godot_product_Git_or_user_file_reads": False, "new_cost_usd": "0", "new_video": False,
    }
    returns.prior.recheck(frozen)
    base.save(REPORT / "registration-and-contact-proposal.json", plan)
    print(json.dumps({"proposal": base.ref(REPORT / "registration-and-contact-proposal.json"), "complete_JPEG_views": len(views)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ["inspect", "prepare"]
    {"inspect": inspect, "prepare": prepare}[sys.argv[1]]()
