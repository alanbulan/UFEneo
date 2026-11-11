"""佐菲特效家族装配：ace/jack 借用段全部换成 zoffy_fx_* 自制重着色段。

色板按招式表（content/fighters/zoffy/moves/*.json data_source）：
  佐菲全家族银蓝白 M87 系；Z光线蓝白电流；超级冻霜淡青白。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from phase3_family_install import install

# 佐菲光色锚点（亮→暗）
PALETTE_M87 = ["#ffffff", "#f2f9ff", "#cfe6ff", "#7ab6f2", "#2f6ecf"]      # M87 银蓝白主束
PALETTE_ZAP = ["#ffffff", "#eef6ff", "#bfe0ff", "#6a9fe8", "#2456b8"]      # Z光线电流蓝白
PALETTE_FROST = ["#ffffff", "#eefcfa", "#c2efe8", "#7ecfdc", "#3a96b8"]    # 超级冻霜淡青白

FAMILIES = [
    # motion_214 超级充能·崩掌 + special3 M87光线蓄力：jack_specium1_start 银蓝白（两招共色共用）
    {"source": "ultraman-jack/specium1_start", "legacy": "jack_specium1_start",
     "name": "zoffy_fx_m87_charge_start", "out": "m87_charge_start", "palette": PALETTE_M87,
     "refs": ["jack_specium1_start"]},
    # motion_214 弹体 + motion_236 光路突袭：ace_diamond 三段 银蓝白（两招共色共用一组）
    {"source": "ultraman-ace/diamond_flight", "legacy": "ace_diamond_flight",
     "name": "zoffy_fx_orb_flight", "out": "orb_flight", "palette": PALETTE_M87,
     "refs": ["ace_diamond_flight"]},
    {"source": "ultraman-ace/diamond_trail", "legacy": "ace_diamond_trail",
     "name": "zoffy_fx_orb_trail", "out": "orb_trail", "palette": PALETTE_M87,
     "refs": ["ace_diamond_trail"]},
    {"source": "ultraman-ace/diamond_hit", "legacy": "ace_diamond_hit",
     "name": "zoffy_fx_orb_hit", "out": "orb_hit", "palette": PALETTE_M87,
     "refs": ["ace_diamond_hit"]},
    # motion_623 队长升掌：jack_air_ray 三段
    {"source": "ultraman-jack/air_ray_flight", "legacy": "jack_air_ray_flight",
     "name": "zoffy_fx_rise_ray_flight", "out": "rise_ray_flight", "palette": PALETTE_M87,
     "refs": ["jack_air_ray_flight"]},
    {"source": "ultraman-jack/air_ray_trail", "legacy": "jack_air_ray_trail",
     "name": "zoffy_fx_rise_ray_trail", "out": "rise_ray_trail", "palette": PALETTE_M87,
     "refs": ["jack_air_ray_trail"]},
    {"source": "ultraman-jack/air_ray_hit", "legacy": "jack_air_ray_hit",
     "name": "zoffy_fx_rise_ray_hit", "out": "rise_ray_hit", "palette": PALETTE_M87,
     "refs": ["jack_air_ray_hit"]},
    # special Z光线：jack_short_{start,beam,hit} 蓝白电流短束
    {"source": "ultraman-jack/short_start", "legacy": "jack_short_start",
     "name": "zoffy_fx_zap_charge_start", "out": "zap_charge_start", "palette": PALETTE_ZAP,
     "refs": ["jack_short_start"]},
    {"source": "ultraman-jack/short_beam", "legacy": "jack_short_beam",
     "name": "zoffy_fx_zap_beam", "out": "zap_beam", "palette": PALETTE_ZAP,
     "refs": ["jack_short_beam"]},
    {"source": "ultraman-jack/short_hit", "legacy": "jack_short_hit",
     "name": "zoffy_fx_zap_hit", "out": "zap_hit", "palette": PALETTE_ZAP,
     "refs": ["jack_short_hit"]},
    # special2 超级冻霜：ace_diamond 四段 淡青白冷冻锥（仅 special2.json 分流）
    {"source": "ultraman-ace/diamond_start", "legacy": "ace_diamond_start",
     "name": "zoffy_fx_frost_charge_start", "out": "frost_charge_start", "palette": PALETTE_FROST,
     "refs": ["ace_diamond_start"], "only_in": ["special2.json"]},
    {"source": "ultraman-ace/diamond_flight", "legacy": "ace_diamond_flight",
     "name": "zoffy_fx_frost_flight", "out": "frost_flight", "palette": PALETTE_FROST,
     "refs": ["ace_diamond_flight"], "only_in": ["special2.json"]},
    {"source": "ultraman-ace/diamond_trail", "legacy": "ace_diamond_trail",
     "name": "zoffy_fx_frost_trail", "out": "frost_trail", "palette": PALETTE_FROST,
     "refs": ["ace_diamond_trail"], "only_in": ["special2.json"]},
    {"source": "ultraman-ace/diamond_hit", "legacy": "ace_diamond_hit",
     "name": "zoffy_fx_frost_hit", "out": "frost_hit", "palette": PALETTE_FROST,
     "refs": ["ace_diamond_hit"], "only_in": ["special2.json"]},
    # special3 M87光线束与命中
    {"source": "ultraman-jack/specium1_beam", "legacy": "jack_specium1_beam",
     "name": "zoffy_fx_m87_beam", "out": "m87_beam", "palette": PALETTE_M87,
     "refs": ["jack_specium1_beam"]},
    {"source": "ultraman-jack/specium1_hit", "legacy": "jack_specium1_hit",
     "name": "zoffy_fx_m87_hit", "out": "m87_hit", "palette": PALETTE_M87,
     "refs": ["jack_specium1_hit"]},
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    install("zoffy", "assets/effects/zoffy", FAMILIES, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
