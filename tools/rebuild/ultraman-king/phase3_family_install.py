"""奥王特效家族装配：jack/teo/leo 借用段全部换成 king_fx_* 自制重着色段。

色板按招式表（content/fighters/ultraman-king/moves/*.json data_source）：
  special    王者闪光   红色玛瑙状破坏光线（登记雷欧时期黄色/UGF 红色冲突，本作取红）
  special2   洗礼光线   胸前红宝玉聚能后的红色能量箭
  special3   王者再生光线 全身泛蓝光的蓝色再生光线
  motion_236/623 连步双掌/升膝迎击 白金神圣系（奥王白金/神圣金基调）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from phase3_family_install import install

# 奥王光色锚点（亮→暗）
PALETTE_DIVINE = ["#ffffff", "#fdf6df", "#f5e3ae", "#d9c27a", "#9a824a"]     # 白金神圣金
PALETTE_RED_FLASHER = ["#ffffff", "#ffdfc8", "#ff9464", "#d8381c", "#7e1408"]  # 红玛瑙破坏光线
PALETTE_RED_ARROW = ["#ffffff", "#ffd6c2", "#ff7e50", "#c22e14", "#6e0e06"]    # 红色能量箭
PALETTE_HOLY_BLUE = ["#ffffff", "#eaf4ff", "#b8d8ff", "#6a9ce8", "#2656b8"]    # 蓝白再生光线

FAMILIES = [
    # special 王者闪光：leo_lion_{start,beam,hit} 红玛瑙光线
    {"source": "ultraman-leo/lion_start", "legacy": "leo_lion_start",
     "name": "king_fx_flasher_charge_start", "out": "flasher_charge_start", "palette": PALETTE_RED_FLASHER,
     "refs": ["leo_lion_start"]},
    {"source": "ultraman-leo/lion_beam", "legacy": "leo_lion_beam",
     "name": "king_fx_flasher_beam", "out": "flasher_beam", "palette": PALETTE_RED_FLASHER,
     "refs": ["leo_lion_beam"]},
    {"source": "ultraman-leo/lion_hit", "legacy": "leo_lion_hit",
     "name": "king_fx_flasher_hit", "out": "flasher_hit", "palette": PALETTE_RED_FLASHER,
     "refs": ["leo_lion_hit"]},
    # motion_236/623 连步双掌/升膝迎击：teo_episode11_arrow 三段 白金神圣系
    {"source": "ultraman-teo/episode11_arrow_flight", "legacy": "teo_episode11_arrow_flight",
     "name": "king_fx_palm_arrow_flight", "out": "palm_arrow_flight", "palette": PALETTE_DIVINE,
     "refs": ["teo_episode11_arrow_flight"]},
    {"source": "ultraman-teo/episode11_arrow_trail", "legacy": "teo_episode11_arrow_trail",
     "name": "king_fx_palm_arrow_trail", "out": "palm_arrow_trail", "palette": PALETTE_DIVINE,
     "refs": ["teo_episode11_arrow_trail"]},
    {"source": "ultraman-teo/episode11_arrow_hit", "legacy": "teo_episode11_arrow_hit",
     "name": "king_fx_palm_arrow_hit", "out": "palm_arrow_hit", "palette": PALETTE_DIVINE,
     "refs": ["teo_episode11_arrow_hit"]},
    # special2 洗礼光线：teo_episode11_arrow_{start,flight,trail,hit} 红色能量箭（仅 special2.json 分流）
    {"source": "ultraman-teo/episode11_arrow_start", "legacy": "teo_episode11_arrow_start",
     "name": "king_fx_baptism_arrow_start", "out": "baptism_arrow_start", "palette": PALETTE_RED_ARROW,
     "refs": ["teo_episode11_arrow_start"], "only_in": ["special2.json"]},
    {"source": "ultraman-teo/episode11_arrow_flight", "legacy": "teo_episode11_arrow_flight",
     "name": "king_fx_baptism_arrow_flight", "out": "baptism_arrow_flight", "palette": PALETTE_RED_ARROW,
     "refs": ["teo_episode11_arrow_flight"], "only_in": ["special2.json"]},
    {"source": "ultraman-teo/episode11_arrow_trail", "legacy": "teo_episode11_arrow_trail",
     "name": "king_fx_baptism_arrow_trail", "out": "baptism_arrow_trail", "palette": PALETTE_RED_ARROW,
     "refs": ["teo_episode11_arrow_trail"], "only_in": ["special2.json"]},
    {"source": "ultraman-teo/episode11_arrow_hit", "legacy": "teo_episode11_arrow_hit",
     "name": "king_fx_baptism_arrow_hit", "out": "baptism_arrow_hit", "palette": PALETTE_RED_ARROW,
     "refs": ["teo_episode11_arrow_hit"], "only_in": ["special2.json"]},
    # special3 王者再生光线：jack_cinerama_{start,beam,hit} 蓝白
    {"source": "ultraman-jack/cinerama_start", "legacy": "jack_cinerama_start",
     "name": "king_fx_rebirth_charge_start", "out": "rebirth_charge_start", "palette": PALETTE_HOLY_BLUE,
     "refs": ["jack_cinerama_start"]},
    {"source": "ultraman-jack/cinerama_beam", "legacy": "jack_cinerama_beam",
     "name": "king_fx_rebirth_beam", "out": "rebirth_beam", "palette": PALETTE_HOLY_BLUE,
     "refs": ["jack_cinerama_beam"]},
    {"source": "ultraman-jack/cinerama_hit", "legacy": "jack_cinerama_hit",
     "name": "king_fx_rebirth_hit", "out": "rebirth_hit", "palette": PALETTE_HOLY_BLUE,
     "refs": ["jack_cinerama_hit"]},
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    install("ultraman-king", "assets/effects/ultraman-king", FAMILIES, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
