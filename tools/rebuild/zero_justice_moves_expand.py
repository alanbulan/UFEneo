"""赛罗/杰斯全部招式 frames 按基线 ultraman 同名招式扩写（用户 2026-11-11 指令）。

现状 3-12 帧直出是骨架化问题的根源；本脚本把两家所有 content/fighters/<id>/moves/*.json
的 frames 数组扩到基线同名招式长度。人物动作与特效分离（主会话 2026-11-11 追加）：
动作帧只画人物本体，技能光效由运行时 shots 承载。

规则：
- sprite 映射：自有 0..N-1 均匀铺进基线段序列；自有图少于基线段时按段序
  等分循环复用（蓄力渐进，末相落在火姿）；发射/命中 sprite 锚定基线
  发射/命中 tick 所在段（见 SPRITE_ANCHOR）。
- hitboxes：位完全跟基线（active 段）；形状按自有历史框适配（中心对齐、
  宽高取大）。基线 projectile 招自有为 strike 的，判定放基线 shots tick。
- cancel：按基线 tick 位重算，值沿用基线 cancel 列表。
- events：自有 sound 按 sprite 段首发一次（引擎逐 tick 触发，段首防重复）。
- shots：保留现有 effect/spawn/box/speed/life 参数，触发 tick 挪到基线
  发射 tick；赛罗三超必杀按主会话指令转 kind=projectile + shots（FX id
  标 pending，等特效会话产出后接线）；赛罗四个光弹招补顶层 projectile
  （基线模式），spawn 按装机帧实测掌缘。
- 电影化键（cinematic_stage/pause_clock/freeze_opponent）按基线布局重排。
- 投技 target：全帧继承自有 target，按基线 hold/release 分界重排 progress
  与 impact。
- startup/active/recovery 取基线值，与 frames 长度恒等；伤害/能量等数值
  全部保留自有。

不碰 assets/、state_frames.json、father-of-ultra。输入必须是未扩写的原始
文件（脚本不幂等：扩写后 sprite 历史框会丢）；重跑先 git checkout 恢复。

用法：
    .venv/bin/python tools/rebuild/zero_justice_moves_expand.py --fighter ultraman-zero
    .venv/bin/python tools/rebuild/zero_justice_moves_expand.py --fighter ultraman-justice
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "ultraman"
FRAME_BODY_KEYS = {"sprite", "dx", "dy", "hitboxes", "hurtboxes", "cancel", "events",
                   "impact_effect", "block_effect"}
THROW_MOVES = {"throw_forward", "throw_back", "air_throw", "dash_throw", "motion_41236"}

# 赛罗三超必杀转 projectile：FX 特效未自制，effect id 标 pending 前缀；
# presentation/side_view.gd 对未知 effect 只隐藏不崩，pending 不装机可安全进模拟。
# spawn 取自 art/fighters/ultraman-zero/stage1 已装机帧实测掌缘/额灯
# （special: 右前臂前缘 x146/y110 → 局部 [18,138]；special2: 额灯右缘 x150/y90 → [22,158]；
#  special3: 双掌缘 x185，上镖束心 y97 下镖 y135 → [57,151]/[57,113]）。
ZERO_SUPER_SHOTS = {
    "special": {
        "shots": [{
            "effect": "pending_wide_zero_shot", "spawn": [18, 138], "anchor": [18, 138],
            "speed": 0, "life": 32, "box": [0, -22, 420, 44], "color": [0.55, 0.9, 1.0, 1.0],
            "beam": True, "length": 420, "thickness": 44, "level": 1,
        }],
        "beam_origin": [18, 138],
        "startup": 24, "active": 32, "recovery": 16,
    },
    "special2": {
        "shots": [{
            "effect": "pending_emerium_slash", "spawn": [22, 158], "anchor": [22, 158],
            "speed": 0, "life": 32, "box": [0, -14, 420, 28], "color": [0.55, 1.0, 0.68, 1.0],
            "beam": True, "length": 420, "thickness": 28, "level": 2,
        }],
        "beam_origin": [22, 158],
        "startup": 32, "active": 32, "recovery": 16,
    },
    "special3": {
        "shots": [
            {
                "effect": "pending_zero_slugger_a", "spawn": [57, 151], "anchor": [57, 151],
                "speed": 11, "life": 60, "box": [-14, -12, 28, 24], "color": [0.6, 0.9, 1.0, 1.0],
                "beam": False, "weapon_id": "zero_slugger_a",
                "owner_interrupt_policy": "clear", "integer_path": [[0, 0]],
                "return_ticks": 24, "return_anchor": [57, 151],
                "return_anchor_by_tick": {"0": [57, 151]}, "return_effect": "pending_slugger_catch",
                "return_sound": "slugger_catch", "max_hits": 2, "hit_interval": 20,
            },
            {
                "effect": "pending_zero_slugger_b", "spawn": [57, 113], "anchor": [57, 113],
                "speed": 11, "life": 60, "box": [-14, -12, 28, 24], "color": [0.6, 0.9, 1.0, 1.0],
                "beam": False, "weapon_id": "zero_slugger_b",
                "owner_interrupt_policy": "clear", "integer_path": [[0, 0]],
                "return_ticks": 24, "return_anchor": [57, 113],
                "return_anchor_by_tick": {"0": [57, 113]}, "return_effect": "pending_slugger_catch",
                "return_sound": "slugger_catch", "max_hits": 2, "hit_interval": 20,
            },
        ],
        "beam_origin": None,
        "startup": 32, "active": 48, "recovery": 16,
        "cinematic": True,
    },
}

# 赛罗四个光弹招：kind=projectile 顶层弹道（基线模式），spawn 按装机帧实测掌缘。
# FX 未自制，effect 同样标 pending；speed/life 先用基线 pulse/slash 档。
ZERO_TOP_PROJECTILE = {
    "pulse": {"effect": "pending_zero_pulse", "spawn": [60, 143], "box": [-14, -10, 28, 20], "speed": 8, "life": 100},
    "low_pulse": {"effect": "pending_zero_pulse", "spawn": [82, 91], "box": [-14, -10, 28, 20], "speed": 8, "life": 100},
    "air_pulse": {"effect": "pending_zero_pulse", "spawn": [123, 110], "box": [-14, -12, 28, 24], "speed": 7, "vy": -7, "life": 100},
    "ranged_forward": {"effect": "pending_zero_ray", "spawn": [62, 143], "box": [-22, -8, 44, 16], "speed": 10, "vy": 0, "life": 100},
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def segments(frames: list) -> list:
    """连续同 sprite tick 的段 [(sprite, start, end_exclusive), ...]。"""
    out = []
    for i, f in enumerate(frames):
        s = f["sprite"]
        if out and out[-1][0] == s:
            out[-1][2] = i + 1
        else:
            out.append([s, i, i + 1])
    return [tuple(x) for x in out]


def expand_sprites(baseline_segs: list, n_own: int, fire_seg_index: int | None = None) -> list:
    """把自有 sprite 0..n-1 铺进基线段序列，返回逐 tick sprite 列表。

    按自有图数把基线段序列等分成 n_own 个相（循环复用）：自有图 3 张配
    基线 8 段 = 0 1 2 0 1 2 0 1 2，蓄力段保留渐进推进；fire_seg_index 给出
    基线发射段序号时，末一张（火姿）锚定该段及其后的段，保证发射帧姿势
    与 spawn 对掌（发射前的段不受影响）。
    """
    m = len(baseline_segs)
    result = []
    if n_own <= m:
        for si, (sprite, start, end) in enumerate(baseline_segs):
            own = min(si * n_own // m, n_own - 1)
            if fire_seg_index is not None and si >= fire_seg_index:
                own = n_own - 1
            result.extend([own] * (end - start))
    else:
        # 均匀分布：每段分配 n_own/m 张，余数从前往后。
        base, extra = divmod(n_own, m)
        own_idx = 0
        for si, (sprite, start, end) in enumerate(baseline_segs):
            take = base + (1 if si < extra else 0)
            for k in range(end - start):
                own = min(own_idx + min(k, take - 1), n_own - 1)
                if fire_seg_index is not None and si >= fire_seg_index:
                    own = n_own - 1
                result.append(own)
            own_idx += take
    return result


def max_area_box(boxes: list) -> list:
    return max(boxes, key=lambda b: b[2] * b[3]) if boxes else None


def fit_hitbox(base_box: list, candidates: list) -> list:
    """按基线框中心与尺寸比例，把自有最大框适配为同形框。

    优先：取自有 sprite 的全部历史框中面积最大者，中心对齐基线框中心、
    宽高取两者较大（保留双方覆盖），整数。
    """
    own = max_area_box(candidates)
    if own is None:
        return list(base_box)
    cx = base_box[0] + base_box[2] / 2
    cy = base_box[1] + base_box[3] / 2
    w = max(base_box[2], own[2])
    h = max(base_box[3], own[3])
    return [int(round(cx - w / 2)), int(round(cy - h / 2)), int(w), int(h)]


def expand_move(move: dict, base: dict, clip: str, fighter: str) -> dict:
    base_frames = base["frames"]
    own_frames = move["frames"]
    n_own_atlas = max(f["sprite"] for f in own_frames) + 1
    base_segs = segments(base_frames)

    # 自有 per-sprite 数据
    per_sprite = {}
    for f in own_frames:
        s = f["sprite"]
        rec = per_sprite.setdefault(s, {"hurtboxes": [], "hitboxes": [], "events": [], "cancel": set()})
        rec["hurtboxes"].append(f["hurtboxes"])
        rec["hitboxes"].append(f["hitboxes"])
        rec["events"].append(f.get("events", []))
        for c in f.get("cancel", []):
            rec["cancel"].add(c)

    # 现有帧级 shots 与电影化键（取现有触发 tick 的参数）
    own_shots = None
    own_cin = {}
    for f in own_frames:
        if f.get("shots") and own_shots is None:
            own_shots = f["shots"]
        for key in ("cinematic_stage", "pause_clock", "freeze_opponent"):
            if key in f:
                own_cin[key] = f[key]

    # 基线发射 tick（段首 tick，即该 sprite 段的第一 tick）
    base_shot_ticks = [i for i, f in enumerate(base_frames) if f.get("shots")]
    shot_tick = base_shot_ticks[0] if base_shot_ticks else None

    # 赛罗超必杀：转 projectile + pending shots，发射 sprite 锚定基线发射段
    fire_seg_index = None
    for si, (sprite, start, end) in enumerate(base_segs):
        if shot_tick is not None and start <= shot_tick < end:
            fire_seg_index = si
    pending = None
    if fighter == "ultraman-zero" and clip in ZERO_SUPER_SHOTS:
        pending = ZERO_SUPER_SHOTS[clip]
        if fire_seg_index is not None:
            own_segs_adjust = fire_seg_index
        move["kind"] = "projectile"
        move["manual_projectiles"] = True
        move.pop("cancel_rule", None)
        own_shots = [dict(s) for s in pending["shots"]]
        if pending.get("beam_origin"):
            own_cin = own_cin  # 电影化键只在 special3
        move["startup"] = pending["startup"]
        move["active"] = pending["active"]
        move["recovery"] = pending["recovery"]

    new_frames = []
    sprite_seq = expand_sprites(base_segs, n_own_atlas, fire_seg_index)

    # 自有投技 target：按基线 hold/release 分界重排
    is_throw = clip in THROW_MOVES or move.get("kind") == "throw"
    own_hold = next((f["target"] for f in own_frames
                     if (f.get("target") or {}).get("mode") == "hold"), None)
    own_release = next((f["target"] for f in own_frames
                        if (f.get("target") or {}).get("mode") == "release"), None)
    # 基线 hold/release 分界与 release 模板
    base_hold_last = max((i for i, f in enumerate(base_frames)
                          if (f.get("target") or {}).get("mode") == "hold"), default=-1)
    base_rel = [(i, (f.get("target") or {}).get("progress"), bool((f.get("target") or {}).get("impact")))
                for i, f in enumerate(base_frames)
                if (f.get("target") or {}).get("mode") == "release"]

    # 自有 strike 招式（基线同名是 projectile）的判定 sprite：判定挪到这些
    # sprite 的基线段，保持「按动作实际相位」。
    # 基线 shots tick 集（strike 自有判定挪到这里）
    strike_shots_ticks = set(base_shot_ticks) if base_shot_ticks else set()

    for i, bf in enumerate(base_frames):
        nf = {
            "sprite": sprite_seq[i],
            "dx": bf.get("dx", 0),
            "dy": bf.get("dy", 0),
            "hitboxes": [],
            "hurtboxes": per_sprite[sprite_seq[i]]["hurtboxes"][0],
            "cancel": [],
            "events": [],
        }
        # hurtboxes：同 sprite 后续 tick 有不同 hurtboxes 的（受击形态变化），
        # 按自有段内 tick 序号取样；这里统一取首帧 hurtboxes，段内一致。
        # hitboxes：基线 tick 有判定时，从自有该 sprite 历史框适配。
        # 基线 projectile 招（hb 空、shots 触发）转成 kind=projectile 后，
        # 帧级 hitboxes 会让 match_director 再 spawn 一次顶层空弹道——清空。
        if pending and not bf["hitboxes"]:
            pass  # 赛罗三超必杀：帧级 shots 走 emit()，顶层 projectile 不存在
        elif bf["hitboxes"]:
            rec = per_sprite[sprite_seq[i]]
            hist = [b for hb in rec["hitboxes"] for b in hb]
            # 自有全部框（不限 sprite）按 sprite 优先，退化到全局最大
            if not hist:
                hist = [b for f in own_frames for b in f["hitboxes"]]
            nf["hitboxes"] = [fit_hitbox(b, hist) for b in bf["hitboxes"]]
        elif not pending and strike_shots_ticks and i in strike_shots_ticks:
            # 基线同名是 projectile（无 hb）而自有是 strike：判定放基线 shots tick
            # （基线的「生效」位）。形状用自有历史框适配；自有无历史框时跳过
            # （杰斯 motion_214/22 等本就是 projectile，shots 参数照带）。
            hist = [b for f in own_frames for b in f["hitboxes"]]
            if hist:
                nf["hitboxes"] = [fit_hitbox(b, hist) for b in [max(hist, key=lambda x: x[2] * x[3])]]
        # events：自有 sound 事件按 sprite 段首发一次；基线段首 sound 对齐值
        seg_first = i == 0 or sprite_seq[i] != sprite_seq[i - 1]
        if seg_first:
            own_evs = per_sprite[sprite_seq[i]]["events"]
            # 取该 sprite 历史里的首个非空事件组
            ev = next((e for e in own_evs if e), [])
            if ev:
                nf["events"] = [dict(e) for e in ev]
        # cancel：按基线 tick 位照抄基线值（值沿用基线，动作名两角色一致）
        nf["cancel"] = list(bf.get("cancel", []))
        # shots：挪到基线发射 tick（只一次）；赛罗 pending shots 在此注入
        if shot_tick is not None and i == shot_tick and own_shots:
            nf["shots"] = [dict(s) for s in own_shots]
            if pending and pending.get("beam_origin"):
                nf["beam_origin"] = list(pending["beam_origin"])
            if pending and pending.get("cinematic"):
                nf["cinematic_stage"] = "beam"
                nf["pause_clock"] = True
        # 电影化：发射 tick 前一律 portrait+freeze（超必杀特写），发射 tick 起
        # beam（画面切束，对手解冻、束逐帧出）。pause_clock 发射后仍 true（束期时钟暂停）。
        if (own_cin or pending) and shot_tick is not None and len(base_frames) >= 48:
            if i < shot_tick and i >= shot_tick - 4:
                nf["cinematic_stage"] = "portrait"
                nf["pause_clock"] = True
                nf["freeze_opponent"] = True
            elif i >= shot_tick:
                nf["cinematic_stage"] = "beam"
                nf["pause_clock"] = True
        # 投技 target
        if is_throw:
            bt = bf.get("target") or {}
            if bt.get("mode") == "hold" and own_hold:
                nf["target"] = dict(own_hold)
            elif bt.get("mode") == "release" and own_release:
                t = dict(own_release)
                # progress/impact 按基线模板
                base_entry = next(((j, p, im) for j, p, im in base_rel if j == i), None)
                if base_entry:
                    if base_entry[1] is not None:
                        t["progress"] = list(base_entry[1])
                    if not base_entry[2] and "impact" in t:
                        t.pop("impact", None)
                    elif base_entry[2]:
                        t["impact"] = True
                nf["target"] = t
            elif bt and own_hold:
                # 基线 hold 段之外的其它 target 键（如 release 后段）照基线 mode
                t = dict(own_hold)
                t["mode"] = bt.get("mode", "hold")
                nf["target"] = t
        new_frames.append(nf)

    move["frames"] = new_frames
    if not pending:
        move["startup"] = base["startup"]
        move["active"] = base["active"]
        move["recovery"] = base["recovery"]
    # 赛罗四个光弹招：补顶层 projectile（基线模式，由 hitboxes 首帧触发）
    if fighter == "ultraman-zero" and clip in ZERO_TOP_PROJECTILE:
        move["kind"] = "projectile"
        move["projectile"] = dict(ZERO_TOP_PROJECTILE[clip])
    return move


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    moves_dir = ROOT / "content" / "fighters" / args.fighter / "moves"
    base_dir = ROOT / "content" / "fighters" / BASELINE / "moves"
    changed = []
    for path in sorted(moves_dir.glob("*.json")):
        clip = path.stem
        base_path = base_dir / path.name
        if not base_path.is_file():
            print(f"  {clip}: 无基线同名，跳过")
            continue
        move = load(path)
        base = load(base_path)
        before = len(move["frames"])
        expand_move(move, base, clip, args.fighter)
        after = len(move["frames"])
        if not args.dry_run:
            save(path, move)
        changed.append(f"{clip}: {before}→{after}")
    print(f"{args.fighter}: {'(dry-run) ' if args.dry_run else ''}" + "; ".join(changed))


if __name__ == "__main__":
    main()
