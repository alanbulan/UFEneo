"""待机照视角项连续 3 帧拒收后的诊断联系表与数值记录。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
FIGHTER = "ultraman-zero__luna_miracle"
FRAMES = ROOT / "art/fighters" / FIGHTER / "stage1/idle/frames"
REFS = ROOT / "art/fighters" / FIGHTER / "stage1/idle/references"
DIAG = ROOT / "art/fighters" / FIGHTER / "stage1/diagnostic"

ITEMS = [
    ("ref-03 官方皮套照（4/3 正面）", REFS / "suit-wide-canvas.png"),
    ("ref-02 官方头部侧面", REFS / "luna-side-head-official.png"),
    ("已装赛罗侧视待机（只借站姿）", ROOT / "art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png"),
    ("stance-raw-00 拒收：3/4", FRAMES / "stance-raw-00.png"),
    ("stance-raw-01 拒收：3/4", FRAMES / "stance-raw-01.png"),
    ("stance-raw-02 拒收：3/4", FRAMES / "stance-raw-02.png"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    DIAG.mkdir(parents=True, exist_ok=True)
    width = 420
    cols = 3
    thumbs = []
    for label, path in ITEMS:
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
        background = Image.new("RGBA", image.size, (230, 230, 230, 255))
        background.alpha_composite(image)
        image = background.convert("RGB")
        ratio = width / image.width
        image = image.resize((width, max(1, int(image.height * ratio))), Image.LANCZOS)
        thumbs.append((label, path, image))

    cell_h = max(image.height for _, _, image in thumbs) + 34
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (width * cols + 8 * (cols + 1), cell_h * rows), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    for index, (label, path, image) in enumerate(thumbs):
        x = (index % cols) * (width + 8) + 8
        y = (index // cols) * cell_h + 26
        sheet.paste(image, (x, y))
        draw.text((x, y - 20), label, fill=(0, 0, 0))
        draw.text((x, y - 8), path.name, fill=(80, 80, 80))
    out = DIAG / "stance-view-angle-contact.png"
    sheet.save(out)

    records = []
    for name in ("stance-raw-00.png", "stance-raw-01.png", "stance-raw-02.png"):
        path = FRAMES / name
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
        alpha = np.array(image)[:, :, 3]
        ys, xs = np.nonzero(alpha > 0)
        records.append({
            "file": path.name,
            "size": list(image.size),
            "sha256": sha256(path),
            "alpha_levels": int(len(np.unique(alpha))),
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "standing_height": int(ys.max() - ys.min() + 1),
            "touches_canvas_edge": bool(xs.min() == 0 or ys.min() == 0
                                        or xs.max() == image.width - 1
                                        or ys.max() == image.height - 1),
            "view_verdict": "rejected_not_90_side",
            "view_note": "胸甲 X/V 纹正面展开、双肩与双胸可见，为 3/4 正面；非纯右侧视 90°。",
        })

    report = {
        "fighter": FIGHTER,
        "gate": "待机照纯右侧视 90°",
        "attempts": records,
        "rejections": 3,
        "methods_tried": [
            "官方皮套照为主、侧视待机为辅、强调肩线垂直（stance-raw-00/01）",
            "侧视待机为第一参考重绘、皮套照只供材质（stance-raw-02）",
        ],
        "diagnostic": "art/fighters/ultraman-zero__luna_miracle/stage1/diagnostic/stance-view-angle-contact.png",
        "conclusion": "两种修法均未把躯干从 3/4 正面拉到 90° 侧视；按返工刹车停止重生成，留待换思路（改用本人真实侧视身体来源或人工侧视底稿）后再做。",
        "authority": "root_delegated_by_user",
    }
    (DIAG / "stance-view-angle.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(out, sheet.size)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
