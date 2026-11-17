"""盖亚特效家族自绘：gaia_fx_* 全部改为 PixelFX 离线烘焙的原创像素形状。

光色按招式表（content/fighters/ultraman-gaia/moves/*.json data_source）：
  motion_214 盖亚切割   红色三日月光刃（V2）
  motion_236/623 双掌连推/升膝迎击 红蓝量子系白光
  special    光子冰刀   粉红/红光刃
  special2   量子流线   红色超高热光线
  special3   光子粉碎机 红色（V2 继承阿古茹，带红色光）

不沿用 ace/jack/omega 借用图集的轮廓；rects、anchor、ticks、frame_boxes、
frame_hitboxes 与招式数值不动。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from phase3_family_redraw import main

# 盖亚光色锚点（暗→亮）
PALETTE_RED_BLADE = ["#2e0602", "#5e0e06", "#8f1a0c", "#e83a20", "#ff8a5e", "#ffd9c4", "#ffffff"]
PALETTE_PINK_EDGE = ["#2e0610", "#5e0e22", "#8f1e50", "#e8488a", "#ff9ec4", "#ffe4ef", "#ffffff"]
PALETTE_RED_BEAM = ["#2e0602", "#5e0e04", "#96200e", "#e84a28", "#ff9a66", "#ffdfd0", "#ffffff"]
PALETTE_QUANTUM = ["#0a1020", "#14204a", "#32418f", "#6a86d8", "#a9c8f2", "#e2f2ff", "#ffffff"]

FAMILIES = [
    # motion_214 盖亚切割：红色光刃
    {"name": "gaia_fx_slash_charge_start", "out": "slash_charge_start", "kind": "charge", "palette": PALETTE_RED_BLADE},
    {"name": "gaia_fx_slash_flight", "out": "slash_flight", "kind": "blade", "palette": PALETTE_RED_BLADE},
    {"name": "gaia_fx_slash_trail", "out": "slash_trail", "kind": "trail_diag", "palette": PALETTE_RED_BLADE},
    {"name": "gaia_fx_slash_hit", "out": "slash_hit", "kind": "hit", "palette": PALETTE_RED_BLADE},
    # motion_236/623 双掌连推/升膝迎击：量子蓝白掌光
    {"name": "gaia_fx_palm_ray_flight", "out": "palm_ray_flight", "kind": "bolt", "palette": PALETTE_QUANTUM},
    {"name": "gaia_fx_palm_ray_trail", "out": "palm_ray_trail", "kind": "trail", "palette": PALETTE_QUANTUM},
    {"name": "gaia_fx_palm_ray_hit", "out": "palm_ray_hit", "kind": "hit", "palette": PALETTE_QUANTUM},
    # special 光子冰刀：粉红光刃
    {"name": "gaia_fx_edge_charge_start", "out": "edge_charge_start", "kind": "charge", "palette": PALETTE_PINK_EDGE},
    {"name": "gaia_fx_edge_hit", "out": "edge_hit", "kind": "hit", "palette": PALETTE_PINK_EDGE},
    # special2 量子流线：红色超高热光线
    {"name": "gaia_fx_stream_charge_start", "out": "stream_charge_start", "kind": "charge", "palette": PALETTE_RED_BEAM},
    {"name": "gaia_fx_stream_beam", "out": "stream_beam", "kind": "beam", "palette": PALETTE_RED_BEAM},
    {"name": "gaia_fx_stream_hit", "out": "stream_hit", "kind": "hit", "palette": PALETTE_RED_BEAM},
    # special3 光子粉碎机：红色大束（保留发射根点与逐相判定）
    {"name": "gaia_fx_crusher_charge_start", "out": "crusher_charge_start", "kind": "charge", "palette": PALETTE_RED_BEAM},
    {"name": "gaia_fx_crusher_beam", "out": "crusher_beam", "kind": "beam", "palette": PALETTE_RED_BEAM},
    {"name": "gaia_fx_crusher_hit", "out": "crusher_hit", "kind": "hit", "palette": PALETTE_RED_BEAM},
]

if __name__ == "__main__":
    main("ultraman-gaia", FAMILIES)
