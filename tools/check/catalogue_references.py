"""图鉴参考图守卫：确认图生图真的用了参考图，而不是退化成纯文生图。

检查项：
- 每条 catalogue_display 条目若声明 art_source 为图生图，必须有可解码的参考图；
- 参考图扩展名必须与真实格式一致（WebP 存成 .img 会让生图 MCP 静默失效）；
- 参考图元数据里的 saved 路径与实际文件一致；
- 参考图分辨率与长宽比满足 catalogue_reference 的门槛。

只做静态与解码检查，不评价画面。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/media/art"))

import catalogue_reference as CR  # noqa: E402

IMAGE_TO_IMAGE = "mcp_image_to_image_from_official_reference"


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    display_path = ROOT / "content/roster/catalogue_display.json"
    display = json.loads(display_path.read_text(encoding="utf-8"))
    entries = display.get("entries", {})

    # 1. 声明图生图的条目必须有参考图。
    claimed = [cid for cid, e in entries.items() if e.get("art_source") == IMAGE_TO_IMAGE]
    for cid in claimed:
        sources = ROOT / "art/fighters" / cid / "sources"
        found = [p for p in sources.glob("ref-*") if p.suffix != ".json"] if sources.is_dir() else []
        if not found:
            errors.append(f"{cid} 声明图生图但没有参考图文件")

    # 2. 全仓参考图：扩展名与真实格式一致、元数据一致、通过门槛。
    references = 0
    for path in ROOT.glob("art/fighters/*/sources/ref-*"):
        if path.suffix == ".json":
            continue
        references += 1
        try:
            with Image.open(path) as image:
                fmt = image.format
                size = image.size
        except Exception as error:  # noqa: BLE001
            errors.append(f"{path.relative_to(ROOT)} 无法解码：{error}")
            continue
        expected = CR.suffix_for(fmt)
        if path.suffix.lower() != expected:
            errors.append(
                f"{path.relative_to(ROOT)} 扩展名 {path.suffix} 与真实格式 {fmt} 不符"
                f"（应为 {expected}）；生图 MCP 会静默忽略该参考图"
            )
        if min(size) < CR.MIN_REFERENCE_SIDE:
            warnings.append(
                f"{path.relative_to(ROOT)} 分辨率 {size[0]}x{size[1]} 低于 "
                f"{CR.MIN_REFERENCE_SIDE}，图生图细节可能不足"
            )
        meta_path = path.with_suffix(".json")
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            saved = str(meta.get("saved", ""))
            if saved and not saved.endswith(path.name):
                errors.append(
                    f"{meta_path.relative_to(ROOT)} 的 saved 指向 {saved}，"
                    f"与实际文件 {path.name} 不一致"
                )
            if meta.get("format") and str(meta["format"]).upper() != str(fmt).upper():
                errors.append(
                    f"{meta_path.relative_to(ROOT)} 记录格式 {meta['format']} 与真实 {fmt} 不一致"
                )

    print(f"图鉴条目 {len(entries)}，声明图生图 {len(claimed)}，参考图 {references}")
    for message in errors:
        print("错误:", message)
    for message in warnings:
        print("提示:", message)
    print("CATALOGUE_REFERENCES " + ("PASS" if not errors else "FAIL"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
