"""从已装待机像素整帧裁出 36×36 HUD 肖像。

HUD 只读 `content/roster/selection.json` 的 `hud_portrait`（缺失时回退主题图标，
再回退 locked）。新角色没有主题图标，直接由待机身份锚裁头肩是最小改动：同一
像素画风、不重新生成身份；裁切以头部列带中心为准，保留头冠/双角完整（头宽大于
36 px 的角色按头宽取正方形后最近邻缩到 36）。

用法：
    .venv/bin/python tools/art/make_hud_portraits.py            # 只生成 PNG
    .venv/bin/python tools/art/make_hud_portraits.py --write     # 同时写 selection.json
    .venv/bin/python tools/art/make_hud_portraits.py --fighter ultraman-zero
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NEW = [
    "ultraman-justice", "ultraman-zero", "zoffy", "mother-of-ultra",
    "ultraman-gaia", "ultraman-king", "father-of-ultra",
]
ICON = 36


def head_crop(im: Image.Image) -> Image.Image:
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > 0)
    if not len(ys):
        raise SystemExit("待机帧为空")
    top, bottom = int(ys.min()), int(ys.max())
    # 只取顶部 24% 列带估头宽；披风/举拳不影响待机帧顶部。
    band = a[top:top + max(4, int((bottom - top) * 0.24))]
    bys, bxs = np.where(band)
    if not len(bxs):
        raise SystemExit("头部列带为空")
    cx = int(round((bxs.min() + bxs.max()) / 2))
    head_w = int(bxs.max() - bxs.min() + 1)
    side = max(40, head_w + 10)
    x0 = max(0, min(im.width - side, cx - side // 2))
    y0 = max(0, top - 3)
    if y0 + side > im.height:
        y0 = im.height - side
    return im.crop((x0, y0, x0 + side, y0 + side)).resize((ICON, ICON), Image.NEAREST)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", action="append", default=[])
    ap.add_argument("--write", action="store_true", help="同时写 selection.json 的 hud_portrait")
    args = ap.parse_args()
    fighters = args.fighter or NEW
    sel_path = ROOT / "content/roster/selection.json"
    sel = json.loads(sel_path.read_text(encoding="utf-8")) if sel_path.is_file() else {"entries": []}
    done = []
    for fid in fighters:
        man_path = ROOT / f"assets/fighters/{fid}/animations/manifest.json"
        man = json.loads(man_path.read_text(encoding="utf-8"))
        clip = man.get("clips", {}).get("idle")
        if not clip:
            print(f"{fid}: 缺 idle clip，跳过")
            continue
        x, y, w, h = clip["rects"][0]
        atlas = Image.open(ROOT / clip["texture"].removeprefix("res://")).convert("RGBA")
        icon = head_crop(atlas.crop((x, y, x + w, y + h)))
        out = ROOT / f"assets/fighters/{fid}/portraits/hud.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        icon.save(out)
        for e in sel.get("entries", []):
            if e.get("id") == fid:
                e["hud_portrait"] = f"res://assets/fighters/{fid}/portraits/hud.png"
        done.append(fid)
        print(f"{fid}: {out.relative_to(ROOT)}")
    if args.write:
        sel_path.write_text(json.dumps(sel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写 {sel_path.relative_to(ROOT)}：{len(done)} 条 hud_portrait")


if __name__ == "__main__":
    main()
