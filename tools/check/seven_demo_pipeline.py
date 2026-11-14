#!/usr/bin/env python3
"""赛文示范流水线的数据门：走路等长、受击盖住硬直、命中框相对身高。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEVEN = ROOT / "content/fighters/ultraseven"
MANIFEST = ROOT / "assets/fighters/ultraseven/animations/manifest.json"
MISSING = ROOT / "tools/rebuild/ultraseven/demo-pipeline/missing_frames.json"
TARGET_HEIGHT = 144
MIN_HIT = 32
MIN_HURT_H = 130
MIN_HURT_W = 66

TIERS = {
    "light1": (1, 5, 4, 7),
    "light2": (1, 5, 4, 7),
    "light3": (0, 6, 5, 9),
    "heavy": (-3, 4, 6, 12),
    "crush": (-3, 4, 6, 12),
    "sweep": (0, 6, 5, 9),
    "special3": (-6, 4, 8, 16),
}


def load(path: Path):
    return json.loads(path.read_text())


def recovery_after_first(frames) -> int:
    for index, frame in enumerate(frames):
        if frame.get("hitboxes"):
            return len(frames) - index - 1
    return -1


def windows(frames):
    first = None
    last = None
    for index, frame in enumerate(frames):
        if frame.get("hitboxes"):
            if first is None:
                first = index
            last = index
    if first is None:
        return None
    return first, last - first + 1, len(frames) - last - 1


def union(boxes):
    x0 = min(box[0] for box in boxes)
    y0 = min(box[1] for box in boxes)
    x1 = max(box[0] + box[2] for box in boxes)
    y1 = max(box[1] + box[3] for box in boxes)
    return x1 - x0, y1 - y0


def main() -> int:
    errors: list[str] = []
    manifest = load(MANIFEST)
    state = load(SEVEN / "state_frames.json")
    clips = manifest["clips"]
    for key in ("walk_forward", "walk_back"):
        ticks = [int(item) for item in clips[key]["ticks"]]
        mean = sum(ticks) / len(ticks)
        variance = sum((item - mean) ** 2 for item in ticks) / len(ticks)
        if variance != 0:
            errors.append(f"{key} 帧时长方差 {variance}")
        runs: list[int] = []
        current = None
        for pose in state[key]:
            sprite = int(pose["sprite"])
            if current is None or current[0] != sprite:
                current = [sprite, 0]
                runs.append(0)
            runs[-1] += 1
            current[0] = sprite
        if len(set(runs)) != 1 or runs[0] != ticks[0]:
            errors.append(f"{key} 状态帧重复 {runs} 与 ticks {ticks} 不一致")

    standing = []
    hit_short = 0
    hurt_short = 0
    for path in sorted((SEVEN / "moves").glob("*.json")):
        move = load(path)
        move_id = str(move["id"])
        frames = move.get("frames", [])
        kind = str(move.get("kind", ""))
        header = windows(frames)
        if header is not None and (
            int(move.get("startup", -1)),
            int(move.get("active", -1)),
            int(move.get("recovery", -1)),
        ) != header:
            errors.append(f"{move_id} 起手/持续/收招与命中框窗口不一致")
        row = TIERS.get(move_id)
        recovery = recovery_after_first(frames)
        if row is not None and kind != "throw" and recovery >= 0:
            block_adv, hit_adv, push, hitstop = row
            blockstun = max(4, recovery + block_adv)
            hitstun = max(blockstun + 2, recovery + hit_adv)
            if int(move["blockstun"]) != blockstun or int(move["hitstun"]) != hitstun:
                errors.append(f"{move_id} 硬直 {move['hitstun']}/{move['blockstun']} 不是档位 {hitstun}/{blockstun}")
            if int(move.get("pushback", 0)) not in (0, push) and int(move.get("pushback", 0)) == 8:
                errors.append(f"{move_id} 推退仍是模板 8")
            feedback = move.get("feedback") or {}
            if int(feedback.get("hitstop", -1)) != hitstop:
                errors.append(f"{move_id} 命中停顿 {feedback.get('hitstop')} 不是 {hitstop}")
        if kind == "strike" and not move.get("knockdown") and not move.get("launch") and int(move.get("hitstun", 0)) > 0:
            standing.append(int(move["hitstun"]))
        if kind != "strike":
            continue
        for frame in frames:
            for box in frame.get("hitboxes", []):
                width, height = int(box[2]), int(box[3])
                if min(width, height) < 16:
                    continue
                if min(width, height) < MIN_HIT:
                    hit_short += 1
            if frame.get("hurtboxes"):
                width, height = union(frame["hurtboxes"])
                if width < MIN_HURT_W or height < MIN_HURT_H:
                    hurt_short += 1
    if hit_short:
        errors.append(f"{hit_short} 个近身命中框短边小于 {MIN_HIT}（身高 {TARGET_HEIGHT} 的 0.22）")
    if hurt_short:
        errors.append(f"{hurt_short} 帧受击框并集小于 {MIN_HURT_W}×{MIN_HURT_H}")
    max_stun = max(standing) if standing else 0
    for key in ("hit_high", "hit_mid", "hit_crouch", "hit_air"):
        length = len(state[key])
        total = sum(int(item) for item in clips[key]["ticks"])
        if length < max_stun or total < max_stun or total != length:
            errors.append(f"{key} 长度 {length} / 时长 {total} 未盖住硬直 {max_stun}")

    if not MISSING.is_file():
        errors.append("缺少缺帧清单")
        count = 0
    else:
        payload = load(MISSING)
        frames = payload.get("frames", [])
        count = len(frames)
        if int(payload.get("count", -1)) != count:
            errors.append("缺帧清单 count 与条目数不一致")
        for item in frames:
            for field in ("clip", "order", "pose", "cell", "anchor"):
                if field not in item or item[field] in ("", None, []):
                    errors.append(f"缺帧条目缺 {field}: {item.get('clip')}")
                    break
    if errors:
        print("SEVEN_DEMO_PIPELINE FAIL")
        for error in errors:
            print(" -", error)
        return 1
    print(f"SEVEN_DEMO_PIPELINE PASS walk_variance=0 hitstun_cover={max_stun} hitbox_min={MIN_HIT}/{TARGET_HEIGHT} missing_frames={count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
