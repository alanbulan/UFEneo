"""月亮基础跳跃正式main工具；缺17张已审本人整源则拒绝freeze，当前不运行Godot。"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SHARED = ROOT / "tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1"
spec = importlib.util.spec_from_file_location("luna_jump_runtime_common_helpers", SHARED / "runtime_bundle.py")
generic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generic)
sha, read, rel, save, ref = generic.sha, generic.read, generic.rel, generic.save, generic.ref
FID = "ultraman-arc__luna"
TICKS = {"takeoff": [1, 1], "vertical_jump": [8, 7, 3, 8, 7], "flip_forward": [8, 8, 8, 9], "flip_back": [8, 8, 8, 9], "land": [2, 2]}
STATE_KEYS = {"takeoff": "takeoff", "vertical_jump": "vertical_air", "flip_forward": "diagonal_air", "flip_back": "backward_air", "land": "land"}
STARTS = [60, 150, 240]
DEFAULT_ENGINE = Path("F:/Games/Steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe")


def safe_report(path):
    path = path.resolve()
    top = ROOT / "reports/review/2026-11-02"
    relative = path.relative_to(top)
    assert relative.parts[0].startswith("luna-jump-resume-")
    return path


def make_state_frames(rows):
    frames = []
    for row in rows:
        with Image.open(ROOT / row["image"]) as picture:
            assert picture.size == (320, 320) and picture.mode == "RGBA"
            alpha = np.asarray(picture)[:, :, 3]
            assert set(np.unique(alpha)) == {0, 255}
            mask = alpha >= 128
            assert not mask[0, :].any() and not mask[-1, :].any() and not mask[:, 0].any() and not mask[:, -1].any()
        yy, _ = np.where(mask)
        top, bottom = int(yy.min()), int(yy.max()) + 1
        hurt = []
        for band in range(3):
            y0, y1 = top + (bottom - top) * band // 3, top + (bottom - top) * (band + 1) // 3
            _, xx = np.where(mask[y0:y1])
            if len(xx):
                hurt.append([int(xx.min()) - 160, 280 - y1, int(xx.max() - xx.min() + 1), y1 - y0])
        for _ in range(row["ticks"]):
            frames.append(dict(sprite=row["phase"], dx=0, dy=0, hitboxes=[], hurtboxes=copy.deepcopy(hurt), cancel=[], events=[]))
    return frames


def assemble(manifest_path, review_path, engine):
    # JSON只是最终处理包的接口；当前没有manifest或候选假图来填这个入口。
    assert manifest_path.is_file() and review_path.is_file() and engine.is_file()
    manifest, review = read(manifest_path), read(review_path)
    assert manifest["schema"] == "ufeneo.arc-luna.s2.jump-whole-registered.v1" and manifest["fighter"] == FID
    assert set(manifest["actions"]) == set(TICKS)
    assert review["reviewer"] == "root_delegated_by_user" and review["accepted_for_formal_main_candidate"] is True
    assert review["manifest"] == {"path": rel(manifest_path), "sha256": sha(manifest_path)} and review["actual_complete_views"]
    resources = {manifest_path, review_path}
    for viewed in review["actual_complete_views"]:
        path = ROOT / viewed["path"]
        assert sha(path) == viewed["sha256"]
        with Image.open(path) as image:
            assert image.format == "JPEG" and image.width <= 768 and path.stat().st_size <= 150000
        resources.add(path)
    reg_path = ROOT / manifest["registration_contract"]["path"]
    assert sha(reg_path) == manifest["registration_contract"]["sha256"]
    registration = read(reg_path)
    assert registration["root_all_sources_terminal_and_processing_permission_received"] is True
    assert registration["common_full_source_raster"] == [159, 159] and registration["runtime_root"] == [160, 280]
    assert registration["per_phase_scale_or_area_fitting"] is False and registration["air_lowest_boot_is_not_ground"] is True
    resources.add(reg_path)
    for name, digest in registration["frozen_inputs"].items():
        path = ROOT / name
        assert sha(path) == digest
        resources.add(path)
    clips, states, sources, native_hashes = {}, {}, [], []
    for action, ticks in TICKS.items():
        group = manifest["actions"][action]
        rows = group["frames"]
        assert [row["phase"] for row in rows] == list(range(len(ticks)))
        assert [row["ticks"] for row in rows] == ticks
        clip_path = ROOT / group["clip"]["path"]
        assert sha(clip_path) == group["clip"]["sha256"]
        clip = read(clip_path)
        atlas = Path(clip["texture"])
        assert atlas.is_absolute() and atlas.is_relative_to(ROOT / "art/fighters" / FID)
        assert sha(atlas) == clip["atlas_sha256"]
        assert clip["source_fighter"] == FID and clip["ticks"] == ticks and clip["loop"] is False
        assert clip["cell"] == 320 and clip["anchors"] == [[160, 280]] * len(ticks)
        assert len(clip["rects"]) == len(ticks) and clip.get("simulation_sprite_offset", 0) == 0
        if action in ["vertical_jump", "flip_forward", "flip_back"]:
            assert clip["trajectory_driven"] is True
        resources.update([clip_path, atlas])
        for row in rows:
            for key in ["source", "image"]:
                path = ROOT / row[key]
                path.resolve().relative_to(ROOT / "art/fighters" / FID)
                assert sha(path) == row[key + "_sha256"]
                resources.add(path)
            sources.append(row["source_sha256"])
            native_hashes.append(row["image_sha256"])
            rect = clip["rects"][row["phase"]]
            assert len(rect) == 4 and rect[2:] == [320, 320]
            with Image.open(atlas) as atlas_image, Image.open(ROOT / row["image"]) as native_image:
                assert atlas_image.convert("RGBA").crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])).tobytes() == native_image.convert("RGBA").tobytes()
        clips[action] = clip
        states[STATE_KEYS[action]] = make_state_frames(rows)
    assert len(sources) == 17 and len(set(sources)) == 17 and len(set(native_hashes)) == 17, "17个独立完整本人源不可用旧帧/镜像/复制充数"
    prior = ROOT / f"art/fighters/{FID}/stage2/movement-contract-20261101-v1"
    bundle, old_states = read(prior / "bundle.json"), read(prior / "state_frames.json")
    resources.update([prior / "bundle.json", prior / "state_frames.json"])
    for action in ["idle", "turn"]:
        folder = ROOT / f"art/fighters/{FID}/stage2/goal-closeout-20261101-v1/{action}"
        clips[action] = copy.deepcopy(bundle["clips"][action])
        atlas = folder / "atlas.png"
        assert sha(atlas) == clips[action]["atlas_sha256"]
        clips[action].update(texture=atlas.as_posix(), source_fighter=FID)
        states[action] = copy.deepcopy(old_states[action])
        resources.update([atlas, folder / "frames.json"])
        for row in read(folder / "frames.json")["frames"]:
            for key in ["source", "image"]:
                path = ROOT / row[key]
                assert sha(path) == row[key + "_sha256"]
                resources.add(path)
    flags_path = ROOT / f"content/fighters/{FID}/definition.json"
    flags = read(flags_path)
    assert all(flags[key] is False for key in ["playable", "implemented", "select_visible"])
    model = ROOT / f"art/fighters/{FID}/model/model-native.png"
    resources.update([flags_path, model, ROOT / "project.godot", ROOT / "tools/godot_lock.py", ROOT / "third_party/shoto/motion_parser.gd"])
    for name in ["core", "input", "presentation", "ui", "app", "content"]:
        resources.update(p for p in (ROOT / name).rglob("*") if p.is_file() and p.suffix.lower() in {".gd", ".gdshader", ".tscn", ".tres", ".json"})
    for folder in [HERE, SHARED]:
        resources.update(p for p in folder.iterdir() if p.is_file() and p.suffix in {".gd", ".py"})
    for name in ["assets/ui", "assets/fonts", "assets/stages", "assets/backgrounds", "assets/fighters/zetton"]:
        if (ROOT / name).is_dir():
            resources.update(p for p in (ROOT / name).rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".wav", ".ogg", ".ttf", ".otf", ".json", ".tres"})
    bound = [ref(path) for path in sorted(resources, key=rel)]
    return {"schema": "ufeneo.arc-luna.s2.jump-main-candidate.v1", "fighter": FID, "opponent": "zetton", "root_runtime_ready": True,
            "playable": False, "implemented": False, "select_visible": False, "transform_enabled": False, "jump_art_accepted": False,
            "definition": dict(id=FID, display_name="亚刻奥特曼 · 月亮装甲 · 基础跳跃候选", max_health=1000, walk_speed=2, jump_speed=16, body_radius=18, moves={}, command_table=[], state_frames=states),
            "presentation": dict(model=model.as_posix(), native=True, anchor_y=184, manifest_data=dict(fighter=FID, clips=clips)),
            "initial_positions": dict(right=dict(p1_x=360, p2_x=900), left=dict(p1_x=920, p2_x=380)),
            "input_contract": dict(length_frames=320, starts=STARTS, inputs="单tick 8、9、7对应方向InputFrame；陪练中立", post_sim_mutation=False),
            "bound_resources": bound, "source_fingerprint": generic.source_fingerprint(bound), "engine": dict(path=engine.resolve().as_posix(), sha256=sha(engine)),
            "root_native_review": ref(review_path), "write_policy": dict(user_settings=False, last_replay=False, only_new_reports=True)}


def check_trace(data):
    assert not data["failures"] and len(data["trace"]) == 320
    direction = int(data["direction"])
    for episode, start in enumerate(STARTS):
        rows = data["trace"][start:start + 38]
        base_x = int(data["trace"][start - 1]["pair"][0]["x"])
        axis = [0, direction, -direction][episode]
        air = ["vertical_jump", "flip_forward", "flip_back"][episode]
        for n, row in enumerate(rows):
            f = row["pair"][0]
            assert row["movie_frame"] == start + n and row["input_relative_n"] == n and row["jump_episode"] == episode
            state = "takeoff" if n < 2 else "air" if n < 33 else "land" if n < 37 else "idle"
            assert f["state"] == state and f["state_tick"] == (n if n < 2 else n - 2 if n < 33 else n - 33 if n < 37 else 0)
            assert f["height"] == (n * (33 - n) // 2 if n < 33 else 0) and f["vy"] == (16 - n if n < 33 else 0)
            assert f["x"] == base_x + axis * 4 * min(n, 33) and f["facing"] == direction
            if n < 37:
                key = "takeoff" if n < 2 else air if n < 33 else "land"
                table = [phase for phase, count in enumerate(TICKS[key]) for _ in range(count)]
                expected = table[n if n < 33 else n - 33]
                assert f["animation"]["key"] == key and f["animation"]["index"] == expected and f["frame_sprite"] == expected
        assert [n for n, row in enumerate(rows) if row["pair"][0]["height"] == 136] == [16, 17]
        assert len([row for row in rows if row["pair"][0]["state"] == "air"]) == 31
    for row in data["trace"]:
        for f in row["pair"]:
            x, y, width, height = f["full_alpha_viewport_bounds"]
            assert x >= 0 and y >= 0 and x + width <= 640 and y + height <= 360


def execute(cfg, contract, folder, direction, size, tape=None):
    folder.mkdir()
    engine_log, stdout = folder / "engine.log", folder / "stdout-stderr.log"
    command = [cfg["engine"]["path"], "--path", str(ROOT), "--windowed", "--resolution", size, "--fixed-fps", "60", "--log-file", str(engine_log), "--script", "res://" + rel(HERE / "main_entry.gd"), "--", "--luna-s2-contract=" + contract.as_posix(), "--luna-s2-out=" + folder.as_posix(), "--luna-s2-direction=" + direction]
    if tape:
        command.append("--luna-s2-original-tape=" + tape.as_posix())
    started = time.time()
    with stdout.open("x", encoding="utf-8", newline="\n") as stream:
        result = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, timeout=120, creationflags=0x08000000 if os.name == "nt" else 0)
    save(folder / "process-exit.json", dict(command=command, exit_code=result.returncode, elapsed_seconds=round(time.time() - started, 3)))
    assert result.returncode == 0 and engine_log.is_file()
    logs = engine_log.read_text("utf-8", errors="replace") + "\n" + stdout.read_text("utf-8", errors="replace")
    diagnostics = [line for line in logs.splitlines() if any(word in line for word in ["SCRIPT ERROR:", "Parse Error:", "ERROR:", "WARNING:"])]
    save(folder / "engine-log-review.json", {"diagnostics": diagnostics})
    assert not diagnostics
    trace = read(folder / "main-trace.json")
    check_trace(trace)
    assert not read(folder / "auxiliary-fresh-sim-replay.json")["errors"]
    return trace


def run(contract, out, root_confirmed):
    assert root_confirmed, "仅根确认17源终态/最终整图签收且Godot可用后执行"
    cfg = generic.check(contract)
    assert cfg["schema"] == "ufeneo.arc-luna.s2.jump-main-candidate.v1"
    out = safe_report(out)
    assert not out.exists()
    sys.path.insert(0, str(ROOT / "tools"))
    import godot_lock
    godot_lock.acquire(timeout=60)
    try:
        out.mkdir(parents=True)
        before = generic.user_snapshot(out)
        parts, error = [], None
        try:
            for size in ["1280x720", "1920x1080"]:
                for direction in ["right", "left"]:
                    generic.check(contract)
                    original = execute(cfg, contract, out / (size + "-" + direction), direction, size)
                    replay = execute(cfg, contract, out / (size + "-" + direction + "-visible-replay"), direction, size, out / (size + "-" + direction) / "actual-input-tape.json")
                    for key in ["state_hash", "events", "projectiles", "original_inputs", "pair"]:
                        assert [row[key] for row in original["trace"]] == [row[key] for row in replay["trace"]], key
                    parts.append(dict(size=size, direction=direction, absolute_clock_and_original_replay=True))
        except BaseException as exc:
            error = repr(exc)
        finally:
            restored = generic.user_restore(out, before)
            try:
                generic.check(contract)
            except BaseException as exc:
                error = (error or "") + " source_recheck=" + repr(exc)
            save(out / "runner-result.json", dict(completed=error is None, error=error, parts=parts, user_files_exact_after_restoration=all(row["restored_exact_bytes"] for row in restored), unexpected_user_writes=any(row["unexpected_write_detected"] for row in restored), script_InputFrame_not_human_keyboard=True, no_product_install=True, art_accepted=False))
        assert error is None and not any(row["unexpected_write_detected"] for row in restored), error
    finally:
        godot_lock.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("freeze")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--root-review", type=Path, required=True)
    p.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--root-confirm-sources-stable", action="store_true")
    p = commands.add_parser("run")
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--root-confirm-sources-terminal-and-Godot-available", action="store_true", dest="confirmed")
    p = commands.add_parser("check-trace")
    p.add_argument("--trace", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        assert args.root_confirm_sources_stable
        out = safe_report(args.out)
        assert not out.exists()
        cfg = assemble(args.manifest.resolve(), args.root_review.resolve(), args.engine.resolve())
        out.mkdir(parents=True)
        save(out / "candidate-runtime.json", cfg)
        save(out / "freeze-seal.json", dict(contract=ref(out / "candidate-runtime.json"), source_fingerprint=cfg["source_fingerprint"], Godot_not_started=True, GDScript_not_yet_parsed=True))
        print(json.dumps(dict(contract=rel(out / "candidate-runtime.json"), sha256=sha(out / "candidate-runtime.json")), ensure_ascii=False))
    elif args.command == "run":
        run(args.contract.resolve(), args.out.resolve(), args.confirmed)
    else:
        check_trace(read(args.trace))
        print(json.dumps(dict(actual_trace_clock_accepted=True, trace=ref(args.trace)), ensure_ascii=False))
