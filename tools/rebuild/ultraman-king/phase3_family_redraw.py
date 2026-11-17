"""奥王特效家族自绘：king_fx_* 全部改为 PixelFX 离线烘焙的原创像素形状。

光色按招式表（content/fighters/ultraman-king/moves/*.json data_source）：
  special    王者闪光   红色玛瑙状破坏光线
  special2   洗礼光线   胸前红宝玉聚能后的红色能量箭
  special3   王者再生光线 全身泛蓝光的蓝色再生光线
  motion_236/623 连步双掌/升膝迎击 白金神圣系

不沿用 jack/teo/leo 借用图集的轮廓；rects、anchor、ticks、frame_boxes 与招式数值不动。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from phase3_family_redraw import main

# 奥王光色锚点（暗→亮）
PALETTE_DIVINE = ["#2a1a06", "#4e330c", "#7a5a14", "#a8821e", "#d9ae3c", "#f2d878", "#fff0c4", "#ffffff"]
PALETTE_RED_FLASHER = ["#2a0501", "#5e1006", "#7e1408", "#d8381c", "#ff9464", "#ffdfc8", "#ffffff"]
PALETTE_RED_ARROW = ["#2a0402", "#521006", "#6e0e06", "#c22e14", "#ff7e50", "#ffd6c2", "#ffffff"]
PALETTE_HOLY_BLUE = ["#081630", "#102a5a", "#2656b8", "#6a9ce8", "#b8d8ff", "#eaf4ff", "#ffffff"]

FAMILIES = [
    # special 王者闪光：红色玛瑙状光线
    {"name": "king_fx_flasher_charge_start", "out": "flasher_charge_start", "kind": "charge", "palette": PALETTE_RED_FLASHER},
    {"name": "king_fx_flasher_beam", "out": "flasher_beam", "kind": "beam", "palette": PALETTE_RED_FLASHER},
    {"name": "king_fx_flasher_hit", "out": "flasher_hit", "kind": "hit", "palette": PALETTE_RED_FLASHER},
    # motion_236/623 连步双掌/升膝迎击：白金能量箭
    {"name": "king_fx_palm_arrow_flight", "out": "palm_arrow_flight", "kind": "arrow", "palette": PALETTE_DIVINE},
    {"name": "king_fx_palm_arrow_trail", "out": "palm_arrow_trail", "kind": "trail", "palette": PALETTE_DIVINE},
    {"name": "king_fx_palm_arrow_hit", "out": "palm_arrow_hit", "kind": "hit", "palette": PALETTE_DIVINE},
    # special2 洗礼光线：胸前红宝玉聚能的红色能量箭
    {"name": "king_fx_baptism_arrow_start", "out": "baptism_arrow_start", "kind": "charge", "palette": PALETTE_RED_ARROW},
    {"name": "king_fx_baptism_arrow_flight", "out": "baptism_arrow_flight", "kind": "arrow", "palette": PALETTE_RED_ARROW},
    {"name": "king_fx_baptism_arrow_trail", "out": "baptism_arrow_trail", "kind": "trail", "palette": PALETTE_RED_ARROW},
    {"name": "king_fx_baptism_arrow_hit", "out": "baptism_arrow_hit", "kind": "hit", "palette": PALETTE_RED_ARROW},
    # special3 王者再生光线：蓝白再生光
    {"name": "king_fx_rebirth_charge_start", "out": "rebirth_charge_start", "kind": "charge", "palette": PALETTE_HOLY_BLUE},
    {"name": "king_fx_rebirth_beam", "out": "rebirth_beam", "kind": "beam", "palette": PALETTE_HOLY_BLUE},
    {"name": "king_fx_rebirth_hit", "out": "rebirth_hit", "kind": "hit", "palette": PALETTE_HOLY_BLUE},
]

if __name__ == "__main__":
    main("ultraman-king", FAMILIES)
