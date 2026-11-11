"""把已签整帧的 Alpha 轮廓转成招式帧数据与状态受击框。

用途：角色美术已落格、但 content/fighters/<id>/ 只有模板继承时，按实际像素
逐帧量出受击框，并把同体型已审招式的规则字段映射到本角色交付帧数上。
不是重新设计招式：伤害/硬直/取消规则沿用同体型已审数据，只把帧号、攻击框
和受击框换成本角色整帧实测值。

输入：
- assets/fighters/<id>/animations/manifest.json（已装 clip）
- art/fighters/<id>/stage1/move_fx.json（本角色技能发射帧、光色、弹体）
- content/fighters/ultraman-zero/moves/<id>.json 或
  content/templates/humanoid/moves/<id>.json（规则字段来源）

输出：
- content/fighters/<id>/moves/<id>.json（全部本地招式）
- content/fighters/<id>/move_manifest.json
- content/fighters/<id>/state_frames.json

用法：
    .venv/bin/python tools/art/derive_fighter_data.py --fighter ultraman-justice --write
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

MOVE_IDS = [
    "light1", "light2", "light3", "heavy", "launcher", "spin_heavy", "crush",
    "tackle", "throw_forward", "throw_back", "crouch_light", "sweep", "slide",
    "crouch_light2", "vertical_light", "vertical_heavy", "diagonal_light",
    "diagonal_heavy", "air_crush", "dive", "air_throw", "chase_light1",
    "chase_light2", "chase_end", "dash_light", "dash_heavy", "dash_throw",
    "back_counter", "dodge_counter", "wake_low", "wake_mid", "guard_counter",
    "burst", "pulse", "low_pulse", "air_pulse", "ranged_forward",
    "motion_236", "motion_623", "motion_214", "motion_22",
    "motion_41236", "special", "special2", "special3", "air_special", "taunt",
    "crouch_sweep", "bounce_sweep", "bounce_crush",
]

THROW_IDS = {"throw_forward", "throw_back", "air_throw", "dash_throw", "motion_41236"}

DISPLAY_NAMES = {
    "light1": "前手短直拳", "light2": "后手直拳", "light3": "进身上勾拳",
    "heavy": "踏步重拳", "launcher": "升龙上勾拳", "spin_heavy": "回身横扫肘",
    "crush": "双拳破甲砸击", "tackle": "沉肩突进",
    "throw_forward": "前投·扣臂过肩摔", "throw_back": "后投·抱腰回身摔",
    "crouch_light": "蹲姿下段直拳", "sweep": "低扫脚跟", "slide": "低身滑铲",
    "crouch_light2": "蹲姿二段直拳", "vertical_light": "垂直跳短拳",
    "vertical_heavy": "垂直跳下砸拳", "diagonal_light": "斜跳膝撞",
    "diagonal_heavy": "斜跳飞踢", "air_crush": "空中双拳下砸",
    "dive": "俯冲脚跟踢", "air_throw": "空投·空中揽肩翻摔",
    "chase_light1": "追击前刺拳", "chase_light2": "追击横肘",
    "chase_end": "追击双掌砸地", "dash_light": "冲刺直拳",
    "dash_heavy": "冲刺飞踢", "dash_throw": "冲步抱身摔",
    "back_counter": "后闪反击", "dodge_counter": "闪避反击",
    "guard_counter": "防御反击", "wake_low": "起身下段拳",
    "wake_mid": "起身中段拳", "burst": "爆气",
    "motion_236": "连步双掌", "motion_623": "升膝迎击",
    "motion_214": "突击光箭", "motion_22": "杰斯提斯屏障",
    "motion_41236": "正义扼制", "special": "闪光效应",
    "special2": "杰斯提斯粉碎", "special3": "比库托流姆光线",
    "taunt": "挑衅", "crouch_sweep": "蹲姿扫腿",
    "bounce_sweep": "弹地追击低扫", "bounce_crush": "弹地追击双拳砸",
}


def load_mask(im: Image.Image, rect: list[int]) -> np.ndarray:
    cell = np.array(im.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])))
    return cell[:, :, 3] > 0


def largest_component(mask: np.ndarray) -> np.ndarray:
    """只取最大连通块，避免把屏障/贴体光焰量进受击框。"""
    from collections import deque
    seen = np.zeros_like(mask, bool)
    best: list[tuple[int, int]] = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            queue = deque([(y, x)])
            seen[y, x] = True
            comp = []
            while queue:
                cy, cx = queue.popleft()
                comp.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            if len(comp) > len(best):
                best = comp
    out = np.zeros_like(mask, bool)
    for y, x in best:
        out[y, x] = True
    return out


def band_boxes(mask: np.ndarray, ax: int, ay: int) -> list[list[int]]:
    """按可见高度三等分，自下而上量 3 个受击框（局部坐标，y 从脚底向上）。"""
    ys, xs = np.where(mask)
    if not len(ys):
        return [[-18, 0, 36, 128]]
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    boxes: list[list[int]] = []
    for band in range(3):
        r1 = bottom - (band * height) // 3
        r0 = bottom - ((band + 1) * height) // 3 + 1
        sub = mask[r0:r1 + 1]
        bys, bxs = np.where(sub)
        if not len(bxs):
            continue
        x0, x1 = int(bxs.min()), int(bxs.max())
        yy = ay - 1 - r1
        hh = r1 - r0 + 1
        boxes.append([x0 - ax - 2, max(0, yy), x1 - x0 + 1 + 4, hh + 2])
    return boxes


def front_band_box(mask: np.ndarray, ax: int, ay: int) -> list[int]:
    """取最前方 12 px 列带内的像素框，作为攻击杆位置。"""
    ys, xs = np.where(mask)
    if not len(xs):
        return [20, 80, 16, 16]
    xmax, xmin = int(xs.max()), int(xs.min())
    band = mask[:, max(xmin, xmax - 11):xmax + 1]
    bys, bxs = np.where(band)
    y0, y1 = int(bys.min()), int(bys.max())
    x0 = max(xmin, xmax - 11)
    w = max(14, xmax - x0 + 3)
    h = max(12, y1 - y0 + 1)
    return [x0 - ax - 1, ay - 1 - y1 - 1, w, h + 2]


def height_band_box(mask: np.ndarray, ax: int, ay: int, y_window: list[int]) -> list[int]:
    """在指定高度窗口内取最前方 20 px 的像素框（贴体光刃等已知高度的攻击）。"""
    rows = np.arange(mask.shape[0])[:, None]
    world_y = ay - 1 - rows
    band = mask & (world_y >= int(y_window[0])) & (world_y <= int(y_window[1]))
    if not band.any():
        return front_band_box(mask, ax, ay)
    bys, bxs = np.where(band)
    xmax = int(bxs.max())
    front = band & (np.arange(mask.shape[1])[None, :] >= xmax - 19)
    fys, fxs = np.where(front)
    return [int(fxs.min()) - ax - 1, ay - 1 - int(fys.max()) - 1,
            max(12, int(fxs.max() - fxs.min()) + 3), max(12, int(fys.max() - fys.min()) + 3)]


def fit_donor_box(mask: np.ndarray, box: list[int], ax: int, ay: int, scale: float) -> list[int]:
    """把源角色攻击框缩放到本角色，并贴到该帧实际伸出的肢体上。"""
    ys, xs = np.where(mask)
    if not len(xs):
        return [20, 80, 16, 16]
    x, y, w, h = [int(round(v * scale)) for v in box]
    w, h = max(w, 8), max(h, 8)
    xmin, xmax = int(xs.min()) - ax - 2, int(xs.max()) - ax + 2
    x = max(xmin, min(x, xmax - w))
    y = max(0, min(y, ay - 1 - int(ys.min())))
    local = np.zeros_like(mask)
    rows = np.arange(mask.shape[0])[:, None]
    cols = np.arange(mask.shape[1])[None, :]
    world_y = ay - 1 - rows
    local = mask & (world_y >= y - 2) & (world_y < y + h + 2) & (cols >= x + ax) & (cols < x + ax + w)
    if local.any():
        lys, lxs = np.where(local)
        return [int(lxs.min()) - ax - 1, ay - 1 - int(lys.max()) - 1,
                max(8, int(lxs.max() - lxs.min()) + 3), max(8, int(lys.max() - lys.min()) + 3)]
    # 来源与本角色出拳高度/伸展不同：在来源框中心高度上找本帧最前方像素，
    # 再把它周围一圈像素收成小框，避免退回整条前缘（会把前脚量成拳头）。
    cy = y + h // 2
    band = mask & (np.abs(world_y - cy) <= 22)
    if band.any():
        bys, bxs = np.where(band)
        px = int(bxs.max())
        front = band & (cols >= px - 2) & (cols <= px)
        fys, _ = np.where(front)
        py = int(np.median(fys)) if len(fys) else int(bys.mean())
        near = mask & (np.abs(cols - px) <= 7) & (np.abs(rows - py) <= 9)
        nys, nxs = np.where(near)
        if len(nys):
            return [int(nxs.min()) - ax - 1, ay - 1 - int(nys.max()) - 2,
                    max(12, int(nxs.max() - nxs.min()) + 4), max(12, int(nys.max() - nys.min()) + 4)]
    return front_band_box(mask, ax, ay)


def hand_point(mask: np.ndarray, ax: int, ay: int, y_window: list[int] | None = None) -> list[int]:
    """发射点：指定高度窗口内最前方 13 px 列带的像素重心（根部局部坐标）。

    不限定高度时最前方像素常是前脚，会把束根量到地面；y_window 用世界坐标
    （脚底向上）圈住掌/指所在高度，按实际整帧取值。
    """
    ys, xs = np.where(mask)
    if not len(xs):
        return [40, 90]
    work = mask
    if y_window:
        rows = np.arange(mask.shape[0])[:, None]
        world_y = ay - 1 - rows
        work = mask & (world_y >= int(y_window[0])) & (world_y <= int(y_window[1]))
        if not work.any():
            work = mask
    wys, wxs = np.where(work)
    xmax = int(wxs.max())
    band = work[:, max(0, xmax - 13):xmax + 1]
    bys, bxs = np.where(band)
    cx = float(bxs.mean() + max(0, xmax - 13))
    cy = float(bys.mean())
    return [int(round(cx)) - ax, ay - 1 - int(round(cy))]


DONOR_ALIAS = {
    "crouch_sweep": "sweep",
    "bounce_sweep": "sweep",
    "bounce_crush": "crush",
}


def donor_for(fighter: str, move_id: str) -> dict | None:
    """规则来源：赛罗同 id > 泰罗同 id > 模板同 id > 明确登记的同构招。

    不读本角色刚生成的 moves/：否则第二次运行会把上次吸附框当来源，逐轮漂移。
    motion_41236 是投技，必须带逐帧 target（抱持/受投姿势）才有完整动作；
    模板这一条是旧的 strike 草案、无 target，因此跳过模板，改用泰罗的完整投技。
    """
    lookup = DONOR_ALIAS.get(move_id, move_id)
    paths = [ROOT / f"content/fighters/ultraman-zero/moves/{lookup}.json",
             ROOT / f"content/fighters/ultraman-taro/moves/{lookup}.json",
             ROOT / f"content/templates/humanoid/moves/{lookup}.json"]
    if lookup != "motion_41236":
        paths.pop(1)
    for p in paths:
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        if lookup == "motion_41236" and not any("target" in f for f in data.get("frames", [])):
            continue
        return data
    return None


def scale_fields(donor: dict, n: int, cfg: dict) -> dict:
    d = {k: v for k, v in donor.items() if k != "frames"}
    dn = max(1, len(donor.get("frames", [])))
    startup = int(d.get("startup", 1))
    active = int(d.get("active", 1))
    recovery = int(d.get("recovery", 1))
    if cfg.get("active_frames"):
        active_frames = [int(v) for v in cfg["active_frames"] if 0 <= int(v) < n]
        first = min(active_frames) if active_frames else 1
        d["startup"] = first
        d["active"] = len(active_frames)
        d["recovery"] = max(0, n - first - len(active_frames))
        if d["startup"] + d["active"] + d["recovery"] < n:
            d["startup"] += n - (d["startup"] + d["active"] + d["recovery"])
    else:
        s = int(round(startup * n / dn))
        a = max(1, int(round(active * n / dn)))
        if s + a > n:
            a = max(1, n - s)
        d["startup"], d["active"], d["recovery"] = s, a, max(0, n - s - a)
    d["id"] = cfg.get("id", d.get("id", ""))
    d["display_name"] = cfg.get("display_name", DISPLAY_NAMES.get(d["id"], d.get("display_name", d["id"])))
    for key in ("damage", "chip_damage", "energy_cost", "kind", "level",
                "knockdown", "unblockable", "super_level", "self_heal", "chill"):
        if key in cfg:
            d[key] = cfg[key]
    if cfg.get("feedback_color"):
        d.setdefault("feedback", {})["color"] = cfg["feedback_color"]
    d["frames"] = []
    return d


def build_frames(donor: dict, masks: list[np.ndarray], ax: int, ay: int, scale: float,
                 cfg: dict) -> list[dict]:
    dn = max(1, len(donor.get("frames", [])))
    n = len(masks)
    drop_hit = bool(cfg.get("shot"))
    active_cfg = [int(v) for v in cfg.get("active_frames", []) if 0 <= int(v) < n]
    frames = []
    for i, mask in enumerate(masks):
        if dn == 1 or n == 1:
            j = 0
        else:
            j = int(round(i * (dn - 1) / (n - 1)))
        src = donor.get("frames", [{}])[min(j, dn - 1)] if donor.get("frames") else {}
        frame = {
            "sprite": i, "dx": 0, "dy": 0,
            "hitboxes": [], "hurtboxes": band_boxes(mask, ax, ay),
            "cancel": list(src.get("cancel", [])),
            "events": list(src.get("events", [])),
            "impact_effect": src.get("impact_effect", "impact_light"),
            "block_effect": src.get("block_effect", "impact_guard"),
        }
        if "target" in src:
            frame["target"] = src["target"]
        if drop_hit:
            # 招式由 shots 生成独立弹体/光束；帧内再放攻击框会形成二次近战判定。
            frame["hitboxes"] = []
        elif active_cfg:
            if i in active_cfg:
                if cfg.get("burst_box"):
                    frame["hitboxes"] = [cfg["burst_box"]]
                elif cfg.get("hit_y"):
                    frame["hitboxes"] = [height_band_box(mask, ax, ay, cfg["hit_y"])]
                else:
                    frame["hitboxes"] = [front_band_box(mask, ax, ay)]
        else:
            frame["hitboxes"] = [fit_donor_box(mask, b, ax, ay, scale)
                                 for b in src.get("hitboxes", [])]
        cinematic = cfg.get("cinematic", {})
        if i in [int(v) for v in cinematic.get("portrait", [])]:
            frame["cinematic_stage"] = "portrait"
            frame["pause_clock"] = True
            frame["freeze_opponent"] = True
        elif i in [int(v) for v in cinematic.get("beam", [])]:
            frame["cinematic_stage"] = "beam"
        if cfg.get("shot") and i == int(cfg["shot"]["frame"]):
            shot = {k: v for k, v in cfg["shot"].items() if k != "frame"}
            spawn = hand_point(mask, ax, ay, cfg.get("hand_y"))
            if cfg.get("kind") == "projectile" and not cfg.get("shot", {}).get("beam"):
                spawn = [spawn[0] - 2, spawn[1]]
            shot.setdefault("spawn", spawn)
            shot.setdefault("anchor", list(spawn))
            if shot.get("wall"):
                # wall 保留给 core：光壁不击中人物，只拦截对方弹体。
                shot["spawn"] = [spawn[0] - 2, 82]
                shot["anchor"] = list(shot["spawn"])
            frame["shots"] = [shot]
        frames.append(frame)
    return frames


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--standing", type=int, default=154)
    ap.add_argument("--donor-standing", type=int, default=188)
    ap.add_argument("--states-only", action="store_true",
                    help="只按已装 clip 重写 state_frames，不重建招式（手工调过的招式不被覆盖）")
    ap.add_argument("--state-clip", action="append", default=[],
                    help="配合 --states-only：只重算这些状态 clip，并与现有 state_frames 合并")
    args = ap.parse_args()

    fighter = args.fighter
    manifest = json.loads((ROOT / f"assets/fighters/{fighter}/animations/manifest.json").read_text(encoding="utf-8"))
    ax, ay = manifest.get("anchor", [96, 184])
    cfg_path = ROOT / f"art/fighters/{fighter}/stage1/move_fx.json"
    config = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    move_cfg = config.get("moves", {})
    scale = args.standing / args.donor_standing

    clips = manifest["clips"]
    move_ids = [m for m in MOVE_IDS if m in clips]
    missing = [m for m in MOVE_IDS if m not in clips]
    state_ids = [k for k in clips if k not in MOVE_IDS]

    out_moves = {}
    for move_id in ([] if args.states_only else move_ids):
        donor = donor_for(fighter, move_id)
        clip = clips[move_id]
        im = Image.open(ROOT / clip["texture"].replace("res://", "")).convert("RGBA")
        masks = [largest_component(load_mask(im, r)) for r in clip["rects"]]
        if donor is None:
            # 模板没有该招（如 special2/special3）：规则字段由 move_fx 全量给出，
            # 帧只保留本角色实测的受击框与配置的发射/攻击窗口。
            if not move_cfg.get(move_id):
                raise SystemExit(f"{move_id}: 缺少规则来源（赛罗/模板）且无 move_fx 配置")
            donor = {"id": move_id, "frames": [{} for _ in masks]}
        cfg = dict(move_cfg.get(move_id, {}))
        cfg["id"] = move_id
        data = scale_fields(donor, len(masks), cfg)
        data["frames"] = build_frames(donor, masks, ax, ay, scale, cfg)
        if cfg.get("source_note"):
            data["data_source"] = cfg["source_note"]
        if move_id in THROW_IDS:
            data["kind"] = "throw"
        if cfg.get("shot") and not data.get("projectile"):
            # shots 已按帧携带全部字段；projectile 留空避免自动再生成一发。
            data["manual_projectiles"] = True
        out_moves[move_id] = data

    if args.state_clip:
        unknown = [c for c in args.state_clip if c not in clips or c in MOVE_IDS]
        if unknown:
            raise SystemExit(f"--state-clip 不是已装状态 clip：{unknown}")
        state_ids = list(dict.fromkeys(args.state_clip))

    states = {}
    for clip_id in state_ids:
        clip = clips[clip_id]
        im = Image.open(ROOT / clip["texture"].replace("res://", "")).convert("RGBA")
        masks = [largest_component(load_mask(im, r)) for r in clip["rects"]]
        entries = []
        for i, mask in enumerate(masks):
            entries.append({
                "sprite": i, "dx": 0, "dy": 0, "hitboxes": [],
                "hurtboxes": band_boxes(mask, ax, ay), "cancel": [], "events": [],
                "impact_effect": "impact_light", "block_effect": "impact_guard",
            })
        states[clip_id] = entries

    print(f"{fighter}: moves {len(out_moves)} (缺 clip {missing}) states {len(states)}")
    if not args.write:
        return
    content = ROOT / f"content/fighters/{fighter}"
    if not args.states_only:
        moves_dir = content / "moves"
        moves_dir.mkdir(parents=True, exist_ok=True)
        for move_id, data in out_moves.items():
            (moves_dir / f"{move_id}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (content / "move_manifest.json").write_text(
            json.dumps(sorted(out_moves), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sf_path = content / "state_frames.json"
    if args.states_only and sf_path.is_file():
        merged = json.loads(sf_path.read_text(encoding="utf-8"))
        merged.update(states)
        states = {k: merged[k] for k in sorted(merged)}
    sf_path.write_text(
        json.dumps(states, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"已写入 {content}" + ("（仅 state_frames）" if args.states_only else ""))


if __name__ == "__main__":
    main()
