"""轻击滚动只读预检v2：只对选定下一单拒绝提交痕迹，既有终态不误挡后续。"""
from pathlib import Path
from decimal import Decimal
import argparse
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import art.pipeline
from art.image_budget import OfficialImageBudget
from PIL import Image

PLAN = ROOT / "art/fighters/ultraman-arc__luna/stage2/light-chain-whole-briefs-20261102-v1/plan.json"
REPORT = ROOT / "reports/review/2026-11-02/luna-s2-light-chain-briefs-v1"
LEGACY_UNKNOWN = "011ff77710ed49c9b441ed80f91733be"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_ref(row):
    path = (ROOT / row["path"]).resolve()
    path.relative_to(ROOT)
    assert path.is_file() and sha(path) == row["sha256"], row["path"]
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-plan-sha256", required=True)
    parser.add_argument("--only", choices=["light1-00", "light1-01", "light1-02", "light3-04", "light3-05"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    assert sha(PLAN) == args.expect_plan_sha256
    plan = read(PLAN)
    for key in ["root_source_gap_review", "source_contract", "timing_contract"]:
        check_ref(plan[key])
    source_contract = read(check_ref(plan["source_contract"]))
    for source in source_contract["current_existing_sources"] + [source_contract["idle_reference"]]:
        for key in ["client1024", "metadata", "saved_provider1254", "request_state"]:
            check_ref(source[key])
    check_ref(source_contract["identity_master1024"])
    check_ref(source_contract["model_measurements"])
    timing = read(check_ref(plan["timing_contract"]))
    for action in timing["actions"]:
        check_ref(action["current_base_rule_reference_not_luna_install"])

    local = art_pipeline.local_image_config()
    assert art_pipeline.image_route(local) == "api"
    url = (os.environ.get("UFE_IMAGE_BASE_URL") or local.get("base_url") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    assert url == "https://api.openai.com/v1"
    checks = []
    budget = None
    for row in plan["briefs"]:
        brief_path = check_ref(row["brief"])
        check_ref(row["prompt_file"])
        brief = read(brief_path)
        assert brief["preparation_only_no_post"] and brief["root_POST_decision_pending"]
        refs = [check_ref(value) for value in brief["references"]]
        assert len(refs) <= 4
        for reference in refs:
            with Image.open(reference) as image:
                assert image.size == (1024, 1024) and image.mode == "RGBA"
        fields = art_pipeline.image_fields(brief)
        # __init__只校已授权包络并记录本地对象，begin/complete都不调用。
        budget = OfficialImageBudget(local, url, fields, refs)
        assert budget.reserve == Decimal("1") and budget.limit == Decimal("60")
        command = next(value for value in plan["commands"] if value["key"] == row["key"])
        output = Path(command["future_out"])
        output.resolve().relative_to(PLAN.parent.resolve())
        markers = [name for name in ["before-submit.json", "submission-result.json", "candidate.provider.png", "candidate.frontend-task.json", "candidate.png", "rejected/candidate.png"] if (output.parent / name).exists()]
        selected_for_new_submit = args.only is None or row["key"] == args.only
        if selected_for_new_submit:
            assert not markers, "选定下一单已有提交痕迹；先恢复原单，禁止重发POST"
        checks.append({"key": row["key"], "brief_sha256": row["brief"]["sha256"],
                       "reference_sha256_in_order": [value["sha256"] for value in brief["references"]],
                       "actual_project_client_model": fields["model"], "quality": fields["quality"], "size": fields["size"],
                       "background": fields["background"], "output_format": fields["output_format"], "n": fields["n"],
                       "prompt_utf8_bytes_with_client_suffix": len(fields["prompt"].encode("utf-8")),
                       "fits_reviewed_official_budget_envelope": True,
                       "reference_count": len(refs), "future_out_absent": not markers,
                       "selected_for_new_submission_absence_gate": selected_for_new_submit,
                       "existing_attempt_markers": markers})
    assert budget is not None and budget.path.is_file()
    ledger_before = sha(budget.path)
    data = budget._read()  # 仅读取既有账本，不取锁、不创建lock、不写入。
    committed = sum((Decimal(str(row["committed_usd"])) for row in data["entries"]), Decimal("0"))
    legacy = next(row for row in data["entries"] if row["id"] == LEGACY_UNKNOWN)
    assert Decimal(str(legacy["committed_usd"])) == Decimal("10")
    unresolved = [row for row in data["entries"] if row["id"] != LEGACY_UNKNOWN and any(token in str(row.get("status", "")).lower() for token in ["unknown", "reserved"])]
    next_reserve = budget.reserve
    remaining = [row for row in checks if row["future_out_absent"]]
    five_reserve = budget.reserve * len(remaining)
    next_ok = not unresolved and committed + next_reserve <= budget.limit
    five_ok = not unresolved and committed + five_reserve <= budget.limit
    assert sha(budget.path) == ledger_before, "预检期间账本变化；先重新只读预检，不能据此POST"
    selected = [row for row in checks if args.only is None or row["key"] == args.only]
    result = {
        "schema": "ufeneo.arc-luna.s2.light-chain-readonly-budget-preflight.v2",
        "plan": str(PLAN), "plan_sha256": args.expect_plan_sha256, "selected": selected,
        "all_five_briefs_and_references_verified": True,
        "project_client": {"path": "tools/art/pipeline.py", "sha256": sha(ROOT / "tools/art/pipeline.py")},
        "project_budget_gate": {"path": "tools/art/image_budget.py", "sha256": sha(ROOT / "tools/art/image_budget.py")},
        "root_serial_entry": {"path": "tools/rebuild/shared/root_serial_image_request_20261101.py", "sha256": sha(ROOT / "tools/rebuild/shared/root_serial_image_request_20261101.py")},
        "official_host": url, "machine_ledger_sha256": ledger_before,
        "local_committed_and_held_usd": str(committed), "hard_cap_usd": str(budget.limit),
        "future_per_request_reserve_usd": str(budget.reserve), "remaining_unsubmitted_briefs_count": len(remaining),
        "remaining_proposals_worst_case_additional_reserve_usd": str(five_reserve),
        "project_headroom_usd": str(budget.limit - committed),
        "legacy_unknown_preserved": {"id": LEGACY_UNKNOWN, "committed_usd": str(legacy["committed_usd"]), "status": legacy["status"], "resubmission_forbidden": True},
        "new_unresolved_requests_blocking_POST": [{"id": row["id"], "status": row["status"], "committed_usd": row["committed_usd"]} for row in unresolved],
        "one_next_reserve_fits_at_this_readonly_snapshot": next_ok,
        "all_remaining_conservative_reserves_fit_at_this_readonly_snapshot": five_ok,
        "user_provided_balance_usd": "40.94", "balance_not_verified_by_api": True,
        "this_is_local_cost_exposure_not_account_balance": True,
        "budget_begin_called": False, "reservation_or_ledger_write_performed": False,
        "credentials_decrypted_or_api_key_read": False, "network_request_or_POST": False,
        "root_brief_approval_not_assumed": True, "before_each_POST_repeat_fresh_preflight": True,
        "submit_only_one_then_wait_for_actual_usage_and_root_source_review": True,
        "unknown_result_never_retried_or_released": True,
        "sampling_product_Godot_Git_or_original_user_reads": False,
    }
    if args.out:
        out = args.out.resolve()
        out.relative_to(REPORT.resolve())
        assert not out.exists()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"preflight": out.relative_to(ROOT).as_posix(), "sha256": sha(out),
                          "one_next_reserve_fits": next_ok, "all_five_reserves_fit": five_ok,
                          "local_committed_and_held_usd": str(committed), "no_POST_or_reservation": True}, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if not next_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
