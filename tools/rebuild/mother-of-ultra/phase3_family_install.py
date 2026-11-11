"""奥母特效家族装配：ace/jack 借用段全部换成 mother_fx_* 自制重着色段。

色板按招式表（content/fighters/mother-of-ultra/moves/*.json data_source）：
  motion_214 奥特耳光   红金充能（同 special2 母亲破坏光线红金系）
  motion_236/623 双掌连推/升掌迎击 白金治疗系光
  special    母亲光线   蓝白治疗束
  special2   母亲破坏光线 红金大束
  special3   母亲淋浴   青绿白再生光
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
import argparse

from phase3_family_install import ROOT, install

# 奥母光色锚点（亮→暗）
PALETTE_RED_GOLD = ["#fffef4", "#ffe9a8", "#ffc23e", "#ff8a1e", "#c85a10"]   # 红金破坏系
PALETTE_BLUE_WHITE = ["#ffffff", "#eaf6ff", "#bfe0ff", "#7ab6f2", "#2f6ecf"]  # 蓝白治疗系
PALETTE_PLATINUM = ["#ffffff", "#fdf6df", "#f5e3ae", "#d9c27a", "#9a824a"]    # 白金充电系
PALETTE_MINT = ["#ffffff", "#e9fff6", "#bdf2df", "#6fd8b8", "#2e9e82"]        # 青绿再生系

FAMILIES = [
    # motion_214 奥特耳光：ace_metalium2_start 充能 → 红金；ace_diamond_{flight,trail} 弹体 → 红金；ace_diamond_hit 命中 → 红金
    {"source": "ultraman-ace/metalium2_start", "legacy": "ace_metalium2_start",
     "name": "mother_fx_slap_charge_start", "out": "slap_charge_start", "palette": PALETTE_RED_GOLD,
     "refs": ["ace_metalium2_start"]},
    {"source": "ultraman-ace/diamond_flight", "legacy": "ace_diamond_flight",
     "name": "mother_fx_slap_orb_flight", "out": "slap_orb_flight", "palette": PALETTE_RED_GOLD,
     "refs": ["ace_diamond_flight"]},
    {"source": "ultraman-ace/diamond_trail", "legacy": "ace_diamond_trail",
     "name": "mother_fx_slap_orb_trail", "out": "slap_orb_trail", "palette": PALETTE_RED_GOLD,
     "refs": ["ace_diamond_trail"]},
    {"source": "ultraman-ace/diamond_hit", "legacy": "ace_diamond_hit",
     "name": "mother_fx_slap_orb_hit", "out": "slap_orb_hit", "palette": PALETTE_RED_GOLD,
     "refs": ["ace_diamond_hit"]},
    # motion_236/623 双掌连推/升掌迎击：jack_air_ray → 白金
    {"source": "ultraman-jack/air_ray_flight", "legacy": "jack_air_ray_flight",
     "name": "mother_fx_palm_ray_flight", "out": "palm_ray_flight", "palette": PALETTE_PLATINUM,
     "refs": ["jack_air_ray_flight"]},
    {"source": "ultraman-jack/air_ray_trail", "legacy": "jack_air_ray_trail",
     "name": "mother_fx_palm_ray_trail", "out": "palm_ray_trail", "palette": PALETTE_PLATINUM,
     "refs": ["jack_air_ray_trail"]},
    {"source": "ultraman-jack/air_ray_hit", "legacy": "jack_air_ray_hit",
     "name": "mother_fx_palm_ray_hit", "out": "palm_ray_hit", "palette": PALETTE_PLATINUM,
     "refs": ["jack_air_ray_hit"]},
    # special 母亲光线：jack_specium1_{start,beam,hit} → 蓝白
    {"source": "ultraman-jack/specium1_start", "legacy": "jack_specium1_start",
     "name": "mother_fx_ray_charge_start", "out": "ray_charge_start", "palette": PALETTE_BLUE_WHITE,
     "refs": ["jack_specium1_start"]},
    {"source": "ultraman-jack/specium1_beam", "legacy": "jack_specium1_beam",
     "name": "mother_fx_ray_beam", "out": "ray_beam", "palette": PALETTE_BLUE_WHITE,
     "refs": ["jack_specium1_beam"]},
    {"source": "ultraman-jack/specium1_hit", "legacy": "jack_specium1_hit",
     "name": "mother_fx_ray_hit", "out": "ray_hit", "palette": PALETTE_BLUE_WHITE,
     "refs": ["jack_specium1_hit"]},
    # special2 母亲破坏光线：ace_metalium2_{beam,hit} → 红金
    {"source": "ultraman-ace/metalium2_beam", "legacy": "ace_metalium2_beam",
     "name": "mother_fx_buster_beam", "out": "buster_beam", "palette": PALETTE_RED_GOLD,
     "refs": ["ace_metalium2_beam"]},
    {"source": "ultraman-ace/metalium2_hit", "legacy": "ace_metalium2_hit",
     "name": "mother_fx_buster_hit", "out": "buster_hit", "palette": PALETTE_RED_GOLD,
     "refs": ["ace_metalium2_hit"]},
    # special3 母亲淋浴：jack_specium1_start 复用为青绿再生蓄力（仅 special3.json 分流）
    {"source": "ultraman-jack/specium1_start", "legacy": "jack_specium1_start",
     "name": "mother_fx_shower_charge_start", "out": "shower_charge_start", "palette": PALETTE_MINT,
     "refs": ["jack_specium1_start"], "only_in": ["special3.json"]},
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    install("mother-of-ultra", "assets/effects/mother-of-ultra", FAMILIES, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
