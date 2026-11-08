"""两EX直选：正式前台自然对局、实际F4与独立原输入回放；只保存JPG，零视频。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "reports/review/2026-11-01/ex-direct-selection-runtime-v1"
PREFIX = "res://tests/ex_direct_selection_review_"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/rebuild/ultraman-omega"))
from verify import godot_path
from codex_s6_energy_runtime import lock_required

CASES = [{'id': 'cpu-ex-gomora-left', 'mode': 'cpu', 'fighters': ['ex_gomora', 'zetton'], 'stage': 'light-country', 'music': 'auto', 'focus': 0}, {'id': 'local-ex-gomora-right', 'mode': 'local', 'fighters': ['ultraseven', 'ex_gomora'], 'stage': 'ultra-arena', 'music': 'monster-pressure', 'focus': 1}, {'id': 'cpu-ex-red-king-left', 'mode': 'cpu', 'fighters': ['ex_red_king', 'zetton'], 'stage': 'monster-graveyard', 'music': 'auto', 'focus': 0}, {'id': 'local-ex-red-king-right', 'mode': 'local', 'fighters': ['ultraseven', 'ex_red_king'], 'stage': 'light-country', 'music': 'off', 'focus': 1}]


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def valid_id(value: str) -> str:
    assert re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value), "报告ID只能使用小写字母、数字和横线"
    return value


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def source_paths() -> list[Path]:
    """冻结运行代码/数据，以及本组角色、选场、UI和音频所消费的资源。"""
    paths = {ROOT / "project.godot", Path(__file__), ROOT / "tools/godot_lock.py",
             ROOT / "tools/verify.py", ROOT / "tools/rebuild/ultraman-omega/codex_s6_energy_runtime.py"}
    for folder in ["app", "core", "input", "presentation", "ui", "content", "addons/controller_icons", "third_party/shoto"]:
        paths.update(path for path in (ROOT / folder).rglob("*") if path.is_file()
                     and path.suffix in {".gd", ".gdshader", ".json", ".tres", ".tscn"})
    for folder in ["assets/ui", "assets/app", *[f"assets/fighters/{identity}" for identity in ["ex_gomora", "ex_red_king", "zetton", "ultraseven"]],
                   *[f"assets/effects/{identity}" for identity in ["ultraman-omega", "zetton", "ultraseven", "shared"]]]:
        paths.update(path for path in (ROOT / folder).rglob("*") if path.is_file() and path.suffix != ".import")
    # 场景和音频的真实资源来自产品数据；不把离线原剧/生产候选计作运行资源。
    data_paths = [ROOT / "content/stages/catalog.json", *sorted((ROOT / "content/audio").rglob("*.json"))]
    for path in data_paths:
        for text in strings(read(path)):
            if text.startswith("res://assets/"):
                candidate = ROOT / text.removeprefix("res://")
                if candidate.is_file():
                    paths.add(candidate)
    paths.update((ROOT / "content/fighters/ultraman-omega").glob("codex_s7_match_review_*.gd.uid"))
    paths.update(ROOT / (PREFIX.removeprefix("res://")+name+".gd") for name in ["entry","game","driver","replay"])
    return sorted(paths)


def sources() -> dict[str, str]:
    return {relative(path): sha(path) for path in source_paths()}


def gate() -> dict:
    selected = read(ROOT / "content/roster/selection.json")["entries"]
    fighters = {}
    for identity in ["ex_gomora", "ex_red_king"]:
        definition = read(ROOT / f"content/fighters/{identity}/definition.json")
        fighters[identity] = dict(playable=definition.get("playable",False),implemented=definition.get("implemented",False),
            normal_selection_present=any(row["id"]==identity for row in selected),selection_visible=definition.get("selection_visible",definition.get("select_visible",False)))
    return dict(fighters=fighters,playable=all(row["playable"] for row in fighters.values()),implemented=all(row["implemented"] for row in fighters.values()),
        normal_selection_present=all(row["normal_selection_present"] for row in fighters.values()),pilot_bypass_used=False,direct_battle_used=False,training_used=False)


def preflight(require_unlocked: bool = False) -> dict:
    state = gate()
    if require_unlocked:
        assert state["playable"] and state["implemented"] and state["normal_selection_present"], "两EX须由根按用户授权正式放行，工具不改标志、不使用pilot/训练绕行"
    for name in ["entry","game","driver","replay"]:
        assert (ROOT / (PREFIX.removeprefix("res://")+name+".gd")).is_file()
    stages=read(ROOT / "content/stages/catalog.json")["stages"]
    tracks=read(ROOT / "content/audio/battle_music.json")
    for case in CASES:assert any(row["id"]==case["stage"] for row in stages)
    assert "monster-pressure" in set(strings(tracks))
    return dict(gate=state,fingerprints=sources(),cases=CASES,generated_videos=0)


def engine(directory: Path, label: str, options: list[str], frozen: dict[str, str], timeout: int) -> bool:
    lock_required()
    directory.mkdir(parents=True, exist_ok=True)
    log = directory / f"{label}.log"
    result_path = directory / f"{label}-exit.json"
    assert not log.exists() and not result_path.exists(), "原运行日志拒绝覆盖，须另用run-id/replay-id"
    command = [str(godot_path()), "--path", str(ROOT), *map(str, options)]
    exit_code: int | str
    with log.open("xb") as stream:
        try:
            result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            exit_code = "timeout"
    lines = log.read_text("utf-8", errors="replace").splitlines()
    errors = [line for line in lines if "SCRIPT ERROR:" in line or "Parse Error:" in line or line.lstrip().startswith("ERROR:")]
    warnings = [line for line in lines if "WARNING:" in line]
    current = sources()
    changed = sorted(path for path in frozen.keys() | current.keys() if frozen.get(path) != current.get(path))
    value = dict(command=command, exit_code=exit_code, errors=errors, warnings=warnings,
                 changed_sources=changed, log_sha256=sha(log), generated_videos=0)
    value["ok"] = exit_code == 0 and not errors and not warnings and not changed
    save(result_path, value)
    print(json.dumps(dict(label=label, output=relative(directory), **{key: value[key] for key in ["exit_code", "errors", "warnings", "changed_sources", "ok"]}), ensure_ascii=False), flush=True)
    return value["ok"]


def preserve_user_data(target: Path) -> tuple[Path, dict[str, bytes | None]]:
    user_data = Path.home() / "Library/Application Support/Godot/app_userdata/奥特曼格斗进化Neo"
    original: dict[str, bytes | None] = {}
    evidence = []
    for name in ["settings.json", "last_replay.json"]:
        path = user_data / name
        original[name] = path.read_bytes() if path.is_file() else None
        if original[name] is not None:
            preserved = target / "user-data-before" / name
            preserved.parent.mkdir(parents=True, exist_ok=True)
            with preserved.open("xb") as stream:
                stream.write(original[name])
        evidence.append(dict(name=name, original_existed=original[name] is not None,
                             sha256=hashlib.sha256(original[name]).hexdigest() if original[name] is not None else None))
    save(target / "user-data-before.json", dict(user_data_dir=str(user_data), files=evidence))
    return user_data, original


def restore_user_data(target: Path, user_data: Path, original: dict[str, bytes | None]) -> None:
    results = []
    for name, saved in original.items():
        assert name in {"settings.json", "last_replay.json"}, "只恢复本轮明确保全的用户文件"
        path = user_data / name
        assert path.resolve().parent == user_data.resolve()
        generated = target / "user-data-generated-final" / name
        generated_sha256 = None
        if path.exists():
            assert path.is_file()
            payload = path.read_bytes()
            generated_sha256 = hashlib.sha256(payload).hexdigest()
            generated.parent.mkdir(parents=True, exist_ok=True)
            assert not generated.exists()
            with generated.open("xb") as stream:
                stream.write(payload)
            assert sha(generated) == generated_sha256, "跨卷生成文件保全校验失败，保留用户目录原文件"
            assert path.read_bytes() == payload, "用户文件在保全期间改变，不能删除"
            path.unlink()  # 仅删除已逐字节保全并核SHA的这一个明确文件，再恢复原字节/原不存在状态。
        if saved is not None:
            with path.open("xb") as stream:
                stream.write(saved)
        restored = (path.read_bytes() if path.exists() else None) == saved
        results.append(dict(name=name, restored_exact_bytes=restored, original_existed=saved is not None,
                            preservation_method="copy_verify_sha256_then_unlink", generated_sha256=generated_sha256,
                            final_sha256=sha(path) if path.is_file() else None))
    save(target / "user-data-restoration.json", dict(files=results, restored_exact_bytes=all(row["restored_exact_bytes"] for row in results)))
    assert all(row["restored_exact_bytes"] for row in results), "原偏好和上次回放须逐字节恢复"


def replay(target: Path, size: str, replay_id: str) -> bool:
    lock_required()
    index = read(target / "source-index.json")
    source = target / size / "input-trace.json"
    assert source.is_file(), "先完成正式主游戏并保留原输入"
    assert sources() == index["fingerprints"], "独立回放须使用正式对局的冻结源"
    destination = target / size / f"{replay_id}.json"
    assert not destination.exists(), "原回放结果拒绝覆盖"
    return engine(target / size, replay_id, ["--headless", "--script", PREFIX + "replay.gd", "--",
                  "--ex-select-out=" + str(destination), "--ex-select-trace=" + str(source),
                  "--ex-select-index=" + str(target / "source-index.json")], index["fingerprints"], 300)


def audit_shared(target: Path, sizes: list[str], replay_id: str, audit_id: str | None = None) -> dict:
    from PIL import Image
    errors: list[str] = []

    def need(ok, label):
        if not ok and len(errors) < 100:
            errors.append(label)

    index = read(target / "source-index.json")
    plan = read(target / "plan.json")
    need(sources() == index["fingerprints"], "当前运行代码和资源不再等于本轮冻结源")
    need(sha(target / "plan.json") == index["plan"]["sha256"], "正式对局原计划发生改变")
    need(not any(path.suffix.lower() in {".mp4", ".avi", ".mov", ".webm"} for path in target.rglob("*")), "本轮出现视频")
    summaries = []
    for size in sizes:
        directory = target / size
        events = read(directory / "events.json")
        trace = read(directory / "input-trace.json")
        independent = read(directory / f"{replay_id}.json")
        need(not events["errors"] and all(events["checks"].values()), size + "正式流程存在失败")
        need(trace["sources_before"] == trace["sources_after"] == events["sources_before"] == events["sources_after"] == index["fingerprints"], size + "正式主游戏期间源变化")
        need(independent["passed"] and not independent["errors"] and independent["trace_sha256"] == sha(directory / "input-trace.json"), size + "独立原输入回放失败")
        need(independent["sources_before"] == independent["sources_after"] == index["fingerprints"] and independent["sample_called"] is False, size + "独立回放源或不重跑AI约束失败")
        need(trace["plan"] == plan, size + "计划改变")
        need(len(trace["groups"]) == 2 * len(plan["cases"]), size + "完整对局或再战缺组")
        need(events["window"] == list(map(int, size.split("x"))), size + "实际窗口尺寸不符")
        final_cursor = 0
        groups = []
        for group in trace["groups"]:
            label = size + "/" + group["id"]
            rows = trace["rows"][group["first_row"]:group["last_row"]]
            need(group["first_row"] == final_cursor and rows, label + "原输入流不连续或为空")
            final_cursor = group["last_row"]
            need(group["intro_at_reset"] == 75 and group["initial_tick"] == 0, label + "未走正式登场/默认初态")
            need(not any(group[key] for key in ["training", "review", "demo", "direct_battle"]), label + "存在训练/试制/直开绕行")
            need(group["local"] == (group["mode"] == "local"), label + "CPU/本地模式不符")
            initial = group["initial_snapshot"]
            need(initial[0] == 0 and initial[1] == 5400 and initial[2] == 0 and initial[3] is False and initial[4] == -1 and not initial[5], label + "正式默认计时/胜负/弹体不符")
            for player, fighter in enumerate(initial[6:8]):
                need(fighter[1] == [470, 750][player] and fighter[2] == 0 and fighter[10]["hp"] == 1000 and fighter[10]["energy"] == 0 and fighter[10]["stamina"] == 1000, label + "默认站位/HP/能量/体力被改")
            previous_hash = group["initial_hash"]
            for offset, row in enumerate(rows):
                need(row["group"] == group["index"] and row["pre_hash"] == previous_hash and row["snapshot"][0] == offset + 1, label + "逐tick状态链断裂")
                previous_hash = row["post_hash"]
                need(row["inputs"][0] == row["routed_players"][0] and (group["mode"] != "local" or row["inputs"][1] == row["routed_players"][1]), label + "真实路由输入不符")
                need(row["cpu_second_original"] == (group["mode"] == "cpu"), label + "CPU输入来源标签不符")
                for player, intended in enumerate(row["intended_players"]):
                    expected = list(intended)
                    # 2P默认Up同时绑定方向上与跳；保留正式键盘语义。
                    if player == 1 and (expected[1] > 0 or expected[2] & 512):
                        expected[1] = 1
                        expected[2] |= 512
                    need(expected == row["routed_players"][player], label + "物理键盘产物偏离所请求InputFrame")
            need(previous_hash == group.get("final_hash"), label + "最终状态链不符")
            if group["complete_required"]:
                need(group["finished"] and group["remaining"] > 0 and min(f["stats"]["hp"] for f in rows[-1]["pair"]) <= 0, label + "未自然KO")
                need(group["result_panel_visible"] and group["ending_tick"] >= 90, label + "结算未真实显示")
                original = read(Path(group["recorder_file"]))
                need(sha(Path(group["recorder_file"])) == group["recorder_sha256"], label + "原产品回放字节改变")
                need(original["format"] == 6 and original["frames"] == [row["inputs"] for row in rows] and original["final_hash"] == group["final_hash"], label + "产品原回放不含完整双方输入")
                need(group.get("f4", {}).get("verified_ticks") == len(rows) and group.get("f4", {}).get("cpu_resampled") is False, label + "实际F4未全长原输入核验")
                if group["mode"] == "cpu":
                    need(original["ai_difficulty"] == "normal" and group["cpu_actions"] and group["cpu_last_tick"] == len(rows) - 1, label + "未实际消费现行普通CPU")
            else:
                need(len(rows) >= 180 or group["finished"], label + "再战没有接受实际新输入")
            matched = [entry for entry in independent["groups"] if entry["id"] == group["id"]]
            need(len(matched) == 1 and matched[0]["verified_ticks"] == len(rows) and matched[0]["final_hash"] == group.get("final_hash"), label + "独立回放未覆盖本组")
            groups.append(dict(id=group["id"], ticks=len(rows), complete=group["complete_required"], winner=group.get("winner"), final_hash=group.get("final_hash")))
        need(final_cursor == len(trace["rows"]), size + "存在未归组的原输入")
        for picture in trace["stills"]:
            path = Path(picture["file"])
            need(path.resolve().is_relative_to(directory.resolve()) and path.is_file(), size + "JPG来源越界或缺失")
            with Image.open(path) as opened:
                need(opened.format == "JPEG" and opened.width <= 768 and path.stat().st_size <= 150 * 1024 and picture["quality"] == 80, size + "JPG格式/尺寸/体积不符")
        for label in ["main-game", replay_id]:
            need(read(directory / f"{label}-exit.json")["ok"], size + "/" + label + "引擎/警告/源冻结失败")
        summaries.append(dict(size=size, groups=groups, original_ticks=len(trace["rows"]), trace_sha256=sha(directory / "input-trace.json"),
                              independent_replay_sha256=sha(directory / f"{replay_id}.json"), stills=len(trace["stills"])))
    restored = read(target / "user-data-restoration.json")
    need(restored["restored_exact_bytes"] and all(row["restored_exact_bytes"] for row in restored["files"]), "原偏好/上次回放未逐字节恢复")
    destination = target / audit_id if audit_id else target
    result = dict(schema="ufeneo.ex.direct-selection.validation.v1", errors=errors, passed=not errors, runs=summaries,
                  original_user_data_restored=True, generated_videos=0, hardware_keyboard_tested=False,
                  acceptance_responsibility="root_delegated_by_user", visual_and_listening_acceptance="待根按实际JPG和本人声音证据审阅；逻辑通过不替代画面或听审")
    save(destination / "validation.json", result)
    assert not errors, "原证据保留，另开版本修正：" + "; ".join(errors[:8])
    print("正式主流程、默认自然KO、实际F4和独立原输入回放一致；原偏好与上次回放已恢复，零视频。", flush=True)
    return result



def audit(target: Path, sizes: list[str], replay_id: str, audit_id: str | None = None) -> dict:
    common = audit_shared(target,sizes,replay_id,audit_id)
    errors = []
    for size in sizes:
        directory=target / size
        trace=read(directory / "input-trace.json")
        events=read(directory / "events.json")
        for group in trace["groups"]:
            for index,identity in enumerate(group["fighters"]):
                if identity in ["ex_gomora","ex_red_king"]:
                    if group["initial_snapshot"][6+index][0]!=identity:errors.append(size+"/"+group["id"]+" 未以EX默认身份进入")
            if group["complete_required"]:
                if not group.get("f4",{}).get("enter_opened"):errors.append(size+"/"+group["id"]+" F4后Enter菜单缺")
                original=read(Path(group["recorder_file"]))
                if original["fighters"]!=group["fighters"]:errors.append(size+"/"+group["id"]+" 产品回放未记EX身份")
                endings=[row for row in trace["terminal_rows"] if row["group"]==group["index"]]
                if not endings:errors.append(size+"/"+group["id"]+" 终局身份实际证据缺")
                if any(row["core_ids"]!=group["fighters"] or row["display_ids"]!=group["fighters"] or row["core_forms"]!=row["display_forms"] for row in endings):errors.append(size+"/"+group["id"]+" KO/结算误还原身份")
            elif group.get("restart_input")!="KEY_R":errors.append(size+"/"+group["id"]+" 没有真实R再战")
        exits=[row for row in events["events"] if row["kind"]=="ex_page_exit_cleanup"]
        if len(exits)!=len(trace["plan"]["cases"]) or not all(row["clean"] for row in exits):errors.append(size+" 页面退出未清理副本/声音")
    result=dict(schema="ufeneo.ex.direct-selection.identity-validation.v1",errors=errors,passed=common["passed"] and not errors,
        common_validation="validation.json",generated_videos=0,hardware_keyboard_tested=False,acceptance_responsibility="root_delegated_by_user")
    save((target / audit_id if audit_id else target) / "ex-identity-validation.json",result)
    assert not errors, "EX身份/生命周期失败，原证据保留："+"; ".join(errors[:8])
    return result


def run(args) -> None:
    lock_required()
    preparation = preflight(require_unlocked=True)
    target = REPORT / args.run_id
    target.mkdir(parents=True, exist_ok=False)
    selected_cases = [item for item in CASES if item["id"] in args.cases]
    plan = dict(schema="ufeneo.ex.direct-selection.plan.v1", cases=selected_cases, max_ticks=6000,
                generated_videos=0, normal_start=True, staged_simulation=False, modify_ai=False,
                input_policy="验收玩家仅用真实物理键，经正式InputRouter进入game_app；CPU原输入只从产品recorder读取")
    save(target / "plan.json", plan)
    preparation["plan"] = dict(path=relative(target / "plan.json"), sha256=sha(target / "plan.json"))
    save(target / "source-index.json", preparation)
    frozen = preparation["fingerprints"]
    if not engine(target, "import", ["--headless", "--editor", "--import", "--quit"], frozen, 360):
        raise SystemExit(1)
    user_data, original = preserve_user_data(target)
    succeeded = True
    try:
        user_data.mkdir(parents=True, exist_ok=True)
        fixture = dict(sfx=0.6, voice=0.7, music=0.65, fullscreen=False, ai_difficulty="normal",
                       key_bindings={}, joy_bindings={}, ex_select_unrelated_sentinel="保留其它偏好字段")
        (user_data / "settings.json").write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
        for size in args.sizes:
            directory = target / size
            directory.mkdir(exist_ok=False)
            options = ["--script", PREFIX + "entry.gd", "--rendering-method", "gl_compatibility", "--rendering-driver", "opengl3",
                       "--fixed-fps", "60", "--max-fps", str(args.max_fps), "--resolution", size, "--disable-vsync", "--",
                       "--ex-select-out=" + str(directory), "--ex-select-index=" + str(target / "source-index.json"),
                       "--ex-select-plan=" + str(target / "plan.json"), "--ex-select-size=" + size]
            if not engine(directory, "main-game", options, frozen, args.timeout):
                succeeded = False
                break
            settings = read(user_data / "settings.json")
            save(directory / "actual-saved-settings.json", settings)
            assert settings["ex_select_unrelated_sentinel"] == fixture["ex_select_unrelated_sentinel"]
            assert settings["key_bindings"] == {} and settings["joy_bindings"] == {} and settings["ai_difficulty"] == "normal"
            if not replay(target, size, args.replay_id):
                succeeded = False
                break
    finally:
        restore_user_data(target, user_data, original)
        save(target / "source-after.json", sources())
    if not succeeded:
        raise SystemExit(1)
    audit(target, args.sizes, args.replay_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "run", "replay", "audit", "parse"])
    parser.add_argument("--run-id", default="runtime-v1", type=valid_id)
    parser.add_argument("--audit-id", type=valid_id)
    parser.add_argument("--replay-id", default="original-replay", type=valid_id)
    parser.add_argument("--sizes", nargs="+", choices=["1280x720", "1920x1080"], default=["1280x720", "1920x1080"])
    parser.add_argument("--cases", nargs="+", choices=[item["id"] for item in CASES], default=[item["id"] for item in CASES])
    parser.add_argument("--require-unlocked", action="store_true")
    parser.add_argument("--max-fps", type=int, default=60)
    parser.add_argument("--timeout", type=int, default=1500)
    args = parser.parse_args()
    assert 30 <= args.max_fps <= 240 and args.timeout >= 60
    target = REPORT / args.run_id
    if args.command == "check":
        result = preflight(args.require_unlocked)
        print(json.dumps(dict(gate=result["gate"], frozen_source_count=len(result["fingerprints"]), cases=result["cases"],
                              generated_videos=0, godot_started=False), ensure_ascii=False, indent=2))
    elif args.command == "run":
        run(args)
    elif args.command == "replay":
        for size in args.sizes:
            if not replay(target, size, args.replay_id): raise SystemExit(1)
    elif args.command == "audit":
        audit(target, args.sizes, args.replay_id, args.audit_id)
    else:
        lock_required()
        target.mkdir(parents=True, exist_ok=False)
        frozen = sources()
        passed = True
        for name in ["entry", "game", "driver", "replay"]:
            passed = engine(target, "parse-" + name, ["--headless", "--check-only", "--script", PREFIX + name + ".gd"], frozen, 120) and passed
        if not passed: raise SystemExit(1)


if __name__ == "__main__":
    main()
