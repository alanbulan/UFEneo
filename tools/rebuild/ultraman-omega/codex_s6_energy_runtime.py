"""欧米伽S6只读主场景/原输入工具。引擎命令必须由 tools/godot_lock.py 包装本入口。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "content/fighters/ultraman-omega"
ART = ROOT / "art/fighters/ultraman-omega/stage6/energy-finish-20261031-v1"
OUT = ROOT / "reports/review/2026-10-31/omega-s6-energy-finish-v1"
PREFIX = "res://content/fighters/ultraman-omega/codex_s6_energy_review_"
ACTIONS = ["pulse", "low_pulse", "air_pulse", "special2", "special3", "air_special"]
sys.path.insert(0, str(ROOT / "tools/rebuild/ultraman-arc"))
from codex_supers_runtime import run_engine


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def local(path):
    result = (ROOT / str(path).removeprefix("res://")).resolve()
    assert result.is_relative_to(ROOT), "路径须在工程内"
    return result


def save_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write("\n")


def ancestor_pids():
    """只读进程树；venv 启动器可以位于锁 owner 和本进程之间。"""
    parents = {}
    current = os.getpid()
    while current > 1 and current not in parents:
        result = subprocess.run(["ps", "-o", "ppid=", "-p", str(current)],
                                capture_output=True, text=True, check=False)
        try:
            parent = int(result.stdout.strip())
        except ValueError:
            break
        parents[current] = parent
        current = parent
    chain, current = set(), os.getpid()
    while current in parents and current not in chain:
        chain.add(current)
        current = parents[current]
    return chain


def lock_required():
    lock = ROOT / "art/shared/locks/godot.lock"
    assert lock.is_file(), "通过 tools/godot_lock.py -- python 本入口 调用引擎"
    owner = int(lock.read_text(encoding="utf-8").strip())
    assert owner in ancestor_pids() and owner != os.getpid(), "活着的唯一锁owner须在当前进程祖先链中；允许venv启动器中间层"


def preflight(presentation=False, profile="standard"):
    assert profile in ["standard", "air-full"]
    baseline = read(ART / "baseline-v1.json")
    logical = baseline["logical_sources"]
    assert all((ROOT / p).is_file() and sha(ROOT / p) == h for p, h in logical.items()), "core/input/moves/定义/命令须保持根冻结的原字节"
    paths = {ROOT / p for p in logical}
    paths.update([Path(__file__), ART / "baseline-v1.json", ART / "attachment-plan-v1.json", CONTENT / "codex_s6_energy_review_driver.gd",
                  CONTENT / "codex_s6_energy_review_replay.gd", ROOT / "tools/godot_lock.py",
                  ROOT / "tools/rebuild/ultraman-arc/codex_supers_runtime.py"])
    for folder in ["app", "presentation", "content/catalogs", "content/templates"]:
        paths.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix in [".gd", ".json", ".gdshader", ".tscn", ".tres"])
    for identity in ["zetton"]:
        paths.update((ROOT / "content/fighters" / identity).rglob("*.json"))
    paths.update(ROOT / p for p in ["project.godot", "content/content_database.gd", "content/states.json", "tests/review/input/review_driver.gd",
                                  "content/rules/neo.tres", "content/presentation/phase3_projectiles.json", "content/presentation/impact_effects.json"])
    if presentation:
        manifest = read(ROOT / "assets/fighters/ultraman-omega/animations/manifest.json")
        effects = read(ROOT / "content/presentation/phase3_projectiles.json")
        paths.add(ROOT / "assets/fighters/ultraman-omega/animations/manifest.json")
        paths.update(CONTENT / f"codex_s6_energy_review_{kind}.gd" for kind in ["entry", "game"])
        for action in ACTIONS:
            clip = manifest["clips"][action]
            rows = clip.get("attachments_by_frame")
            assert isinstance(rows, list) and len(rows) == len(clip["rects"]) and any(rows), action + "身体挂件尚未装入实际clip"
            plan = read(ART / "attachment-plan-v1.json")["actions"][action]
            for index, attached in enumerate(rows):
                phase = plan["effect_phase_by_body_frame"].get(str(index))
                assert len(attached) == (len(plan["layers"]) if phase is not None else 0), action + "蓄光窗口/前后层须与根plan相同"
                assert all(a["sprite"] == phase and a["anchor"] == plan["anchors"][index] for a in attached), action + "实际人物相/能量中心须与plan相同"
            paths.add(local(clip["texture"]))
            for attached in [a for row in rows for a in row]:
                assert attached["effect"] in effects
                folder = local(effects[attached["effect"]]["texture"]).parent
                paths.add(local(effects[attached["effect"]]["texture"]))
                paths.update(p for p in [folder / "effect.json", folder / "provenance.json"] if p.is_file())
            for attached in rows:
                for layer, item in zip(plan["layers"], attached):
                    clip = effects[item["effect"]]
                    z_index = item.get("z_index", 1 if item.get("behind_fighter", clip.get("behind_fighter", False)) else 3)
                    assert z_index == (1 if layer == "back" else 3), action + "前后层须与根plan相同"
        finish = effects["omega_special3_hit"]
        assert len(finish["rects"]) == 12 and "hit_finish" in finish["texture"], "三级实际命中ID须指向4+8相hit_finish"
        paths.add(local(finish["texture"]))
        paths.update(p for p in [local(finish["texture"]).with_name("effect.json"), local(finish["texture"]).with_name("provenance.json")] if p.is_file())
        paths.add(ART / "attachment-plan-v1.json")
    fingerprints = {rel(p): sha(p) for p in sorted(paths)}
    return {"schema": 1, "observer_profile": profile, "logical_sources": logical, "fingerprints": fingerprints, "generated_videos": 0,
            "scope": "同一真实输入控制器；模拟字节冻结。只读manifest挂件/实际节点及命中粒子消费，测试不代替美术、听审或用户验收。"}


def logic_summary(data):
    errors, summaries = [], []
    rows, cases = data["trace"], data["cases"]

    def need(ok, label):
        if not ok and len(errors) < 40:
            errors.append(label)

    profile = data.get("observer_profile", "standard")
    need(profile in ["standard", "air-full"], "实际观察profile非法")
    if profile == "air-full":
        expected = [{"action": "air_special", "case": "whiff", "facing": facing, "gap": 800, "first": part * 320, "span": 320}
                    for part, facing in enumerate([1, -1])]
        need(cases == expected and len(rows) == 640, "补充全相必须为双向远空原输入，原44组不变")
    else:
        need(len(cases) == 44 and len(rows) == 15360, "六招双向真实输入与生命周期分组须完整")
    for part, item in enumerate(cases):
        group = rows[item["first"]:item["first"] + item["span"]]
        tag = f"{part}/{item['action']}/{item['case']}/{item['facing']}/"
        need(len(group) == item["span"], tag + "长度")
        stepped = [r for r in group if r["stepped"]]
        contacts = [e for r in stepped for e in r["events"] if e.get("player") == 0 and e.get("move") == item["action"] and e["kind"] in ["hit", "block"]]
        hits = [e for e in contacts if e["kind"] == "hit"]
        blocks = [e for e in contacts if e["kind"] == "block"]
        shown = [r for r in group if r["pair"][0]["move"] == item["action"]]
        need(bool(shown), tag + "实际招式未启动")
        casts = group[-1]["casts"]
        need(bool(casts), tag + "真实按键未送出")
        if item["case"] != "ko":
            need(len(casts) == 1, tag + "只送一次本招输入")
        if item["case"] == "hit":
            need(bool(hits) and not blocks, tag + "须自然命中")
        if item["case"] == "guard":
            need(bool(blocks) and not hits, tag + "须真实防御")
        if item["case"] == "whiff":
            need(not contacts, tag + "远空不得接触")
        if profile == "air-full":
            need({int(r["pair"][0]["sprite"]) for r in shown} == set(range(8)), tag + "空中必杀人物0至7相须完整自然显示")
            if casts:
                cast = group[int(casts[0])]
                need(2 <= int(casts[0]) - int(cast["jump_age"]) <= 6 and cast["pair"][0]["height"] > 0
                     and cast["pair"][0]["vy"] > 0, tag + "补充P必须来自真实起跳后的上升阶段")
        if item["case"] == "interrupt":
            incoming = [e for r in stepped for e in r["events"] if e.get("player") == 1 and e["kind"] == "hit"]
            need(bool(incoming) and group[-1]["pair"][0]["hp"] < 1000, tag + "真实受击夹具没有命中")
        if item["case"] == "freeze_switch":
            phases = {int(p) for p in read(ART / "attachment-plan-v1.json")["actions"][item["action"]]["effect_phase_by_body_frame"]}
            frozen = [r for r in group if r["pre_hitstop"] > 0 and r["pair"][0]["move"] == item["action"] and r["pair"][0]["sprite"] in phases]
            need(bool(frozen), tag + "前发短束的真实hitstop须落在plan非空身体蓄光相")
            need(any(r["pair"][0]["move"] == "light1" for r in group), tag + "完整收招后的真实J未出现")
        if item["case"] == "ko":
            ended = [r for r in group if r["finished"]]
            need(bool(ended) and group[-1]["pair"][1]["hp"] == 0, tag + "自然多次蓄能未形成KO")
            if ended:
                kill = [e for e in ended[0]["events"] if e.get("player") == 0 and e["kind"] == "hit"]
                need(any(e.get("move") == "special3" and e.get("projectile") for e in kill), tag + "KO须来自最终束真实接触")
                need(all(not r["stepped"] and not r["inputs"] for r in ended[1:]), tag + "KO后不得继续step或伪造输入")
                need(len(ended) >= 48, tag + "KO后呈现观察过短")
        summaries.append(dict(item, casts=casts, hits=len(hits), blocks=len(blocks), final_hp=[p["hp"] for p in group[-1]["pair"]],
                              body_phases=sorted({r["pair"][0]["sprite"] for r in shown})))
    return errors, summaries


def baseline_run(run_id, profile):
    lock_required()
    directory = OUT / run_id
    preparation = preflight(profile=profile)
    directory.mkdir(parents=True, exist_ok=False)
    save_new(directory / "source-index.json", preparation)
    target = directory / "simulation-baseline.json"
    run_engine(directory, "baseline", ["--headless", "--script", PREFIX + "replay.gd", "--",
               "--omega-s6-energy-mode=baseline", "--omega-s6-energy-output=" + str(target),
               "--omega-s6-energy-profile=" + profile,
               "--omega-s6-energy-source-index=" + str(directory / "source-index.json")])
    data = read(target)
    errors, summaries = logic_summary(data)
    errors += data["errors"]
    if preflight(profile=profile)["fingerprints"] != preparation["fingerprints"]:
        errors.append("基线引擎期间源变化")
    save_new(directory / "baseline-validation.json", {"observer_profile": profile, "errors": errors, "groups": summaries, "trace_sha256": sha(target),
             "generated_videos": 0, "runtime_presentation_tested": False, "user_approved": False})
    assert not errors, "原基线与失败保留；修夹具后另开版本，不改产品或放宽断言：" + "; ".join(errors[:6])
    print("S6安装前真实输入模拟基线已冻结；身体挂件及终结尚未运行。", flush=True)


def effect_durations(clip):
    value = clip.get("clip", {}).get("ticks", clip.get("ticks", 4))
    return [max(1, int(value[i] if isinstance(value, list) and i < len(value) else 4 if isinstance(value, list) else value))
            for i in range(len(clip["rects"]))]


def effect_phase(clip, age):
    durations = effect_durations(clip)
    remaining = max(0, min(int(age), sum(durations) - 1))
    for index, duration in enumerate(durations):
        if remaining < duration:
            return index
        remaining -= duration
    return len(durations) - 1


def effect_node(node, clip, phase, position, facing, need, tag, attachment=None):
    phase = int(phase)
    need(0 <= phase < len(clip["rects"]), tag + "实际特效相越界")
    if not 0 <= phase < len(clip["rects"]):
        return
    rect = clip["rects"][phase]
    pivot = clip.get("anchor", [rect[2] / 2, rect[3] / 2])
    half = [rect[2] / 2, rect[3] / 2] if node["centered"] else [0, 0]
    offset = [half[0] + (-pivot[0] if facing >= 0 else pivot[0] - rect[2]), half[1] - pivot[1]]
    scale = clip.get("display_scale", [clip.get("visual_scale", 1)] * 2)
    extra = (attachment or {}).get("display_scale", [(attachment or {}).get("visual_scale", 1)] * 2)
    need(node["visible"] and node["texture"] == clip["texture"] and node["region"] == rect, tag + "实际节点图集/相不符")
    need(node["alpha"] > 0, tag + "实际节点透明不可见")
    need(node["offset"] == offset and node["scale"] == [scale[0] * extra[0], scale[1] * extra[1]], tag + "实际节点原生锚点/比例不符")
    need(node["position"] == position and node["flip_h"] == (facing < 0) and node["rotation"] == 0, tag + "实际节点位置/朝向/旋转不符")


def presentation_summary(data, effects, manifest):
    errors, summaries = [], []
    moves = {a: read(CONTENT / f"moves/{a}.json") for a in ACTIONS}
    light_path = CONTENT / "moves/light1.json"
    moves["light1"] = read(light_path if light_path.is_file() else ROOT / "content/templates/humanoid/moves/light1.json")
    state_frames = read(CONTENT / "state_frames.json")
    assert not any(f.get("attachments") for frames in state_frames.values() if isinstance(frames, list) for f in frames), "状态帧新增挂件须单独明确读取规则"
    body_textures = {effects[a["effect"]]["texture"] for identity in ACTIONS
                     for row in manifest["clips"][identity]["attachments_by_frame"] for a in row}
    finish = effects["omega_special3_hit"]
    lifetime = sum(effect_durations(finish))

    def need(ok, label):
        if not ok and len(errors) < 60:
            errors.append(label)

    for part, item in enumerate(data["cases"]):
        rows = data["trace"][item["first"]:item["first"] + item["span"]]
        tag = f"{part}/{item['action']}/{item['case']}/{item['facing']}/"
        previous, previous_packet = None, None
        seen_particles, pending_removed = {}, set()
        body_seen, frozen_body = set(), []
        planned_body = {int(p) for p in read(ART / "attachment-plan-v1.json")["actions"][item["action"]]["effect_phase_by_body_frame"]}
        trigger_count = 0
        initial_fingerprint = rows[0].get("fingerprint")
        for row in rows:
            label = tag + str(row["age"]) + "/"
            packet = data["views"][row["view"]]
            own = row["pair"][0]
            animation = packet["animation"]
            identity, index = animation.get("key", ""), int(animation.get("index", -1))
            need(row["observer_pure"] and not row["main_paused"], label + "只读观察或主场景时钟不符")
            need(bool(packet["root"]) and bool(packet["view"]) and bool(packet["feedback"]), label + "必须来自实际主场景")
            need(not packet["feedback_orphans"], label + "命中粒子有未登记的实际残留节点")
            if own["move"] in ACTIONS:
                clip = manifest["clips"][own["move"]]
                raw = int(own["move_tick"])
                need(identity == own["move"] and index == int(moves[own["move"]]["frames"][raw]["sprite"]), label + "实际_animation与模拟人物相不符")
                body = packet["body"]
                pivot = clip["anchors"][index] if "anchors" in clip else [int(clip["cell"]) // 2, int(clip["anchor_y"])]
                need(body["texture"] == clip["texture"] and body["region"] == clip["rects"][index] and body["visible"], label + "实际完整人物图集不符")
                need(body["offset"] == [-v for v in pivot] and body["scale"] == [1, 1] and body["rotation"] == 0
                     and body["flip_h"] == (own["facing"] < 0), label + "实际完整人物比例/锚点/朝向不符")
                need(body["position"] == [own["x"] - packet["camera"][0] + 320, 304 - own["height"] + packet["camera"][1]],
                     label + "实际完整人物世界根点不符")
            visual = manifest["clips"].get(identity, {}).get("attachments_by_frame", [])
            expected_visual = visual[index] if 0 <= index < len(visual) else []
            need(animation.get("attachments", []) == expected_visual, label + "实际clip/相索引未消费manifest身体挂件")
            old = moves.get(own["move"], {}).get("frames", [])
            original = old[int(own["move_tick"])].get("attachments", []) if old else []
            original = [a for a in original if "sprite_range" not in a or a["sprite_range"][0] <= own["sprite"] <= a["sprite_range"][1]]
            expected = original + expected_visual
            need(packet["active_attachments"] == expected, label + "实际挂件没有只读合并原帧和清单")
            nodes = packet["attached_nodes"]
            need(len(nodes) == len(expected), label + "真实挂件节点数量/清理不符")
            for slot, (attachment, node) in enumerate(zip(expected, nodes)):
                need(node["slot"] == slot, label + "实际挂件槽位不符")
                clip = effects[attachment["effect"]]
                position = [own["x"] + own["facing"] * attachment["anchor"][0] - packet["camera"][0] + 320,
                            304 - own["height"] - attachment["anchor"][1] + packet["camera"][1]]
                effect_node(node, clip, attachment["sprite"], position, int(attachment.get("facing", own["facing"])), need, label, attachment)
                expected_z = attachment.get("z_index", 1 if attachment.get("behind_fighter", clip.get("behind_fighter", False)) else 3)
                need(node["z_index"] == expected_z, label + "身体/原始挂件前后层不符")
                if node["texture"] in body_textures:
                    body_seen.add((identity, index))
            if not expected_visual:
                need(not any(n["texture"] in body_textures for n in nodes), label + "受击/切招/仪式或非能量相有身体挂件残留")
            if previous is not None and row["pre_hitstop"] > 0 and expected_visual:
                before = previous_packet["animation"]
                need(animation.get("index") == before.get("index") and animation.get("attachments", []) == before.get("attachments", []),
                     label + "hitstop中身体挂件相必须冻结")
                frozen_body.append(row["frame"])
            triggers = [e for e in row["events"] if row["stepped"] and e["kind"] == "hit" and e.get("player") == 0
                        and e.get("move") == "special3" and e.get("projectile")]
            trigger_count += len(triggers)
            current = {p["node"]["path"]: p for p in packet["particles"] if p["id"] == "omega_special3_hit"}
            old_current = {} if previous_packet is None else {p["node"]["path"]: p for p in previous_packet["particles"] if p["id"] == "omega_special3_hit"}
            created = set(current) - set(old_current)
            need(len(created) == len(triggers), label + "专属12相命中/终结只能由最终束真实hit/KO触发一次")
            available_triggers = list(triggers)
            for path, particle in current.items():
                if path in created:
                    origin = next((e for e in available_triggers if [e["x"], e["height"]] == [particle["x"], particle["height"]]), None)
                    need(origin is not None and int(particle["age"]) == 0, label + "新终结节点须在真实最终束接触点从0龄开始")
                    if origin is not None:
                        available_triggers.remove(origin)
                    seen_particles[path] = {"first": row["frame"], "phases": set(), "last_age": -1, "ko": row["finished"],
                                            "x": particle["x"], "height": particle["height"],
                                            "facing": int(origin.get("effect_facing", own["facing"])) if origin is not None else int(item["facing"])}
                info = seen_particles[path]
                info["phases"].add(int(particle["phase"]))
                info["last_age"] = int(particle["age"])
                need(path not in pending_removed, label + "已清理终结节点再次出现")
                need(particle["x"] == info["x"] and particle["height"] == info["height"], label + "终结世界接触点必须保持")
                need(int(particle["phase"]) == effect_phase(finish, particle["age"]) and 0 <= particle["age"] < lifetime, label + "终结实际相/寿命时钟不符")
                position = [particle["x"] - packet["camera"][0] + 320, 304 - particle["height"] + packet["camera"][1]]
                effect_node(particle["node"], finish, particle["phase"], position, info["facing"], need, label)
                if path in old_current:
                    elapsed = int(row["present_frame"]) - int(previous["present_frame"])
                    need(elapsed > 0 and int(particle["age"]) - int(old_current[path]["age"]) == elapsed,
                         label + "命中/KO后的粒子须按实际呈现帧继续推进")
            for path in set(old_current) - set(current):
                need(seen_particles[path]["last_age"] >= lifetime - 1, label + "专属终结未演完就被清理")
                pending_removed.add(path)
            previous, previous_packet = row, packet
        need(len(seen_particles) == trigger_count, tag + "最终束事件与实际终结节点须一一对应")
        for particle in seen_particles.values():
            need(particle["phases"] == set(range(12)), tag + "原命中四相与独立终结八相必须全部实际消费")
        if item["case"] == "freeze_switch":
            need(bool(frozen_body), tag + "真实hitstop没有覆盖实际非空身体挂件")
        if item["case"] in ["hit", "guard", "whiff", "freeze_switch", "ko"]:
            need(bool(body_seen), tag + "实际主场景从未显示本招身体蓄光")
        missing_body = sorted(planned_body - {index for identity, index in body_seen if identity == item["action"]})
        if data.get("observer_profile", "standard") == "air-full":
            need(not missing_body, tag + "补充全相须实际消费plan全部身体蓄光相")
        if item["case"] == "ko":
            need(any(p["ko"] for p in seen_particles.values()), tag + "必须实际看到KO后的专属终结")
            tail = data["views"][rows[-1]["view"]]
            need(not any(p["id"] == "omega_special3_hit" for p in tail["particles"]) and not tail["active_attachments"],
                 tag + "KO仪式阶段的终结/身体挂件应自动回收")
        pictures = [p for p in data.get("stills", []) if p["section"] == part]
        if body_seen:
            need(any("-body-" in p["path"] for p in pictures), tag + "缺真实主场景身体JPG")
        summaries.append({"section": part, "action": item["action"], "case": item["case"], "facing": item["facing"],
                          "fingerprint": initial_fingerprint, "body_phases": sorted(body_seen), "frozen_body_frames": frozen_body,
                          "planned_body_phases": sorted(planned_body), "unobserved_planned_body_phases": missing_body,
                          "finish_triggers": trigger_count, "finish_nodes": len(seen_particles), "screenshots": pictures})
    return errors, summaries


def audit(runtime, audit_id=None):
    from PIL import Image
    preparation = read(runtime / "source-index.json")
    data = read(runtime / "main-trace.json")
    original = read(local(preparation["baseline"]["path"]))
    errors, logical = logic_summary(data)
    need = lambda ok, label: errors.append(label) if not ok and len(errors) < 80 else None
    need(data["sources_before"] == preparation["fingerprints"] == data["sources_after"], "主游戏期间全部源文件冻结")
    changed = {p: {"recorded": h, "current": sha(ROOT / p) if (ROOT / p).is_file() else "<absent>"}
               for p, h in preparation["fingerprints"].items() if not (ROOT / p).is_file() or sha(ROOT / p) != h}
    need(not set(changed) - {rel(Path(__file__))}, "运行后产品/输入/观察器源发生变化")
    need(preparation["baseline"]["sha256"] == sha(local(preparation["baseline"]["path"])), "安装前原输入基线变化")
    need(data.get("observer_profile", "standard") == preparation["observer_profile"] == original.get("observer_profile", "standard"), "实际主场景/安装前基线profile不符")
    need(original["cases"] == data["cases"] and len(original["trace"]) == len(data["trace"]), "实际主场景案例/长度改变")
    for row, before in zip(data["trace"], original["trace"]):
        need(all(row[k] == before[k] for k in ["inputs", "pre_hash", "hash", "events", "projectiles_sha256", "stepped"]),
             str(row["frame"]) + "/实际主场景必须直接消费原基线InputFrame并保持完整状态/事件")
    manifest = read(ROOT / "assets/fighters/ultraman-omega/animations/manifest.json")
    effects = read(ROOT / "content/presentation/phase3_projectiles.json")
    visual_errors, visual = presentation_summary(data, effects, manifest)
    errors += visual_errors
    replay = read(runtime / "actual-replay.json")
    need(replay["passed"] and not replay["errors"] and replay["trace_sha256"] == sha(runtime / "main-trace.json")
         and replay["baseline_sha256"] == preparation["baseline"]["sha256"], "主场景原InputFrame独立回放不一致")
    for label in ["import-atlas", "main-game", "actual-replay"]:
        result = read(runtime / (label + "-exit.json"))
        need(result["exit_code"] == 0 and not result["errors"], label + "引擎或脚本失败")
        warnings = [s for s in (runtime / (label + ".log")).read_text("utf-8", errors="replace").splitlines() if "WARNING:" in s]
        need(not warnings, label + "引擎有警告：" + "; ".join(warnings[:2]))
    for picture in data.get("stills", []):
        path = local(picture["path"])
        need(path.is_relative_to((runtime / "stills").resolve()) and path.is_file(), "JPG位置/文件不符")
        with Image.open(path) as opened:
            need(opened.format == "JPEG" and max(opened.size) <= 768, "单张JPG尺寸/格式不符")
    need(not any(p.suffix.lower() in [".mp4", ".avi", ".webm", ".mov"] for p in runtime.rglob("*")), "本轮不得生成视频")
    destination = runtime / audit_id if audit_id else runtime
    if audit_id:
        destination.mkdir(exist_ok=False)
    save_new(destination / "validation.json", {"observer_profile": preparation["observer_profile"], "errors": errors, "logic_groups": logical, "presentation_groups": visual,
             "trace_sha256": sha(runtime / "main-trace.json"), "trace_bytes": (runtime / "main-trace.json").stat().st_size,
             "baseline_sha256": preparation["baseline"]["sha256"], "replay_sha256": sha(runtime / "actual-replay.json"),
             "changed_validation_sources": changed, "generated_videos": 0, "playable": False,
             "art_passed": False, "listening_reviewed": False, "user_approved": False})
    assert not errors, "原证据保留，另开版本修正：" + "; ".join(errors[:8])
    print("S6实际身体挂件、最终束命中/KO终结、原输入与独立回放保持；美术/听审/用户门仍待。", flush=True)


def replay_run(runtime):
    lock_required()
    preparation = read(runtime / "source-index.json")
    run_engine(runtime, "actual-replay", ["--headless", "--script", PREFIX + "replay.gd", "--",
               "--omega-s6-energy-mode=replay", "--omega-s6-energy-output=" + str(runtime / "actual-replay.json"),
               "--omega-s6-energy-profile=" + preparation["observer_profile"],
               "--omega-s6-energy-source-index=" + str(runtime / "source-index.json"),
               "--omega-s6-energy-trace=" + str(runtime / "main-trace.json"),
               "--omega-s6-energy-baseline=" + str(local(preparation["baseline"]["path"]))])


def actual_run(run_id, baseline_id, profile):
    lock_required()
    preparation = preflight(presentation=True, profile=profile)
    baseline = OUT / baseline_id / "simulation-baseline.json"
    assert not read(OUT / baseline_id / "baseline-validation.json")["errors"], "必须先保留成功的安装前基线"
    assert read(baseline)["logical_sources"] == preparation["logical_sources"], "安装前后core/input/moves/定义/命令原字节保持"
    assert read(baseline).get("observer_profile", "standard") == profile, "实际主场景须显式消费同profile的原tape"
    preparation["baseline"] = {"path": rel(baseline), "sha256": sha(baseline)}
    preparation["fingerprints"][rel(baseline)] = sha(baseline)
    runtime = OUT / run_id
    runtime.mkdir(parents=True, exist_ok=False)
    (runtime / "stills").mkdir()
    save_new(runtime / "source-index.json", preparation)
    run_engine(runtime, "import-atlas", ["--headless", "--editor", "--import", "--quit"])
    observations = 640 if profile == "air-full" else 15360
    run_engine(runtime, "main-game", ["--script", PREFIX + "entry.gd", "--rendering-method", "gl_compatibility", "--rendering-driver", "opengl3",
               "--fixed-fps", "60", "--resolution", "1280x720", "--disable-vsync", "--quit-after", str(observations + 5), "--",
               "--review-trace=" + str(runtime / "main-trace.json"),
               "--omega-s6-energy-profile=" + profile,
               "--omega-s6-energy-source-index=" + str(runtime / "source-index.json"),
               "--omega-s6-energy-baseline=" + str(baseline),
               "--omega-s6-energy-stills-dir=" + str(runtime / "stills")])
    replay_run(runtime)
    audit(runtime)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["baseline", "check", "run", "replay", "audit"])
    parser.add_argument("--run-id", default="baseline-v1")
    parser.add_argument("--baseline-id", default="baseline-v2")
    parser.add_argument("--audit-id")
    parser.add_argument("--presentation", action="store_true")
    parser.add_argument("--profile", choices=["standard", "air-full"], default="standard")
    args = parser.parse_args()
    assert re.fullmatch("[a-z0-9][a-z0-9-]{0,63}", args.run_id)
    assert re.fullmatch("[a-z0-9][a-z0-9-]{0,63}", args.baseline_id)
    assert args.audit_id is None or re.fullmatch("[a-z0-9][a-z0-9-]{0,63}", args.audit_id)
    if args.command == "baseline":
        baseline_run(args.run_id, args.profile)
    elif args.command == "run":
        actual_run(args.run_id, args.baseline_id, args.profile)
    elif args.command == "replay":
        replay_run(OUT / args.run_id)
    elif args.command == "audit":
        audit(OUT / args.run_id, args.audit_id)
    else:
        preparation = preflight(presentation=args.presentation, profile=args.profile)
        print({"logical_sources_frozen": True, "generated_videos": 0, "source_index_sha_count": len(preparation["fingerprints"])})


if __name__ == "__main__":
    main()
