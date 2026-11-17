"""待机像素源降到 188 高后的色板与识别色探针（只读候选，不签收）。

本机没有 agent-sprite-forge 源码，改用项目内 catalogue_native 的
确定性 BOX 降采样与中位切分色板；与 stage_cells 默认落格同一实现。
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/media/art"))
import catalogue_native as cn  # noqa: E402

TARGET_HEIGHT = 188
PALETTE_SIZE = 32


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def color_counts(image: Image.Image) -> Counter:
    array = np.array(image.convert("RGBA"))
    visible = array[:, :, 3] > 0
    colors = [tuple(int(v) for v in rgb) for rgb in array[:, :, :3][visible].reshape(-1, 3)]
    return Counter(colors)


def nearest(palette: list, color: tuple[int, int, int]) -> tuple[tuple[int, int, int], float]:
    best = min(palette, key=lambda c: sum((int(a) - int(b)) ** 2 for a, b in zip(c, color)))
    distance = sum((int(a) - int(b)) ** 2 for a, b in zip(best, color)) ** 0.5
    return tuple(best), round(distance, 1)


def recognition(image: Image.Image) -> dict:
    array = np.array(image.convert("RGBA"))
    visible = array[:, :, 3] > 0
    height = visible.shape[0]
    r = array[:, :, 0].astype(int)
    g = array[:, :, 1].astype(int)
    b = array[:, :, 2].astype(int)
    head = np.zeros_like(visible)
    head[:max(1, int(height * 0.22))] = True
    chest = np.zeros_like(visible)
    chest[int(height * 0.22):int(height * 0.58)] = True
    masks = {
        "eye_yellow": visible & head & (r > 160) & (g > 120) & (b < 140) & ((r - b) > 50),
        "lamp_green": visible & head & (g > 100) & ((g - r) > 20) & ((g - b) > 5),
        "timer_cyan": visible & chest & (b > 140) & (g > 95) & ((b - r) > 50),
    }
    result = {}
    for name, mask in masks.items():
        pixels = [tuple(int(v) for v in rgb) for rgb in array[:, :, :3][mask].reshape(-1, 3)]
        if not pixels:
            result[name] = {"pixels": 0}
            continue
        common = Counter(pixels).most_common(1)[0]
        result[name] = {"pixels": len(pixels), "color": list(common[0]), "count": common[1]}
    return result


def main() -> int:
    source = Path(sys.argv[1])
    if not source.is_absolute():
        source = ROOT / source
    out_dir = source.parent
    sprite = cn.downsample(cn.trim(cn.load_raw(source)), TARGET_HEIGHT)

    down_path = out_dir / "anchor-probe-downscaled.png"
    sprite.save(down_path)
    sprite.resize((sprite.width * 4, sprite.height * 4), Image.Resampling.NEAREST).save(
        out_dir / "anchor-probe-downscaled-x4.png")

    palettes = {
        "frequency": cn.build_palette(sprite, PALETTE_SIZE),
        "head_weighted": cn.build_head_weighted_palette(sprite, PALETTE_SIZE),
    }
    # 识别色：从像素整帧源取样，眼黄、额灯青绿、胸计时器亮蓝。
    pinned = [
        ("eye_yellow", (241, 226, 2)),
        ("lamp_green", (0, 255, 0)),
        ("timer_blue", (0, 143, 253)),
    ]
    base = list(palettes["head_weighted"])
    sprite_array = np.array(sprite)
    visible = sprite_array[:, :, 3] >= 128
    pixels = sprite_array[:, :, :3][visible].astype(np.int32)
    palette_array = np.array(base, dtype=np.int32)
    distances = ((pixels[:, None, :] - palette_array[None, :, :]) ** 2).sum(axis=2)
    usage = np.bincount(distances.argmin(axis=1), minlength=len(base))
    order = np.argsort(usage)
    replaced = []
    pinned_palette = list(base)
    for index, (name, color) in zip(order[:len(pinned)], pinned):
        replaced.append({"name": name, "rgb": list(color), "removed": list(base[index]),
                         "removed_usage": int(usage[index])})
        pinned_palette[int(index)] = color
    palettes["recognition_pinned"] = pinned_palette
    recog = recognition(sprite)
    counts = color_counts(sprite)
    report = {
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source),
        "downscaled": down_path.relative_to(ROOT).as_posix(),
        "downscaled_size": list(sprite.size),
        "downscaled_sha256": sha256(down_path),
        "downscaled_colors": len(counts),
        "recognition": recog,
        "palettes": {},
    }
    for name, palette in palettes.items():
        rows = []
        for color in palette:
            rows.append({"rgb": list(color), "exact_pixels": int(counts.get(tuple(color), 0))})
        report["palettes"][name] = rows
        for key, row in recog.items():
            if row.get("color"):
                best, distance = nearest(palette, tuple(row["color"]))
                row[f"{name}_nearest"] = list(best)
                row[f"{name}_distance"] = distance
        quantized = cn.apply_palette(sprite.copy(), palette)
        q_path = out_dir / f"anchor-probe-{name}.png"
        quantized.save(q_path)
        quantized.resize((quantized.width * 4, quantized.height * 4),
                         Image.Resampling.NEAREST).save(
            out_dir / f"anchor-probe-{name}-x4.png")
        report["palettes"][name] = {
            "colors": rows,
            "quantized": q_path.relative_to(ROOT).as_posix(),
            "quantized_sha256": sha256(q_path),
            "quantized_colors": len(color_counts(quantized)),
        }
    (out_dir / "anchor-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
