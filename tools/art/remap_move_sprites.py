"""把旧招式数据重映射到新整帧数量，并按指定保持序列展开 tick。

用途：角色重做后整帧数变了（如杰斯提斯超杀 8/10/12 → 14/16/16），
`moves/<id>.json` 里的 sprite 序号、events/shots/hitboxes 与时长仍是旧口径。
本工具做三件事，不改伤害/判定值：

1. `--map 旧:新,...` 把旧 sprite 的逐帧数据搬到新序号；未映射的新帧只保留
   impact_effect/block_effect 等静态字段，不继承 events/shots/hitboxes；
   多个旧 sprite 可映射到同一新帧（合并 events/shots/hitboxes）。
2. `--holds` 给每个新帧的保持 tick 数（长度必须等于新帧数）。
3. `--timing 起手/持续/收招` 必须等于保持数之和；缺省时按带 shots/hitboxes
   的首末帧自动推算。

招式总时长与三段结构应照抄已装机基线（如 special 72=24/32/16、
special2 80=32/32/16、special3 96=32/48/16、air_special 24=10/1/13），
保持序列把发射帧对齐到起手末尾。

用法：
    .venv/bin/python tools/art/remap_move_sprites.py --fighter ultraman-justice \
        --move special --sprites 14 --map 0:0,1:4,2:8,3:11,4:12,5:13,6:13,7:13 \
        --holds 3,3,3,3,3,3,3,3,11,11,10,6,5,5 --timing 24/32/16

`--write` 才写回 content；缺省只打印预览。
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/art"))
import expand_move_holds as emh  # noqa: E402

PER_FRAME_DROP = ("events", "shots", "hitboxes", "attachments", "beam_origin")


def load(fighter: str, move: str) -> dict:
    path = ROOT / "content/fighters" / fighter / "moves" / f"{move}.json"
    if not path.exists():
        raise SystemExit(f"缺少招式文件：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_map(text: str) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        old, _, new = part.partition(":")
        if not old or not new:
            raise SystemExit(f"--map 需要 旧:新：{part}")
        mapping[int(old)] = int(new)
    return mapping


def parse_ints(text: str, sep: str = ",") -> list[int]:
    return [int(x) for x in text.replace(sep, ",").split(",") if x.strip()]


def _merge_unique(target: list, extra: list) -> None:
    seen = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in target}
    for item in extra:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            target.append(copy.deepcopy(item))


def old_entries(move: dict) -> dict[int, dict]:
    """每个 sprite 的逐帧数据。

    同一 sprite 常连续保持多 tick：发射/判定/事件只落在其中一 tick，不能只取
    该 sprite 的第一帧（奥母 special2 的发射在 sprite 3 的第 6 个 tick，只取首帧
    会把 shots 丢光）。attachments/events 取首个非空组；shots/hitboxes 全量并集
    并去重。
    """
    out: dict[int, dict] = {}
    for frame in move.get("frames", []):
        sprite = int(frame["sprite"])
        if sprite not in out:
            copied = copy.deepcopy(frame)
            for key in ("attachments", "events"):
                if not copied.get(key):
                    copied.pop(key, None)
            out[sprite] = copied
            continue
        entry = out[sprite]
        for key in ("attachments", "events"):
            if frame.get(key) and not entry.get(key):
                entry[key] = copy.deepcopy(frame[key])
        for key in ("shots", "hitboxes"):
            if frame.get(key):
                entry.setdefault(key, [])
                _merge_unique(entry[key], frame[key])
        if frame.get("beam_origin") and not entry.get("beam_origin"):
            entry["beam_origin"] = copy.deepcopy(frame["beam_origin"])
        for key in ("cinematic_stage", "pause_clock", "freeze_opponent"):
            if key in frame and key not in entry:
                entry[key] = frame[key]
    return out


def build_frames(move: dict, mapping: dict[int, int], sprites: int,
                 dedupe_events: bool) -> list[dict]:
    entries = old_entries(move)
    missing = sorted(set(entries) - set(mapping))
    if missing:
        raise SystemExit(f"旧 sprite 未映射：{missing}")
    extra = sorted(set(mapping) - set(entries))
    if extra:
        raise SystemExit(f"映射包含不存在的旧 sprite：{extra}")

    base = entries[0]
    frames: list[dict] = []
    for index in range(sprites):
        frame = {"sprite": index, "dx": 0, "dy": 0,
                 "hitboxes": [], "cancel": [], "events": []}
        for key in ("impact_effect", "block_effect"):
            if key in base:
                frame[key] = base[key]
        frames.append(frame)

    for old_index in sorted(mapping):
        new_index = mapping[old_index]
        if not 0 <= new_index < sprites:
            raise SystemExit(f"新序号越界：{old_index}->{new_index}")
        source = copy.deepcopy(entries[old_index])
        source["sprite"] = new_index
        target = frames[new_index]
        if target.get("_filled"):
            for key in ("events", "attachments", "shots", "hitboxes"):
                if source.get(key):
                    target.setdefault(key, [])
                    _merge_unique(target[key], source[key])
            if source.get("beam_origin") and not target.get("beam_origin"):
                target["beam_origin"] = copy.deepcopy(source["beam_origin"])
            for key in ("cinematic_stage", "pause_clock", "freeze_opponent"):
                if key in source and key not in target:
                    target[key] = source[key]
            continue
        frames[new_index] = source
        source["_filled"] = True

    if dedupe_events:
        seen: set[str] = set()
        for frame in frames:
            kept = []
            for event in frame.get("events", []):
                ident = f"{event.get('kind')}:{event.get('id')}"
                if ident in seen:
                    continue
                seen.add(ident)
                kept.append(event)
            frame["events"] = kept

    for frame in frames:
        frame.pop("_filled", None)
        # 旧帧可能没有空 events/cancel 键；展开后首 tick 不会补，校验会拒收。
        frame.setdefault("events", [])
        frame.setdefault("cancel", [])
        frame.setdefault("hitboxes", [])
        frame.setdefault("dx", 0)
        frame.setdefault("dy", 0)
    return frames


def timing_from_frames(frames: list[dict], holds: list[int]) -> tuple[int, int, int]:
    active = [i for i, frame in enumerate(frames)
              if frame.get("hitboxes") or frame.get("shots")]
    if not active:
        raise SystemExit("没有 shots/hitboxes，必须显式给 --timing")
    first, last = active[0], active[-1]
    return (sum(holds[:first]), sum(holds[first:last + 1]),
            sum(holds[last + 1:]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fighter", required=True)
    parser.add_argument("--move", required=True)
    parser.add_argument("--sprites", type=int, required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--holds", required=True)
    parser.add_argument("--timing", default="", help="起手/持续/收招，缺省自动")
    parser.add_argument("--dedupe-events", action="store_true",
                        help="去掉重复的同 id 声音/事件")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    move = load(args.fighter, args.move)
    mapping = parse_map(args.map)
    holds = parse_ints(args.holds)
    if len(holds) != args.sprites:
        raise SystemExit(f"保持序列 {len(holds)} 项，与 --sprites {args.sprites} 不符")

    frames = build_frames(move, mapping, args.sprites, args.dedupe_events)
    if args.timing:
        timing = tuple(int(x) for x in args.timing.split("/"))
    else:
        timing = timing_from_frames(frames, holds)
    if len(timing) != 3:
        raise SystemExit("--timing 需要 起手/持续/收招 三项")

    base = copy.deepcopy(move)
    base["frames"] = frames
    result = emh.expand(base, holds, timing)  # type: ignore[arg-type]

    seq = [frame["sprite"] for frame in result["frames"]]
    shots = [i for i, frame in enumerate(result["frames"]) if frame.get("shots")]
    hits = [i for i, frame in enumerate(result["frames"]) if frame.get("hitboxes")]
    print(f"{args.fighter}/{args.move}: {len(move['frames'])} -> {len(result['frames'])} ticks")
    print(f"sprites {args.sprites} holds {holds}")
    print(f"startup/active/recovery {result['startup']}/{result['active']}/{result['recovery']}")
    print(f"shot ticks {shots} hitbox ticks {hits}")
    print(f"sequence {seq}")
    for i, frame in enumerate(result["frames"]):
        if frame.get("events") or frame.get("shots") or frame.get("hitboxes"):
            labels = []
            if frame.get("events"):
                labels.append("events " + str([e.get("id") or e.get("kind")
                                               for e in frame["events"]]))
            if frame.get("shots"):
                labels.append("shots " + str([s.get("effect") for s in frame["shots"]]))
            if frame.get("hitboxes"):
                labels.append(f"hitboxes {len(frame['hitboxes'])}")
            print(f"  tick {i:02d} sprite {frame['sprite']:02d}: " + ", ".join(labels))

    startup, active, recovery = result["startup"], result["active"], result["recovery"]
    window = range(startup, startup + active)
    for tick in shots + hits:
        if tick not in window:
            print(f"警告：tick {tick} 的事件不在 active 窗口 {startup}..{startup + active - 1}")

    if args.write:
        path = ROOT / "content/fighters" / args.fighter / "moves" / f"{args.move}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        print(f"已写入 {path.relative_to(ROOT)}")
    else:
        print("未写入（加 --write 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
