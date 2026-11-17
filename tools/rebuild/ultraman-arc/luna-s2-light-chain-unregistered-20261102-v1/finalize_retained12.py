"""追加本席真实JPEG审图及精确归属清单；不回写冻结采样件。"""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-unregistered-20261102-v1/retained12-v1"
REPORT = ROOT / "reports/review/2026-11-02/luna-light-chain-unregistered-retained12-v1"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def ref(path):
    return {"path": relative(path), "sha256": sha(path)}


def checked(value):
    path = (ROOT / value["path"]).resolve()
    path.relative_to(ROOT)
    assert sha(path) == value["sha256"], value["path"]
    return path


def save(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    result_path = REPORT / "sampling-result.json"
    result = read(result_path)
    contract_path = checked(result["processing_contract"])
    contract = read(contract_path)
    for name, digest in contract["frozen_inputs"].items():
        assert sha(ROOT / name) == digest, name
    assert len(result["receipts"]) == 12 and len(result["views"]) == 27
    notes = {
        ("light1", 0): "根已签request002的近亮拳收在下胸前、远暗拳护颏，双肘折叠与两足完整；159下胸前拳/腕盘相邻细节合并，未自行删改。",
        ("light1", 3): "近亮拳收在腰腹、远拳护颏，腿弓步及头刃完整；与00相比腰高/拳位不同，缺01/02不能签整个出拳回护。",
        ("light1", 4): "双足站稳、近拳仍在腰腹且远拳护面；后跟/前鞋底有像素台阶，未作逐相鞋底修画或与idle注册。",
        ("light2", 0): "近侧腕盘/拳收腰，画面右侧远臂向下屈，双脚完整；远手低是源内姿态，不因完成采样当成合格高位回护。",
        ("light2", 1): "画面右拳屈肘抬起、近拳贴腰，肩胸与腕刃完整；旧客户端透明拒收仍保留，二值候选不释放原隔离。",
        ("light2", 2): "画面右侧手臂向前伸直，另一拳收腰，肩胸向前、弓步与拳尖完整；本席不凭圆盘位置推定正式手侧通过。",
        ("light2", 3): "前臂折回且两拳分在腰腹/胸前，近侧腕盘部分随转臂遮挡；手盘读数与02有变化，根仍需核真实肢体连续性。",
        ("light2", 4): "前臂回到低位屈肘，双足与头刃完整；与00/03的护手高度有差异，不能把5张候选当整条动作已签。",
        ("light3", 0): "一腿提膝、另一腿向左下伸作支撑，两拳屈肘；胫甲/鞋头完整，采样未改足部坐标。",
        ("light3", 1): "重心向前，一足落画面右前、另一足拖后抬跟，双臂仍屈；00→01换重心幅度较大，缺注册不能断言漂移或接续合格。",
        ("light3", 2): "一腿完整向前平踢、另一腿向下支撑，脚尖和双拳均完整；01→02支撑转换须随整组时序与接触核验。",
        ("light3", 3): "继续前踢且膝更伸直，两臂前后屈肘随势，支撑脚完整；04/05新回收尚未获准处理，未拿旧跪地相代填。",
    }
    phases = []
    for value in result["receipts"]:
        receipt_path = checked(value)
        receipt = read(receipt_path)
        sample_path = checked(receipt["whole_source_sample"])
        for key in ["root", "grip", "hitboxes", "hurtboxes", "registration"]:
            assert receipt[key] is None
        for image_ref in receipt["deep_light_complete_views"]:
            checked(image_ref)
        phases.append({
            "action": receipt["action"], "phase": receipt["phase"], "receipt": value,
            "sample": ref(sample_path), "source": receipt["source"],
            "candidate_metrics_diagnostic_only": receipt["candidate_alpha"],
            "actual_dark_light_4x_JPEG_viewed": True,
            "actual_native_1x_dark_light_contact_page_viewed": True,
            "observation": notes[(receipt["action"], receipt["phase"])],
            "subagent_candidate_processing_accepted_only": True,
            "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
            "strict_size_or_complete_motion_accepted": False,
            "source_quarantine_preserved": receipt["source_historical_quarantine_preserved"],
        })
    for value in result["views"]:
        checked(value)
    review = {
        "schema": "ufeneo.arc-luna.s2.light-chain-retained12-subagent-actual-review.v1",
        "reviewer": "/root/luna_jump_resume", "authority": "根明确委派12源离线整图候选处理；本席非根最终验收",
        "sampling_result": ref(result_path), "processing_contract": ref(contract_path),
        "actual_review_method": "逐张通过view_image打开新JPEG；24张每相完整159方精确4倍深浅底与3张159原生1:1深浅完整联系页；未用裁片、PNG展示或指标代替实际看图。",
        "actual_views_opened_and_reviewed": result["views"],
        "view_claim_scope": "views内冻结pending字段记录生成时状态；本新增审图件只补本席实看，不改旧字节，也不声称根已看。",
        "phases": phases,
        "whole_canvas_and_identity_observation": "已看12相头刃、月亮蓝甲/腕盘、胸甲、红银腿及各自双臂双腿和鞋头完整，深浅底没有整片棋盘/实色背景；未见采样新增的缺肢或拼接。细指、腕盘与鞋底的像素合并/台阶保留。",
        "known_limits": [
            "统一源倍率159/1024，未按身高/头尺/面积拟合；不能凭人物完整就签严格骨尺或全相比例一致。",
            "light1缺01/02、light3缺04/05，旧错误相和根未签新相均未代填；不是完整三连或回idle验收。",
            "light2手侧/回护偏低、light3换重心/支撑转换及各相腕甲/细指小差保留，待完整动作根实际核验。",
            "root/grip/攻击区/受击区/registration全null，未出320注册帧、clip、atlas或Godot候选。",
            "旧light2/01和03客户端原透明拒收及其位置/metadata原样保持，仅本次获准Alpha128派生候选。",
        ],
        "frozen_source_and_bound_bytes_rechecked_unchanged": True,
        "ready_for_root_candidate_review": True, "root_actual_visual_review_pending": True,
        "strict_size_accepted": False, "complete_action_accepted": False,
        "root": None, "grip": None, "hitboxes": None, "hurtboxes": None, "registration": None,
        "unregistered": True, "installed": False, "playable": False,
        "sampling_and_finalize_scripts_POST_Godot_product_Git_or_user_file_reads": False,
        "session_required_readonly_git_log5_only": True, "Git_mutations": False,
        "user_settings_replay_contents_or_observe_snapshot_reads": False,
        "new_cost_usd": "0", "new_video": False,
    }
    review_path = REPORT / "subagent-actual-page-review.json"
    save(review_path, review)
    readme = """# 月亮装甲轻击保留12源：未注册159整图候选

本轮只处理根已授权的11张旧客户端1024整源与light1/00 request002。沿已签跳跃相同的Forge RGB兼容处理：源Alpha128二值→整张1024到159采样→本人固定32色→Alpha128二值。未裁bbox、删连通块、逐相拟合或更改本人的配色。

本席已逐页实际打开全部深浅JPEG：每相完整159方精确4倍深浅各一页，以及每动作159原生1:1深浅完整联系页。候选头刃、手脚和装甲轮廓完整；细指/腕盘/鞋底的像素合并及手部回护小差保留。真实观察逐相写在[subagent-actual-page-review.json](subagent-actual-page-review.json)，冻结[sampling-result.json](sampling-result.json)与phase receipt不回写。

原生联系页：[light1](light1-native159-1x-complete-dark-light.jpg)、[light2](light2-native159-1x-complete-dark-light.jpg)、[light3](light3-native159-1x-complete-dark-light.jpg)。每相深浅精确4倍完整页与源/候选的SHA索引见sampling-result.json。

root、grip、hitboxes、hurtboxes、registration均为null。没有320注册帧、clip或atlas，没有运行/安装动作。light1/01与02、light3/04与05仍缺新源；light2低位回护、light3换重心/支撑转换和严格骨尺待完整组根核验。旧客户端隔离保持，本席接受处理候选不等于根接受动作或原生Alpha过门。

本项无POST、Godot、产品/用户档操作、Git变更、新费用或视频。会话必读git log -5仅只读，不计为采样脚本操作。根应在本新增审图件基础上自行实际看图决定后续，不等待用户验收。
"""
    with (REPORT / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(readme)
    owned_nul = REPORT / "subagent-owned-retained12-v1.nul"
    owned_json = REPORT / "subagent-owned-retained12-sha256-v1.json"
    payloads = [path for folder in [ART, REPORT, HERE] for path in folder.rglob("*") if path.is_file()]
    assert len(payloads) == len(set(payloads))
    # NUL精确含本清单及JSON本身；JSON不伪造自哈希，最终哈希另行回报根。
    all_files = sorted([*payloads, owned_nul, owned_json], key=relative)
    with owned_nul.open("xb") as stream:
        stream.write(b"".join(relative(path).encode("utf-8") + b"\0" for path in all_files))
    manifest = {
        "schema": "ufeneo.subagent-owned-files-sha256.v1", "owner": "/root/luna_jump_resume",
        "scope": "仅本席新采样/收口工具、未注册候选、完整JPEG及报告；排除旧冻结包和根生产/签收目录。",
        "owned_pathspec": ref(owned_nul), "total_owned_paths": len(all_files),
        "sha256_entries": [ref(path) for path in all_files if path != owned_json],
        "self_hash_omitted": relative(owned_json), "root_commit_only": True,
    }
    save(owned_json, manifest)
    print(json.dumps({"review": ref(review_path), "owned_nul": ref(owned_nul), "owned_manifest": ref(owned_json),
                      "owned_paths": len(all_files), "root_actual_review_pending": True}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
