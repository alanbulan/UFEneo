"""封5稿的精确新增清单；根随后产生的提交journal/图/usage明确不纳本席owned。"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1"
REPORT = ROOT / "reports/review/2026-11-02/luna-s2-light-chain-briefs-v1"
TOOLS = ROOT / "tools/rebuild/ultraman-arc/luna-s2-light-chain-briefs-20261102-v1"
PLAN = ART / "plan.json"
PLAN_SHA = "225b81a39e952bf34c7d1117a6025b9f2987a9f1fc93f5cda7759f8c10e1e5bd"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def save(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    assert sha(PLAN) == PLAN_SHA
    plan = read(PLAN)
    exact_art = [ART / ".gitattributes", PLAN]
    for key in ["source_contract", "timing_contract"]:
        row = plan[key]
        path = ROOT / row["path"]
        assert sha(path) == row["sha256"]
        exact_art.append(path)
    for row in plan["briefs"]:
        path, prompt = [ROOT / row[key]["path"] for key in ["brief", "prompt_file"]]
        assert sha(path) == row["brief"]["sha256"] and sha(prompt) == row["prompt_file"]["sha256"]
        brief = read(path)
        assert prompt.read_text("utf-8") == brief["prompt"] + "\n"
        for reference in brief["references"]:
            assert sha(ROOT / reference["path"]) == reference["sha256"]
        exact_art += [path, prompt]
    snapshot_v1 = REPORT / "readonly-preflight-light1-00-v1.json"
    snapshot_v2 = REPORT / "readonly-preflight-v2-light1-01-v1.json"
    assert sha(snapshot_v1) == "a0e09a641a4e3a5228470ead4aa74c0661e42232fe48e3c11d49a2172222d525"
    assert sha(snapshot_v2) == "21ac683493c30ae0ae3bc8b781b4df2f4e09dec6939040bd0caea98b886de59c"
    initial = read(snapshot_v1)
    pending = read(snapshot_v2)
    assert initial["one_next_reserve_fits_at_this_readonly_snapshot"] is True
    assert pending["one_next_reserve_fits_at_this_readonly_snapshot"] is False
    assert pending["new_unresolved_requests_blocking_POST"]
    assert all(snapshot["network_request_or_POST"] is False and snapshot["reservation_or_ledger_write_performed"] is False for snapshot in [initial, pending])
    index = REPORT / "five-brief-source-command-index.json"
    save(index, {
        "schema": "ufeneo.arc-luna.s2.light-chain-five-brief-handoff.v1", "owner": "/root/luna_jump_resume",
        "plan": ref(PLAN), "briefs": plan["briefs"], "root_serial_generation_commands": plan["commands"],
        "source_contract": plan["source_contract"], "timing_contract": plan["timing_contract"],
        "current_readonly_preflight_entry": ref(TOOLS / "preflight_v2.py"),
        "initial_readonly_preflight_preserved": ref(snapshot_v1),
        "new_inflight_gate_refusal_preserved": ref(snapshot_v2),
        "new_inflight_refusal_is_expected_and_does_not_authorize_retry": True,
        "preflight_argv_template": ["C:/Users/13080/.codex/venvs/ufeneo/Scripts/python.exe", str(TOOLS / "preflight_v2.py"),
                                    "--expect-plan-sha256", PLAN_SHA, "--only", "<下一张key>", "--out", "<本报告目录内新JSON路径>"],
        "known_phase05_text_correction": plan["old_proposal_text_correction"],
        "root_generated_candidate_journals_usage_are_excluded_from_agent_owned": True,
        "parent_reported_first_return": {"key": "light1-00", "attempt": "request-001", "terminal": True,
            "usage_usd_reported_by_root": "0.082231", "local_committed_usd_reported_by_root": "52.897446",
            "root_visual_disposition": "远暗臂水平伸拳、近臂拳在下巴；错误起手，拒作00及换名安装。根另起request002，两参考简化双肘弯曲。",
            "child_did_not_reinspect_returned_PNG": True, "frozen_five_briefs_not_modified": True,
            "initial_request001_generation_command_is_consumed_do_not_repeat": True, "other_four_briefs_no_POST_by_child": True},
        "agent_POST_count": 0, "agent_sampling_count": 0, "agent_product_Godot_Git_or_original_user_reads": False,
        "stage2_or_art_accepted": False,
    })
    text = """# 月亮S2轻击三连：五个整人补相合同

本轮只准备light1 00/01/02和light3 04/05五张完整人物brief、独立prompt、实际参考SHA及原时序。没有POST、采样、生成PNG、改产品、启动Godot、Git或读原用户文件。根之后串行生成的candidate、before-submit、usage和source review属于另一次根操作，不纳本席owned。

根已另行执行light1-00 request001，并实看返回图退回：远暗臂水平伸拳、近臂拳在下巴，不是双肘弯曲的近拳起手。根通报本次usage0.082231美元、本机占额52.897446；原执行命令已消耗，不能重复。根另备两参考简化稿request002，本席不改五份冻结稿，余四稿保持不POST。以下初始执行表保留历史，后续按根新稿/实际签收继续。

| 稿 | brief SHA-256 |
|---|---|
| light1-00 | a4da21d91255baabb06dc69846c4a5d068f1a368622b2dd497ca780cdc26e62d |
| light1-01 | 2738920b4e8a76e2dd6c3a87e39ceef67bf5b9cc043ad6d7d21ff82f88c50e73 |
| light1-02 | 3ffbbf34e61f986140f2de0628d4e6500b358cd31a6452bc7458085e99d12c15 |
| light3-04 | baf1ebf07c0cfa90e225e2d4a6f66e05ba004af415477c7fe6094f3197d4793f |
| light3-05 | fcca69535532520d837118b006c39c0579a31fd2496e504c57afe62dcbae09bb |

完整路径、每张三参考顺序/SHA、独立prompt和project root_serial的argv见`five-brief-source-command-index.json`。总plan为`art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/plan.json`，SHA 225b81a39e952bf34c7d1117a6025b9f2987a9f1fc93f5cda7759f8c10e1e5bd。brief和prompt固定后不覆盖；返修另立request目录。

light1 00规定近亮左拳起手、远暗右拳护颏和双肩胸髋/双膝共同加载；01必须在tick2–3已经用同一近臂实际伸拳接触，02在tick4–7继续伸展随势，不能换成远肩出拳。light3 04收回暗远踢击腿、亮近腿稳定承重且全身站立；05暗远腿落在画面右前足、亮近腿留左后，双足双臂回护接idle。旧离线提案中的“踢击腿落回后足”文字在新plan显式纠正，旧冻结报告不回改。

三条动作仍各20tick：light1/light2为2/2/4/4/8；light3为2/2/2/3/5/6。active和取消逐tick从当前本体规则只读绑定，尚未成为月亮运行招式；伤害、费用、硬直和规则不改，不能用改active掩盖坏姿势。未来仍须真实J三连、单击收招、命中/防御/落空、双向720/1080、完整人物及独立原输入回放。

16张旧provider为1254方图，但各自已有整张缩到1024的客户端raw.png，metadata逐SHA明确resized=true、padded=false。新合同直接绑定现成1024客户端文件，未重新resize或复制PNG；旧rejected和Alpha门保持。母图与旧源未来一律整张159/1024，同一组整数栅格，禁止逐相头/面积/bbox拟合；实际骨尺、根点、两鞋与回护仍要在新源返回后另审。

预算入口为`tools/rebuild/ultraman-arc/luna-s2-light-chain-briefs-20261102-v1/preflight_v2.py`，每次使用`--expect-plan-sha256`和`--only`指定下一张，在新报告路径保存。v2只对选中下一单拒绝任何before-submit/candidate等痕迹；已完成前单不会因目录存在而误挡其它新稿。它只读本机官方配置/账本并校引用，绝不调用begin/complete、取锁占额、解密凭据或POST。

初次00预检时本机占额52.815215/60，下一单预占1，五稿保守新增5仍容得下；这不是账户余额。随后01的v2只读快照看到53.815215和新的在途占额，正常退出1禁止追加POST，原报告保全；当前单终态及根实际审源后再做鲜检。旧未知011ff77710ed49c9b441ed80f91733be继续占10、禁止重发。40.94美元仅为用户提供余额，未API核实。

真正生成只能由根调用项目`tools/rebuild/shared/root_serial_image_request_20261101.py`，它再调用`tools/art_pipeline.py(generate_image)`，high/1024/透明、每单1、先占额后POST、不自动重发。每张命令都已离线列出，本席没有执行。

跳跃族既有冻结材料保持；严尺、轻击实际效果、全S2和正式可玩装甲均未据本合同通过。
"""
    with (REPORT / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    exact_reports = [REPORT / name for name in [".gitattributes", "preparation-receipt.json", "readonly-preflight-light1-00-v1.json", "readonly-preflight-v2-light1-01-v1.json", "five-brief-source-command-index.json", "README.md"]]
    exact_tools = [TOOLS / name for name in ["prepare.py", "preflight.py", "preflight_v2.py", "finalize.py"]]
    files = sorted(set(exact_art + exact_reports + exact_tools), key=lambda path: path.relative_to(ROOT).as_posix())
    rows = [{**ref(path), "bytes": path.stat().st_size} for path in files]
    nul = REPORT / "subagent-owned-five-briefs-v1.nul"
    with nul.open("xb") as stream:
        stream.write(b"\0".join(row["path"].encode("utf-8") for row in rows) + b"\0")
    owned = REPORT / "subagent-owned-five-briefs-sha256-v1.json"
    save(owned, {"schema": "ufeneo.subagent-luna-s2-five-whole-brief-owned.v1", "owner": "/root/luna_jump_resume",
         "files": rows, "nul_path": nul.relative_to(ROOT).as_posix(), "nul_sha256": sha(nul),
         "manifests_not_recursively_self_hashed": True,
         "root_candidate_before_submit_submission_result_usage_not_owned": True,
         "root_source_review_not_owned": True, "prior_jump_and_offline_source_review_not_modified_or_duplicated": True,
         "agent_POST_sampling_product_Godot_Git_or_original_user_reads": False})
    print(json.dumps({"owned_paths": len(rows), "nul": ref(nul), "owned_index": ref(owned), "command_index": ref(index),
                      "plan": ref(PLAN), "current_preflight_entry": ref(TOOLS / "preflight_v2.py")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
