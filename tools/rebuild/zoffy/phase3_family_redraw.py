"""佐菲特效家族自绘：zoffy_fx_* 全部改为 PixelFX 离线烘焙的原创像素形状。

光色按招式表（content/fighters/zoffy/moves/*.json data_source）：
  special    Z光线      蓝白短束电流
  special2   超级冻霜   淡青白冷冻锥
  special3   M87光线    银蓝白主束
  motion_214 超级充能·崩掌 银蓝白
  motion_236/623 光路突袭/队长升掌 银蓝白

不沿用 ace/jack 借用图集的轮廓；rects、anchor、ticks、frame_boxes 与招式数值不动。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from phase3_family_redraw import main

# 佐菲光色锚点（暗→亮）
PALETTE_M87 = ["#081630", "#102a5a", "#2f6ecf", "#7ab6f2", "#cfe6ff", "#f2f9ff", "#ffffff"]
PALETTE_ZAP = ["#081226", "#102650", "#2456b8", "#6a9fe8", "#bfe0ff", "#eef6ff", "#ffffff"]
PALETTE_FROST = ["#06202a", "#0c4050", "#3a96b8", "#7ecfdc", "#c2efe8", "#eefcfa", "#ffffff"]

FAMILIES = [
    # motion_214 超级充能·崩掌 + special3 M87 蓄力：银蓝白
    {"name": "zoffy_fx_m87_charge_start", "out": "m87_charge_start", "kind": "charge", "palette": PALETTE_M87},
    # motion_214 弹体 + motion_236 光路突袭：银蓝白光团
    {"name": "zoffy_fx_orb_flight", "out": "orb_flight", "kind": "orb", "palette": PALETTE_M87},
    {"name": "zoffy_fx_orb_trail", "out": "orb_trail", "kind": "trail", "palette": PALETTE_M87},
    {"name": "zoffy_fx_orb_hit", "out": "orb_hit", "kind": "hit", "palette": PALETTE_M87},
    # motion_623 队长升掌：银蓝白掌光
    {"name": "zoffy_fx_rise_ray_flight", "out": "rise_ray_flight", "kind": "bolt", "palette": PALETTE_M87},
    {"name": "zoffy_fx_rise_ray_trail", "out": "rise_ray_trail", "kind": "trail", "palette": PALETTE_M87},
    {"name": "zoffy_fx_rise_ray_hit", "out": "rise_ray_hit", "kind": "hit", "palette": PALETTE_M87},
    # special Z光线：蓝白电流短束
    {"name": "zoffy_fx_zap_charge_start", "out": "zap_charge_start", "kind": "charge", "palette": PALETTE_ZAP},
    {"name": "zoffy_fx_zap_beam", "out": "zap_beam", "kind": "beam", "palette": PALETTE_ZAP},
    {"name": "zoffy_fx_zap_hit", "out": "zap_hit", "kind": "hit", "palette": PALETTE_ZAP},
    # special2 超级冻霜：淡青白冷冻锥
    {"name": "zoffy_fx_frost_charge_start", "out": "frost_charge_start", "kind": "charge", "palette": PALETTE_FROST},
    {"name": "zoffy_fx_frost_flight", "out": "frost_flight", "kind": "orb", "palette": PALETTE_FROST},
    {"name": "zoffy_fx_frost_trail", "out": "frost_trail", "kind": "trail", "palette": PALETTE_FROST},
    {"name": "zoffy_fx_frost_hit", "out": "frost_hit", "kind": "hit", "palette": PALETTE_FROST},
    # special3 M87光线：银蓝白主束
    {"name": "zoffy_fx_m87_beam", "out": "m87_beam", "kind": "beam", "palette": PALETTE_M87},
    {"name": "zoffy_fx_m87_hit", "out": "m87_hit", "kind": "hit", "palette": PALETTE_M87},
]

if __name__ == "__main__":
    main("zoffy", FAMILIES)
