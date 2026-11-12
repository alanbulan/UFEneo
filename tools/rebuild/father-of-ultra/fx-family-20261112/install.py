"""安装奥特之父专属运行时特效家族并接线本人招式。

步骤：
  1. node bake.mjs --out reports/fx_father_family（冻结烘焙，不覆盖）
  2. 逐帧核硬 Alpha、主体单连通与主体外数值，不过即停
  3. 复制 atlas / effect.json / provenance.json 到 assets/effects/father-of-ultra/
  4. 写 phase3_entries.json 与 charge_policy.json 提案（不改共享登记文件）
  5. 改 content/fighters/father-of-ultra/moves/*.json 的特效引用与命中映射
  6. 写 build-report.json

用法：
  .venv/bin/python tools/rebuild/father-of-ultra/fx-family-20261112/install.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections import deque
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
BATCH = Path(__file__).resolve().parent
BAKE = BATCH / "bake.mjs"
STAGING = ROOT / "reports/fx_father_family"
DEST = ROOT / "assets/effects/father-of-ultra/fx-family-20261112-v1"
MOVES = ROOT / "content/fighters/father-of-ultra/moves"
UPSTREAM = json.loads((ROOT / "third_party/pixelfx/UPSTREAM.json").read_text(encoding="utf-8"))
LICENSE = ROOT / "third_party/pixelfx/LICENSE"
REPORT = BATCH / "build-report.json"
PHASE3_PROPOSAL = BATCH / "phase3_entries.json"
CHARGE_PROPOSAL = BATCH / "charge_policy.json"

FIGHTER = "father-of-ultra"
DATE = "2026-11-12"
REVIEW = f"{DATE} 奥父专属技能特效自绘原创像素（PixelFX 离线烘焙），待指挥目视终审"
CHARGE_REVIEW = f"{DATE} 奥父 Q 蓄气自绘原创像素（PixelFX 离线烘焙），待指挥目视终审"

SHORT = {
    "father_fx_pulse_flight": "pulse_flight",
    "father_fx_pulse_hit": "pulse_hit",
    "father_fx_beam": "beam",
    "father_fx_beam_hit": "beam_hit",
    "father_fx_arrow_flight": "arrow_flight",
    "father_fx_arrow_hit": "arrow_hit",
    "father_fx_spiral": "spiral",
    "father_fx_spiral_hit": "spiral_hit",
    "father_fx_rings": "rings",
    "father_fx_rings_hit": "rings_hit",
    "father_fx_barrier": "barrier",
    "father_fx_catch_back": "catch_back",
    "father_fx_catch_front": "catch_front",
    "father_fx_q_charge_start": "q_charge_start",
    "father_fx_q_charge": "q_charge",
    "father_fx_q_charge_stop": "q_charge_stop",
}
TICKS = {
    "father_fx_pulse_flight": 3,
    "father_fx_pulse_hit": 3,
    "father_fx_beam": 4,
    "father_fx_beam_hit": 3,
    "father_fx_arrow_flight": 3,
    "father_fx_arrow_hit": 3,
    "father_fx_spiral": 3,
    "father_fx_spiral_hit": 3,
    "father_fx_rings": 3,
    "father_fx_rings_hit": 3,
    "father_fx_barrier": 3,
    "father_fx_catch_back": 3,
    "father_fx_catch_front": 3,
    "father_fx_q_charge_start": 1,
    "father_fx_q_charge": 1,
    "father_fx_q_charge_stop": 1,
}
COLOR_PARAMETER = {"father_fx_beam": True}
FULL_FRAME = {
    "father_fx_q_charge_start": True,
    "father_fx_q_charge": True,
    "father_fx_q_charge_stop": True,
}

SHOT_EFFECTS = {
    "pulse": "father_fx_pulse_flight",
    "beam_loop": "father_fx_beam",
    "special_arrow": "father_fx_arrow_flight",
    "special_spiral": "father_fx_spiral",
    "special_rings": "father_fx_rings",
}
ATTACH_EFFECTS = {
    "special_barrier": "father_fx_barrier",
    "ultraman_catch_ring_form_back": "father_fx_catch_back",
    "ultraman_catch_ring_form_front": "father_fx_catch_front",
}
SHOT_HITS = {
    "father_fx_pulse_flight": "father_fx_pulse_hit",
    "father_fx_beam": "father_fx_beam_hit",
    "father_fx_arrow_flight": "father_fx_arrow_hit",
    "father_fx_spiral": "father_fx_spiral_hit",
    "father_fx_rings": "father_fx_rings_hit",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def detect_indent(path: Path) -> int:
    """按现文件第二层缩进判断 JSON 风格，避免整文件格式重排。"""
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        stripped = line.lstrip(" ")
        if stripped and stripped != line:
            return len(line) - len(stripped)
    return 2


def save(path: Path, data, indent=2) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8", newline="\n")


def run_bake() -> dict:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    proc = subprocess.run(["node", str(BAKE), "--out", str(STAGING.relative_to(ROOT))],
                          cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"烘焙失败：\n{proc.stdout}\n{proc.stderr}")
    print(proc.stdout.strip())
    return load(STAGING / "provenance.json")


def components(mask):
    """4 邻接连通块；返回 (标签图, 各块像素数)。"""
    import numpy as np

    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    sizes: list[int] = []
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if labels[y, x]:
            continue
        current = len(sizes) + 1
        queue = deque([(y, x)])
        labels[y, x] = current
        count = 0
        while queue:
            cy, cx = queue.popleft()
            count += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                    labels[ny, nx] = current
                    queue.append((ny, nx))
        sizes.append(count)
    return labels, sizes


def inspect_frames(atlas: Path, rects, anchor) -> tuple[list, list[dict], list[tuple]]:
    """逐帧核硬 Alpha 与主体外门，返回 frame_boxes、逐帧指标、各帧可见像素数组。"""
    import numpy as np
    from PIL import Image

    image = np.array(Image.open(atlas).convert("RGBA"))
    ax, ay = anchor
    boxes, metrics, volumes = [], [], []
    for index, (x, y, w, h) in enumerate(rects):
        alpha = image[y:y + h, x:x + w, 3]
        values = sorted(int(v) for v in np.unique(alpha))
        if not set(values) <= {0, 255}:
            raise SystemExit(f"{atlas.name} 第{index}帧非硬 Alpha：{values[:16]}")
        mask = alpha >= 200
        labels, sizes = components(mask)
        if not sizes:
            raise SystemExit(f"{atlas.name} 第{index}帧为空")
        main_size = max(sizes)
        main_index = sizes.index(main_size) + 1
        main = labels == main_index
        outside16 = int(((~main) & (alpha >= 16)).sum())
        outside200 = int(((~main) & (alpha >= 200)).sum())
        if outside16 > 100 or outside200 != 0:
            raise SystemExit(f"{atlas.name} 第{index}帧主体外违规：>=16 {outside16} / >=200 {outside200}")
        visible = np.nonzero(alpha)
        min_y, max_y = int(visible[0].min()), int(visible[0].max())
        min_x, max_x = int(visible[1].min()), int(visible[1].max())
        boxes.append([min_x - ax, min_y - ay, max_x - min_x + 1, max_y - min_y + 1])
        metrics.append({
            "frame": index,
            "alpha_values": values,
            "main_component_pixels": int(main_size),
            "outside_16": outside16,
            "outside_200": outside200,
            "bbox": boxes[-1],
        })
        volumes.append((alpha > 0))
    return boxes, metrics, volumes


def color_count(atlas: Path) -> int:
    import numpy as np
    from PIL import Image

    image = np.array(Image.open(atlas).convert("RGBA"))
    visible = image[image[..., 3] > 0][:, :3]
    return int(len({tuple(int(v) for v in c) for c in visible}))


def build_entry(export: dict, atlas: Path, dest_dir: Path, boxes, metrics) -> dict:
    effect_id = export["id"]
    entry = {
        "texture": "res://" + str(atlas.relative_to(ROOT)),
        "rects": export["rects"],
        "anchor": [int(export["AX"]), int(export["AY"])],
        "ticks": TICKS[effect_id],
        "display_scale": [1, 1],
        "behind_fighter": bool(export.get("behind", False)),
        "frame_boxes": boxes,
        "loop": bool(export.get("loop", False)),
        "color_parameter": bool(COLOR_PARAMETER.get(effect_id, False)),
        "alpha_binary": True,
        "orientation": "authored",
        "native_fan": False,
        "atlas_sha256": sha(atlas),
        "colors": color_count(atlas),
        "source_kind": "pixelfx_code_baked",
        "art_source": "pixelfx_code_baked",
        "upstream_commit": UPSTREAM["commit"],
        "license": "MIT",
        "provenance": "res://" + str((dest_dir / "provenance.json").relative_to(ROOT)),
        "dedicated_to": FIGHTER,
        "authoring_source": "res://" + str(BAKE.relative_to(ROOT)),
        "layer": export.get("kind", "flight"),
        "user_approved": False,
        "review_status": CHARGE_REVIEW if export.get("state") else REVIEW,
    }
    if FULL_FRAME.get(effect_id):
        entry["full_frame"] = True
    return entry


def write_effect_files(provenance: dict) -> tuple[dict, dict]:
    entries: dict[str, dict] = {}
    report_effects: dict[str, dict] = {}
    for export in provenance["exports"]:
        effect_id = export["id"]
        short = SHORT[effect_id]
        source_atlas = STAGING / effect_id / "atlas.png"
        dest_dir = DEST / short
        dest_dir.mkdir(parents=True, exist_ok=True)
        atlas = dest_dir / "atlas.png"
        shutil.copyfile(source_atlas, atlas)
        boxes, metrics, volumes = inspect_frames(atlas, export["rects"], [export["AX"], export["AY"]])
        changes = []
        for index in range(1, len(volumes)):
            if volumes[index].shape != volumes[index - 1].shape:
                changes.append(1.0)
                continue
            total = int(volumes[index].sum())
            changed = int((volumes[index] != volumes[index - 1]).sum())
            changes.append(changed / max(1, total))
        entry = build_entry(export, atlas, dest_dir, boxes, metrics)
        save(dest_dir / "effect.json", entry)
        prov = {
            "request": "奥父专属运行时特效家族自绘：按本人红银配色、披风与力量型光线原创像素形状，不借他人图集",
            "character": FIGHTER,
            "family": effect_id,
            "kind": export.get("kind"),
            "shape_source": "原创绘制函数 tools/rebuild/father-of-ultra/fx-family-20261112/bake.mjs",
            "reused_source_atlas_shape": False,
            "source_kind": "pixelfx_code_baked",
            "route": "offline",
            "upstream": "https://github.com/patch-gg/pixelfx/tree/" + UPSTREAM["commit"],
            "upstream_commit": UPSTREAM["commit"],
            "license": "MIT",
            "license_sha256": sha(LICENSE),
            "seed": provenance["seed"],
            "canvas": [export["W"] * export["cols"], export["H"] * ((export["n"] + export["cols"] - 1) // export["cols"])],
            "anchor": [export["AX"], export["AY"]],
            "rects": export["rects"],
            "ticks": TICKS[effect_id],
            "loop": bool(export.get("loop", False)),
            "alpha_binary": True,
            "frame_gate": metrics,
            "bridge_components": export.get("bridged", 0),
            "phase_png_sha256": export["phase_png_sha256"],
            "atlas_sha256": export["atlas_sha256"],
            "character_frames_modified": False,
            "review_status": entry["review_status"],
        }
        save(dest_dir / "provenance.json", prov)
        entries[effect_id] = entry
        report_effects[effect_id] = {
            "short": short,
            "atlas": str(atlas.relative_to(ROOT)),
            "sha256": entry["atlas_sha256"],
            "size": [int(export["W"] * export["cols"]), int(export["H"] * ((export["n"] + export["cols"] - 1) // export["cols"]))],
            "frames": export["n"],
            "rects": export["rects"],
            "anchor": entry["anchor"],
            "ticks": entry["ticks"],
            "loop": entry["loop"],
            "behind_fighter": entry["behind_fighter"],
            "colors": entry["colors"],
            "bridge_components": export.get("bridged", 0),
            "alpha_binary": True,
            "gate": "PASS",
            "frame_gate": metrics,
            "phase_change_ratio": changes,
            "source_kind": "pixelfx_code_baked",
            "license": "MIT",
            "upstream_commit": UPSTREAM["commit"],
        }
    shutil.copyfile(LICENSE, DEST / "PIXELFX-LICENSE.txt")
    return entries, report_effects


def wire_move(path: Path, changes: list[str], *, adaptation: str | None = None,
              data_source: str | None = None) -> None:
    indent = detect_indent(path)
    move = load(path)
    touched: set[str] = set()
    for frame in move.get("frames", []):
        for shot in frame.get("shots", []):
            effect = str(shot.get("effect", ""))
            if effect in SHOT_EFFECTS:
                shot["effect"] = SHOT_EFFECTS[effect]
                touched.add(shot["effect"])
                changes.append(f"{path.name}: 射击特效 {effect} -> {shot['effect']}")
        for attachment in frame.get("attachments", []):
            effect = str(attachment.get("effect", ""))
            if effect in ATTACH_EFFECTS:
                attachment["effect"] = ATTACH_EFFECTS[effect]
                changes.append(f"{path.name}: 挂件 {effect} -> {attachment['effect']}")
                if effect == "special_barrier":
                    attachment["color"] = [1, 1, 1, 1]
                    changes.append(f"{path.name}: 屏障挂件颜色改为原色 [1,1,1,1]（保留红银，不被蓝染）")
    feedback = move.setdefault("feedback", {})
    if str(feedback.get("spark", "")) == "beam_hit":
        feedback["spark"] = "father_fx_beam_hit"
        changes.append(f"{path.name}: 命中火花 beam_hit -> father_fx_beam_hit")
        touched.add("father_fx_beam")
    mapping = dict(feedback.get("projectile_impacts", {}))
    for effect in touched:
        if effect in SHOT_HITS:
            mapping[effect] = SHOT_HITS[effect]
    if mapping:
        feedback["projectile_impacts"] = mapping
        changes.append(f"{path.name}: projectile_impacts = {json.dumps(mapping, ensure_ascii=False)}")
    if adaptation is not None:
        move["adaptation"] = adaptation
        changes.append(f"{path.name}: 更新 adaptation 文案")
    if data_source is not None:
        move["data_source"] = data_source
        changes.append(f"{path.name}: 更新 data_source 文案")
    changes[:] = list(dict.fromkeys(changes))
    save(path, move, indent=indent)


def wire_moves() -> dict[str, list[str]]:
    all_changes: dict[str, list[str]] = {}

    def record(name, **kwargs):
        changes: list[str] = []
        wire_move(MOVES / f"{name}.json", changes, **kwargs)
        all_changes[f"{name}.json"] = changes

    record("pulse", data_source="游戏编排的掌推光弹；不称原剧专名。人物帧只画贴掌光点，飞行弹与命中由运行时 father_fx_pulse_flight / father_fx_pulse_hit 承载；双角与白须不发光。")
    record("low_pulse", data_source="游戏编排的低姿掌弹；不称原剧专名。人物帧只画贴掌光点；飞行弹与命中由运行时 father_fx_pulse_flight / father_fx_pulse_hit 承载；双角与白须不发光。")
    record("air_pulse", data_source="游戏编排的空中斜下掌弹；不称原剧专名。人物帧只画贴掌光点，飞行弹与命中由运行时 father_fx_pulse_flight / father_fx_pulse_hit 承载；双角与白须不发光。")
    record("special", data_source="父亲射击（Father Shot）：双臂 L 字，右臂垂直，将体内光能转为火花能量后从右臂发射；艾斯第38话击破纳玛哈盖，梦比优斯第37话击碎伽休莱因回旋镖，圆谷官方页列为特殊技。原剧光色无可靠记载，本作取暖白主束为游戏定色，不冒充原剧色值；帧序、伤害为游戏编排。人物帧只画身体，束体与命中由奥父专属 father_fx_beam / father_fx_beam_hit 承载。")
    record("special2", data_source="奥特之角（Ultra Horns）是奥特一族一次操纵大量能量的器官，力量光束（Power Beam）自双角发射；泰罗继承角的能量控制。原剧光色无可靠记载，本作取金色为游戏定色。本招是全套动作中唯一以双角为特效发射部位的招式，且有来源；其余招式不从角、须发光。帧序、伤害为游戏编排。人物帧只画身体，束体与命中由奥父专属 father_fx_beam / father_fx_beam_hit 承载。")
    record("air_special", adaptation="游戏改编的空中父亲射击；人物帧只画身体，束体与命中由运行时 father_fx_beam / father_fx_beam_hit 承载，不在人物帧烘焙光束。不声称原剧有此空中发射镜头。")
    record("motion_236")
    record("ranged_forward", data_source="月牙射击（Crescent Shot）：从指尖/手掌发出三日月状光弹，对希波利特星人造成伤害；本作以父亲专属 father_fx_arrow_flight / father_fx_arrow_hit 承载红银月牙弹与命中，弹形、帧序与伤害为游戏改编。原剧光色未见可靠记载。")
    record("motion_623")
    record("motion_22")
    record("motion_214")
    return all_changes


def write_proposals(entries: dict) -> None:
    save(PHASE3_PROPOSAL, entries)
    placements = {
        state: {
            "effect": f"father_fx_q_{state}",
            "anchor": [0, 0],
            "color": [1, 1, 1, 1],
            "behind_fighter": True,
            "frames": 9 if state != "charge" else 24,
            "loop": state == "charge",
        }
        for state in ("charge_start", "charge", "charge_stop")
    }
    proposal = {
        "schema": 1,
        "status": "proposal_for_root_merge",
        "character": FIGHTER,
        "merge_into": "content/presentation/charge_overlay_policy.json",
        "placements": {FIGHTER: placements},
        "charge_only_effects": [
            "father_fx_q_charge_start",
            "father_fx_q_charge",
            "father_fx_q_charge_stop",
        ],
        "effects_already_registered_by_root": False,
        "integration_note": (
            "现 father-of-ultra 的 charge_start/charge/charge_stop 状态帧没有 attachments。"
            "UfeChargeEffectPolicy.filter 只替换已存在的受限附件，因此根会话除了合并本 placements，"
            "还需在三个蓄气状态帧各挂一个 charge_aura（sprite 0，anchor [0,-96]，颜色自定，"
            "与 zoffy/gaia 等已装角色同口径）才能让本家族蓄气图显示；"
            "本次任务只允许改 moves/*.json，故未改 state_frames。"
        ),
        "basis": (
            "不使用通用 charge_aura 形状：三态为本角色独立红银披风焰整帧（9/24/9，384×256，脚底锚 [192,246]），"
            "只在真实 Q 起势/保持/收势出现，符合专项特效家族要求。"
        ),
    }
    save(CHARGE_PROPOSAL, proposal)


def main() -> None:
    provenance = run_bake()
    entries, report_effects = write_effect_files(provenance)
    write_proposals(entries)
    move_changes = wire_moves()
    report = {
        "schema": "ufeneo.pixelfx.father-fx-family.report.v1",
        "generated": DATE,
        "character": FIGHTER,
        "upstream": "https://github.com/patch-gg/pixelfx/tree/" + UPSTREAM["commit"],
        "upstream_commit": UPSTREAM["commit"],
        "license": "MIT",
        "license_file": "third_party/pixelfx/LICENSE",
        "license_sha256": sha(LICENSE),
        "bake_source": "tools/rebuild/father-of-ultra/fx-family-20261112/bake.mjs",
        "install_source": "tools/rebuild/father-of-ultra/fx-family-20261112/install.py",
        "alpha_policy": "硬 Alpha：仅 0/255；主体=alpha>=200 最大 4 连通块；主体外 alpha>=16 必须 0（门限 <=100）、alpha>=200 必须 0",
        "gate": "PASS",
        "effects": report_effects,
        "move_changes": move_changes,
        "proposals": {
            "phase3_entries": str(PHASE3_PROPOSAL.relative_to(ROOT)),
            "charge_policy": str(CHARGE_PROPOSAL.relative_to(ROOT)),
        },
        "character_frames_modified": False,
        "notes": [
            "phase3_projectiles.json 与 charge_overlay_policy.json 未改，等根会话统一合并。",
            "未登记前运行时会静默跳过这些 id；这是本任务明确的范围边界。",
        ],
    }
    save(REPORT, report)
    print(json.dumps({
        "effects": len(entries),
        "gate": report["gate"],
        "moves": sorted(move_changes),
        "report": str(REPORT.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
