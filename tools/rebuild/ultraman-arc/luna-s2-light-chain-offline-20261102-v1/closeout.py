"""保存实际离线图审与最小缺口，不运行游戏或媒体请求；另列新owned。"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "reports/review/2026-11-02/luna-s2-light-chain-offline-review-v1"
TOOLS = ROOT / "tools/rebuild/ultraman-arc/luna-s2-light-chain-offline-20261102-v1"
INVENTORY = OUT / "existing-source-inventory.json"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def save(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    inventory = read(INVENTORY)
    for row in inventory["sources"]:
        assert sha(ROOT / row["source"]) == row["source_sha256"]
    for key in ["basis_bundle", "guide_profiles", "timing_contract"]:
        assert sha(ROOT / inventory[key]) == inventory[key + "_sha256"]
    old_v6 = ROOT / "reports/review/2026-11-02/luna-jump-resume-final-main-v5-final-closeout-v1/subagent-owned-incremental-sha256-v6.json"
    assert sha(old_v6) == "5fedc4fbd817f35f481cf0eadef2eb09236a011e4bac29fb46ea59139c4f318d"
    pages = []
    for row in inventory["pages"]:
        assert sha(ROOT / row["path"]) == row["sha256"]
        pages.append({"path": row["path"], "sha256": row["sha256"], "actually_opened": True})
    assert len(pages) == 12
    existing_rules = []
    for action in inventory["action_group"]:
        path = ROOT / f"content/fighters/ultraman-arc/moves/{action}.json"
        move = read(path)
        existing_rules.append({"action": action, "reference_base_move_only": rel(path), "sha256": sha(path),
                               "not_luna_installed_data": True, "rule_ticks": len(move["frames"]),
                               "active_sprites": sorted({row["sprite"] for row in move["frames"] if row["hitboxes"]}),
                               "cancel_targets": sorted({target for row in move["frames"] for target in row["cancel"]})})
    findings = [
        {"action": "light1", "frames": [0, 1, 2], "severity": "blocking_for_direct_adoption",
         "observed": "00已有一臂向前伸；01该前手降到腰下，另一只手抬到胸前；02再由屏右肩臂打水平拳。旧near近侧左拳合同未在起手/接触中稳定落实，01也没有与active相对应的前伸接触。",
         "evidence": "light1-00-full-source-dark.jpg", "do_not_fix_by": ["复制02覆盖01", "拼接或旋转手臂", "把修改玩法active时钟当成美术完成"]},
        {"action": "light1/light2", "frames": [2], "severity": "blocking_for_promised_near_far_chain",
         "observed": "两招02都可见屏右肩臂向前水平伸拳，而另一只带圆盘的近侧臂留在腰侧；现有完整源没有实现原编排的近侧刺拳→远侧直拳交替。不同SHA不能证明不同攻击手。",
         "evidence": ["light1-00-full-source-light.jpg", "light2-00-full-source-light.jpg"]},
        {"action": "light3", "frames": [4, 5], "severity": "blocking_for_one_shot_recovery",
         "observed": "03高位侧蹬后，04/05突然变为低身单膝/手触地。05仍未起身，不能接回既有站立idle，也不能作为收膝落地的完整回护。",
         "evidence": "light3-04-full-source-dark.jpg", "do_not_fix_by": ["拉长05代替起身", "循环旧接触相", "改成滑铲或挪入其它招式冒充收势"]},
        {"action": "all", "severity": "processing_contract_required",
         "observed": "16张源均为1254方图；旧诊断逐相按面积/头拟合给不同比例，整体0.1098194144–0.1288800733。它们不是当前1024→159整张统一倍率的批准资源，不能直接混用旧153图集。",
         "evidence": "existing-source-inventory.json"},
        {"action": "all", "severity": "alpha_history_must_remain",
         "observed": "16张实体Alpha128都不触源边；14张存在低Alpha触边，4份历史request-state仍记returned_requires_review。只作已有源审，不把半透明和旧隔离历史改写成原生Alpha门已通过。",
         "evidence": "existing-source-inventory.json"},
    ]
    proposed = [
        {"action": "light1", "phase": phase, "purpose": purpose, "whole_character_source_needed": True,
         "no_post_prepared_or_sent": True} for phase, purpose in [
             (0, "近侧左拳从腹前起势、双肩胸髋协调，远侧手护颏，双脚保原支撑"),
             (1, "近侧左拳向前建立真实接触，远侧前臂回护，不能用低手站姿占active01"),
             (2, "近侧左拳充分前伸的接触/随势，与01连续，远侧手仍护头胸")]
    ]
    proposed += [{"action": "light3", "phase": phase, "purpose": purpose, "whole_character_source_needed": True,
                  "no_post_prepared_or_sent": True} for phase, purpose in [
        (4, "实际踢击腿收膝，支撑脚稳定，双肩双臂回护，身体保持站立高度"),
        (5, "踢击腿真正落回后足并站稳，双足/手架接既有idle；不得手触地或一膝跪地")]]
    review = {
        "schema": "ufeneo.arc-luna.s2.light-chain.actual-offline-review.v1", "reviewer": "/root/luna_jump_resume",
        "art_source": "existing", "source_inventory": rel(INVENTORY), "source_inventory_sha256": sha(INVENTORY),
        "actual_pages_viewed": pages, "whole_originals_shown_on_light_and_dark": True,
        "observations": findings, "minimal_possible_new_whole_frame_proposal_for_root_review": proposed,
        "proposal_not_approved_or_generated": True,
        "candidate_whole_sources_to_preserve_for_further_review": {"light1": [3, 4], "light2": [0, 1, 2, 3, 4], "light3": [0, 1, 2, 3]},
        "preserved_candidates_not_action_acceptance": True, "old_base_rule_reference": existing_rules,
        "next_step": "根实看本组完整源/缺口后决定整人补源；先补近侧拳有效相及第三击站立收势，再按同一源格合同做Forge候选和正式main双向真实J连段。",
        "official_basis_boundary": "普通近拳/远拳/侧踢顺序为本作街机游戏编排，不能冒称原剧同名连招；本人装甲身份依据沿既有模型。",
        "native_frames_generated": False, "post_count": 0, "godot_executed": False,
        "old_sources_or_product_changed": False, "original_user_files_read": False,
        "action_accepted": False, "strict_size_accepted": False, "whole_s2_accepted": False,
    }
    save(OUT / "actual-source-review-and-gaps.json", review)
    doctor = read(OUT / "doctor.json")
    non_ok = [row for row in doctor["checks"] if row["status"] != "OK"]
    save(OUT / "doctor-non-ok-disclosure.json", {"doctor": rel(OUT / "doctor.json"), "doctor_sha256": sha(OUT / "doctor.json"),
         "all_non_ok_checks_verbatim": non_ok, "warn_fail_threshold_fields": "doctor原输出没有threshold字段；原样保全，不自行编数。",
         "scope_effect": "本轮只审已有RGBA整源，不调用媒体、视频、代码美术或新Python环境；固定项目Python已使用，不因本报告安装依赖。",
         "generation_routes_not_invoked": True})
    text = """# 月亮S2轻击三连：既有源与真实缺口（仅离线）

按旧27动作顺序，下一项是light1→light2→light3。现有5/5/6张本人整源各有独立SHA，但没有本组月亮正式main签收。本轮实际看完12页完整源明/暗底JPEG，并核对旧时序；没有采样新运行帧、调用Godot、POST、改产品或读原用户文件。

直接装旧包的硬缺：light1 active01前手下垂，02与light2都由同侧肩臂水平出拳，未兑现原near→far编排；light3的04/05突然单膝/手触地，05不站回，缺收膝落足接idle。不能用不同文件名、改active时钟或拉长跪姿来放行。详见`actual-source-review-and-gaps.json`，其中仅提出供根复核的5张整人补源方向，未准备或发送POST。

旧16源全是1254方图。旧诊断逐相倍率0.1098194144–0.1288800733来自面积/头拟合；不能直接混入当前统一159整源合同。全部实体Alpha128不触边；14张低Alpha触边和4份returned_requires_review历史保持，不修改原件或历史门结论。旧light1末两相、light2五相、light3前四相仅保留候选，不代表动作通过。

图片都是JPEG80、宽768、≤150KB，完整源按同一368边界同比显示，不裁人或拼件。新索引绑定所有原源、时序、旧诊断及页SHA。资料只说明本作普通连段编排，没有虚构原剧技能名。

技能使用：generate2dsprite；art_source=existing。项目规则覆盖技能默认媒体路线，本轮没有调用该路线。doctor的WARN原文为：

- python.path — other python.exe on PATH: F:/Dev/Environment/shims/python.exe; F:/Dev/Environment/apps/python312/current/python.exe; ~/AppData/Local/Microsoft/WindowsApps/python.exe
- skills.present — ~/.codex/skills: missing generate2dmap, video2dsprite, codeart2d

doctor没有数值threshold字段；完整WARN/MISSING/UNKNOWN原文与文件引用保存在`doctor-non-ok-disclosure.json`及`doctor.json`。这些媒体能力不用于本轮已有源审；Python始终为项目固定解释器，没有安装依赖。

下一步由根实看明确源缺口，再决定整人补源与统一源格处理；本轮未接受轻击三连、严尺、全S2或正式可玩装甲。
"""
    with (OUT / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    excluded = {"subagent-owned-light-chain-offline-v1.nul", "subagent-owned-light-chain-offline-sha256-v1.json"}
    files = sorted([path for scope in [OUT, TOOLS] for path in scope.rglob("*") if path.is_file() and path.name not in excluded and "__pycache__" not in path.parts], key=rel)
    rows = [{"path": rel(path), "sha256": sha(path), "bytes": path.stat().st_size} for path in files]
    nul = OUT / "subagent-owned-light-chain-offline-v1.nul"
    with nul.open("xb") as stream:
        stream.write(b"\0".join(row["path"].encode("utf-8") for row in rows) + b"\0")
    index = OUT / "subagent-owned-light-chain-offline-sha256-v1.json"
    save(index, {"schema": "ufeneo.subagent-luna-s2-light-chain-offline-owned.v1", "owner": "/root/luna_jump_resume",
         "files": rows, "nul_path": rel(nul), "nul_sha256": sha(nul), "manifests_not_recursively_self_hashed": True,
         "prior_jump_v6_unchanged": True, "post_count": 0, "godot_executed": False,
         "product_changed": False, "original_user_read": False, "git_operations": False})
    print(json.dumps({"owned_file_count": len(rows), "nul_path": rel(nul), "nul_sha256": sha(nul), "index_path": rel(index),
                      "index_sha256": sha(index), "actual_review_sha256": sha(OUT / "actual-source-review-and-gaps.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
