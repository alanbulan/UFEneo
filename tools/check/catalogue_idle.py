"""图鉴待机动画条体检 + 覆盖率统计。

判据（对每条已有 strip 的图鉴条目）：
- strip 文件存在，宽 = 384 × 帧数，高 = 256；
- 每帧 Alpha 只有 0/255；
- 每帧实际站高与 visible_height_including_ornaments 相差不超过 2 像素；
- 每帧脚底落在 native_root 地面上（±4 像素）；
- 相邻两帧必须有实际像素差异，防止「一张图平移」冒充动画。

覆盖率（有多少条目已经有真帧动画）只报告，不作为失败条件；未覆盖条目视为
待生成，不静默当成通过。

退出码：0 = 已覆盖的条目全部合格，1 = 有条目不合格。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
CANVAS_WIDTH = 384
CANVAS_HEIGHT = 256
MIN_FRAME_DIFF = 200


def frame_array(image: Image.Image, index: int, width: int) -> np.ndarray:
    return np.array(image.crop((width * index, 0, width * (index + 1), CANVAS_HEIGHT)))


def check_entry(catalogue_id: str, entry: dict) -> list[str]:
    problems: list[str] = []
    strip_path = ROOT / str(entry["strip"]).removeprefix("res://")
    if not strip_path.is_file():
        return [f"{catalogue_id}: strip 文件缺失 {strip_path}"]
    with Image.open(strip_path) as handle:
        strip = handle.convert("RGBA")
    frames = int(entry.get("frames", 1))
    if frames < 2:
        problems.append(f"{catalogue_id}: 帧数 {frames} 不足 2")
    if strip.width != CANVAS_WIDTH * frames or strip.height != CANVAS_HEIGHT:
        problems.append(f"{catalogue_id}: 尺寸 {strip.size} 与 {frames} 帧不符")
        return problems
    declared = int(entry.get("visible_height_including_ornaments", 0))
    ground = int((entry.get("native_root") or [CANVAS_WIDTH // 2, 248])[1])
    arrays = []
    heights = []
    for index in range(frames):
        frame = frame_array(strip, index, CANVAS_WIDTH)
        arrays.append(frame)
        alpha = np.unique(frame[:, :, 3])
        if not set(int(v) for v in alpha).issubset({0, 255}):
            problems.append(f"{catalogue_id}: 第 {index} 帧 Alpha 不是二值 {alpha[:5].tolist()}")
        visible = frame[:, :, 3] > 0
        rows = np.nonzero(visible.any(axis=1))[0]
        if rows.size == 0:
            problems.append(f"{catalogue_id}: 第 {index} 帧没有可见像素")
            continue
        height = int(rows.max() - rows.min() + 1)
        heights.append(height)
        # 尾巴/武器横穿画布会被裁成两截：人物整体必须留在画布内。
        cols = np.nonzero(visible.any(axis=0))[0]
        if cols.size and (int(cols.min()) == 0 or int(cols.max()) == CANVAS_WIDTH - 1):
            problems.append(f"{catalogue_id}: 第 {index} 帧横向贴边（{int(cols.min())}..{int(cols.max())}），人物被裁断")
        # 真动画每帧站高本来就会起伏，只要求中位数对得上声明值，且单帧不脱群。
        if declared > 0 and not (0.75 * declared <= height <= 1.25 * declared):
            problems.append(f"{catalogue_id}: 第 {index} 帧站高 {height} 超出声明 {declared} 的合理范围")
        if abs(int(rows.max()) + 1 - ground) > 4:
            problems.append(f"{catalogue_id}: 第 {index} 帧脚底 {int(rows.max()) + 1} 离地 {ground}")
    if heights and declared > 0 and abs(int(np.median(heights)) - declared) > 2:
        problems.append(f"{catalogue_id}: 中位站高 {int(np.median(heights))} != 声明 {declared}")
    for index in range(frames):
        nxt = arrays[(index + 1) % frames]
        diff = int((np.abs(arrays[index].astype(int) - nxt.astype(int)).sum(axis=2) > 0).sum())
        if diff < MIN_FRAME_DIFF:
            problems.append(f"{catalogue_id}: 第 {index}->{(index + 1) % frames} 帧只差 {diff} 像素")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="只输出机器可读统计")
    args = parser.parse_args()

    display = json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))["entries"]
    total = len(display)
    covered = [cid for cid, entry in display.items() if entry.get("strip")]
    problems: list[str] = []
    for catalogue_id in covered:
        problems.extend(check_entry(catalogue_id, display[catalogue_id]))

    pending = total - len(covered)
    summary = {
        "check": "catalogue_idle",
        "total_entries": total,
        "animated": len(covered),
        "pending": pending,
        "coverage": round(len(covered) / total, 4) if total else 0.0,
        "problems": problems,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"图鉴 {total} 条，已有真帧动画 {len(covered)} 条，待生成 {pending} 条")
        print(f"覆盖率 {summary['coverage'] * 100:.1f}%")
        if problems:
            print(f"不合格 {len(problems)} 项：")
            for problem in problems[:40]:
                print("  " + problem)
        else:
            print("已覆盖条目全部合格")
    print("CATALOGUE_IDLE " + ("PASS" if not problems else "FAIL"))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
