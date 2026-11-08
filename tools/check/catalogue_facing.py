"""图鉴朝向启发式检查：用 alpha 轮廓左右翻转 IoU 找出疑似正面图。

方法：
- 只取 Alpha 通道的二值轮廓，忽略颜色和内部线条；
- 按轮廓自身包围盒的垂直中线翻转（人物在画布内通常不居中，用画布中线会误判）；
- IoU = 交集 / 并集，越接近 1 越像左右对称的正面图。

这是启发式，不是身份或朝向的最终判定。窄幅侧视人物、球状怪兽、
正面物体都可能进入疑似清单，必须人工复核。脚本不修改任何图片或数据。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_layout_root = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
sys.path[:0] = [
    str(_layout_root / "tools"),
    *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()],
    *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()],
]

ROOT = _layout_root
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
DEFAULT_THRESHOLD = 0.85


def symmetry_iou(mask: np.ndarray) -> tuple[float, tuple[int, int, int, int] | None, int]:
    """返回 (轮廓包围盒中线翻转 IoU, 包围盒, 前景像素数)。"""
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return 0.0, None, 0
    top, bottom = int(ys.min()), int(ys.max()) + 1
    left, right = int(xs.min()), int(xs.max()) + 1
    cropped = mask[top:bottom, left:right]
    flipped = cropped[:, ::-1]
    intersection = int(np.logical_and(cropped, flipped).sum())
    union = int(np.logical_or(cropped, flipped).sum())
    return (intersection / union if union else 0.0), (left, top, right, bottom), int(ys.size)


def histogram(values: list[float]) -> list[dict]:
    """0.50 以下合并，0.50 到 1.00 每 0.05 一档。"""
    bins: list[dict] = [{"low": 0.0, "high": 0.5, "label": "<0.50", "count": 0}]
    for index in range(10, 20):
        low = index / 20.0
        high = (index + 1) / 20.0
        bins.append({"low": low, "high": high, "label": f"{low:.2f}-{high:.2f}", "count": 0})
    for value in values:
        if value < 0.5:
            bins[0]["count"] += 1
            continue
        index = min(19, int(value * 20.0))
        if index < 10:
            index = 10
        bins[index - 9]["count"] += 1
    return bins


def print_histogram(bins: list[dict], total: int) -> None:
    print("IoU 分布（轮廓包围盒中线翻转）：")
    peak = max((int(row["count"]) for row in bins), default=0)
    for row in bins:
        count = int(row["count"])
        bar = "#" * (round(count / peak * 40) if peak else 0)
        share = count / total * 100.0 if total else 0.0
        print(f"  {row['label']:>9}  {count:>4}  {share:>5.1f}%  {bar}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="疑似正面阈值，严格大于该值（默认 0.85）")
    parser.add_argument("--json-out", type=Path, help="把完整评分写入 JSON")
    args = parser.parse_args()
    if not 0.0 < args.threshold <= 1.0:
        parser.error("--threshold 必须在 (0, 1] 内")

    display = json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))
    entries = display.get("entries", {})
    index = json.loads((ROOT / "content/roster/index.json").read_text(encoding="utf-8"))
    supplemental = display.get("supplemental_entries", [])
    aliases = display.get("aliases", {})

    def canonical_id(value: str) -> str:
        seen: set[str] = set()
        while value in aliases:
            if value in seen or not aliases[value] or aliases[value] == value:
                break
            seen.add(value)
            value = str(aliases[value])
        return value

    canonical_rows = {canonical_id(str(row.get("id", ""))) for row in index.get("entries", [])}
    canonical_rows.update(canonical_id(str(row.get("id", ""))) for row in supplemental)
    names: dict[str, str] = {str(row.get("id", "")): str(row.get("name", "")) for row in index.get("entries", [])}
    for row in supplemental:
        names.setdefault(str(row.get("id", "")), str(row.get("name", "")))

    scores: list[dict] = []
    errors: list[str] = []
    for cid, entry in entries.items():
        image_ref = str(entry.get("image", ""))
        if not image_ref.startswith("res://"):
            errors.append(f"{cid}: image 不是 res:// 路径：{image_ref}")
            continue
        path = ROOT / image_ref[len("res://"):]
        if not path.is_file():
            errors.append(f"{cid}: 图片不存在：{image_ref}")
            continue
        try:
            with Image.open(path) as image:
                alpha = np.asarray(image.convert("RGBA"))[:, :, 3]
        except Exception as error:  # noqa: BLE001
            errors.append(f"{cid}: 无法读取 {image_ref}：{error}")
            continue
        mask = alpha > 0
        iou, bounds, pixels = symmetry_iou(mask)
        if bounds is None:
            errors.append(f"{cid}: Alpha 为空：{image_ref}")
            continue
        left, top, right, bottom = bounds
        width, height = right - left, bottom - top
        ys, xs = np.nonzero(mask)
        centroid_offset = (float(xs.mean()) - (left + right - 1) / 2.0) / width if width else 0.0
        scores.append({
            "id": str(cid),
            "name": names.get(str(cid), str(entry.get("display_name", ""))),
            "image": image_ref,
            "iou": round(iou, 6),
            "aspect": round(width / height, 4) if height else 0.0,
            "horizontal_centroid_offset": round(centroid_offset, 4),
            "alpha_pixels": pixels,
            "reachable": str(cid) == canonical_id(str(cid)) and str(cid) in canonical_rows,
        })

    if errors:
        for message in errors:
            print("错误:", message)
        print(f"CATALOGUE_FACING FAIL errors={len(errors)}")
        return 1

    scores.sort(key=lambda row: (-float(row["iou"]), str(row["id"])))
    suspicious = [row for row in scores if float(row["iou"]) > args.threshold]
    values = [float(row["iou"]) for row in scores]
    bins = histogram(values)
    print_histogram(bins, len(scores))
    print(f"\n图鉴条目 {len(scores)}，阈值 >{args.threshold:.2f}，疑似正面 {len(suspicious)}")
    print("疑似正面清单（按 IoU 降序；name 为图鉴页显示名）：")
    for rank, row in enumerate(suspicious, 1):
        print(f"  {rank:>2}. {row['iou']:.4f}  {row['id']:<26} {row['name']}  (宽高比 {row['aspect']:.2f})")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "method": "alpha silhouette, vertical flip about the bounding-box center, IoU",
            "threshold": args.threshold,
            "total": len(scores),
            "suspicious_count": len(suspicious),
            "histogram": bins,
            "suspicious": suspicious,
            "all_scores": scores,
        }
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nJSON 已写入 {args.json_out}")
    print(f"CATALOGUE_FACING PASS total={len(scores)} suspicious={len(suspicious)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
