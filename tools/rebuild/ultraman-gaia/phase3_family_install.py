"""盖亚特效家族装配：ace/jack/omega 借用段全部换成 gaia_fx_* 自制重着色段。

色板按招式表（content/fighters/ultraman-gaia/moves/*.json data_source）：
  motion_214 盖亚切割   红色三日月光刃（V2）
  motion_236/623 双掌连推/升膝迎击 红蓝量子系白光
  special    光子冰刀   粉红/红光刃
  special2   量子流线   红色超高热光线
  special3   光子粉碎机 红色（V2 继承阿古茹，带红色光）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from phase3_family_install import install

# 盖亚光色锚点（亮→暗）
PALETTE_RED_BLADE = ["#ffffff", "#ffd9c4", "#ff8a5e", "#e83a20", "#8f1a0c"]    # 红光刃
PALETTE_PINK_EDGE = ["#ffffff", "#ffe4ef", "#ff9ec4", "#e8488a", "#8f1e50"]    # 粉红冰刀
PALETTE_RED_BEAM = ["#ffffff", "#ffdfd0", "#ff9a66", "#e84a28", "#96200e"]     # 红色大束
PALETTE_QUANTUM = ["#ffffff", "#e2f2ff", "#a9c8f2", "#6a86d8", "#32418f"]      # 量子蓝白（连推/升膝）

FAMILIES = [
    # motion_214 盖亚切割：ace_vertical_blade_{start,flight,trail,hit} → 红
    {"source": "ultraman-ace/vertical_blade_start", "legacy": "ace_vertical_blade_start",
     "name": "gaia_fx_slash_charge_start", "out": "slash_charge_start", "palette": PALETTE_RED_BLADE,
     "refs": ["ace_vertical_blade_start"]},
    {"source": "ultraman-ace/vertical_blade_flight", "legacy": "ace_vertical_blade_flight",
     "name": "gaia_fx_slash_flight", "out": "slash_flight", "palette": PALETTE_RED_BLADE,
     "refs": ["ace_vertical_blade_flight"]},
    {"source": "ultraman-ace/vertical_blade_trail", "legacy": "ace_vertical_blade_trail",
     "name": "gaia_fx_slash_trail", "out": "slash_trail", "palette": PALETTE_RED_BLADE,
     "refs": ["ace_vertical_blade_trail"]},
    {"source": "ultraman-ace/vertical_blade_hit", "legacy": "ace_vertical_blade_hit",
     "name": "gaia_fx_slash_hit", "out": "slash_hit", "palette": PALETTE_RED_BLADE,
     "refs": ["ace_vertical_blade_hit"]},
    # motion_236/623 双掌连推/升膝迎击：jack_air_ray → 量子蓝白
    {"source": "ultraman-jack/air_ray_flight", "legacy": "jack_air_ray_flight",
     "name": "gaia_fx_palm_ray_flight", "out": "palm_ray_flight", "palette": PALETTE_QUANTUM,
     "refs": ["jack_air_ray_flight"]},
    {"source": "ultraman-jack/air_ray_trail", "legacy": "jack_air_ray_trail",
     "name": "gaia_fx_palm_ray_trail", "out": "palm_ray_trail", "palette": PALETTE_QUANTUM,
     "refs": ["jack_air_ray_trail"]},
    {"source": "ultraman-jack/air_ray_hit", "legacy": "jack_air_ray_hit",
     "name": "gaia_fx_palm_ray_hit", "out": "palm_ray_hit", "palette": PALETTE_QUANTUM,
     "refs": ["jack_air_ray_hit"]},
    # special 光子冰刀：ace_vertical_blade_{start,hit} → 粉红（仅 special.json 分流）
    {"source": "ultraman-ace/vertical_blade_start", "legacy": "ace_vertical_blade_start",
     "name": "gaia_fx_edge_charge_start", "out": "edge_charge_start", "palette": PALETTE_PINK_EDGE,
     "refs": ["ace_vertical_blade_start"], "only_in": ["special.json"]},
    {"source": "ultraman-ace/vertical_blade_hit", "legacy": "ace_vertical_blade_hit",
     "name": "gaia_fx_edge_hit", "out": "edge_hit", "palette": PALETTE_PINK_EDGE,
     "refs": ["ace_vertical_blade_hit"], "only_in": ["special.json"]},
    # special2 量子流线：jack_specium2_{start,beam,hit} → 红
    {"source": "ultraman-jack/specium2_start", "legacy": "jack_specium2_start",
     "name": "gaia_fx_stream_charge_start", "out": "stream_charge_start", "palette": PALETTE_RED_BEAM,
     "refs": ["jack_specium2_start"]},
    {"source": "ultraman-jack/specium2_beam", "legacy": "jack_specium2_beam",
     "name": "gaia_fx_stream_beam", "out": "stream_beam", "palette": PALETTE_RED_BEAM,
     "refs": ["jack_specium2_beam"]},
    {"source": "ultraman-jack/specium2_hit", "legacy": "jack_specium2_hit",
     "name": "gaia_fx_stream_hit", "out": "stream_hit", "palette": PALETTE_RED_BEAM,
     "refs": ["jack_specium2_hit"]},
    # special3 光子粉碎机：omega_special2_{start,beam,hit} → 红金
    {"source": "ultraman-omega/special2_start", "legacy": "omega_special2_start",
     "name": "gaia_fx_crusher_charge_start", "out": "crusher_charge_start", "palette": PALETTE_RED_BEAM,
     "refs": ["omega_special2_start"]},
    {"source": "ultraman-omega/special2_beam", "legacy": "omega_special2_beam",
     "name": "gaia_fx_crusher_beam", "out": "crusher_beam", "palette": PALETTE_RED_BEAM,
     "refs": ["omega_special2_beam"]},
    {"source": "ultraman-omega/special2_hit", "legacy": "omega_special2_hit",
     "name": "gaia_fx_crusher_hit", "out": "crusher_hit", "palette": PALETTE_RED_BEAM,
     "refs": ["omega_special2_hit"]},
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    install("ultraman-gaia", "assets/effects/ultraman-gaia", FAMILIES, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
