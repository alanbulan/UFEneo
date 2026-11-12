"""从已批准图鉴定稿生成 4× 最近邻身份锚。

标准（2026-11-09 定死）：动作帧生成只引用一张身份锚图——该角色已批准
像素定稿裁到 Alpha bbox 后的 4× 最近邻放大。锚图保留原始颜色与二值
Alpha，不做调色、平滑或重采样。

来源以 content/roster/catalogue_display.json 的 entries[<id>].image 为准，
并要求 image_sha256 与磁盘文件 SHA-256 一致；不一致时跳过并报告，不猜、
不改 display。输出：

    art/fighters/<id>/model/identity-anchor-x4.png
    art/fighters/<id>/model/identity-anchor.json

--all 只处理 selection.json 中 selection_category == "ultra" 且没有
assets/fighters/<id>/animations/manifest.json 的角色；已实机角色默认跳过。
单个 id 加 --force 可越过实机排除，供人工排查。zoffy 由用户手工制作，
任何模式下都不生成本工具的锚图。

用法：
    .venv/bin/python tools/art/identity_anchor.py --all
    .venv/bin/python tools/art/identity_anchor.py <id>
    .venv/bin/python tools/art/identity_anchor.py <id> --force

重复运行输出逐字节相同。
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
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = _layout_root
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
SELECTION_PATH = ROOT / "content/roster/selection.json"
SCALE = 4
BINARY_ALPHA = {0, 255}
MAX_VISIBLE_COLORS = 32
# 用户正在手工制作佐菲；默认不生成，避免与其 stage1 工作冲突。
MANUAL_EXCLUSIONS = {
    "zoffy": "用户正在制作；现有锚图 art/fighters/zoffy/stage1/idle/references/identity-pixel-x4.png",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def manifest_path(fighter_id: str) -> Path:
    return ROOT / "assets/fighters" / fighter_id / "animations/manifest.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def output_paths(fighter_id: str) -> tuple[Path, Path]:
    model_dir = ROOT / "art/fighters" / fighter_id / "model"
    return model_dir / "identity-anchor-x4.png", model_dir / "identity-anchor.json"


def skip(fighter_id: str, reason: str, detail: str, **extra) -> dict:
    row = {"id": fighter_id, "reason": reason, "detail": detail}
    row.update(extra)
    return row


def precheck(fighter_id: str, entry: dict | None, force: bool) -> dict | None:
    """返回跳过记录；通过则返回 None。"""
    if fighter_id in MANUAL_EXCLUSIONS:
        return skip(fighter_id, "manual_exclusion", MANUAL_EXCLUSIONS[fighter_id])
    installed = manifest_path(fighter_id)
    if installed.is_file() and not force:
        return skip(fighter_id, "installed", f"已实机安装：{relative(installed)} 存在")
    if entry is None:
        return skip(fighter_id, "no_display_entry", "catalogue_display.json 没有该条目")
    image_value = entry.get("image")
    if not image_value:
        return skip(fighter_id, "no_image", "display 条目没有 image")
    if not image_value.startswith("res://"):
        return skip(fighter_id, "invalid_image_path", f"image 不是 res:// 路径：{image_value}")
    source = ROOT / image_value[len("res://"):]
    if not source.is_file():
        return skip(fighter_id, "image_missing", f"文件不存在：{image_value}")
    expected = entry.get("image_sha256")
    actual = sha256(source)
    if actual != expected:
        return skip(
            fighter_id,
            "sha256_mismatch",
            f"display.image_sha256 与文件不一致：{image_value}",
            expected_sha256=expected,
            actual_sha256=actual,
        )
    return None


def head_height(mask: np.ndarray) -> int:
    """头顶到颈（12%–50% 高度区间内最窄行）的行数，仅供报告参考。"""
    ys = np.nonzero(mask.any(axis=1))[0]
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    window = [
        (y, int(mask[y].sum())) for y in range(top, bottom + 1)
        if top + int(height * 0.12) <= y <= top + int(height * 0.50)
    ]
    neck, _ = min(window, key=lambda item: item[1])
    return neck - top


def build(fighter_id: str, entry: dict) -> dict:
    source = ROOT / entry["image"][len("res://"):]
    with Image.open(source) as opened:
        has_alpha = "A" in opened.getbands()
        image = opened.convert("RGBA")
    if not has_alpha:
        return skip(fighter_id, "no_alpha_channel", f"源图没有 Alpha 通道：{entry['image']}")

    array = np.array(image)
    alpha = array[:, :, 3]
    alpha_values = sorted(int(v) for v in np.unique(alpha))
    if not set(alpha_values).issubset(BINARY_ALPHA):
        return skip(
            fighter_id, "non_binary_alpha",
            f"源图 Alpha 不是二值：{alpha_values[:12]}", alpha_values=alpha_values,
        )
    mask = alpha > 0
    if not mask.any():
        return skip(fighter_id, "empty_alpha", f"源图没有可见像素：{entry['image']}")

    ys, xs = np.nonzero(mask)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    subject = image.crop(tuple(bbox))
    scaled = subject.resize(
        (subject.width * SCALE, subject.height * SCALE), Image.Resampling.NEAREST
    )

    png_path, json_path = output_paths(fighter_id)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    scaled.save(png_path)

    output_array = np.array(Image.open(png_path).convert("RGBA"))
    output_alpha = output_array[:, :, 3]
    output_values = sorted(int(v) for v in np.unique(output_alpha))
    visible = output_alpha > 0
    visible_colors = int(
        np.unique(output_array[:, :, :3][visible].reshape(-1, 3), axis=0).shape[0]
    )

    warnings: list[str] = []
    metadata_height = entry.get("visible_height_including_ornaments")
    if metadata_height is not None and int(metadata_height) != subject.height:
        warnings.append(
            f"站高与 display 记录不一致：bbox={subject.height}, display={metadata_height}"
        )
    if bbox[0] == 0 or bbox[1] == 0 or bbox[2] == image.width or bbox[3] == image.height:
        warnings.append(f"源图 bbox 触及画布边缘：{bbox}")
    if visible_colors > MAX_VISIBLE_COLORS:
        warnings.append(f"源图可见色超过 {MAX_VISIBLE_COLORS}：{visible_colors}")

    head = head_height(output_alpha > 0)
    output_height = scaled.height
    png_sha = sha256(png_path)
    metadata = {
        "schema": 1,
        "id": fighter_id,
        "display_name": entry.get("display_name", ""),
        "source": relative(source),
        "source_res_path": entry["image"],
        "source_sha256": entry["image_sha256"],
        "source_bbox": bbox,
        "source_bbox_size": [subject.width, subject.height],
        "output": relative(png_path),
        "output_sha256": png_sha,
        "output_size": [scaled.width, scaled.height],
        "scale": SCALE,
        "alpha_values": output_values,
        "binary_alpha": output_values == [0, 255],
        "visible_colors": visible_colors,
        "standing_height": subject.height,
        "head_height_px": head,
        "head_height_ratio": round(head / output_height, 4),
        "head_height_note": "启发式：12%–50% 高度区间最窄行到头顶；头冠/角会让数值偏小，仅供报告参考",
        "warnings": warnings,
    }
    json_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def selected_ultra_ids() -> list[str]:
    selection = read_json(SELECTION_PATH)
    return [
        entry["id"] for entry in selection["entries"]
        if entry.get("selection_category") == "ultra"
    ]


def run(fighter_ids: list[str], entries: dict, force: bool) -> dict:
    generated: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    for fighter_id in fighter_ids:
        entry = entries.get(fighter_id)
        reason = precheck(fighter_id, entry, force)
        if reason is not None:
            skipped.append(reason)
            continue
        try:
            result = build(fighter_id, entry)
        except Exception as error:  # 报告具体角色和异常，不静默跳过。
            failed.append(skip(fighter_id, "error", f"{type(error).__name__}: {error}"))
            continue
        if result.get("reason"):
            # build() 的输入问题（非二值 Alpha 等）按无效源跳过，不放行。
            skipped.append(result)
        else:
            generated.append(result)

    summary = {
        "requested": len(fighter_ids),
        "generated": len(generated),
        "skipped": len(skipped),
        "failed": len(failed),
        "skipped_installed": sum(1 for row in skipped if row["reason"] == "installed"),
        "skipped_manual": sum(1 for row in skipped if row["reason"] == "manual_exclusion"),
        "skipped_invalid": sum(
            1 for row in skipped
            if row["reason"] not in {"installed", "manual_exclusion"}
        ),
    }
    return {
        "scale": SCALE,
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从已批准图鉴定稿生成 4× 最近邻身份锚。"
    )
    parser.add_argument("fighter", nargs="?", help="角色 id")
    parser.add_argument("--all", action="store_true", help="批量处理未实机的 ultra 角色")
    parser.add_argument(
        "--force", action="store_true",
        help="允许对已实机角色生成（人工排查用；手工排除角色仍不处理）",
    )
    args = parser.parse_args()
    if args.all == bool(args.fighter):
        parser.error("请给出单个角色 id，或使用 --all（二者只能选一个）")

    entries = read_json(DISPLAY_PATH)["entries"]
    if args.all:
        fighter_ids = selected_ultra_ids()
    else:
        fighter_ids = [args.fighter]

    report = run(fighter_ids, entries, args.force)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["failed"]:
        return 1
    if not args.all and not report["generated"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
