# 临时诊断：举拳/举臂帧用眼列定位头壳宽度，避免顶部带宽把拳并入头。
import sys
import numpy as np
from PIL import Image

def measure(path):
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    alpha = a[:, :, 3] > 128
    ys = np.nonzero(alpha.any(axis=1))[0]
    top, bottom = int(ys.min()), int(ys.max())
    h = bottom - top + 1
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    eye = alpha & (r > 180) & (g > 140) & (b < 120)
    eye[: top + int(h * 0.02)] = False
    eye[top + int(h * 0.35):] = False
    eys, exs = np.nonzero(eye)
    if not len(eys):
        return None
    ey = int(np.median(eys))
    ex = int(np.median(exs))
    def run_at(y, x):
        row = alpha[y]
        if not row[x]:
            return 0
        x0 = x
        while x0 > 0 and row[x0 - 1]:
            x0 -= 1
        x1 = x
        while x1 + 1 < len(row) and row[x1 + 1]:
            x1 += 1
        return x1 - x0 + 1, x0, x1
    best = (0, ey, 0, 0)
    for y in range(max(top, ey - int(h * 0.03)), min(bottom, ey + int(h * 0.05))):
        # 只跟踪包含眼列的连通行段；允许眼列在头壳内偏左/右，取覆盖 eye x 的段
        res = run_at(y, ex)
        if not res:
            continue
        w, x0, x1 = res
        if w > best[0]:
            best = (w, y, x0, x1)
    return {"eye_y": ey, "eye_x": ex, "headw": best[0], "row": best[1],
            "span": [best[2], best[3]], "bbox": [top, bottom]}

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p.split("/")[-1], measure(p))
