"""图生视频（I2V）短片抽帧、自动去背与像素化管线。

将图生视频模型（如 magpie-image.generate_video）产出的 MP4 短片转换为
干净、二值 Alpha、同比例缩放并映射到本人 ≤32 色调色板的 PNG 整帧序列，
同时生成可直接喂给 tools/art/stage_cells.py 的清单。

严禁切肢拼片或按单帧外框归一身高：全序列使用由待机锚点推出的唯一比例。
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from art import sprite_extract  # noqa: E402
from media.art.catalogue_native import build_head_weighted_palette  # noqa: E402

MAX_PALETTE_COLORS = 32


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_rate(text: str) -> float:
    if not text or text == "0/0":
        return 0.0
    if "/" in text:
        num, den = text.split("/", 1)
        den_f = float(den)
        return float(num) / den_f if den_f else 0.0
    return float(text)


def probe_video(video_path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("未找到 ffprobe；请先安装 FFmpeg")
    if not video_path.is_file():
        raise FileNotFoundError(f"视频文件不存在：{video_path}")
    cmd = [
        ffprobe, "-v", "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,pix_fmt",
        "-of", "json", str(video_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe 解析失败：{proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if stream is None:
        raise RuntimeError(f"未在 {video_path} 中找到视频流")
    duration_s = float(data.get("format", {}).get("duration", 0) or 0)
    fps = _parse_rate(str(stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0"))
    if duration_s <= 0:
        raise RuntimeError(f"视频时长无效：{duration_s}")
    nb_frames_raw = stream.get("nb_frames")
    nb_frames = int(nb_frames_raw) if str(nb_frames_raw).isdigit() else max(1, round(duration_s * max(fps, 1.0)))
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "duration_s": round(duration_s, 6),
        "fps": round(fps, 4),
        "nb_frames": nb_frames,
        "pix_fmt": str(stream.get("pix_fmt", "")),
    }


def resolve_timestamps(
    duration_s: float,
    fps: float,
    *,
    count: int = 6,
    start_s: float = 0.0,
    end_s: float | None = None,
    timestamps: list[float] | None = None,
    sample_fps: float | None = None,
) -> list[float]:
    safe_end = max(start_s + 1e-3, min(duration_s, end_s) if end_s is not None else duration_s)
    eof_guard = min(0.02, 0.5 / max(fps, 24.0))
    max_ts = max(0.0, duration_s - eof_guard)
    if timestamps:
        return [round(min(max(0.0, float(t)), max_ts), 6) for t in timestamps]
    if sample_fps and sample_fps > 0:
        step = 1.0 / sample_fps
        out: list[float] = []
        t = max(0.0, start_s)
        while t <= min(safe_end, max_ts) + 1e-6:
            out.append(round(min(t, max_ts), 6))
            t += step
            if count > 0 and len(out) >= count:
                break
        return out or [round(min(start_s, max_ts), 6)]
    if count <= 1:
        mid = (max(0.0, start_s) + min(safe_end, max_ts)) / 2.0
        return [round(min(mid, max_ts), 6)]
    span = max(0.0, min(safe_end, max_ts) - max(0.0, start_s))
    return [round(min(max(0.0, start_s) + span * i / (count - 1), max_ts), 6) for i in range(count)]


def extract_raw_frames(
    video_path: Path,
    raw_dir: Path,
    timestamps: list[float],
    prefix: str = "frame",
) -> list[dict[str, Any]]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("未找到 ffmpeg；请先安装 FFmpeg")
    raw_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for index, ts in enumerate(timestamps):
        out_path = raw_dir / f"{prefix}-{index:02d}-raw.png"
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-nostdin", "-loglevel", "error",
            "-ss", f"{ts:.6f}", "-i", str(video_path),
            "-frames:v", "1", "-pix_fmt", "rgba", str(out_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        if proc.returncode != 0 or not out_path.is_file():
            raise RuntimeError(f"ffmpeg 抽帧失败 (t={ts:.3f}s): {proc.stderr.strip()}")
        with Image.open(out_path) as opened:
            size = list(opened.size)
        records.append({
            "index": index,
            "timestamp_s": ts,
            "raw_path": out_path,
            "raw_sha256": sha256_file(out_path),
            "raw_size": size,
        })
    return records


def sample_corner_background(image: Image.Image) -> tuple[tuple[int, int, int], bool]:
    """从四角采样背景主色；返回 (RGB, 是否高饱和色键)。"""
    rgb = np.array(image.convert("RGB"), dtype=np.uint8)
    h, w = rgb.shape[:2]
    pw = max(4, w // 20)
    ph = max(4, h // 20)
    patches = np.concatenate([
        rgb[:ph, :pw].reshape(-1, 3),
        rgb[:ph, w - pw :].reshape(-1, 3),
        rgb[h - ph :, :pw].reshape(-1, 3),
        rgb[h - ph :, w - pw :].reshape(-1, 3),
    ], axis=0)
    med = np.median(patches, axis=0)
    key = (int(round(med[0])), int(round(med[1])), int(round(med[2])))
    is_chroma = (max(key) - min(key)) >= 25
    return key, is_chroma


def _has_existing_alpha(image: Image.Image) -> bool:
    if "A" not in image.getbands():
        return False
    rgba = image.convert("RGBA")
    alpha = np.array(rgba.getchannel("A"), dtype=np.uint8)
    h, w = alpha.shape
    corners = [alpha[0, 0], alpha[0, w - 1], alpha[h - 1, 0], alpha[h - 1, w - 1]]
    clear_frac = float(np.count_nonzero(alpha < 128)) / alpha.size
    visible_frac = float(np.count_nonzero(alpha >= 128)) / alpha.size
    return all(int(c) == 0 for c in corners) and clear_frac >= 0.05 and visible_frac >= 0.01


def _flood_clear_border_bg(
    image: Image.Image, key_rgb: tuple[int, int, int], tolerance: float
) -> Image.Image:
    """从四边连通域泛洪抠出背景，避免误伤人物内部的同色区域（如白眼/银甲）。"""
    rgba = np.array(image.convert("RGBA"), dtype=np.uint8)
    h, w = rgba.shape[:2]
    lab = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2LAB).astype(np.float32)
    key_lab = cv2.cvtColor(np.uint8([[list(key_rgb)]]), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
    dist_lab = np.linalg.norm(lab - key_lab[None, None, :], axis=2)
    dist_rgb = np.linalg.norm(rgba[:, :, :3].astype(np.float32) - np.array(key_rgb, dtype=np.float32), axis=2)
    match = (dist_rgb <= tolerance) & (dist_lab <= tolerance * 0.7)

    visited = np.zeros((h, w), dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if match[y, x] and not visited[y, x]:
                visited[y, x] = True
                queue.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if match[y, x] and not visited[y, x]:
                visited[y, x] = True
                queue.append((y, x))
    while queue:
        cy, cx = queue.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and match[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))
    rgba[visited] = 0
    return Image.fromarray(rgba, "RGBA").copy()


def remove_background(
    image: Image.Image,
    *,
    mode: str = "auto",
    chroma_key: tuple[int, int, int] | None = None,
    bg_tolerance: float = 28.0,
    key_threshold: float = 96.0,
    fringe_threshold: float = 180.0,
    fringe_delta: float = 18.0,
) -> tuple[Image.Image, dict[str, Any]]:
    if mode == "alpha" or (mode == "auto" and _has_existing_alpha(image)):
        cleaned = sprite_extract.binarize_alpha(image.convert("RGBA"))
        return _clear_hidden(cleaned), {
            "mode": "existing_alpha",
            "key_rgb": None,
        }

    detected_rgb, is_chroma = sample_corner_background(image)
    key_rgb = chroma_key if chroma_key is not None else detected_rgb
    is_chroma = (max(key_rgb) - min(key_rgb)) >= 25

    chosen = mode
    if chosen == "auto":
        chosen = "chroma-ycbcr" if is_chroma else "flood-lab"

    if chosen == "chroma-ycbcr":
        matted = sprite_extract.remove_chroma_background_ycbcr(image, key_rgb)
        alpha_arr = np.array(matted.getchannel("A"), dtype=np.uint8)
        vis_frac = float(np.count_nonzero(alpha_arr >= 128)) / max(1, alpha_arr.size)
        if vis_frac < 0.005 or vis_frac > 0.85:
            matted = _flood_clear_border_bg(image, key_rgb, bg_tolerance)
        else:
            matted = _flood_clear_border_bg(matted, key_rgb, bg_tolerance * 0.8)
        out = sprite_extract.binarize_alpha(matted)
    elif chosen == "chroma-rgb":
        matted = sprite_extract.remove_chroma_background(
            image, key_rgb, key_threshold, fringe_threshold, fringe_delta
        )
        out = sprite_extract.binarize_alpha(matted)
    elif chosen == "flood-lab":
        flooded = _flood_clear_border_bg(image, key_rgb, bg_tolerance)
        out = sprite_extract.binarize_alpha(flooded)
    else:
        raise ValueError(f"未知去背模式：{mode}")

    return _clear_hidden(out), {"mode": chosen, "key_rgb": list(key_rgb)}


def _clear_hidden(image: Image.Image) -> Image.Image:
    arr = np.array(image.convert("RGBA"), dtype=np.uint8)
    arr[arr[:, :, 3] == 0] = 0
    return Image.fromarray(arr, "RGBA").copy()


def load_palette_json(path: Path) -> list[tuple[int, int, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("colors", data) if isinstance(data, dict) else data
    if not isinstance(raw, list) or not raw or len(raw) > MAX_PALETTE_COLORS:
        raise ValueError(f"色板 JSON 必须是 1–{MAX_PALETTE_COLORS} 个 RGB 三元组：{path}")
    return [(int(c[0]), int(c[1]), int(c[2])) for c in raw]


def anchor_palette_and_height(anchor_path: Path, max_colors: int = MAX_PALETTE_COLORS) -> tuple[list[tuple[int, int, int]], int]:
    with Image.open(anchor_path) as opened:
        rgba = sprite_extract.binarize_alpha(opened.convert("RGBA"))
    box = sprite_extract.solid_alpha_bbox(rgba)
    if box is None:
        raise ValueError(f"身份锚没有可见像素：{anchor_path}")
    cropped = rgba.crop(box)
    arr = np.array(cropped, dtype=np.uint8)
    visible = arr[:, :, 3] > 0
    unique_rgb = np.unique(arr[:, :, :3][visible].reshape(-1, 3), axis=0)
    if len(unique_rgb) <= max_colors:
        palette = [tuple(int(v) for v in row) for row in unique_rgb]
    else:
        palette = build_head_weighted_palette(cropped, max_colors)
    return palette, cropped.height


def _snap_to_pixel_grid(
    tight_frames: list[Image.Image],
    *,
    grid_snap: str,
    max_pitch: int,
    min_snapped_height: int = 24,
) -> tuple[list[Image.Image], dict[str, Any]]:
    if grid_snap == "off":
        return tight_frames, {"applied": False, "reason": "disabled"}
    grids = [sprite_extract.detect_pixel_grid(frame, max_pitch=max_pitch) for frame in tight_frames]
    valid_x = sorted(g[0][0] for g in grids if g[0][0] >= 2.0)
    valid_y = sorted(g[0][1] for g in grids if g[0][1] >= 2.0)
    if not valid_x or not valid_y:
        return tight_frames, {"applied": False, "reason": "no_grid_detected"}
    cons_x = valid_x[len(valid_x) // 2]
    cons_y = valid_y[len(valid_y) // 2]
    snapped: list[Image.Image] = []
    used_pitches: list[list[float]] = []
    for frame, ((own_x, own_y), _) in zip(tight_frames, grids):
        if min(own_x, own_y) >= 2.0:
            (use_x, use_y), _ = sprite_extract.resolve_frame_pitch((own_x, own_y), (cons_x, cons_y))
        else:
            use_x, use_y = cons_x, cons_y
        phase = sprite_extract._best_phase(frame, (use_x, use_y))
        xs = sprite_extract._grid_edges(frame.width, use_x, phase[0])
        ys = sprite_extract._grid_edges(frame.height, use_y, phase[1])
        xs, ys = sprite_extract.refine_edges_to_boundaries(frame, xs, ys, (use_x, use_y))
        snapped_frame = sprite_extract.snap_by_edges(frame, xs, ys, detail_bias=True)
        box = sprite_extract.solid_alpha_bbox(snapped_frame) or snapped_frame.getbbox()
        snapped.append(snapped_frame.crop(box) if box else snapped_frame)
        used_pitches.append([round(use_x, 2), round(use_y, 2)])
    if grid_snap == "auto" and min(f.height for f in snapped) < min_snapped_height:
        return tight_frames, {
            "applied": False,
            "reason": "snapped_below_target_floor",
            "detected_pitch": [round(cons_x, 2), round(cons_y, 2)],
        }
    return snapped, {"applied": True, "consensus_pitch": [round(cons_x, 2), round(cons_y, 2)], "per_frame_pitch": used_pitches}


def pixelize_sequence(
    matted_frames: list[Image.Image],
    *,
    target_standing: int | None = None,
    scale_frame: int = 0,
    explicit_scale: float = 0.0,
    palette: list[tuple[int, int, int]] | None = None,
    palette_size: int = MAX_PALETTE_COLORS,
    grid_snap: str = "auto",
    max_pitch: int = 48,
) -> tuple[list[Image.Image], dict[str, Any]]:
    if not matted_frames:
        raise ValueError("没有可像素化的帧")
    tight: list[Image.Image] = []
    for index, frame in enumerate(matted_frames):
        box = sprite_extract.solid_alpha_bbox(frame)
        if box is None:
            raise ValueError(f"第 {index:02d} 帧去背后为空")
        tight.append(frame.crop(box))

    min_snap_h = max(24, round(target_standing * 0.85)) if target_standing else 24
    snapped, grid_info = _snap_to_pixel_grid(
        tight, grid_snap=grid_snap, max_pitch=max_pitch, min_snapped_height=min_snap_h
    )
    ref_index = max(0, min(len(snapped) - 1, scale_frame))
    ref_height = snapped[ref_index].height

    if explicit_scale > 0:
        scale = float(explicit_scale)
    elif target_standing and target_standing > 0:
        scale = float(target_standing) / max(1, ref_height)
    else:
        scale = 1.0

    scaled: list[Image.Image] = []
    for frame in snapped:
        if math.isclose(scale, 1.0, rel_tol=1e-6):
            resized = frame.copy()
        elif scale < 1.0:
            tw = max(1, round(frame.width * scale))
            th = max(1, round(frame.height * scale))
            resized = sprite_extract._kcentroid_downscale(frame, tw, th, detail_bias=True)
        else:
            tw = max(1, round(frame.width * scale))
            th = max(1, round(frame.height * scale))
            resized = frame.resize((tw, th), Image.Resampling.NEAREST)
        resized = sprite_extract.binarize_alpha(resized)
        box = sprite_extract.solid_alpha_bbox(resized) or resized.getbbox()
        scaled.append(resized.crop(box) if box else resized)

    cap_colors = min(MAX_PALETTE_COLORS, max(2, palette_size))
    used_palette = palette if palette else sprite_extract.build_shared_palette(scaled, cap_colors)
    if len(used_palette) > MAX_PALETTE_COLORS:
        used_palette = used_palette[:MAX_PALETTE_COLORS]

    final_frames: list[Image.Image] = []
    for frame in scaled:
        mapped = sprite_extract.apply_palette(frame.copy(), used_palette)
        mapped = _clear_hidden(sprite_extract.binarize_alpha(mapped))
        final_frames.append(mapped)

    return final_frames, {
        "grid_snap": grid_info,
        "scale": round(scale, 6),
        "scale_ref_frame": ref_index,
        "scale_ref_height": ref_height,
        "target_standing": target_standing or ref_height,
        "palette_size": len(used_palette),
        "palette": [list(c) for c in used_palette],
    }


def _parse_rgb(text: str) -> tuple[int, int, int]:
    parts = [int(x.strip()) for x in text.split(",")]
    if len(parts) != 3 or any(not 0 <= v <= 255 for v in parts):
        raise argparse.ArgumentTypeError(f"RGB 需要 0..255 三元组：{text}")
    return (parts[0], parts[1], parts[2])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True, help="输入 MP4/视频路径")
    parser.add_argument("--out-dir", type=Path, required=True, help="输出帧与清单目录")
    parser.add_argument("--clip", default="clip", help="输出帧命名前缀（如 walk_forward）")
    parser.add_argument("--anchor", type=Path, default=None, help="待机像素身份锚 PNG（提供站高与调色板）")
    parser.add_argument("--palette-json", type=Path, default=None, help="显式 ≤32 色冻结调色板 JSON")
    parser.add_argument("--target-standing", type=int, default=0, help="目标站高；缺省取 --anchor 站高")
    parser.add_argument("--scale", type=float, default=0.0, help="显式统一缩放比（覆盖目标站高推算）")
    parser.add_argument("--scale-frame", type=int, default=0, help="用作比例基准的帧序号（默认 0）")
    parser.add_argument("--count", type=int, default=6, help="等距抽帧数（默认 6）")
    parser.add_argument("--start", type=float, default=0.0, help="起始时间（秒）")
    parser.add_argument("--end", type=float, default=None, help="结束时间（秒）")
    parser.add_argument("--fps", type=float, default=None, help="按固定帧率抽帧（可选）")
    parser.add_argument("--timestamps", default="", help="逗号分隔的精确时间码（秒）")
    parser.add_argument("--bg-mode", choices=("auto", "chroma-ycbcr", "chroma-rgb", "flood-lab", "alpha"), default="auto")
    parser.add_argument("--chroma-key", type=_parse_rgb, default=None, help="手工指定背景 R,G,B")
    parser.add_argument("--bg-tolerance", type=float, default=24.0, help="四角泛洪抠像容差（RGB 距离）")
    parser.add_argument("--grid-snap", choices=("auto", "on", "off"), default="auto")
    parser.add_argument("--pixel-grid-max-pitch", type=int, default=48)
    parser.add_argument("--palette-size", type=int, default=MAX_PALETTE_COLORS)
    parser.add_argument("--keep-raw", action="store_true", help="保留未缩放原始 PNG 与去背中介图")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    video_path = args.video if args.video.is_absolute() else ROOT / args.video
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    probe = probe_video(video_path)
    timestamps_list = [float(x) for x in args.timestamps.split(",") if x.strip()] if args.timestamps else None
    timestamps = resolve_timestamps(
        probe["duration_s"], probe["fps"],
        count=args.count, start_s=args.start, end_s=args.end,
        timestamps=timestamps_list, sample_fps=args.fps,
    )

    raw_dir = out_dir / "raw"
    raw_records = extract_raw_frames(video_path, raw_dir, timestamps, prefix=args.clip)

    palette: list[tuple[int, int, int]] | None = None
    target_standing = args.target_standing
    if args.anchor is not None:
        anchor_path = args.anchor if args.anchor.is_absolute() else ROOT / args.anchor
        anchor_pal, anchor_h = anchor_palette_and_height(anchor_path, min(MAX_PALETTE_COLORS, args.palette_size))
        palette = anchor_pal
        if target_standing <= 0:
            target_standing = anchor_h
    if args.palette_json is not None:
        pal_path = args.palette_json if args.palette_json.is_absolute() else ROOT / args.palette_json
        palette = load_palette_json(pal_path)

    matted: list[Image.Image] = []
    bg_infos: list[dict[str, Any]] = []
    for rec in raw_records:
        with Image.open(rec["raw_path"]) as opened:
            clean_rgba, bg_info = remove_background(
                opened,
                mode=args.bg_mode,
                chroma_key=args.chroma_key,
                bg_tolerance=args.bg_tolerance,
            )
        matted.append(clean_rgba)
        bg_infos.append(bg_info)

    pixelized, seq_meta = pixelize_sequence(
        matted,
        target_standing=target_standing if target_standing > 0 else None,
        scale_frame=args.scale_frame,
        explicit_scale=args.scale,
        palette=palette,
        palette_size=args.palette_size,
        grid_snap=args.grid_snap,
        max_pitch=args.pixel_grid_max_pitch,
    )

    frame_entries: list[dict[str, Any]] = []
    stage_args: list[str] = []
    for rec, img, bg_info in zip(raw_records, pixelized, bg_infos):
        idx = rec["index"]
        name = f"{args.clip}-{idx:02d}"
        out_path = out_dir / f"{name}.png"
        img.save(out_path, format="PNG")
        arr = np.array(img)
        visible = arr[:, :, 3] > 0
        colors = int(len(np.unique(arr[:, :, :3][visible].reshape(-1, 3), axis=0))) if visible.any() else 0
        comps = len(sprite_extract.connected_components(img))
        rel_out = out_path.resolve().relative_to(ROOT).as_posix() if out_path.resolve().is_relative_to(ROOT) else str(out_path)
        stage_args.append(f"{name}={rel_out}")
        frame_entries.append({
            "index": idx,
            "name": name,
            "timestamp_s": rec["timestamp_s"],
            "path": rel_out,
            "sha256": sha256_file(out_path),
            "size": list(img.size),
            "colors": colors,
            "components": comps,
            "alpha_values": sorted(int(v) for v in np.unique(arr[:, :, 3])),
            "bg_removal": bg_info,
            "raw_sha256": rec["raw_sha256"],
        })

    if not args.keep_raw and raw_dir.is_dir():
        shutil.rmtree(raw_dir)

    manifest = {
        "schema": 1,
        "clip": args.clip,
        "video": {
            "path": video_path.resolve().relative_to(ROOT).as_posix() if video_path.resolve().is_relative_to(ROOT) else str(video_path),
            "sha256": sha256_file(video_path),
            **probe,
        },
        "anchor": (args.anchor.resolve().relative_to(ROOT).as_posix() if args.anchor and args.anchor.resolve().is_relative_to(ROOT) else str(args.anchor) if args.anchor else None),
        "processing": seq_meta,
        "stage_cells_frames": stage_args,
        "frames": frame_entries,
    }
    manifest_path = out_dir / "video_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
