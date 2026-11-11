"""奥母特效家族自绘：mother_fx_* 全部改为 PixelFX 离线烘焙的原创像素形状。

光色按招式表（content/fighters/mother-of-ultra/moves/*.json data_source）：
  special    母亲光线   蓝白治疗束
  special2   母亲破坏光线 红金大束
  special3   母亲淋浴   青绿白再生光
  motion_214 奥特耳光   红金充能
  motion_236/623 双掌连推/升掌迎击 白金治疗系光

不沿用 ace/jack 借用图集的轮廓；rects、anchor、ticks、frame_boxes 与招式数值不动。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from phase3_family_redraw import main

# 奥母光色锚点（暗→亮）
PALETTE_RED_GOLD = ["#2e0802", "#5e1406", "#8f2a08", "#c85a10", "#ff8a1e", "#ffc23e", "#fffef4"]
PALETTE_BLUE_WHITE = ["#081826", "#0f3048", "#1c4a7a", "#2f6ecf", "#7ab6f2", "#bfe0ff", "#ffffff"]
PALETTE_PLATINUM = ["#2a200a", "#4e3c12", "#7a6228", "#9a824a", "#d9c27a", "#f5e3ae", "#ffffff"]
PALETTE_MINT = ["#062018", "#0a3026", "#1e6a52", "#2e9e82", "#6fd8b8", "#bdf2df", "#ffffff"]

FAMILIES = [
    # motion_214 奥特耳光：红金聚能 → 光团 → 命中
    {"name": "mother_fx_slap_charge_start", "out": "slap_charge_start", "kind": "charge", "palette": PALETTE_RED_GOLD},
    {"name": "mother_fx_slap_orb_flight", "out": "slap_orb_flight", "kind": "orb", "palette": PALETTE_RED_GOLD},
    {"name": "mother_fx_slap_orb_trail", "out": "slap_orb_trail", "kind": "trail", "palette": PALETTE_RED_GOLD},
    {"name": "mother_fx_slap_orb_hit", "out": "slap_orb_hit", "kind": "hit", "palette": PALETTE_RED_GOLD},
    # motion_236/623 双掌连推/升掌迎击：白金掌光
    {"name": "mother_fx_palm_ray_flight", "out": "palm_ray_flight", "kind": "bolt", "palette": PALETTE_PLATINUM},
    {"name": "mother_fx_palm_ray_trail", "out": "palm_ray_trail", "kind": "trail", "palette": PALETTE_PLATINUM},
    {"name": "mother_fx_palm_ray_hit", "out": "palm_ray_hit", "kind": "hit", "palette": PALETTE_PLATINUM},
    # special 母亲光线：蓝白治疗束
    {"name": "mother_fx_ray_charge_start", "out": "ray_charge_start", "kind": "charge", "palette": PALETTE_BLUE_WHITE},
    {"name": "mother_fx_ray_beam", "out": "ray_beam", "kind": "beam", "palette": PALETTE_BLUE_WHITE},
    {"name": "mother_fx_ray_hit", "out": "ray_hit", "kind": "hit", "palette": PALETTE_BLUE_WHITE},
    # special2 母亲破坏光线：红金大束
    {"name": "mother_fx_buster_beam", "out": "buster_beam", "kind": "beam", "palette": PALETTE_RED_GOLD},
    {"name": "mother_fx_buster_hit", "out": "buster_hit", "kind": "hit", "palette": PALETTE_RED_GOLD},
    # special3 母亲淋浴：青绿白再生光
    {"name": "mother_fx_shower_charge_start", "out": "shower_charge_start", "kind": "charge", "palette": PALETTE_MINT},
]

if __name__ == "__main__":
    main("mother-of-ultra", FAMILIES)
