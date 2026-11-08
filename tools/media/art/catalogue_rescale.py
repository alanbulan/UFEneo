"""按原作设定身高把图鉴像素形象校正到正确的相对大小。

问题：之前所有图都被拉到 192 像素站高，导致 40 米的奥特曼和 60 米的怪兽
显示成一样大。本工具读 catalogue_scale.json 的标尺，按设定身高换算目标
站高，再重排到画布。

两条路径：
- 有 raw.png 的：从原始高分图重新降采样（画质最好）
- 只有定稿 PNG 的：对现有像素图做最近邻缩放（保持像素硬边）

人类（story）不按米换算，统一用固定站高。
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
SCALE_PATH = ROOT / "content/roster/catalogue_scale.json"
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
CANVAS_WIDTH = 384
CANVAS_HEIGHT = 256
ROOT_Y = 248


def load_scale() -> dict:
    return json.loads(SCALE_PATH.read_text(encoding="utf-8"))


def target_height(scale: dict, catalogue_id: str, kind: str) -> tuple[int, str]:
    """返回 (目标站高像素, 依据说明)。"""
    convention = scale["convention"]
    if kind in convention["human"]["applies_to_kinds"]:
        return int(convention["human"]["fixed_pixels"]), "human_fixed"

    giant = convention["giant"]
    meters = scale.get("heights_m", {}).get(catalogue_id)
    basis = "canonical"
    if meters is None:
        meters = scale["default_meters_by_kind"].get(kind, 50)
        basis = "kind_default"
    pixels = round(meters * giant["pixels_per_meter"])
    clamped = max(giant["min_pixels"], min(giant["max_pixels"], pixels))
    if clamped != pixels:
        basis += "_clamped"
    return clamped, basis


def trim(image: Image.Image) -> Image.Image:
    box = image.getchannel("A").getbbox()
    if box is None:
        raise ValueError("没有可见像素")
    return image.crop(box)


def place(image: Image.Image, height: int) -> tuple[Image.Image, dict]:
    """按目标站高把人物放到画布上，脚底贴 ROOT_Y，水平居中。

    先裁掉透明边再算比例——之前拿整张 384×256 画布当分母，人物被二次
    缩小并偏移，最低只剩十几个像素高。
    """
    image = trim(image)
    scale = height / image.height
    width = max(1, round(image.width * scale))
    if width > CANVAS_WIDTH - 8:
        shrink = (CANVAS_WIDTH - 8) / width
        width, height = max(1, round(width * shrink)), max(1, round(height * shrink))
    resized = trim(image.resize((width, height), Image.NEAREST))
    # 最近邻缩放偶尔丢一行可见像素（216→192 会得到 191）。以裁后实际高度
    # 落位，脚底仍然贴地，避免把 1 像素误差带进声明值。
    width, height = resized.size
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    left = (CANVAS_WIDTH - width) // 2
    top = max(0, ROOT_Y - height)
    canvas.alpha_composite(resized, (left, top))
    return canvas, {"subject": [width, height], "left": left, "top": top}


def binarize(image: Image.Image) -> Image.Image:
    array = np.array(image)
    array[:, :, 3] = np.where(array[:, :, 3] >= 128, 255, 0).astype(np.uint8)
    return Image.fromarray(array, "RGBA")


def native_path(catalogue_id: str, display_entry: dict) -> Path:
    """图鉴图有两个存放位置：catalogue/ 子目录，或 fighters/<id>/ 根目录。"""
    declared = str(display_entry.get("image", "")).removeprefix("res://")
    if declared:
        candidate = ROOT / declared
        if candidate.is_file():
            return candidate
    return ROOT / f"assets/fighters/{catalogue_id}/catalogue/model-native.png"


def rescale_one(catalogue_id: str, kind: str, scale: dict,
                display_entry: dict, dry_run: bool = False,
                force: bool = False) -> dict:
    height, basis = target_height(scale, catalogue_id, kind)
    native = native_path(catalogue_id, display_entry)
    raw = ROOT / f"reports/catalogue-ref/{catalogue_id}/raw.png"
    if not native.is_file():
        return {"id": catalogue_id, "status": "missing_native", "path": native.relative_to(ROOT).as_posix()}

    with Image.open(native) as source:
        current = source.convert("RGBA")
    before = trim(current).height
    # 幂等：宽度超限会被再压一次，只认 last_target，避免越跑越小。
    if int(display_entry.get("scale_target", -1)) == height and not force:
        return {"id": catalogue_id, "status": "unchanged", "height": before,
                "target": height, "basis": basis}
    if before == height and not raw.is_file() and not force:
        return {"id": catalogue_id, "status": "unchanged", "height": before,
                "target": height, "basis": basis}

    if raw.is_file():
        # 从原始高分图重跑，画质最好。
        from catalogue_native import build_head_weighted_palette, downsample, load_raw
        source = load_raw(raw)
        reduced = downsample(trim(source), height)
        palette = build_head_weighted_palette(reduced)
        from catalogue_native import apply_palette
        quantized = apply_palette(reduced, palette)
        canvas, placement = place(quantized, height)
        path = "raw"
    else:
        # 只有像素定稿：最近邻缩放，保持硬边。
        canvas, placement = place(binarize(current), height)
        path = "native"

    # 自检：写盘后重新量一次，实际站高必须等于落位高度，否则宁可报错。
    actual = trim(canvas).height if not dry_run else placement["subject"][1]
    if actual != placement["subject"][1]:
        raise SystemExit(f"{catalogue_id}: 实际站高 {actual} 与落位 {placement['subject'][1]} 不符")

    if not dry_run:
        canvas.save(native)
    return {
        "id": catalogue_id,
        "status": "rescaled" if not dry_run else "would_rescale",
        "path": path,
        "from": before,
        "to": placement["subject"][1],
        "target": height,
        "basis": basis,
        "sha256": hashlib.sha256(native.read_bytes()).hexdigest() if not dry_run else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="忽略 scale_target，强制重算")
    parser.add_argument("--only", nargs="*", help="只处理指定 id")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/catalogue-scale/report.json")
    args = parser.parse_args()

    scale = load_scale()
    index = json.loads((ROOT / "content/roster/index.json").read_text(encoding="utf-8"))
    kind_of = {row["id"]: row.get("kind", "") for row in index["entries"]}
    display = json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))

    targets = args.only if args.only else [
        cid for cid, entry in display["entries"].items() if entry.get("image")
    ]

    results = [rescale_one(cid, kind_of.get(cid, ""), scale,
                            display["entries"].get(cid, {}), args.dry_run, args.force)
               for cid in targets]
    counts: dict[str, int] = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    # 同步 display 里的 visible_height_including_ornaments 与 native_root。
    # 逐条经 catalogue_store 的 flock 合并，避免与其它批处理并发时整文件覆盖。
    if not args.dry_run:
        import catalogue_store
        for row in results:
            entry = display["entries"].get(row["id"])
            if entry is None:
                continue
            if row["status"] == "unchanged":
                # 已经对过尺寸的也记下标尺，下一轮直接跳过。
                if "target" in row:
                    catalogue_store.update_entry(row["id"], {"scale_target": row["target"]})
                continue
            if row["status"] != "rescaled":
                continue
            # 声明高度一律按磁盘实际像素回写，避免图与记录各说各话。
            image = str(entry.get("image", "")).removeprefix("res://")
            candidate = ROOT / image
            actual = row["to"]
            sha = row["sha256"]
            if candidate.is_file():
                with Image.open(candidate) as handle:
                    box = handle.convert("RGBA").getchannel("A").getbbox()
                actual = (box[3] - box[1]) if box else 0
                sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
            catalogue_store.update_entry(row["id"], {
                "visible_height_including_ornaments": actual,
                "native_canvas": [CANVAS_WIDTH, CANVAS_HEIGHT],
                "native_root": [CANVAS_WIDTH // 2, ROOT_Y],
                "image_sha256": sha,
                "scale_target": row["target"],
            })

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps({"dry_run": args.dry_run, "counts": counts, "rows": results},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(counts, ensure_ascii=False, indent=2))
    changed = [r for r in results if r["status"] in ("rescaled", "would_rescale")]
    for row in changed[:15]:
        print(f"  {row['id']:28s} {row['from']:3d} -> {row['to']:3d}  ({row['basis']})")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools/media/art"))
    raise SystemExit(main())
