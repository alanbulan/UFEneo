"""把 MCP magpie-image 生成的赛罗光弹图集落成运行时图集与登记条目。

流程：
  1. 读 art/fighters/ultraman-zero/basic-pulse-fx-20261112/raw/*.png（MCP 实收原图）
  2. 按 2×2 分格，核每格 Alpha 边界与真透明
  3. 统一比例块主色缩放，硬 Alpha、16 色赛罗银红蓝板、只保留最大连通块
  4. 写 assets/effects/ultraman-zero/basic-pulse-fx-20261112/<段>/atlas.png
  5. 生成 phase3_entries.json 与 build-report.json（不写共享 phase3_projectiles.json）
"""
from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
BATCH = Path(__file__).resolve().parent
ART = ROOT / "art/fighters/ultraman-zero/basic-pulse-fx-20261112"
RAW = ART / "raw"
REQUESTS = ART / "requests.json"
DEST = ROOT / "assets/effects/ultraman-zero/basic-pulse-fx-20261112"
ENTRIES = BATCH / "phase3_entries.json"
REPORT = BATCH / "build-report.json"

# 赛罗银、红、蓝识别色：白热芯→蓝白内层→深蓝环→绯红外焰→银灰碎屑。
PALETTE = [
    (4, 5, 12), (9, 13, 30), (14, 30, 70), (22, 60, 128),
    (38, 106, 194), (92, 170, 232), (196, 230, 252), (255, 255, 255),
    (32, 6, 12), (82, 10, 20), (146, 22, 32), (208, 42, 46),
    (255, 96, 70), (58, 64, 78), (148, 158, 174), (226, 234, 242),
]

SPECS = {
    "zero_fx_pulse_flight": {
        "short": "pulse_flight",
        "sheet": RAW / "flight-sheet-01.png",
        "cell": [96, 96],
        "anchor": [48, 48],
        "ticks": 4,
        "loop": True,
        "layer": "flight",
        "margin": 6,
        "orientation": None,
        "kind_cn": "飞行弹体",
        "shape": "向右飞行的紧凑光弹：银白亮芯、蓝白等离子内层、深蓝中环、绯红锯齿外焰与银色碎屑",
    },
    "zero_fx_pulse_hit": {
        "short": "pulse_hit",
        "sheet": RAW / "hit-sheet-01.png",
        "cell": [128, 128],
        "anchor": [64, 64],
        "ticks": 4,
        "loop": False,
        "layer": "impact",
        "margin": 8,
        "orientation": "authored",
        "kind_cn": "命中爆点",
        "shape": "以命中点为中心的放射爆点：银白亮核、蓝白锯齿内环、绯红外焰尖刺与银蓝碎屑",
    },
}

SHADER_TINT = [1, 1, 1, 1]


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def alpha_report(image: Image.Image) -> dict:
    rgba = image.convert("RGBA")
    a = np.asarray(rgba)[..., 3]
    total = a.size
    bounds = rgba.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
    corners = [(0, 0), (rgba.width - 1, 0), (0, rgba.height - 1), (rgba.width - 1, rgba.height - 1)]
    matte = False
    if bounds:
        x0, y0, x1, y1 = bounds
        pts = [rgba.getpixel(p) for p in [(x0, y0), (x1 - 1, y0), (x0, y1 - 1), (x1 - 1, y1 - 1)]]
        matte = all(p[3] >= 200 for p in pts) and all(
            max(p[c] for p in pts) - min(p[c] for p in pts) < 6 for c in range(3))
    return {
        "size": [rgba.width, rgba.height],
        "mode": rgba.mode,
        "has_alpha_channel": "A" in rgba.getbands(),
        "transparent_fraction": round(float((a == 0).mean()), 6),
        "visible_fraction": round(float((a >= 128).mean()), 6),
        "nonzero_fraction": round(float((a > 0).mean()), 6),
        "opaque_fraction": round(float((a == 255).mean()), 6),
        "alpha_levels": int(len(np.unique(a))),
        "rectangular_matte": bool(matte),
        "clear_corners": all(rgba.getpixel(p)[3] == 0 for p in corners),
    }


def split_cells(sheet: Image.Image) -> list[Image.Image]:
    w, h = sheet.size
    if w % 2 or h % 2:
        raise SystemExit(f"2×2 分格要求偶数尺寸：{sheet.size}")
    cw, ch = w // 2, h // 2
    cells = []
    for j in range(2):
        for i in range(2):
            cells.append(sheet.crop((i * cw, j * ch, (i + 1) * cw, (j + 1) * ch)))
    return cells


def visible_mask(cell: Image.Image) -> np.ndarray:
    return np.asarray(cell.convert("RGBA"))[..., 3] >= 128


def edge_touch(mask: np.ndarray) -> bool:
    return bool(mask[0, :].any() or mask[-1, :].any() or mask[:, 0].any() or mask[:, -1].any())


def components(mask: np.ndarray) -> list[np.ndarray]:
    """8 邻域连通块像素坐标列表，按像素数降序。"""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y0 in range(h):
        for x0 in range(w):
            if not mask[y0, x0] or seen[y0, x0]:
                continue
            stack = [(y0, x0)]
            seen[y0, x0] = True
            pts = []
            while stack:
                y, x = stack.pop()
                pts.append((y, x))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True
                            stack.append((yy, xx))
            out.append(np.array(pts, dtype=np.int32))
    out.sort(key=len, reverse=True)
    return out


def keep_largest(mask: np.ndarray) -> tuple[np.ndarray, int]:
    parts = components(mask)
    if not parts:
        return mask, 0
    out = np.zeros_like(mask, dtype=bool)
    ys, xs = parts[0][:, 0], parts[0][:, 1]
    out[ys, xs] = True
    return out, len(parts)


def palette_index(rgb: np.ndarray) -> np.ndarray:
    pal = np.array(PALETTE, dtype=np.int32)
    flat = rgb.reshape(-1, 3).astype(np.int32)
    # 分块避免 16384×16 的距离矩阵过大；帧本身很小，这里直接广播。
    dist = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
    return dist.argmin(axis=1).reshape(rgb.shape[:2])


def block_downscale(cell: Image.Image, bbox: tuple[int, int, int, int], scale: float,
                    size: tuple[int, int]) -> Image.Image:
    """按统一比例取目标像素，块内多数 Alpha + 可见块的中位色。"""
    rgba = np.asarray(cell.convert("RGBA"))
    x0, y0, x1, y1 = bbox
    crop = rgba[y0:y1 + 1, x0:x1 + 1]
    cw, ch = size
    src_w, src_h = crop.shape[1], crop.shape[0]
    tw, th = max(1, int(round(src_w * scale))), max(1, int(round(src_h * scale)))
    if tw > cw or th > ch:
        raise SystemExit(f"缩放后 {tw}×{th} 超过格 {cw}×{ch}")
    out = np.zeros((th, tw, 4), dtype=np.uint8)
    for ty in range(th):
        sy0 = int(np.floor(ty * src_h / th))
        sy1 = max(sy0 + 1, int(np.floor((ty + 1) * src_h / th)))
        for tx in range(tw):
            sx0 = int(np.floor(tx * src_w / tw))
            sx1 = max(sx0 + 1, int(np.floor((tx + 1) * src_w / tw)))
            block = crop[sy0:sy1, sx0:sx1]
            vis = block[..., 3] >= 128
            if vis.sum() * 2 < vis.size:
                continue
            colors = block[vis][:, :3].astype(np.int32)
            # 中位色（逐通道）比均值更稳，避免把红蓝交界调成紫色。
            median = np.median(colors, axis=0).astype(np.uint8)
            out[ty, tx, :3] = median
            out[ty, tx, 3] = 255
    return Image.fromarray(out, "RGBA")


def place_in_cell(frame: Image.Image, cell_w: int, cell_h: int, anchor: list[int]) -> Image.Image:
    mask = np.asarray(frame)[..., 3] >= 128
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise SystemExit("空帧")
    bw, bh = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
    left = int(anchor[0] - bw // 2)
    top = int(anchor[1] - bh // 2)
    if left < 0 or top < 0 or left + bw > cell_w or top + bh > cell_h:
        raise SystemExit(f"帧 {bw}×{bh} 放不进 {cell_w}×{cell_h}（anchor {anchor}）")
    canvas = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    canvas.paste(frame.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)), (left, top))
    return canvas


def enforce_hard_alpha(frame: Image.Image) -> tuple[Image.Image, dict]:
    rgba = np.asarray(frame.convert("RGBA")).copy()
    mask = rgba[..., 3] >= 128
    mask, parts_before = keep_largest(mask)
    rgba[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
    idx = palette_index(rgba[..., :3])
    pal = np.array(PALETTE, dtype=np.uint8)
    rgba[..., :3] = pal[idx]
    rgba[~mask] = 0
    return Image.fromarray(rgba, "RGBA"), {"components_before_cleanup": parts_before}


def gate_metrics(frame: Image.Image, anchor: list[int]) -> dict:
    a = np.asarray(frame.convert("RGBA"))[..., 3]
    body = a >= 200
    parts = components(body)
    if not parts:
        raise SystemExit("主体为空")
    main = parts[0]
    expanded = np.zeros_like(body, dtype=bool)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy > 9:
                continue
            yy = main[:, 0] + dy
            xx = main[:, 1] + dx
            ok = (yy >= 0) & (yy < a.shape[0]) & (xx >= 0) & (xx < a.shape[1])
            expanded[yy[ok], xx[ok]] = True
    outside = ~expanded
    ys, xs = np.nonzero(a >= 128)
    return {
        "alpha_levels": sorted(int(v) for v in np.unique(a)),
        "alpha_binary": bool(set(np.unique(a)).issubset({0, 255})),
        "main_component_pixels": int(len(main)),
        "components_alpha200": int(len(parts)),
        "components_alpha128": int(len(components(a >= 128))),
        "outside_expanded_alpha16": int(((a >= 16) & outside).sum()),
        "outside_expanded_alpha200": int(((a >= 200) & outside).sum()),
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
        "frame_box": [int(xs.min()) - anchor[0], int(ys.min()) - anchor[1],
                      int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
        "visible_pixels": int((a > 0).sum()),
    }


def build_entry(eid: str, spec: dict, atlas: Path, dest_dir: Path) -> tuple[dict, list[dict]]:
    arr = np.asarray(Image.open(atlas).convert("RGBA"))
    cell_w, cell_h = spec["cell"]
    rects = [[i * cell_w, 0, cell_w, cell_h] for i in range(4)]
    boxes, metrics = [], []
    for i, (x, y, w, h) in enumerate(rects):
        frame = Image.fromarray(arr[y:y + h, x:x + w], "RGBA")
        m = gate_metrics(frame, spec["anchor"])
        g = m
        if not g["alpha_binary"]:
            raise SystemExit(f"{eid} 帧 {i} Alpha 不是二值")
        if g["outside_expanded_alpha16"] > 100:
            raise SystemExit(f"{eid} 帧 {i} 主体外 alpha≥16 {g['outside_expanded_alpha16']} > 100")
        if g["outside_expanded_alpha200"] != 0:
            raise SystemExit(f"{eid} 帧 {i} 主体外 alpha≥200 {g['outside_expanded_alpha200']} != 0")
        boxes.append(g["frame_box"])
        metrics.append(g)
    colors = int(len({tuple(int(v) for v in c) for c in arr[arr[..., 3] > 0][:, :3]}))
    entry = {
        "texture": "res://" + str(atlas.relative_to(ROOT)),
        "rects": rects,
        "anchor": spec["anchor"],
        "ticks": spec["ticks"],
        "display_scale": [1, 1],
        "behind_fighter": False,
        "frame_boxes": boxes,
        "loop": bool(spec["loop"]),
        "color_parameter": False,
        "alpha_binary": True,
        "native_fan": False,
        "atlas_sha256": sha(atlas),
        "colors": colors,
        "source_kind": "mcp_magpie_image",
        "art_source": "mcp_magpie_image",
        "model": "codex/gpt-image-2",
        "license": "project_generated",
        "provenance": "res://" + str((dest_dir / "provenance.json").relative_to(ROOT)),
        "dedicated_to": "ultraman-zero",
        "authoring_source": "res://tools/rebuild/ultraman-zero/basic-pulse-fx-20261112/build.py",
        "layer": spec["layer"],
        "user_approved": False,
        "review_status": "2026-11-12 赛罗专属银红蓝光弹 MCP 生成像素整帧，待指挥目视终审",
    }
    if spec.get("orientation"):
        entry["orientation"] = spec["orientation"]
    return entry, metrics


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict] = {}
    report: dict = {
        "batch": "basic-pulse-fx-20261112",
        "character": "ultraman-zero",
        "source": "MCP magpie-image / codex/gpt-image-2 / quality high / background transparent",
        "license": "project_generated",
        "palette": PALETTE,
        "palette_identity": "赛罗银红蓝：银白芯、蓝白内层、深蓝环、绯红外焰、银灰碎屑",
        "shared_phase3_modified": False,
        "charge_overlay_policy_modified": False,
        "character_frames_modified": False,
        "requests": json.loads(REQUESTS.read_text(encoding="utf-8")) if REQUESTS.is_file() else None,
        "effects": {},
    }
    for eid, spec in SPECS.items():
        sheet_path = spec["sheet"]
        if not sheet_path.is_file():
            raise SystemExit(f"缺少 MCP 原图：{sheet_path}")
        sheet = Image.open(sheet_path).convert("RGBA")
        src = alpha_report(sheet)
        if not (src["has_alpha_channel"] and src["clear_corners"] and not src["rectangular_matte"]):
            raise SystemExit(f"{sheet_path} 不是真透明：{src}")
        cells = split_cells(sheet)
        cell_w, cell_h = spec["cell"]
        info = []
        bboxes = []
        for i, cell in enumerate(cells):
            mask = visible_mask(cell)
            if not mask.any():
                raise SystemExit(f"{eid} 第 {i} 格为空")
            if edge_touch(mask):
                raise SystemExit(f"{eid} 第 {i} 格主体贴格边，拒绝")
            ys, xs = np.nonzero(mask)
            bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
            bboxes.append(bbox)
            info.append({"cell": i, "visible_pixels": int(mask.sum()),
                         "bbox": [bbox[0], bbox[1], bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1]})
        max_w = max(b[2] - b[0] + 1 for b in bboxes)
        max_h = max(b[3] - b[1] + 1 for b in bboxes)
        scale = min((cell_w - 2 * spec["margin"]) / max_w, (cell_h - 2 * spec["margin"]) / max_h)
        frames = []
        for i, (cell, bbox) in enumerate(zip(cells, bboxes)):
            small = block_downscale(cell, bbox, scale, (cell_w, cell_h))
            placed = place_in_cell(small, cell_w, cell_h, spec["anchor"])
            clean, cleanup = enforce_hard_alpha(placed)
            frames.append(clean)
            info[i]["cleanup"] = cleanup
        atlas = Image.new("RGBA", (cell_w * 4, cell_h), (0, 0, 0, 0))
        for i, frame in enumerate(frames):
            atlas.paste(frame, (i * cell_w, 0))
        dest_dir = DEST / spec["short"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        atlas_path = dest_dir / "atlas.png"
        atlas.save(atlas_path)
        entry, metrics = build_entry(eid, spec, atlas_path, dest_dir)
        entries[eid] = entry
        provenance = {
            "character": "ultraman-zero",
            "effect": eid,
            "kind": spec["layer"],
            "shape": spec["shape"],
            "request": "2×2 四相图集；每格 512×512（实收按 1254/2=627 分格），透明背景，固定中心，硬边像素簇。",
            "generator": "MCP magpie-image",
            "model": "codex/gpt-image-2",
            "quality": "high",
            "background": "transparent",
            "source_kind": "mcp_magpie_image",
            "license": "project_generated",
            "raw_sheet": "res://" + str(sheet_path.relative_to(ROOT)),
            "raw_sheet_sha256": sha(sheet_path),
            "raw_alpha": src,
            "split": "2×2，左上/右上/左下/右下",
            "source_cells": info,
            "uniform_scale": round(scale, 8),
            "cell": spec["cell"],
            "anchor": spec["anchor"],
            "palette": PALETTE,
            "operations": [
                "Alpha≥128 二值化，按格取主体外框",
                "全段统一比例块多数 Alpha + 逐通道中位色缩放",
                "只保留最大 8 邻域连通块，其余可见像素清零",
                "16 色赛罗银红蓝板最近邻量化，硬 Alpha 255",
            ],
            "atlas_sha256": sha(atlas_path),
            "frame_metrics": metrics,
            "character_frames_modified": False,
            "shared_phase3_modified": False,
        }
        (dest_dir / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        (dest_dir / "effect.json").write_text(
            json.dumps(entry, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        report["effects"][eid] = {
            "atlas": "res://" + str(atlas_path.relative_to(ROOT)),
            "atlas_sha256": entry["atlas_sha256"],
            "file_size": atlas_path.stat().st_size,
            "atlas_size": [atlas.width, atlas.height],
            "cell": spec["cell"],
            "frames": 4,
            "ticks": spec["ticks"],
            "loop": spec["loop"],
            "colors": entry["colors"],
            "uniform_scale": round(scale, 8),
            "raw_sheet": "res://" + str(sheet_path.relative_to(ROOT)),
            "raw_sheet_sha256": sha(sheet_path),
            "raw_alpha": src,
            "frame_metrics": metrics,
        }
        print(f"安装 {eid} -> {atlas_path.relative_to(ROOT)}  {atlas.size}  colors={entry['colors']}  scale={scale:.6f}")
    ENTRIES.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"写入 {ENTRIES.relative_to(ROOT)} 与 {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
