"""按基线节奏展开招式帧数：同一 sprite 保持多 tick。

用途：新角色整帧数已按基线交付（如 special 16 帧），但 `moves/<id>.json`
仍是「每 sprite 一 tick」的旧数据；本工具把本角色每帧的 sprite/dx/dy/
hitboxes/hurtboxes/cancel 数据按目标 tick 数复制，events/shots 只在每个
sprite 的首 tick 触发一次，使该招时长与已装机基线一致。

两种展开方式：
1. `--template-fighter/--template-move`：逐字沿用模板的 sprite 保持序列
   （要求双方 sprite 数一致），并沿用模板的 startup/active/recovery。
2. `--ticks N`：按本招式 sprite 数均分 N tick（余数给靠前的起手帧），
   startup/active/recovery 由实际带 hitboxes 或 shots 的帧自动推算，
   使攻击窗口与整帧动作对齐；无攻击帧时要求同时给模板。

不重新设计招式，不改伤害/判定值。

用法：
    .venv/bin/python tools/art/expand_move_holds.py --fighter father-of-ultra \
        --move special --template-fighter mother-of-ultra --template-move special
    .venv/bin/python tools/art/expand_move_holds.py --fighter father-of-ultra \
        --move special --ticks 72 --write
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(fighter: str, move: str) -> dict:
    path = ROOT / "content/fighters" / fighter / "moves" / f"{move}.json"
    if not path.exists():
        raise SystemExit(f"缺少招式文件：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sprite_entries(move: dict) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for frame in move.get("frames", []):
        sprite = frame.get("sprite")
        if not isinstance(sprite, int):
            raise SystemExit("帧缺少整数 sprite")
        out.setdefault(sprite, frame)
    return out


def even_holds(n_sprites: int, ticks: int) -> list[int]:
    base, extra = divmod(ticks, n_sprites)
    if base < 1:
        raise SystemExit(f"{ticks} tick 不够分给 {n_sprites} 个 sprite")
    return [base + (1 if i < extra else 0) for i in range(n_sprites)]


def template_holds(template: dict, n_sprites: int) -> list[int]:
    order: list[int] = []
    count: dict[int, int] = {}
    for frame in template.get("frames", []):
        sprite = int(frame["sprite"])
        if sprite not in count:
            order.append(sprite)
        count[sprite] = count.get(sprite, 0) + 1
    if sorted(order) != list(range(n_sprites)):
        raise SystemExit(f"模板 sprite 集 {sorted(order)} 与目标 0..{n_sprites - 1} 不一致")
    return [count[i] for i in range(n_sprites)]


def auto_timing(entries: dict[int, dict], holds: list[int],
                fallback: dict | None) -> tuple[int, int, int]:
    active_sprites = [
        sprite for sprite in range(len(holds))
        if entries[sprite].get("hitboxes") or entries[sprite].get("shots")
    ]
    if active_sprites:
        first, last = active_sprites[0], active_sprites[-1]
        start = sum(holds[:first])
        end = sum(holds[:last + 1]) - 1
        return start, end - start + 1, sum(holds) - end - 1
    if fallback:
        return (int(fallback.get("startup", 1)), int(fallback.get("active", 1)),
                int(fallback.get("recovery", max(0, sum(holds) - 2))))
    raise SystemExit("没有可推算的攻击帧，请用模板提供三段时间")


def expand(target: dict, holds: list[int], timing: tuple[int, int, int]) -> dict:
    entries = sprite_entries(target)
    n = len(entries)
    if sorted(entries) != list(range(n)):
        raise SystemExit(f"目标 sprite 必须是 0..{n - 1}，实际 {sorted(entries)}")
    if len(holds) != n:
        raise SystemExit("保持序列长度与 sprite 数不一致")

    frames: list[dict] = []
    for sprite in range(n):
        for hold in range(holds[sprite]):
            frame = copy.deepcopy(entries[sprite])
            if hold > 0:
                frame["events"] = []
                frame.pop("shots", None)
            frames.append(frame)

    startup, active, recovery = timing
    if startup + active + recovery != len(frames):
        raise SystemExit(
            f"三段时间 {startup}/{active}/{recovery} 之和与 {len(frames)} 帧不符")

    result = copy.deepcopy(target)
    result["frames"] = frames
    result["startup"] = startup
    result["active"] = active
    result["recovery"] = recovery
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fighter", required=True)
    parser.add_argument("--move", required=True)
    parser.add_argument("--template-fighter", default="")
    parser.add_argument("--template-move", default="")
    parser.add_argument("--ticks", type=int, default=0)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    target = load(args.fighter, args.move)
    n_sprites = len(sprite_entries(target))
    template = None
    if args.template_fighter and args.template_move:
        template = load(args.template_fighter, args.template_move)

    if args.ticks:
        holds = even_holds(n_sprites, args.ticks)
    elif template:
        holds = template_holds(template, n_sprites)
    else:
        raise SystemExit("需要 --ticks 或模板")

    entries = sprite_entries(target)
    if args.ticks:
        timing = auto_timing(entries, holds, template)
    elif template:
        timing = (int(template.get("startup", 1)), int(template.get("active", 1)),
                  int(template.get("recovery", 1)))
    else:
        raise SystemExit("模板模式缺少三段时间")

    result = expand(target, holds, timing)
    seq = [f["sprite"] for f in result["frames"]]
    print(f"{args.fighter}/{args.move}: {len(target['frames'])} -> {len(seq)} ticks")
    print(f"sprites: {seq}")
    print(f"startup/active/recovery: {result['startup']}/{result['active']}/{result['recovery']}")
    if args.write:
        path = ROOT / "content/fighters" / args.fighter / "moves" / f"{args.move}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        print(f"已写入 {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
