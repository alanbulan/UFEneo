"""佐菲 stage1 20261111 批次逐帧自检。

用法: .venv/bin/python tools/art/zoffy_20261111_selfcheck.py <路径...> [--crouch ...]
检查: 实收尺寸、RGBA Alpha、bbox 宽高比、红像素数、主体 bbox 高度（体型一致性门）。
"""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image

# 体型一致性门（coordinator 20261111 追加硬规则）：
# 锚 raw-01-v4 主体高 1528 px；站姿类帧主体高应大致与锚一致。
# 硬带：1375–1681 px（锚 ±10%）。蹲/腾空/被投/大幅前扑等姿势可出带但须登记。
STAND_H_MIN = 1375
STAND_H_MAX = 1681
RATIO_MIN = 0.3
RATIO_MAX = 2.6
RED_MIN = 150


def check(path: str, standing: bool = True) -> dict:
    img = Image.open(path).convert("RGBA")
    a = np.array(img)
    alpha = a[:, :, 3]
    ys, xs = np.where(alpha >= 200)
    if len(ys) == 0:
        return {"path": path, "ok": False, "reason": ["无主体(alpha>=200为空)"], "size": img.size}
    w = int(xs.max() - xs.min() + 1)
    h = int(ys.max() - ys.min() + 1)
    r, g, b = (a[:, :, i].astype(int) for i in range(3))
    red = int(((r > 150) & (g < 80) & (b < 80) & (alpha > 0)).sum())
    size_ok = img.size == (1024, 1536)
    ratio = w / h
    ratio_ok = RATIO_MIN <= ratio <= RATIO_MAX
    red_ok = red >= RED_MIN
    h_ok = STAND_H_MIN <= h <= STAND_H_MAX
    ok = size_ok and ratio_ok and red_ok and (h_ok or not standing)
    fails = []
    if not size_ok:
        fails.append("尺寸")
    if not ratio_ok:
        fails.append("宽高比")
    if not red_ok:
        fails.append("红像素")
    if standing and not h_ok:
        fails.append("站高")
    return {
        "path": path,
        "ok": ok,
        "size": img.size,
        "w": w,
        "h": h,
        "ratio": round(ratio, 3),
        "red": red,
        "standing": standing,
        "fails": fails,
    }


def main(argv: list[str]) -> int:
    # --crouch 后的文件按非站姿处理（仍登记数值）
    paths: list[tuple[str, bool]] = []
    standing = True
    for arg in argv:
        if arg == "--crouch":
            standing = False
            continue
        paths.append((arg, standing))
    bad = 0
    for path, st in paths:
        r = check(path, standing=st)
        tag = "PASS" if r["ok"] else "FAIL " + ",".join(r["fails"])
        crouch_tag = "" if r["standing"] else " [非站姿登记]"
        print(f"{tag}{crouch_tag} {r['path']} size={r['size']} w={r['w']} h={r['h']} ratio={r['ratio']} red={r['red']}")
        if not r["ok"]:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
