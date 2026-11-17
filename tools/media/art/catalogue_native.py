"""把 MCP 生成的整帧高分红图转成项目图鉴定稿格式。

输入：任意尺寸、软 Alpha、上万色的整帧 PNG。
输出：原生像素画布、二值 Alpha、约 32 色硬色阶、脚底对齐画布底边的 PNG。

生成图是"像素风格"而非精确整数网格，因此不做网格检测：直接按目标原生
站高做区域平均降采样，再二值化 Alpha 并量化到固定色数。全过程确定，
不含随机。身份正确性仍须人眼审片，本工具不评价造型。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

# 图鉴画布约定：与既有 598 张定稿一致。
CANVAS_WIDTH = 384
CANVAS_HEIGHT = 256
ROOT_Y = 248
TARGET_STANDING_HEIGHT = 192
PALETTE_SIZE = 32
ALPHA_CUTOFF = 128
# 头部优先调色板：上部 26% 的像素加权 6 倍，避免肤色被大面积服装挤掉。
HEAD_FRACTION = 0.26
HEAD_WEIGHT = 6


def load_raw(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGBA")


def trim(image: Image.Image) -> Image.Image:
    box = image.getchannel("A").getbbox()
    if box is None:
        raise ValueError("输入图没有可见像素")
    return image.crop(box)


def harden_alpha(image: Image.Image) -> Image.Image:
    """软 Alpha 二值化：只有明确不透明处保留，避免半透明毛边。"""
    array = np.array(image)
    array[:, :, 3] = np.where(array[:, :, 3] >= ALPHA_CUTOFF, 255, 0).astype(np.uint8)
    return Image.fromarray(array, "RGBA")


def downsample(image: Image.Image, height: int) -> Image.Image:
    """先二值化并裁到实心轮廓，再区域平均缩到目标高度。

    先硬边后缩放，避免软边在缩放后又被裁掉、导致最终站高偏小。
    """
    solid = trim(harden_alpha(image))
    scale = height / solid.height
    width = max(1, round(solid.width * scale))
    resized = solid.resize((width, height), Image.BOX)
    return harden_alpha(trim(resized))


def build_palette(image: Image.Image, size: int = PALETTE_SIZE) -> list:
    """按出现频次取前 N 色作为硬色阶，不做平滑。"""
    array = np.array(image)
    visible = array[:, :, 3] > ALPHA_CUTOFF
    if not visible.any():
        raise ValueError("降采样后没有可见像素")
    colors = array[:, :, :3][visible]
    values, counts = np.unique(colors, axis=0, return_counts=True)
    order = np.argsort(-counts)[:size]
    return [tuple(int(c) for c in values[i]) for i in order]


def build_head_weighted_palette(image: Image.Image, size: int = PALETTE_SIZE) -> list:
    """头部优先调色板。

    纯按频次取色时，大面积高饱和队服/装甲会把面部肤色挤出调色板，脸会
    变成衣服色。这里把上部 26%（头部）的像素加权 6 倍再中位切分，
    保证脸和发色一定占名额，其余名额仍按整幅分布。
    """
    array = np.array(image)
    visible = array[:, :, 3] > ALPHA_CUTOFF
    ys = np.nonzero(visible)[0]
    if ys.size == 0:
        return []
    top, bottom = int(ys.min()), int(ys.max())
    head_limit = top + int((bottom - top + 1) * HEAD_FRACTION)
    head = visible.copy()
    head[head_limit:] = False

    body_pixels = array[:, :, :3][visible].reshape(-1, 3)
    head_pixels = array[:, :, :3][head].reshape(-1, 3)
    if head_pixels.size == 0:
        return build_palette(image, size)
    stacked = np.concatenate([body_pixels] + [head_pixels] * HEAD_WEIGHT, axis=0)
    sample = Image.fromarray(stacked.reshape(1, -1, 3), "RGB")
    quantized = sample.quantize(colors=size, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
    raw_palette = quantized.getpalette() or []
    return [
        tuple(int(c) for c in raw_palette[i * 3 : i * 3 + 3])
        for i in range(size)
        if len(raw_palette) >= (i + 1) * 3
    ]


def apply_palette(image: Image.Image, palette: list) -> Image.Image:
    """每个像素映射到调色板最近色（欧氏距离）。"""
    if not palette:
        return image
    array = np.array(image)
    visible = array[:, :, 3] > ALPHA_CUTOFF
    palette_array = np.array(palette, dtype=np.int32)
    result = array.copy()
    if visible.any():
        pixels = array[:, :, :3][visible].astype(np.int32)
        distances = ((pixels[:, None, :] - palette_array[None, :, :]) ** 2).sum(axis=2)
        chosen = palette_array[distances.argmin(axis=1)].astype(np.uint8)
        rgb = result[:, :, :3]
        rgb[visible] = chosen
        result[:, :, :3] = rgb
    return Image.fromarray(result, "RGBA")


def place_on_canvas(image: Image.Image) -> tuple[Image.Image, dict]:
    """脚底贴 ROOT_Y，水平居中，不缩放到画布外。"""
    box = image.getchannel("A").getbbox()
    if box is None:
        raise ValueError("放置前没有可见像素")
    subject = image.crop(box)
    width, height = subject.size
    if width > CANVAS_WIDTH - 8 or height > ROOT_Y:
        scale = min((CANVAS_WIDTH - 8) / width, ROOT_Y / height)
        width, height = max(1, round(width * scale)), max(1, round(height * scale))
        subject = subject.resize((width, height), Image.NEAREST)
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    left = (CANVAS_WIDTH - width) // 2
    top = ROOT_Y - height
    canvas.alpha_composite(subject, (left, top))
    return canvas, {"subject": [width, height], "left": left, "top": top}


def convert(raw_path: Path, out_path: Path, palette: list | None = None) -> dict:
    source = load_raw(raw_path)
    reduced = downsample(trim(source), TARGET_STANDING_HEIGHT)
    used = palette if palette is not None else build_head_weighted_palette(reduced)
    quantized = apply_palette(reduced, used)
    canvas, placement = place_on_canvas(quantized)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    alpha_values = sorted({int(v) for v in np.unique(np.array(canvas.getchannel("A")))})
    visible = np.array(canvas)[:, :, 3] > 0
    colors = np.unique(np.array(canvas)[:, :, :3][visible].reshape(-1, 3), axis=0)
    return {
        "source": raw_path.as_posix(),
        "source_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "output": out_path.as_posix(),
        "output_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
        "placement": placement,
        "canvas": [CANVAS_WIDTH, CANVAS_HEIGHT],
        "native_root": [CANVAS_WIDTH // 2, ROOT_Y],
        "visible_height": placement["subject"][1],
        "alpha_values": alpha_values,
        "binary_alpha": alpha_values == [0, 255],
        "palette_size": len(used),
        "visible_colors": int(colors.shape[0]),
    }


def main() -> int:
    if len(sys.argv) < 3:
        print("用法: catalogue_native.py <raw.png> <out.png> [palette.json]", file=sys.stderr)
        return 2
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    palette = None
    if len(sys.argv) > 3:
        palette = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    report = convert(raw, out, palette)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["binary_alpha"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
