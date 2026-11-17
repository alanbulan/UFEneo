"""逐帧核人物本体尺度：头骨顶到脚底的站高、头部宽度/面积与同 clip 中位数比较。

用途：找出整帧人物被生成/安装放大（或缩小）的帧；不把举武器、特效、蹲姿、
腾空收腿当成尺度错误。报告写到 reports/frame-scale-jumps.json，异常或
需要人眼复核时非零退出。

判定口径（STYLE.md“尺寸校验”）：
- 头部是无遮挡时最稳定的比例基准；头宽与头部面积（面积取平方根折成线性比例）
  必须同时明显偏大，且站高也偏大，才记为确定的整帧尺度突变。
- 只有站高偏大、头部正常：视为姿势（站直/抬臂/特效）不报。
- 只有头部偏大、站高不偏大：无法区分转头、局部重画还是蹲姿中放大，列入
  人工复核，不自动缩放。
- 头部特征被遮挡、头发/角/尾巴使顶部不稳定时写入 uncertain。

修复口径：
- 只对确定的整帧尺度突变，以该帧脚底 anchor 为不动点做最近邻整数反向采样；
  Alpha 保持 0/255，不裁肢体，不改 manifest 的 rects/anchors/ticks、招式或模拟数据。
- 只替换目标帧矩形内的像素，其它帧逐字节不变；同步替换 manifest 中该图集的
  atlas_sha256，并留下修复前后逐帧测量记录。

运行：
    .venv/bin/python tools/check/frame_scale_jumps.py
    .venv/bin/python tools/check/frame_scale_jumps.py --fighter ultraman-jack
    .venv/bin/python tools/check/frame_scale_jumps.py --fighter ultraman-jack --clip motion_214 --verbose
    .venv/bin/python tools/check/frame_scale_jumps.py --fighter ultraman-jack --clip motion_214 --fix --frames 1 2 3
"""

from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = _LayoutNativePath(_layout_root)
DEFAULT_REPORT = ROOT / "reports/frame-scale-jumps.json"
THRESHOLD = 0.08
# 确定突变要求两个头部指标都至少达到阈值的一半，避免单人头的转头/局部重画误判。
CORROBORATE = 0.04
# 这些动作本身就会让角色变大/变小，不是生成事故。
INTENTIONAL_SCALE_CLIPS = {"capture_shrinking", "capture_restore"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def playable_fighters() -> list[str]:
    """definition.json 未写 playable 的历史角色按可玩处理（与 content_database.gd 一致）。"""
    fighters = []
    for path in sorted((ROOT / "content/fighters").glob("*/definition.json")):
        data = read_json(path)
        if data.get("playable", True) is not True:
            continue
        fighter = path.parent.name
        if (ROOT / "assets/fighters" / fighter / "animations/manifest.json").is_file():
            fighters.append(fighter)
    return fighters


def _runs(row: np.ndarray) -> list[tuple[int, int]]:
    diff = np.diff(np.concatenate(([0], row.view(np.int8), [0])))
    return list(zip(np.where(diff == 1)[0].tolist(), (np.where(diff == -1)[0] - 1).tolist()))


def _largest_component(mask: np.ndarray) -> np.ndarray:
    """按行段做并查集，避免依赖 scipy/cv2。"""
    height, width = mask.shape
    runs = [_runs(mask[y]) for y in range(height)]
    offsets = []
    total = 0
    for row_runs in runs:
        offsets.append(total)
        total += len(row_runs)
    if total == 0:
        return mask
    parent = list(range(total))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for y in range(1, height):
        previous = runs[y - 1]
        current = runs[y]
        po = offsets[y - 1]
        co = offsets[y]
        j = 0
        for k, (start, end) in enumerate(current):
            while j < len(previous) and previous[j][1] < start:
                j += 1
            jj = j
            while jj < len(previous) and previous[jj][0] <= end:
                union(co + k, po + jj)
                jj += 1
    areas: dict[int, int] = {}
    for y, row_runs in enumerate(runs):
        offset = offsets[y]
        for k, (start, end) in enumerate(row_runs):
            root = find(offset + k)
            areas[root] = areas.get(root, 0) + (end - start + 1)
    if not areas:
        return mask
    best = max(areas, key=areas.get)
    result = np.zeros_like(mask)
    for y, row_runs in enumerate(runs):
        offset = offsets[y]
        for k, (start, end) in enumerate(row_runs):
            if find(offset + k) == best:
                result[y, start:end + 1] = True
    return result


def _thickness(frame: Image.Image) -> int:
    """最大内切半径（3×3 腐蚀次数），用来粗查躯干/肢体厚度是否跟着头部一起变。

    纯 Pillow 实现，避免把 scipy/OpenCV 变成验证依赖。整数像素有 ±1 的量化误差，
    所以只作为“是否允许自动缩放”的旁证，不单独判定。
    """
    alpha = (np.asarray(frame.convert("RGBA"))[:, :, 3] > 0)
    if not alpha.any():
        return 0
    ys, xs = np.nonzero(alpha)
    crop = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    mask = Image.fromarray((crop * 255).astype(np.uint8), "L")
    count = 0
    while True:
        narrowed = mask.filter(ImageFilter.MinFilter(3))
        if not np.asarray(narrowed).any():
            return count
        mask = narrowed
        count += 1


def _run_near(row: np.ndarray, x: int, tol: int) -> tuple[int, int] | None:
    best = None
    for start, end in _runs(row):
        if start - tol <= x <= end + tol:
            if best is None or end - start > best[1] - best[0]:
                best = (start, end)
    return best


def _overlap_run(row: np.ndarray, start: int, end: int, tol: int = 1) -> tuple[int, int] | None:
    best = None
    for s, e in _runs(row):
        if min(e, end) - max(s, start) >= 0 or (s - tol <= end and e + tol >= start):
            if best is None or e - s > best[1] - best[0]:
                best = (s, e)
    return best


def measure_frame(frame: Image.Image) -> dict | None:
    """测一帧的人物本体：排除细武器/特效后的最大连通块 + 头部宽度/面积。

    量的是“这一帧人物被画成多大”，不是绝对站高：蹲伏、腾空收腿会体现在
    height 上，头宽/头面积仍按同 clip 中位数比较。
    """
    alpha = np.asarray(frame.convert("RGBA"))[:, :, 3] > 0
    if not alpha.any():
        return None
    # 3×3 开运算去掉 1–2 像素宽的武器杆、光刃、粒子连线；头部和躯干保留。
    mask_image = Image.fromarray((alpha * 255).astype(np.uint8), "L")
    opened = np.asarray(mask_image.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))) > 0
    body = _largest_component(opened)
    ys, xs = np.nonzero(body)
    if len(ys) == 0:
        return None
    body_top = int(ys.min())
    body_bottom = int(max(0, min(alpha.shape[0] - 1, ys.max() + 1)))  # 开运算各缩 1 像素
    height_est = body_bottom - max(0, body_top - 1) + 1
    band = max(6, int(round(height_est * 0.18)))
    band = min(band, alpha.shape[0] - 1)
    top_band = body[body_top:min(body.shape[0], body_top + band)]
    band_ys, band_xs = np.nonzero(top_band)
    if len(band_xs) == 0:
        return None
    cx = int(np.median(band_xs))

    # 顶部带内最宽的、靠近中轴的段就是头（举起的细手臂通常更窄）。
    best = None
    tol = max(2, int(round(height_est * 0.02)))
    for y in range(body_top, min(alpha.shape[0], body_top + band)):
        run = _run_near(alpha[y], cx, tol)
        if run and (best is None or run[1] - run[0] > best[1] - best[0]):
            best = (run[0], run[1], y)
    if best is None:
        return None
    start, end, widest_y = best
    head_top = widest_y
    # 从最宽处向上接续头部；手/武器与头之间通常断开，不会被接上。
    for y in range(widest_y - 1, max(-1, body_top - 3), -1):
        run = _overlap_run(alpha[y], start, end)
        if run is None or min(run[1], end) - max(run[0], start) < 0:
            break
        start, end = run
        head_top = y

    # 头宽与头部面积只在约 0.16 倍站高的窗口内量，避免滑进肩部。
    window = max(8, int(round(height_est * 0.16)))
    head_width = 0
    head_area = 0
    for y in range(head_top, min(alpha.shape[0], head_top + window)):
        run = _run_near(alpha[y], cx, max(2, int(round(height_est * 0.03))))
        if run:
            width = run[1] - run[0] + 1
            head_area += width
            head_width = max(head_width, width)
    if head_width == 0:
        return None
    foot_bottom = body_bottom - 1
    return {
        "head_top": head_top,
        "head_cx": cx,
        "head_width": int(head_width),
        "head_area": int(head_area),
        "body_top": body_top,
        "body_width": int(xs.max() - xs.min() + 1),
        "foot_bottom": foot_bottom,
        "height": int(foot_bottom - head_top + 1),
        "thickness": _thickness(frame),
    }


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def analyze_clip(fighter: str, name: str, clip: dict, verbose: bool = False) -> dict:
    texture_path = ROOT / str(clip["texture"]).removeprefix("res://")
    atlas = Image.open(texture_path).convert("RGBA")
    atlas_array = np.asarray(atlas)
    rows = []
    for index, rect in enumerate(clip["rects"]):
        x, y, w, h = [int(v) for v in rect]
        frame = Image.fromarray(atlas_array[y:y + h, x:x + w].copy())
        measurement = measure_frame(frame)
        anchor = clip["anchors"][index] if index < len(clip.get("anchors", [])) else clip.get("anchor")
        rows.append({"index": index, "rect": [x, y, w, h], "anchor": anchor, "measurement": measurement})
    measured = [row for row in rows if row["measurement"]]
    if len(measured) < 2:
        return {
            "clip": name,
            "texture": clip["texture"],
            "status": "unmeasured",
            "reason": "可测帧不足 2 帧，无法建立同 clip 中位数",
            "frames": rows,
            "anomalies": [],
            "suspects": [],
        }
    median_width = _median([row["measurement"]["head_width"] for row in measured])
    median_area = _median([row["measurement"]["head_area"] for row in measured])
    median_height = _median([row["measurement"]["height"] for row in measured])
    median_thickness = _median([row["measurement"]["thickness"] for row in measured])
    intentional = name in INTENTIONAL_SCALE_CLIPS
    anomalies, suspects = [], []
    for row in rows:
        measurement = row["measurement"]
        if not measurement:
            row["status"] = "unmeasured"
            row["reason"] = "空帧或无法分离人物本体"
            continue
        width_scale = measurement["head_width"] / median_width if median_width else None
        area_scale = (measurement["head_area"] / median_area) ** 0.5 if median_area else None
        height_ratio = measurement["height"] / median_height if median_height else None
        thickness_ratio = measurement["thickness"] / median_thickness if median_thickness else None
        body_aspect = measurement["body_width"] / measurement["height"] if measurement["height"] else 0.0
        row.update({"head_width_scale": round(width_scale, 4) if width_scale else None,
                    "head_area_scale": round(area_scale, 4) if area_scale else None,
                    "height_ratio": round(height_ratio, 4) if height_ratio else None,
                    "thickness_ratio": round(thickness_ratio, 4) if thickness_ratio else None,
                    "body_aspect": round(body_aspect, 4)})
        head_high = max(filter(None, [width_scale, area_scale]), default=None)
        head_low = min(filter(None, [width_scale, area_scale]), default=None)
        if head_high is None or height_ratio is None:
            row["status"] = "unmeasured"
            continue
        # 整帧等比缩放时，头宽、头面积（开方）和站高应按同一比例走；
        # 转头、抬臂、尾巴/角进入测量区会破坏这些比值，不能当尺度突变。
        shape_ratio = area_scale / width_scale if width_scale else 0.0
        area_height = area_scale / height_ratio if height_ratio else 0.0
        width_height = width_scale / height_ratio if height_ratio else 0.0
        coherent = (0.92 <= shape_ratio <= 1.08 and 0.90 <= area_height <= 1.10
                    and 0.90 <= width_height <= 1.10)
        row["coherence"] = {"area_over_width": round(shape_ratio, 4),
                            "area_over_height": round(area_height, 4),
                            "width_over_height": round(width_height, 4),
                            "coherent": coherent}
        # 自动缩放的旁证：躯干/肢体厚度也应跟着变大，且人物仍接近直立；
        # 厚度不跟随、或身体横过来（击飞/翻滚）时只交人眼，不自动缩。
        safe = bool(thickness_ratio and thickness_ratio >= 0.97
                    and abs(thickness_ratio - area_scale) <= 0.15
                    and body_aspect <= 1.15)
        row["fix_safe"] = safe
        if (height_ratio >= 1 + THRESHOLD and head_low >= 1 + CORROBORATE
                and head_high >= 1 + THRESHOLD and coherent):
            if intentional:
                row["status"] = "intentional"
                row["reason"] = "捕捉/恢复动作本身就会改变人物大小，不是尺度事故"
            else:
                row["status"] = "scale_jump"
                row["reason"] = "站高与头宽/头面积同比例偏大，判定整帧人物放大"
                anomalies.append(row["index"])
        elif (height_ratio >= 1.10 and head_high >= 1.10) or (head_high >= 1.10 and height_ratio >= 1.02):
            if intentional:
                row["status"] = "intentional"
                row["reason"] = "捕捉/恢复动作本身就会改变人物大小，不是尺度事故"
            else:
                row["status"] = "suspect"
                row["reason"] = "尺度指标偏大但彼此不一致，可能含转头/遮挡/武器，需人眼复核"
                suspects.append(row["index"])
        elif head_high >= 1.15 and head_low >= 1.08 and coherent and 0.95 <= height_ratio <= 1.05:
            row["status"] = "suspect"
            row["reason"] = "头部同比例偏大但站高未同步，可能为蹲姿中放大或局部重画，需人眼复核"
            suspects.append(row["index"])
        elif height_ratio <= 1 - THRESHOLD and head_high <= 1 - CORROBORATE:
            row["status"] = "suspect"
            row["reason"] = "头部与站高同时偏小，可能存在另一方向尺度漂移，需人眼复核"
            suspects.append(row["index"])
        else:
            row["status"] = "ok"
            row["reason"] = ""
    if anomalies:
        status = "anomaly"
    elif suspects:
        status = "suspect"
    else:
        status = "ok"
    result = {
        "clip": name,
        "texture": clip["texture"],
        "cell": clip.get("cell"),
        "anchor": clip.get("anchor"),
        "median": {"head_width": median_width, "head_area": median_area,
                   "height": median_height, "thickness": median_thickness},
        "frames": rows,
        "anomalies": anomalies,
        "suspects": suspects,
        "status": status,
    }
    if verbose:
        print(f"  {fighter}/{name}: {status} 中位头宽={median_width:.1f} 中位头面积={median_area:.0f} 中位站高={median_height:.1f}")
        for row in rows:
            if row["status"] in ("scale_jump", "suspect"):
                print(f"    frame {row['index']}: {row['status']} "
                      f"头宽x{row.get('head_width_scale')} 头面积x{row.get('head_area_scale')} "
                      f"站高x{row.get('height_ratio')} — {row['reason']}")
    return result


def scan(fighters: list[str], clips: list[str], verbose: bool = False) -> dict:
    report = {"schema": 1, "tool": "frame_scale_jumps", "threshold": THRESHOLD,
              "corroborate": CORROBORATE, "fighters": []}
    for fighter in fighters:
        manifest_path = ROOT / "assets/fighters" / fighter / "animations/manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = read_json(manifest_path)
        clip_rows = []
        for name, clip in manifest.get("clips", {}).items():
            if clips and name not in clips:
                continue
            clip_rows.append(analyze_clip(fighter, name, clip, verbose=verbose))
        report["fighters"].append({"fighter": fighter, "manifest": manifest_path.relative_to(ROOT).as_posix(),
                                   "clips": clip_rows})
        if verbose:
            print(f"{fighter}: {len(clip_rows)} clips")
    all_clips = [clip for fighter in report["fighters"] for clip in fighter["clips"]]
    report["summary"] = {
        "fighters": len(report["fighters"]),
        "clips": len(all_clips),
        "anomaly_clips": sum(1 for clip in all_clips if clip["status"] == "anomaly"),
        "suspect_clips": sum(1 for clip in all_clips if clip["status"] == "suspect"),
        "anomaly_frames": sum(len(clip["anomalies"]) for clip in all_clips),
        "suspect_frames": sum(len(clip["suspects"]) for clip in all_clips),
    }
    return report


def _scale_estimate(row: dict) -> float:
    """确定突变帧的目标/现状比例；头部两指标与站高都参与，避免单指标量化误差。"""
    measurement = row["measurement"]
    values = []
    if row.get("head_area_scale"):
        values.append(row["head_area_scale"])
    if row.get("head_width_scale"):
        values.append(row["head_width_scale"])
    if row.get("height_ratio") and row["height_ratio"] >= 1 + CORROBORATE:
        values.append(row["height_ratio"])
    # 头部指标权重更高：姿势站直只影响站高。
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return (values[0] * 0.6 + values[1] * 0.4) if row.get("head_area_scale") else statistics.mean(values)
    return values[0] * 0.45 + values[1] * 0.35 + values[2] * 0.20


def resize_around_anchor(frame: Image.Image, anchor: list[int], factor: float) -> Image.Image:
    """以 anchor 为不动点做最近邻反采样；factor<1 表示缩回。Alpha 保持 0/255。"""
    source = np.asarray(frame.convert("RGBA")).copy()
    height, width = source.shape[:2]
    ax, ay = float(anchor[0]), float(anchor[1])
    ys, xs = np.mgrid[0:height, 0:width]
    sx = np.floor(ax + (xs - ax) / factor + 0.5).astype(np.int32)
    sy = np.floor(ay + (ys - ay) / factor + 0.5).astype(np.int32)
    valid = (sx >= 0) & (sx < width) & (sy >= 0) & (sy < height)
    out = np.zeros_like(source)
    out[valid] = source[sy[valid], sx[valid]]
    out[:, :, 3] = np.where(out[:, :, 3] > 0, 255, 0)
    return Image.fromarray(out)


def refine_factor(frame: Image.Image, anchor: list[int], row: dict, medians: dict) -> tuple[float, dict]:
    """在初估附近细搜最近邻系数，优先让头面积/站高回到中位数；头宽量化粗，权重较低。"""
    estimate = 1.0 / _scale_estimate(row)
    low = max(0.30, estimate * 0.94)
    high = min(1.20, estimate * 1.06)
    best = None
    factor = low
    while factor <= high + 1e-9:
        measurement = measure_frame(resize_around_anchor(frame, anchor, factor))
        if measurement:
            width_ratio = measurement["head_width"] / medians["head_width"]
            area_ratio = (measurement["head_area"] / medians["head_area"]) ** 0.5
            height_ratio = measurement["height"] / medians["height"]
            cost = (0.45 * abs(math.log(area_ratio)) + 0.30 * abs(math.log(height_ratio))
                    + 0.25 * abs(math.log(width_ratio)))
            if best is None or cost < best[0]:
                best = (cost, factor, measurement)
        factor += 0.005
    if best is None:
        return estimate, {}
    return best[1], {"refine_cost": round(best[0], 6), "refined_measurement": best[2]}


def _object_span_end(data: bytes, start: int) -> int:
    """start 指向对象/数组左括号，返回配对右括号之后的位置。"""
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(data)):
        byte = data[i]
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth == 0:
                return i + 1
    raise SystemExit("manifest 结构不完整，拒绝写入")


def _depth_at(data: bytes, start: int, pos: int) -> int:
    """返回 pos 处相对 start（左括号）的嵌套深度。"""
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, pos):
        byte = data[i]
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
        elif byte in (0x7D, 0x5D):
            depth -= 1
    return depth


def _replace_clip_sha(data: bytes, clip_name: str, old_sha: str, new_sha: str) -> bytes:
    """只改 clips 下该 clip 对象顶层的 atlas_sha256，保留历史 review SHA 与排版。"""
    clips = re.search(rb'"clips"\s*:\s*\{', data)
    if not clips:
        raise SystemExit("manifest 中找不到 clips，拒绝写入")
    clips_open = clips.end() - 1
    clips_end = _object_span_end(data, clips_open)
    pattern = re.compile(rb'"' + re.escape(clip_name.encode("ascii")) + rb'"\s*:\s*\{')
    match = next((m for m in pattern.finditer(data, clips_open, clips_end)
                  if _depth_at(data, clips_open, m.start()) == 1), None)
    if not match:
        raise SystemExit(f"manifest 中找不到 clip {clip_name}，拒绝写入")
    block_start = match.end() - 1
    block_end = _object_span_end(data, block_start)
    block = data[block_start:block_end]
    key = b'"atlas_sha256"'
    key_at = block.find(key)
    if key_at < 0:
        raise SystemExit(f"clip {clip_name} 缺少 atlas_sha256，拒绝写入")
    quote1 = block.find(b'"', key_at + len(key))
    quote2 = block.find(b'"', quote1 + 1) if quote1 >= 0 else -1
    if quote1 < 0 or quote2 < 0:
        raise SystemExit(f"clip {clip_name} 的 atlas_sha256 格式异常，拒绝写入")
    if block[quote1 + 1:quote2].decode("ascii") != old_sha:
        raise SystemExit(f"clip {clip_name} 的 atlas_sha256 与预期不符，拒绝写入")
    new_block = block[:quote1 + 1] + new_sha.encode("ascii") + block[quote2:]
    return data[:block_start] + new_block + data[block_end:]


def apply_fix(fighter: str, clip_name: str, frames: list[int], report: dict, record_path: Path,
              force: bool = False) -> dict:
    """只缩放指定帧的矩形；其它帧像素不变，并同步 manifest 图集 SHA。"""
    manifest_path = ROOT / "assets/fighters" / fighter / "animations/manifest.json"
    manifest = read_json(manifest_path)
    clip = manifest["clips"][clip_name]
    clip_report = next(c for f in report["fighters"] if f["fighter"] == fighter
                       for c in f["clips"] if c["clip"] == clip_name)
    by_index = {row["index"]: row for row in clip_report["frames"]}
    texture_path = ROOT / str(clip["texture"]).removeprefix("res://")
    atlas = Image.open(texture_path).convert("RGBA")
    atlas_array = np.asarray(atlas).copy()
    before_sha = sha256(texture_path)
    before = []
    for index in frames:
        row = by_index[index]
        if row["status"] != "scale_jump":
            raise SystemExit(f"{fighter}/{clip_name} frame {index} 不是确定的整帧尺度突变，拒绝自动缩放")
        if not row.get("fix_safe") and not force:
            raise SystemExit(f"{fighter}/{clip_name} frame {index} 的厚度/朝向旁证不足"
                             "（可能含武器、转头或横躺姿态）；须先人眼复核再用 --force")
        x, y, w, h = row["rect"]
        anchor = row["anchor"]
        cell = Image.fromarray(atlas_array[y:y + h, x:x + w].copy())
        factor, refinement = refine_factor(cell, anchor, row, clip_report["median"])
        atlas_array[y:y + h, x:x + w] = np.asarray(resize_around_anchor(cell, anchor, factor))
        after = measure_frame(Image.fromarray(atlas_array[y:y + h, x:x + w]))
        before.append({
            "frame": index,
            "rect": row["rect"],
            "anchor": anchor,
            "measurement_before": row["measurement"],
            "scales_before": {k: row.get(k) for k in ("head_width_scale", "head_area_scale", "height_ratio")},
            "estimated_scale": round(_scale_estimate(row), 6),
            "applied_factor": round(factor, 6),
            "forced_without_safe_gate": bool(force and not row.get("fix_safe")),
            "refinement": refinement,
            "measurement_after": after,
        })
    result_image = Image.fromarray(atlas_array)
    result_image.save(texture_path)
    after_sha = sha256(texture_path)
    old_sha = clip.get("atlas_sha256")
    if old_sha:
        # 只替换该 clip 顶层的 atlas_sha256；motion_review 等历史 SHA 保持原样。
        manifest_bytes = manifest_path.read_bytes()
        manifest_path.write_bytes(_replace_clip_sha(manifest_bytes, clip_name, old_sha, after_sha))
    # 修复后重测整段，留下前后对照。
    updated_manifest = read_json(manifest_path)
    after_clip = analyze_clip(fighter, clip_name, updated_manifest["clips"][clip_name])
    record = {
        "fighter": fighter,
        "clip": clip_name,
        "texture": clip["texture"],
        "atlas_sha256_before": before_sha,
        "atlas_sha256_after": after_sha,
        "force": bool(force),
        "frames": before,
        "clip_median": clip_report["median"],
        "remeasure": {"median": after_clip["median"],
                      "frames": [{k: row.get(k) for k in
                                  ("index", "status", "head_width_scale", "head_area_scale", "height_ratio", "reason")}
                                 for row in after_clip["frames"]]},
    }
    if record_path.exists():
        try:
            existing = read_json(record_path)
        except (OSError, ValueError):
            existing = None
        if existing and existing.get("fighter") == fighter and existing.get("clip") == clip_name:
            # 同一 clip 分批修复时保留先前帧的记录与最初 SHA，不覆盖旧证据。
            passes = list(existing.get("passes") or [])
            if not passes and existing.get("atlas_sha256_after"):
                passes.append({"atlas_sha256_before": existing.get("atlas_sha256_before"),
                               "atlas_sha256_after": existing.get("atlas_sha256_after"),
                               "force": existing.get("force", False),
                               "frames": [f["frame"] for f in existing.get("frames", [])],
                               "clip_median": existing.get("clip_median"),
                               "remeasure": existing.get("remeasure")})
            merged = {f["frame"]: f for f in existing.get("frames", [])}
            for f in before:
                merged[f["frame"]] = f
            record["frames"] = [merged[i] for i in sorted(merged)]
            record["atlas_sha256_before"] = existing.get("atlas_sha256_before", before_sha)
            record["passes"] = passes + [{
                "atlas_sha256_before": before_sha,
                "atlas_sha256_after": after_sha,
                "force": bool(force),
                "frames": [f["frame"] for f in before],
                "clip_median": clip_report["median"],
                "remeasure": record["remeasure"],
            }]
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fighter", action="append", default=[], help="只扫这些角色 id，可重复")
    parser.add_argument("--clip", action="append", default=[], help="只扫这些 clip，可重复")
    parser.add_argument("--output", default=str(DEFAULT_REPORT), help="JSON 报告路径")
    parser.add_argument("--verbose", action="store_true", help="逐帧打印异常")
    parser.add_argument("--fix", action="store_true", help="自动修复确定的整帧尺度突变（须同时给 --fighter/--clip/--frames）")
    parser.add_argument("--force", action="store_true", help="人眼已复核时，允许修复厚度/朝向旁证不足的确定突变帧")
    parser.add_argument("--frames", nargs="+", type=int, default=[], help="要修复的帧号")
    parser.add_argument("--record", default="",
                        help="修复前后测量记录路径；缺省为 reports/frame-scale-jumps/<fighter>-<clip>.json")
    args = parser.parse_args()

    fighters = args.fighter or playable_fighters()
    report = scan(fighters, args.clip, verbose=args.verbose)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    if args.verbose:
        print("SUMMARY " + json.dumps(summary, ensure_ascii=False))

    if args.fix:
        if not (args.fighter and args.clip and args.frames):
            parser.error("--fix 需要 --fighter、--clip 和 --frames")
        if len(args.fighter) != 1 or len(args.clip) != 1:
            parser.error("--fix 一次只允许一个角色和一个 clip")
        record_path = Path(args.record) if args.record else (
            ROOT / "reports/frame-scale-jumps" / f"{args.fighter[0]}-{args.clip[0]}.json")
        if not record_path.is_absolute():
            record_path = ROOT / record_path
        record = apply_fix(args.fighter[0], args.clip[0], args.frames, report, record_path, force=args.force)
        print("FIXED " + json.dumps({
            "fighter": record["fighter"], "clip": record["clip"],
            "atlas_sha256": record["atlas_sha256_after"],
            "frames": [f["frame"] for f in record["frames"]],
            "scales": [f["applied_factor"] for f in record["frames"]],
        }, ensure_ascii=False))
        return 0

    anomalies = [f"{f['fighter']}/{c['clip']} frames={c['anomalies']}"
                 for f in report["fighters"] for c in f["clips"] if c["anomalies"]]
    suspects = [f"{f['fighter']}/{c['clip']} frames={c['suspects']}"
                for f in report["fighters"] for c in f["clips"] if c["suspects"]]
    if anomalies:
        print("FRAME_SCALE_JUMP：仅清单如下，未自动修改。")
        for line in anomalies:
            print("  " + line)
    if suspects:
        print("FRAME_SCALE_REVIEW：无法确定人物本体或武器/特效，需人眼复核。")
        for line in suspects:
            print("  " + line)
    if not anomalies and not suspects:
        print("FRAME_SCALE_PASS：全部已测帧与同 clip 中位尺度一致（阈值 ±8%）。")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
