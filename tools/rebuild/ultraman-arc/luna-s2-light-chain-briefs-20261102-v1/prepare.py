"""仅准备月亮轻击三连5张整人缺相brief/来源/时序；不采样、不提交请求。"""
from pathlib import Path
import hashlib
import json

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1"
REPORT = ROOT / "reports/review/2026-11-02/luna-s2-light-chain-briefs-v1"
OLD = ROOT / "art/fighters/ultraman-arc__luna/stage2/ground-codex-20261027"
IDENTITY = ROOT / "art/fighters/ultraman-arc__luna/stage2/walk-forward-repair-20261102-v1/references/identity.png"
ROOT_REVIEW = ROOT / "reports/review/2026-11-02/luna-light-chain-root-review-v1/root-source-gap-review.json"
ROOT_REVIEW_SHA = "6e743a17873cfc5b83a60382b47efe0478c261cb4c3dc53680cd33dffd2fd25f"
PYTHON = "C:/Users/13080/.codex/venvs/ufeneo/Scripts/python.exe"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def client_source(action, phase):
    folder = OLD / action / f"phase-{phase:02}/request-001"
    paths = [path for path in [folder / "raw.png", folder / "rejected/raw.png"] if path.is_file()]
    assert len(paths) == 1
    source = paths[0]
    metadata_path = source.with_suffix(".metadata.json")
    metadata = read(metadata_path)
    provider = folder / "raw.provider.png"
    assert sha(source) == metadata["image_sha256"]
    assert metadata["dimensions"] == [1024, 1024]
    assert metadata["provider_dimensions"] == [1254, 1254]
    assert metadata["resized_to_requested_size"] is True and metadata["padded_to_requested_aspect"] is False
    with Image.open(source) as image:
        assert image.size == (1024, 1024) and image.mode == "RGBA"
    with Image.open(provider) as image:
        assert image.size == (1254, 1254) and image.mode == "RGBA"
    return {
        "action": action, "phase": phase, "client1024": ref(source), "metadata": ref(metadata_path),
        "saved_provider1254": ref(provider), "request_state": ref(folder / "request-state.json"),
        "metadata_http_payload_sha256": metadata.get("provider_image_sha256"),
        "saved_provider_png_encoding_not_assumed_equal_to_http_payload": True,
        "client1024_metadata_sha_verified": True,
        "provider_to_client_operation_recorded_by_existing_metadata": "整张同纵横比Lanczos 1254→1024；无padding，不按人物bbox裁切",
        "new_reconstruction_or_sampling_performed": False,
        "metadata_transparency_accepted": metadata["transparency_accepted"],
        "historical_quarantine": source.parent.name == "rejected",
        "historical_state": read(folder / "request-state.json").get("status"),
        "historical_state_or_alpha_gate_changed": False,
    }


POSES = [
    ("light1", 0, "近侧刺拳起手", "本图是轻击第一段第00相，只持续起手2tick。双足沿参考2的护架脚序：近侧亮银左腿在画面左后、远侧暗银右腿在右前，两个完整鞋底都落地，膝盖轻压。近侧亮银左肩随胸髋轻向前送，近侧左肘仍弯曲，左拳从腹前抬向胸前准备刺拳，不提前伸到最远。远侧暗银右拳抬在下巴旁护头，右肘也随肩胸轻收，不能把右手垂到髋下。两肩、胸、髋及两膝协调加载，不是一只手挪位、其余身体复制不动。下一个01已经是真实攻击接触，本相要能直接送出同一条近侧左臂。"),
    ("light1", 1, "近侧刺拳首次有效接触", "本图是轻击第一段第01相，对应tick2–3，已经是有效攻击，不能画成等待或低垂手。主动出拳必须是离镜头近的亮银左臂：从画面左侧可见的近肩连续经过近肘、亮银前臂和本人圆盘腕甲，整条前臂横过胸前的近景，拳头向画面右方击出，达到胸口高度的实际接触。拳必须越过躯干前缘，肘保留少量弯曲，仍可在下一相继续伸展。另一条暗银远侧右臂保持在胸/近臂后方，右拳护在下巴侧，右肘自然回收；绝不能换成右侧远肩的暗臂出直拳，不能让攻击拳垂到腰下。胸髋轻转、肩胛前送，前膝承重、后足推动，双足仍完整着地。两臂都随这次加载变化，双手不重叠融为一团。"),
    ("light1", 2, "近侧刺拳充分接触与随势", "本图是轻击第一段第02相，对应tick4–7，继续同一只近侧亮银左拳的接触和随势。左肩→左肘→亮银左前臂→左圆盘腕甲→左拳连续相连，近侧整臂在胸口前方横向朝画面右伸出，肘接近伸直但不反折，拳比01再前送一小段；不能突然换到远侧右肩出拳。远侧暗银右拳继续贴近下巴护头，右肘随肩胸后收，保持两条完整不同的手臂。胸腰髋有适度转动和前送，前膝吸收重心、后腿仍在左后撑地，头壳和躯干不能被拳头拉长。下一相03会收回近拳、恢复护架；参考3只说明那张已有收势的完整体态，不能把它当成本图的静止姿势。"),
    ("light3", 4, "远侧侧蹬后收膝", "本图是轻击第三段第04相，对应tick9–13，紧接参考2第03相的远侧暗银右腿水平侧蹬。仍由近侧亮银左腿支撑：左髋、左膝、左踝、左靴连续稳定，支撑足留在画面左后，不换成另一条腿。把刚才向右蹬出的暗银远侧右腿从前方真实收回：右髋与右大腿保持相连，右膝弯曲抬在身体右前方，右小腿向下折回，暗右靴悬空，尚未着地。右膝保持明显离地，整个角色仍站在一条腿上，头胸处在接近站姿的高度。两拳与两圆盘腕甲共同收回护住胸/下巴，双肩、胸髋从踢击扭转中回正，不能一只胳膊留在背后不动。禁止一膝跪地、手掌/拳头撑地或俯身变成滑铲；不照抄旧04/05跪姿。下一相05才让暗右足落回右前方。"),
    ("light3", 5, "远侧前足落稳并回护", "本图是轻击第三段第05相，对应tick14–19，完成收膝后的实际落足。暗银远侧右腿从右前方降下，完整右靴落回画面右前方的前足位置；亮银近侧左腿仍位于画面左后方。两条髋→膝→踝→靴链完整，恰好两只脚都站稳，膝盖自然微屈。此处明确是暗远腿落回右前足，不是后足，也不能交换两腿的明暗或把脚位倒过来。身体抬回参考3已有idle护架的整体高度，肩胸髋转回侧面朝右，近侧亮臂圆盘收在腹/下胸前，远侧暗拳护在下巴旁；两臂和双肩共同完成回护。头部与胸灯/甲片保持同一体量，这一相后能够直接接idle，不再残留高抬膝、单膝落地、跪姿、触地手或奔跑姿。参考2只证明前面确实由暗远腿踢击，当前必须完成上述双足落稳，不能继续照抄参考2伸腿接触。"),
]


def main():
    assert not ART.exists() and not REPORT.exists()
    assert sha(ROOT_REVIEW) == ROOT_REVIEW_SHA
    assert sha(IDENTITY) == "d70d0f5fba22d54281b50703158ac2ba8ff1d29624f3020b4bdbe7c20992a6da"
    with Image.open(IDENTITY) as image:
        assert image.size == (1024, 1024)
    clients = [client_source(action, phase) for action, count in [("light1", 5), ("light2", 5), ("light3", 6)] for phase in range(count)]
    idle = client_source("idle", 0)
    by_key = {(row["action"], row["phase"]): row for row in clients}
    model_path = ROOT / "art/fighters/ultraman-arc__luna/model/measurements.json"
    model = read(model_path)
    assert round(model["source_to_native_uniform_scale"] * 1254) == 159
    ART.mkdir(parents=True)
    REPORT.mkdir(parents=True)
    (ART / ".gitattributes").write_text("*.json -text -whitespace\n*.txt -text\n", encoding="utf-8", newline="\n")
    (REPORT / ".gitattributes").write_text("*.json -text -whitespace\n*.nul -text\n", encoding="utf-8", newline="\n")
    source_contract = ART / "source-reference-contract.json"
    save(source_contract, {
        "schema": "ufeneo.arc-luna.s2.light-chain-source-reference-contract.v1", "fighter": "ultraman-arc__luna",
        "root_source_gap_review": ref(ROOT_REVIEW), "identity_master1024": ref(IDENTITY), "model_measurements": ref(model_path),
        "current_existing_sources": clients, "idle_reference": idle,
        "future_common_source_grid": [1024, 1024], "future_common_whole_source_raster": [159, 159],
        "future_source_to_native_ratio": 159 / 1024, "runtime_canvas_plan_only": [320, 320], "runtime_root_plan_only": [160, 280],
        "one_rounding_for_full_group": True, "per_phase_head_area_bbox_scale_fitting": False,
        "crop_and_resize_body_or_limb": False, "whole_frame_integer_registration_only_after_root_review": True,
        "source1024_coordinates_required_for_future_actual_landmarks": True,
        "guides_or_old_mapped_points_not_actual_returned_landmarks": True,
        "future_registration_requires_actual_head_torso_pelvis_both_shoes_review": True,
        "quarantined_old_sources_remain_quarantined": True,
        "current_step_only_reads_existing_png_dimensions_and_metadata": True,
        "sampling_reconstruction_or_new_png_created": False, "post_count": 0, "product_mutated": False,
    })
    timing_path = ART / "timing-contract.json"
    actions = []
    for action, expected_ticks in [("light1", [2, 2, 4, 4, 8]), ("light2", [2, 2, 4, 4, 8]), ("light3", [2, 2, 2, 3, 5, 6])]:
        move_path = ROOT / f"content/fighters/ultraman-arc/moves/{action}.json"
        move = read(move_path)
        runs = []
        for tick, frame in enumerate(move["frames"]):
            key = {"sprite": frame["sprite"], "active": bool(frame["hitboxes"]), "hitboxes": frame["hitboxes"], "cancel": frame["cancel"]}
            if runs and all(runs[-1][field] == value for field, value in key.items()):
                runs[-1]["last_tick0_inclusive"] = tick
                runs[-1]["ticks"] += 1
            else:
                runs.append({"first_tick0": tick, "last_tick0_inclusive": tick, "ticks": 1, **key})
        assert [row["ticks"] for row in runs] == expected_ticks
        actions.append({"action": action, "current_base_rule_reference_not_luna_install": ref(move_path),
                        "phase_ticks": expected_ticks, "total_ticks": len(move["frames"]), "frame_runs": runs,
                        "unchanged_rule_summary": {key: move[key] for key in ["startup", "active", "recovery", "damage", "hitstun", "blockstun", "pushback", "stun", "stamina_cost", "energy_cost", "kind", "level", "unblockable", "launch", "bounce", "knockdown"]}})
    save(timing_path, {
        "schema": "ufeneo.arc-luna.s2.light-chain-offline-timing-contract.v1", "fighter": "ultraman-arc__luna",
        "tick_indices": "0起算、闭区间；纯数据引用，不是运行结果", "actions": actions,
        "light1_near_left_active_phases": [1, 2], "light2_far_right_active_phases": [2], "light3_far_right_kick_active_phases": [2, 3],
        "future_real_input": "中立J→J→J依原取消窗口接light1→light2→light3；原时序/费用/判定/伤害/取消数据保持。",
        "do_not_change_active_or_cancel_to_disguise_wrong_pose": True, "luna_runtime_moves_installed": False,
        "future_main_review_still_required": ["720/1080双向完整两人", "真实J连段及单击收招接idle", "命中/防御/落空", "active01/02实际近拳接触", "第三击03→04→05→idle", "独立原双方InputFrame回放与完整玩法/镜头逐tick一致"],
        "post_count": 0, "godot_executed": False, "product_mutated": False,
    })
    common = (
        "透明背景。只画亚刻奥特曼月亮装甲的一个新完整人物、一张独立整帧动作相，固定侧视朝画面右，1024×1024真正RGBA透明PNG，high质量。\n"
        "参考1是本次沿用已签跳跃族的同一1024身份母图，唯一负责本人身份、低银色后掠头刃及开孔、黄眼、青蓝胸灯、冰蓝月形胸肩甲、双腕圆盘甲、红银花纹与完整身材。近侧左臂左腿永远亮银，远侧右臂右腿永远暗银；离镜头远近不能因肢体伸到前方而互换。双小腿保持本人红银皮套，禁止银河装甲的蓝胫甲、鳍片或蓝靴甲。\n"
        "完整身体一次共同重画：两肩、胸、腰髋、两臂和双腿都按本相协调发力或回护。逐条追清肩→肘→腕→拳及髋→膝→踝→靴，恰好两个完整手臂、两只手、两条腿和两只靴，自然连续皮套关节，保留本人真实装甲分节。禁止分件、拼肢、旋转或镜像旧肢体、浮空甲片、重复腿、第三只手、玩具球关节/活动轴/插接缝/螺丝/支架/分模线/塑料高光。\n"
        "严格沿参考1在整张1024方图中的同一头壳、胸髋和肢段体量，不按当前剪影面积放大/缩小，不把人物拉长填满方图，不把原生设计坐标误当1024成品身高。后续整组统一159/1024整张采样，不能靠本相单独变大变小掩盖姿势错误。全头刃、双手、两只完整靴和所有甲尖留在透明边内。整数模拟提供世界位移，本图不另画人物的世界前移、跳高轨迹或影子。\n"
        "最终为既有街机像素画风：硬边32色块、阶梯深描边、左上光、近亮远暗，不能用平滑SVG/简单矢量、3D金属或照片纹理代替。没有文字、格子、引导线、骨架、地面、投影、其他人物、武器、光束、速度线、烟尘、光环或Q/蓄气挂件；背景必须实际Alpha透明，不画棋盘格。\n"
    )
    briefs, commands = [], []
    for action, phase, label, pose in POSES:
        if action == "light1":
            references = [ref(IDENTITY), idle["client1024"], by_key[("light1", 3)]["client1024"]]
            roles = ["唯一身份/体量/头刃/甲片/画风", "双足护架、左右腿序及idle连接", "既有03收势目标；不复制当前攻击姿态"]
            instruction = "参考2是已在main使用的idle所对应的完整1024原源，只约束完整站姿脚序和收尾连接；参考3是已有light1第03收势整源，只供当前02之后回护衔接，三张都不能替代下面新动作。\n"
        else:
            references = [ref(IDENTITY), by_key[("light3", 3)]["client1024"], idle["client1024"]]
            roles = ["唯一身份/体量/头刃/甲片/画风", "已有03远腿有效侧蹬；只看前一接触的腿身份与支撑", "双足站稳和回护终点idle"]
            instruction = "参考2是已有light3第03有效侧蹬完整1024源，只负责前一接触的暗远腿/亮近支撑腿关系；参考3是main已有idle对应完整1024原源，负责结束时两腿脚序、站姿和双臂回护。当前相按下面独立新姿势重画，不复制03伸腿，也不要照抄任何跪地源。\n"
        for row in references:
            with Image.open(ROOT / row["path"]) as image:
                assert image.size == (1024, 1024)
        draft = ART / action / f"phase-{phase:02}" / "request-001" / "brief.json"
        prompt = common + instruction + f"独立动作相：{action} {phase:02}，{label}。\n{pose}\n普通近拳、远拳、侧踢三连是本作街机编排，不给画面增加原剧技能名或文字。"
        assert len(prompt.encode("utf-8")) <= 24000
        save(draft, {
            "id": f"arc_luna_{action}_{phase:02}_whole_brief_20261102_v1", "fighter": "ultraman-arc__luna",
            "stage": 2, "action": action, "phase": phase, "asset_kind": "character",
            "model": "gpt-image-2.5-sunburst", "quality": "high", "background": "transparent", "size": "1024x1024",
            "prompt": prompt, "references": references, "reference_roles_in_order": roles,
            "source_contract": ref(source_contract), "timing_contract": ref(timing_path),
            "replaces_motion_candidate_source_only": by_key[(action, phase)]["client1024"],
            "bad_pose_source_not_attached_to_model": True, "prior_source_and_alpha_history_retained": True,
            "authority": "root_delegated_by_user", "art_source_when_executed": "api_via_project_generate_image",
            "whole_body_only": True, "pose_game_adaptation": True, "official_episode_pose_claimed": False,
            "draft_not_a_submitted_request_or_returned_source": True, "preparation_only_no_post": True,
            "root_pre_post_review_required": True, "root_POST_decision_pending": True,
            "not_installed": True, "native_sampling_performed": False,
        })
        prompt_file = draft.parent / "prompt.txt"
        with prompt_file.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(prompt + "\n")
        future_out = draft.parent / "candidate.png"
        purpose = f"月亮装甲S2轻击三连本人整人补相 {action}/{phase:02}；根逐张实看后串行请求"
        argv = [PYTHON, str(ROOT / "tools/rebuild/shared/root_serial_image_request_20261101.py"), str(draft), "--purpose", purpose]
        key = f"{action}-{phase:02}"
        briefs.append({"key": key, "label": label, "brief": ref(draft), "prompt_file": ref(prompt_file), "references": references,
                       "phase_ticks": next(item["phase_ticks"][phase] for item in actions if item["action"] == action)})
        commands.append({"key": key, "generation_argv_for_root_only_do_not_execute_now": argv,
                         "project_root_serial_delegates_to_generate_image": True, "future_out": str(future_out),
                         "root_must_first_match_brief_and_reference_sha": True,
                         "root_must_run_fresh_readonly_budget_preflight_before_each_POST": True,
                         "set_only_UFE_IMAGE_SLOTS_to_1_for_serial_root_execution": True,
                         "unknown_result_blocks_next_POST_do_not_change_filename_and_resubmit": True})
    plan = ART / "plan.json"
    save(plan, {
        "schema": "ufeneo.arc-luna.s2.light-chain-five-whole-brief-plan.v1", "fighter": "ultraman-arc__luna",
        "root_source_gap_review": ref(ROOT_REVIEW), "source_contract": ref(source_contract), "timing_contract": ref(timing_path),
        "briefs": briefs, "commands": commands, "suggested_serial_order": ["light1-00", "light1-01", "light1-02", "light3-04", "light3-05"],
        "after_each_return": "根实际看完整源/Alpha/手侧/两臂肩胸髋后再发下一张；未知结果先恢复原单，不能改名或重复POST。",
        "old_proposal_text_correction": {"old_file": "reports/review/2026-11-02/luna-s2-light-chain-offline-review-v1/actual-source-review-and-gaps.json",
            "old_text": "踢击腿真正落回后足", "future_phase05_authoritative_text": "暗远踢击腿落回画面右前足，近亮腿留左后足，接既有idle", "old_file_not_changed": True},
        "current_step_post_count": 0, "current_step_native_sampling": False, "current_step_godot": False,
        "current_step_product_or_prior_frozen_files_changed": False, "git_operations": False,
        "root_brief_approval_pending": True, "whole_stage2_or_playable_accepted": False,
    })
    save(REPORT / "preparation-receipt.json", {
        "plan": ref(plan), "brief_count": len(briefs), "source_contract": ref(source_contract), "timing_contract": ref(timing_path),
        "source_files_verified_unchanged": [row["client1024"] for row in clients] + [idle["client1024"], ref(IDENTITY)],
        "no_new_reference_png_copies_or_guide_png": True, "only_json_text_drafts": True, "no_POST_sampling_product_Godot_Git": True,
        "root_source_gap_review": ref(ROOT_REVIEW), "root_new_brief_approval_pending": True,
    })
    print(json.dumps({"plan": ref(plan), "briefs": [{"key": row["key"], "brief": row["brief"], "references": row["references"]} for row in briefs],
                      "source_contract": ref(source_contract), "timing_contract": ref(timing_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
