"""把 MCP 图生图产出的待机帧拼成图鉴动画条。

流程（每个条目）：
1. 以该条目已定稿的 model-native.png 为第 0 帧，也是全条的尺度与配色基准；
2. 每张新帧按同一站高降采样、量化到第 0 帧的调色板，保证帧间不跳色；
3. 按脚底重心水平对齐、脚底贴 ROOT_Y，拼成水平 strip。

输出：assets/fighters/<id>/catalogue/anim-strip.png
      content/roster/catalogue_display.json 补 strip / frames / idle_source

用法：
    python tools/media/art/catalogue_anim.py <id> --frames f1.png f2.png f3.png
    python tools/media/art/catalogue_anim.py <id> --frames ... --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
CANVAS_WIDTH = 384
CANVAS_HEIGHT = 256
ROOT_Y = 248
# 脚底重心只取最低的这一段行，避免尾巴/武器把水平对齐拉偏。
FOOT_FRACTION = 0.12

sys.path.insert(0, str(ROOT / "tools/media/art"))
from catalogue_native import (  # noqa: E402
    apply_palette, build_palette, downsample, harden_alpha, load_raw, trim,
)


def foot_center(image: Image.Image) -> float:
    """可见像素最低一段的横向重心，用作站立点。"""
    array = np.array(image)
    visible = array[:, :, 3] > 0
    ys = np.nonzero(visible.any(axis=1))[0]
    if ys.size == 0:
        return image.width / 2.0
    bottom = int(ys.max())
    top = bottom - max(1, int((bottom - int(ys.min()) + 1) * FOOT_FRACTION))
    band = visible[top : bottom + 1]
    xs = np.nonzero(band.any(axis=0))[0]
    if xs.size == 0:
        return image.width / 2.0
    return float((band.sum(axis=0) * np.arange(band.shape[1])).sum() / max(1, band.sum()))


def native_path(entry: dict) -> Path:
    return ROOT / str(entry["image"]).removeprefix("res://")


def build_strip(catalogue_id: str, entry: dict, frame_paths: list[Path],
                dry_run: bool = False) -> dict:
    native = native_path(entry)
    with Image.open(native) as handle:
        base = handle.convert("RGBA")
    base = harden_alpha(base)
    height = trim(base).height
    palette = build_palette(trim(base))
    anchor = foot_center(base)

    frames = [base]
    details = [{"index": 0, "source": "model-native.png", "height": height}]
    for path in frame_paths:
        reduced = downsample(trim(load_raw(path)), height)
        reduced = apply_palette(reduced, palette)
        left = round(anchor - foot_center(reduced))
        left = max(-reduced.width // 2, min(CANVAS_WIDTH - reduced.width // 2, left))
        canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        canvas.alpha_composite(reduced, (left, ROOT_Y - reduced.height))
        frames.append(canvas)
        details.append({"index": len(frames) - 1, "source": path.name,
                        "height": reduced.height, "left": left,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

    strip = Image.new("RGBA", (CANVAS_WIDTH * len(frames), CANVAS_HEIGHT), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        strip.alpha_composite(frame, (CANVAS_WIDTH * index, 0))

    out = ROOT / f"assets/fighters/{catalogue_id}/catalogue/anim-strip.png"
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        strip.save(out)
    return {
        "id": catalogue_id,
        "frames": len(frames),
        "size": [strip.width, strip.height],
        "height": height,
        "frames_detail": details,
        "out": out.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest() if not dry_run else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue_id")
    parser.add_argument("--frames", type=Path, nargs="*", default=[],
                        help="MCP 生成的待机帧（第 0 帧自动取已定稿 model-native.png）")
    parser.add_argument("--prepare", action="store_true",
                        help="只输出给生图模型用的 4 倍参考图路径")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    display = json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))
    entry = display["entries"].get(args.catalogue_id)
    if entry is None:
        print(f"图鉴里没有 {args.catalogue_id}", file=sys.stderr)
        return 1
    if args.prepare:
        # 4 倍最近邻放大：给生图模型足够的像素，又不改变造型和配色。
        native = native_path(entry)
        with Image.open(native) as handle:
            still = handle.convert("RGBA")
        big = still.resize((still.width * 4, still.height * 4), Image.NEAREST)
        out = ROOT / f"reports/catalogue-anim/{args.catalogue_id}/ref.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        big.save(out)
        print(json.dumps({"id": args.catalogue_id, "reference": out.relative_to(ROOT).as_posix(),
                          "size": list(big.size), "native": native.relative_to(ROOT).as_posix()},
                         ensure_ascii=False, indent=2))
        return 0

    if not args.frames:
        print("至少给一张 --frames 生成帧", file=sys.stderr)
        return 1
    missing = [str(p) for p in args.frames if not p.is_file()]
    if missing:
        print(f"帧文件不存在：{missing}", file=sys.stderr)
        return 1

    report = build_strip(args.catalogue_id, entry, args.frames, args.dry_run)
    if not args.dry_run:
        from catalogue_store import update_entry
        update_entry(args.catalogue_id, {
            "strip": "res://" + report["out"],
            "frames": report["frames"],
            "strip_sha256": report["sha256"],
            "idle_source": "mcp_image_to_image_idle_frames",
        })
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
