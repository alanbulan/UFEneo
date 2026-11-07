"""Runtime regression suite for the clean repository; no historical art pools required."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
from runtime.environment import ROOT, godot_path, isolated_test_environment

CASES = [
    "logic_2d", "review_inputs", "armor_transform_routing", "air_only_start", "chase_interrupt",
    "projectile_ground_expiry", "projectile_ground_clip", "projectile_contact_direction", "projectile_air_knockdown_direction", "projectile_move_isolation", "projectile_beam_reflection", "hit_pushback_bounds",
    "throw_hold_point_overrides", "throw_root_overrides", "throw_current_capture", "capture_mechanism",
    "capture_receiver_availability", "ko_finish_presentation", "transform_mechanism",
    "phase3_standing", "phase3_air", "phase3_reaction", "phase3_zetton",
    "phase3_zetton_air", "phase3_zetton_defense", "phase3_throws",
    "phase3_specials", "phase3_supers", "phase3_fx_audio", "codex_impact_feedback_policy",
    "catalogue_identity_display", "computer_ai", "training_tape", "training_lifecycle", "replay_match_loading", "training_input_audit", "pixel_ui", "pixel_pages", "ui_facing",
    "main_shutdown_menu_exit", "main_shutdown_reentrancy",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--only", nargs="*", help="Specific existing test stems")
    parser.add_argument("--skip-import", action="store_true")
    args = parser.parse_args()
    output = ROOT / "reports/verification"
    output.mkdir(parents=True, exist_ok=True)
    run_output = output / "runs" / uuid.uuid4().hex[:12]
    run_output.mkdir(parents=True)
    env = isolated_test_environment(run_output)
    executable = godot_path()
    outcomes = []

    def run(name, command, timeout=240):
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=timeout,
                                    creationflags=0x08000000 if os.name == "nt" else 0)
            log = result.stdout + result.stderr
            # Godot AI 编辑器插件（addons/godot_ai）注册的全局类会在进程退出时留下
            # ObjectDB/Resource 告警。它只影响编辑器开发工具，不是被测游戏的缺陷，
            # 因此退出期的泄漏告警不参与判定；真正的 SCRIPT ERROR 和其它 ERROR 仍然失败。
            exit_noise = re.compile(
                r"^(?:WARNING: \d+ ObjectDB instances were leaked at exit|"
                r"ERROR: \d+ resources? still in use at exit|"
                r"\s+at: (?:cleanup \(core/object/object\.cpp|clear \(core/io/resource\.cpp))",
                re.M)
            judged = exit_noise.sub("", log)
            passed = result.returncode == 0 and not re.search(r"(?:SCRIPT ERROR:|^ERROR:)", judged, re.M)
            for line in log.splitlines():
                if line.startswith(("MAIN_SHUTDOWN_LOGIC ", "MAIN_MENU_EXIT ")):
                    passed = passed and not json.loads(line[line.index('{'):]).get("failures", [])
            code = result.returncode
        except subprocess.TimeoutExpired as error:
            log = str(error)
            passed, code = False, None
        (run_output / (name + ".log")).write_text(log, encoding="utf-8")
        outcomes.append({"name": name, "status": "passed" if passed else "failed", "exit": code})
        (run_output / "results.json").write_text(json.dumps(outcomes, ensure_ascii=False, indent=2), encoding="utf-8")
        (output / "latest-run.json").write_text(json.dumps({"directory": run_output.relative_to(ROOT).as_posix(), "results": outcomes}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(name + (": PASS" if passed else ": FAIL"), flush=True)
        if not passed:
            print(log[-3500:], flush=True)
            if not args.keep_going:
                raise SystemExit(1)

    if not args.skip_import:
        run("import", [executable, "--headless", "--path", str(ROOT), "--editor", "--import", "--quit"], 600)
    for case in args.only if args.only is not None else CASES:
        path = ROOT / "tests" / (case + ".gd")
        if not path.is_file():
            raise RuntimeError(f"Missing test: {case}")
        command = [executable]
        if case != "main_shutdown_menu_exit":
            command.append("--headless")
        command += ["--path", str(ROOT), "--script", "res://tests/" + case + ".gd"]
        case_output = run_output / case
        if case in ("hit_pushback_bounds", "chase_interrupt", "projectile_contact_direction", "projectile_air_knockdown_direction", "projectile_move_isolation", "projectile_beam_reflection", "capture_mechanism", "frame_guard", "phase3_specials", "phase3_zetton"):
            command += ["--", "--test-out=" + str(case_output)]
        elif case == "replay_match_loading":
            command += ["--", "--replay-test-out=" + str(case_output)]
        elif case == "training_input_audit":
            command += ["--", "--audit-test-out=" + str(case_output)]
        elif case == "capture_receiver_availability":
            command += ["--", "--expect-fixed", "--output=" + str(run_output / "capture-receivers.json")]
        elif case.startswith("main_shutdown_"):
            command += ["--", "--shutdown-out=" + str(case_output)]
        run(case, command)
        if case == "capture_mechanism" and outcomes[-1]["status"] == "passed":
            run("capture_mechanism_replay", command + ["--replay"])
    if args.only is None:
        run("fx-audio-resources", [sys.executable, str(ROOT / "tools/check_fx_audio.py")])
        run("pixel-ui-resources", [sys.executable, str(ROOT / "tools/check_pixel_ui.py")])
        run("main-startup", [executable, "--headless", "--path", str(ROOT), "--quit-after", "120"])
    if any(row["status"] != "passed" for row in outcomes):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
