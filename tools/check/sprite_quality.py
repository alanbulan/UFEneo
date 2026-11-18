"""通用精灵像素质检硬门 CLI（无任何角色硬编码）。

硬门指标（与 docs/HANDBOOK.md 4.3 节对齐）：
1. 真实 Alpha 与辉光门：主体（alpha>=200 最大 4 连通块）外扩 3 px 外，
   alpha>=200 像素数 == 0 且 alpha>=16 像素数 <= 100；成品帧要求二值 Alpha {0, 255}。
2. 游离孤岛像素检测：4 连通分离碎点（<=16 px 或非多部件豁免片段内 >1 连通块）。
3. 全套共用调色板颜色数 <= 32。
4. 站姿高度相对锚点偏差 <= 8%，同组相邻站姿帧高度突变 <= 10%（蹲/躺/被投/腾空豁免并登记）。
5. 走路循环帧时长方差 variance == 0，且相邻帧存在可见像素位移（非整图平移）。

用法：
    .venv/bin/python tools/check/sprite_quality.py --fighter ultraseven
    .venv/bin/python tools/check/sprite_quality.py --frames f0.png f1.png --anchor idle.png --ticks 10,10
    .venv/bin/python tools/check/sprite_quality.py --dir art/fighters/<id>/stage1/cells --anchor anchor.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MAX_PALETTE_COLORS = 32
GLOW_DILATION_RADIUS = 3
MAX_OUTER_ALPHA16 = 100
DEFAULT_STRAY_ISLAND_AREA = 16
STANDING_ANCHOR_TOLERANCE = 0.08
STANDING_ADJACENT_TOLERANCE = 0.10
DEFAULT_MIN_WALK_DIFF_PX = 20

# 非站姿豁免列表（蹲、躺、被投、腾空、倒地、滚翻等），只登记不按站姿站高门判错。
NON_STANDING_TOKENS = (
    "crouch", "sweep", "slide", "down", "ko", "defeat", "wake", "roll", "bounce",
    "thrown", "air", "jump", "takeoff", "launch", "fall", "dive",
    "chase", "vertical", "diagonal", "hit_crouch", "hit_air",
    "block_crouch", "guard_crouch", "low_pulse", "capture_", "backstep",
)
MULTI_COMPONENT_TOKENS = (
    "air_special", "throw", "thrown", "special", "motion_", "win", "victory", "intro", "taunt",
)
WALK_CLIPS = ("walk_forward", "walk_back")


def is_standing_clip(clip_name: str) -> bool:
    low = clip_name.lower()
    return not any(token in low for token in NON_STANDING_TOKENS)


def allows_multi_component(clip_name: str) -> bool:
    low = clip_name.lower()
    return any(token in low for token in MULTI_COMPONENT_TOKENS)


def analyze_frame(arr: np.ndarray, *, max_stray_area: int = DEFAULT_STRAY_ISLAND_AREA) -> dict[str, Any]:
    alpha = arr[:, :, 3]
    alpha_values = sorted(int(v) for v in np.unique(alpha))
    visible = alpha > 0
    if not visible.any():
        return {
            "empty": True,
            "alpha_values": alpha_values,
            "binary_alpha": False,
            "height": 0,
            "width": 0,
            "glow_out200": 0,
            "glow_out16": 0,
            "components": 0,
            "stray_islands": [],
        }

    ys, xs = np.nonzero(visible)
    height = int(ys.max() - ys.min() + 1)
    width = int(xs.max() - xs.min() + 1)

    solid200 = (alpha >= 200).astype(np.uint8)
    n200, labels200, stats200, _ = cv2.connectedComponentsWithStats(solid200, connectivity=4)
    if n200 <= 1:
        glow_out200 = int(np.count_nonzero(alpha >= 200))
        glow_out16 = int(np.count_nonzero(alpha >= 16))
    else:
        areas = stats200[1:, cv2.CC_STAT_AREA]
        main_label = 1 + int(np.argmax(areas))
        main_mask = (labels200 == main_label).astype(np.uint8)
        kernel = np.ones((GLOW_DILATION_RADIUS * 2 + 1, GLOW_DILATION_RADIUS * 2 + 1), np.uint8)
        dilated = cv2.dilate(main_mask, kernel, iterations=1) > 0
        glow_out200 = int(np.count_nonzero((alpha >= 200) & ~dilated))
        glow_out16 = int(np.count_nonzero((alpha >= 16) & ~dilated))

    mask_nonzero = (alpha > 0).astype(np.uint8)
    n_comp, _, stats_comp, _ = cv2.connectedComponentsWithStats(mask_nonzero, connectivity=4)
    comp_areas = [int(stats_comp[i, cv2.CC_STAT_AREA]) for i in range(1, n_comp)]
    main_area = max(comp_areas, default=0)
    stray = [
        {"area": int(stats_comp[i, cv2.CC_STAT_AREA]),
         "bbox": [int(stats_comp[i, cv2.CC_STAT_LEFT]), int(stats_comp[i, cv2.CC_STAT_TOP]),
                  int(stats_comp[i, cv2.CC_STAT_WIDTH]), int(stats_comp[i, cv2.CC_STAT_HEIGHT])]}
        for i in range(1, n_comp)
        if int(stats_comp[i, cv2.CC_STAT_AREA]) <= max_stray_area and int(stats_comp[i, cv2.CC_STAT_AREA]) < main_area
    ]

    return {
        "empty": False,
        "alpha_values": alpha_values,
        "binary_alpha": set(alpha_values).issubset({0, 255}) and 255 in alpha_values,
        "height": height,
        "width": width,
        "glow_out200": glow_out200,
        "glow_out16": glow_out16,
        "components": max(0, n_comp - 1),
        "stray_islands": stray,
    }


def _aligned_pose_diff(arr_a: np.ndarray, arr_b: np.ndarray) -> tuple[int, int]:
    """返回 (同画布不同像素数, 对齐各自底边中心后的轮廓异或像素数)。"""
    if arr_a.shape == arr_b.shape:
        raw_diff = int(np.count_nonzero(np.any(arr_a != arr_b, axis=-1)))
    else:
        ch = max(arr_a.shape[0], arr_b.shape[0])
        cw = max(arr_a.shape[1], arr_b.shape[1])
        ca_pad = np.zeros((ch, cw, 4), dtype=np.uint8)
        cb_pad = np.zeros((ch, cw, 4), dtype=np.uint8)
        ca_pad[ch - arr_a.shape[0] :, (cw - arr_a.shape[1]) // 2 : (cw - arr_a.shape[1]) // 2 + arr_a.shape[1]] = arr_a
        cb_pad[ch - arr_b.shape[0] :, (cw - arr_b.shape[1]) // 2 : (cw - arr_b.shape[1]) // 2 + arr_b.shape[1]] = arr_b
        raw_diff = int(np.count_nonzero(np.any(ca_pad != cb_pad, axis=-1)))
    ma = arr_a[:, :, 3] > 0
    mb = arr_b[:, :, 3] > 0
    if not ma.any() or not mb.any():
        return raw_diff, 0
    ya, xa = np.nonzero(ma)
    yb, xb = np.nonzero(mb)
    ca = ma[int(ya.min()):int(ya.max()) + 1, int(xa.min()):int(xa.max()) + 1]
    cb = mb[int(yb.min()):int(yb.max()) + 1, int(xb.min()):int(xb.max()) + 1]
    h = max(ca.shape[0], cb.shape[0])
    w = max(ca.shape[1], cb.shape[1])
    pa = np.zeros((h, w), dtype=bool)
    pb = np.zeros((h, w), dtype=bool)
    pa[h - ca.shape[0] :, (w - ca.shape[1]) // 2 : (w - ca.shape[1]) // 2 + ca.shape[1]] = ca
    pb[h - cb.shape[0] :, (w - cb.shape[1]) // 2 : (w - cb.shape[1]) // 2 + cb.shape[1]] = cb
    aligned_xor = int(np.count_nonzero(pa ^ pb))
    return raw_diff, aligned_xor


def inspect_clip_sequence(
    clip_name: str,
    frames: list[np.ndarray],
    *,
    ticks: list[int] | None = None,
    anchor_height: int | None = None,
    allow_soft_alpha: bool = False,
    allow_multi_component: bool | None = None,
    max_stray_area: int = DEFAULT_STRAY_ISLAND_AREA,
    min_walk_diff: int = DEFAULT_MIN_WALK_DIFF_PX,
    standing_override: bool | None = None,
    palette_colors: set[tuple[int, int, int]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    exempt_frames: list[dict[str, Any]] = []
    frame_rows: list[dict[str, Any]] = []

    standing = standing_override if standing_override is not None else is_standing_clip(clip_name)
    multi_ok = allow_multi_component if allow_multi_component is not None else allows_multi_component(clip_name)

    prev_standing_h: int | None = None
    for idx, arr in enumerate(frames):
        info = analyze_frame(arr, max_stray_area=max_stray_area)
        info["clip"] = clip_name
        info["frame"] = idx
        info["standing"] = standing
        frame_rows.append(info)

        if info["empty"]:
            errors.append(f"{clip_name}[{idx:02d}]: 帧全透明无像素")
            continue

        if palette_colors is not None:
            visible = arr[:, :, 3] >= (128 if allow_soft_alpha else 1)
            if visible.any():
                uniq = np.unique(arr[:, :, :3][visible].reshape(-1, 3), axis=0)
                palette_colors.update((int(r), int(g), int(b)) for r, g, b in uniq)

        if not allow_soft_alpha and not info["binary_alpha"]:
            errors.append(f"{clip_name}[{idx:02d}]: Alpha 非二值 {info['alpha_values'][:8]}")
        if info["glow_out200"] > 0:
            errors.append(f"{clip_name}[{idx:02d}]: 辉光门失败 out200={info['glow_out200']} (>0)")
        if info["glow_out16"] > MAX_OUTER_ALPHA16:
            errors.append(f"{clip_name}[{idx:02d}]: 辉光门失败 out16={info['glow_out16']} (>{MAX_OUTER_ALPHA16})")
        if info["stray_islands"]:
            errors.append(
                f"{clip_name}[{idx:02d}]: 检测到 {len(info['stray_islands'])} 处游离孤岛像素"
            )
        if not multi_ok and info["components"] > 1:
            warnings.append(f"{clip_name}[{idx:02d}]: 连通块 {info['components']} (>1)")

        h = info["height"]
        if not standing:
            exempt_frames.append({"clip": clip_name, "frame": idx, "height": h, "reason": "non_standing_pose"})
            continue

        if anchor_height and anchor_height > 0:
            drift = abs(h - anchor_height) / anchor_height
            if drift > STANDING_ANCHOR_TOLERANCE:
                errors.append(
                    f"{clip_name}[{idx:02d}]: 站高 {h} 相对锚点 {anchor_height} 偏差 {drift:.1%} (>8%)"
                )
        if prev_standing_h is not None and min(h, prev_standing_h) > 0:
            jump = abs(h - prev_standing_h) / min(h, prev_standing_h)
            if jump > STANDING_ADJACENT_TOLERANCE:
                errors.append(
                    f"{clip_name}[{idx:02d}]: 相邻站姿高度突变 {prev_standing_h}->{h} ({jump:.1%} > 10%)"
                )
        prev_standing_h = h

    is_walk = clip_name in WALK_CLIPS or "walk" in clip_name.lower()
    if is_walk and ticks:
        mean_t = sum(ticks) / len(ticks)
        variance = sum((t - mean_t) ** 2 for t in ticks) / len(ticks)
        if variance != 0:
            errors.append(f"{clip_name}: 走路帧时长方差 variance={variance:.4f} (!=0), ticks={ticks}")
    if is_walk and len(frames) >= 2:
        for i in range(len(frames)):
            nxt = (i + 1) % len(frames)
            raw_diff, aligned_xor = _aligned_pose_diff(frames[i], frames[nxt])
            if raw_diff < min_walk_diff or aligned_xor == 0:
                errors.append(
                    f"{clip_name}[{i:02d}->{nxt:02d}]: 走路相邻帧位移不足 raw_diff={raw_diff}, aligned_xor={aligned_xor}"
                )

    return {
        "clip": clip_name,
        "frames": len(frames),
        "standing": standing,
        "frame_metrics": frame_rows,
        "exempt_frames": exempt_frames,
        "errors": errors,
        "warnings": warnings,
    }


def _load_fighter_clips(fighter: str) -> tuple[dict[str, tuple[list[np.ndarray], list[int]]], int | None]:
    manifest_path = ROOT / f"assets/fighters/{fighter}/animations/manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"缺少角色动画清单：{manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips_data: dict[str, tuple[list[np.ndarray], list[int]]] = {}
    atlas_cache: dict[Path, Image.Image] = {}
    for clip_name, entry in sorted((manifest.get("clips") or {}).items()):
        tex_rel = str(entry["texture"]).removeprefix("res://")
        atlas_path = ROOT / tex_rel
        if not atlas_path.is_file():
            raise FileNotFoundError(f"{clip_name}: 缺少图集 {atlas_path}")
        atlas = atlas_cache.get(atlas_path)
        if atlas is None:
            with Image.open(atlas_path) as opened:
                atlas = opened.convert("RGBA")
            atlas_cache[atlas_path] = atlas
        frames = [
            np.array(atlas.crop((int(r[0]), int(r[1]), int(r[0]) + int(r[2]), int(r[1]) + int(r[3]))), dtype=np.uint8)
            for r in entry.get("rects", [])
        ]
        ticks = [int(t) for t in entry.get("ticks", [])]
        clips_data[clip_name] = (frames, ticks)

    anchor_height: int | None = None
    if "idle" in clips_data and clips_data["idle"][0]:
        idle0 = clips_data["idle"][0][0]
        ys = np.nonzero(idle0[:, :, 3] > 0)[0]
        if ys.size:
            anchor_height = int(ys.max() - ys.min() + 1)
    return clips_data, anchor_height


def run_check(args: argparse.Namespace) -> dict[str, Any]:
    palette_colors: set[tuple[int, int, int]] = set()
    clip_reports: list[dict[str, Any]] = []
    all_errors: list[str] = []
    all_warnings: list[str] = []
    exempt_frames: list[dict[str, Any]] = []

    anchor_height = args.anchor_height
    if args.anchor is not None:
        anchor_path = args.anchor if args.anchor.is_absolute() else ROOT / args.anchor
        with Image.open(anchor_path) as opened:
            arr = np.array(opened.convert("RGBA"), dtype=np.uint8)
        ys = np.nonzero(arr[:, :, 3] > 0)[0]
        if ys.size == 0:
            raise ValueError(f"锚点图无可见像素：{anchor_path}")
        anchor_height = int(ys.max() - ys.min() + 1)

    if args.fighter:
        clips_data, idle_h = _load_fighter_clips(args.fighter)
        if anchor_height is None:
            anchor_height = idle_h
        selected = set(args.clip) if args.clip else None
        for clip_name, (frames, ticks) in clips_data.items():
            if selected is not None and clip_name not in selected:
                continue
            rep = inspect_clip_sequence(
                clip_name, frames, ticks=ticks, anchor_height=anchor_height,
                allow_soft_alpha=args.allow_soft_alpha,
                allow_multi_component=True if args.allow_multi_component else None,
                max_stray_area=args.max_stray_area,
                min_walk_diff=args.min_walk_diff,
                palette_colors=palette_colors,
            )
            clip_reports.append(rep)
            all_errors.extend(rep["errors"])
            all_warnings.extend(rep["warnings"])
            exempt_frames.extend(rep["exempt_frames"])
    else:
        paths: list[Path] = []
        if args.frames:
            paths = [p if p.is_absolute() else ROOT / p for p in args.frames]
        elif args.dir:
            base = args.dir if args.dir.is_absolute() else ROOT / args.dir
            paths = sorted(p for p in base.glob("*.png") if not p.name.startswith("."))
        else:
            raise SystemExit("请指定 --fighter、--frames 或 --dir")
        if not paths:
            raise SystemExit("未找到可检查的 PNG 帧")
        frames: list[np.ndarray] = []
        for p in paths:
            with Image.open(p) as opened:
                frames.append(np.array(opened.convert("RGBA"), dtype=np.uint8))
        if anchor_height is None and frames:
            ys = np.nonzero(frames[0][:, :, 3] > 0)[0]
            if ys.size:
                anchor_height = int(ys.max() - ys.min() + 1)
        ticks = [int(t) for t in args.ticks.split(",") if t.strip()] if args.ticks else None
        clip_name = args.clip[0] if args.clip else "sequence"
        rep = inspect_clip_sequence(
            clip_name, frames, ticks=ticks, anchor_height=anchor_height,
            allow_soft_alpha=args.allow_soft_alpha,
            allow_multi_component=args.allow_multi_component,
            max_stray_area=args.max_stray_area,
            min_walk_diff=args.min_walk_diff,
            standing_override=False if args.non_standing else None,
            palette_colors=palette_colors,
        )
        clip_reports.append(rep)
        all_errors.extend(rep["errors"])
        all_warnings.extend(rep["warnings"])
        exempt_frames.extend(rep["exempt_frames"])

    palette_count = len(palette_colors)
    if palette_count > MAX_PALETTE_COLORS:
        all_errors.append(f"全套可见调色板颜色数 {palette_count} 超过上限 {MAX_PALETTE_COLORS}")

    return {
        "check": "sprite_quality",
        "target": args.fighter or str(args.dir or f"{len(args.frames)} frames"),
        "anchor_height": anchor_height,
        "palette_colors": palette_count,
        "palette_limit": MAX_PALETTE_COLORS,
        "clips_checked": len(clip_reports),
        "frames_checked": sum(r["frames"] for r in clip_reports),
        "exempt_frames": exempt_frames,
        "errors": all_errors,
        "warnings": all_warnings,
        "passed": not all_errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fighter", default="", help="检查已装角色 assets/fighters/<id>")
    parser.add_argument("--dir", type=Path, default=None, help="检查指定目录下全部 PNG 帧")
    parser.add_argument("--frames", type=Path, nargs="*", default=[], help="检查显式 PNG 帧序列")
    parser.add_argument("--clip", action="append", default=[], help="仅检查指定 clip 名（可重复）")
    parser.add_argument("--anchor", type=Path, default=None, help="参考待机身份锚 PNG")
    parser.add_argument("--anchor-height", type=int, default=None, help="显式锚点站高（像素）")
    parser.add_argument("--ticks", default="", help="帧时长列表（逗号分隔，用于走路方差检查）")
    parser.add_argument("--allow-soft-alpha", action="store_true", help="允许软 Alpha（仅检辉光门，用于 raw 原图）")
    parser.add_argument("--allow-multi-component", action="store_true", help="允许多个连通块（如飞行道具分离帧）")
    parser.add_argument("--non-standing", action="store_true", help="把目标序列标为蹲/躺/被投/腾空非站姿（豁免并登记）")
    parser.add_argument("--max-stray-area", type=int, default=DEFAULT_STRAY_ISLAND_AREA, help="孤岛碎点最大面积阈值")
    parser.add_argument("--min-walk-diff", type=int, default=DEFAULT_MIN_WALK_DIFF_PX, help="走路相邻帧最小像素差异")
    parser.add_argument("--json-out", type=Path, default=None, help="写入 JSON 报告路径")
    parser.add_argument("--json", action="store_true", help="标准输出打印完整 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_check(args)
    if args.json_out is not None:
        out_path = args.json_out if args.json_out.is_absolute() else ROOT / args.json_out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"target={report['target']} clips={report['clips_checked']} "
            f"frames={report['frames_checked']} palette={report['palette_colors']}/{MAX_PALETTE_COLORS} "
            f"exempt={len(report['exempt_frames'])} warnings={len(report['warnings'])} errors={len(report['errors'])}"
        )
        for err in report["errors"][:30]:
            print("  ERROR:", err)
        for warn in report["warnings"][:15]:
            print("  WARN:", warn)
    print("SPRITE_QUALITY " + ("PASS" if report["passed"] else "FAIL"))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
