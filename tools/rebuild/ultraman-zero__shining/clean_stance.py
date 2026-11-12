"""把通过照片门的待机照清成像素化的单参考图。

Alpha128 硬化、裁到主体、按站高 1100 等比缩放，再置入 1024×1536
透明画布（脚底 1410）。输出作为转像素整帧的唯一参考。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/media/art'))
from catalogue_native import harden_alpha, trim  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit('用法：clean_stance.py <输入照片> <输出清图>')
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    im = harden_alpha(Image.open(src).convert('RGBA'))
    im = trim(im)
    target_h = 1100
    scale = target_h / im.height
    im = im.resize((round(im.width * scale), target_h), Image.LANCZOS)
    im = harden_alpha(im)
    arr = np.array(im)
    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    im = im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    canvas = Image.new('RGBA', (1024, 1536), (0, 0, 0, 0))
    canvas.alpha_composite(im, (round(512 - im.width / 2), 1410 - im.height + 1))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    ca = np.array(canvas)
    visible = ca[:, :, 3] > 0
    cys, cxs = np.nonzero(visible)
    print('saved', out, canvas.size, 'bbox',
          [int(cxs.min()), int(cys.min()), int(cxs.max()), int(cys.max())],
          'foot_row', int(cys.max()), 'standing', int(cys.max() - cys.min() + 1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
