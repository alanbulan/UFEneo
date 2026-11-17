"""把基础赛罗四招的共享弹体 pulse 换成本角色弹体家族。

只改两处：
  * projectile.effect -> zero_fx_pulse_flight
  * feedback.projectile_impacts -> {zero_fx_pulse_flight: zero_fx_pulse_hit}

不动人物帧、判定、伤害、tick、发射点、速度或寿命。
共享 content/presentation/phase3_projectiles.json 与 charge_overlay_policy.json 不在此文件写。
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
MOVES = ROOT / "content/fighters/ultraman-zero/moves"
NAMES = ("pulse", "low_pulse", "air_pulse", "ranged_forward")
FLIGHT = "zero_fx_pulse_flight"
HIT = "zero_fx_pulse_hit"


def main() -> None:
    for name in NAMES:
        path = MOVES / f"{name}.json"
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        before = deepcopy(data)
        current = str(data.get("projectile", {}).get("effect", ""))
        if current not in ("pulse", FLIGHT):
            raise SystemExit(f"{name}: 预期共享 pulse 或 {FLIGHT}，实为 {current}")
        data["projectile"]["effect"] = FLIGHT
        data.setdefault("feedback", {})["projectile_impacts"] = {FLIGHT: HIT}
        # 除两处目标字段外必须逐字段一致。
        expected = deepcopy(before)
        expected["projectile"]["effect"] = FLIGHT
        expected.setdefault("feedback", {})["projectile_impacts"] = {FLIGHT: HIT}
        if data != expected:
            raise SystemExit(f"{name}: 出现目标外改动")
        out = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        path.write_text(out, encoding="utf-8", newline="\n")
        changed = [line for line in out.splitlines() if line not in text.splitlines()]
        print(f"{name}: effect {current} -> {FLIGHT}; projectile_impacts -> {HIT}; 新增行 {len(changed)}")


if __name__ == "__main__":
    main()
