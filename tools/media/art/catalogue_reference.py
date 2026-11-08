"""图鉴参考图收集与图生图出图规格。

用户要求：图鉴形象必须用官方剧照/皮套照做图生图，不接受纯文生图。
本模块只做两件确定性的事：
1. 从候选 URL 下载参考图，校验可解码、有足够分辨率、不是网页截图；
2. 生成图生图用的 prompt，明确"只参考造型，去掉玩具塑料感与关节穿帮"。

实际的 WebSearch 与 generate_image 调用由执行者完成；这里不联网。
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import urllib.parse

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_ROOT = ROOT / "art/fighters"
MIN_REFERENCE_SIDE = 320
# 明显是商品/玩具页的关键词，出现时 prompt 必须加强去塑料化。
TOY_HINTS = ("figuarts", "sofubi", "ソフビ", "フィギュア", "扭蛋", "软胶", "ultra-kaiju",
             "超合金", "chogokin", "gashapon", "ガシャポン", "banpresto", "バンプレスト")


def reference_path(catalogue_id: str, index: int = 1) -> Path:
    """参考图存放位置：art/fighters/<id>/sources/ref-<n>.<ext>。"""
    return REFERENCE_ROOT / catalogue_id / "sources" / f"ref-{index:02d}.img"


def validate(image_bytes: bytes) -> dict:
    """校验一张候选参考图。不合格抛 ValueError。"""
    try:
        with Image.open(io.BytesIO(image_bytes)) as probe:
            probe.load()
            size = probe.size
            mode = probe.mode
            fmt = probe.format
    except Exception as error:  # noqa: BLE001 - 任何解码失败都算不合格
        raise ValueError(f"不是可解码的图片：{error}") from None
    if min(size) < MIN_REFERENCE_SIDE:
        raise ValueError(f"分辨率过低：{size[0]}x{size[1]}，至少 {MIN_REFERENCE_SIDE}")
    # 网页截图常见特征：极长或极扁，且颜色数极少。
    ratio = max(size) / max(1, min(size))
    if ratio > 4.0:
        raise ValueError(f"长宽比异常 {ratio:.1f}:1，可能是网页截图")
    return {"size": list(size), "mode": mode, "format": fmt,
            "sha256": hashlib.sha256(image_bytes).hexdigest()}


def save(reference: bytes, catalogue_id: str, index: int = 1) -> Path:
    """校验后保存参考图；返回路径。"""
    info = validate(reference)
    path = reference_path(catalogue_id, index)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(reference)
    meta = path.with_suffix(".json")
    meta.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def looks_like_toy(source_url: str, page_title: str = "") -> bool:
    """判断参考来源是不是玩具/商品页。"""
    haystack = (urllib.parse.unquote(source_url) + " " + page_title).lower()
    return any(hint in haystack for hint in TOY_HINTS)


def image_prompt(name: str, name_jp: str, series: str, appearance: str,
                 toy_reference: bool) -> str:
    """构造图生图 prompt。参考图由 reference_images 传入，不在 prompt 里重复。"""
    parts = [
        "Convert the attached reference photograph into a single full-body pixel art sprite.",
        "",
        f"Subject: {name} ({name_jp}) — from the Ultraman series ({series}). {appearance}",
        "",
        "IDENTITY IS THE TOP PRIORITY: keep the exact silhouette, proportions, head shape, "
        "horn/crest layout, limb count, colour blocking and any distinctive markings visible in "
        "the reference. Do not redesign, do not add parts that are not in the reference, "
        "do not swap in another character's features.",
    ]
    if toy_reference:
        parts += [
            "",
            "The reference is a toy or action figure. Reproduce ONLY the creature's shape and "
            "colours. Do NOT draw ball joints, hinge seams, peg holes, plastic gloss, "
            "specular highlights, stand pegs, stickers or product text. The result must look "
            "like a living creature in the show, not merchandise.",
        ]
    parts += [
        "",
        "Pose: fixed side view facing right, in profile — only the near-side eye visible. "
        "Not three-quarter, not front view, not looking at the viewer. Neutral standing stance "
        "with both feet on the same ground line.",
        "",
        "Style: chunky 16-bit pixel art, hard pixel grid, roughly 32 flat colour steps, "
        "dark 1-pixel outline, top-left light source, no smooth gradients, no anti-aliasing, "
        "no noise, no realistic metal shading. Near-side limbs bright, far-side limbs in a "
        "darker shade of the same hue, separated by a dark outline where they cross.",
        "",
        "Composition: whole body including the full tail inside a centred 80% safe area with "
        "generous transparent margin on all sides. Feet must not touch the image border. "
        "No ground, no shadow, no scenery, no text, no UI, no glow, no effects. "
        "Genuine PNG alpha transparency — not a checkerboard, not a solid colour backdrop.",
    ]
    return "\n".join(parts)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="校验一个本地图片能否作为参考")
    p.add_argument("path", type=Path)

    p = sub.add_parser("prompt", help="输出图生图 prompt")
    p.add_argument("--name", required=True)
    p.add_argument("--name-jp", default="")
    p.add_argument("--series", default="")
    p.add_argument("--appearance", required=True)
    p.add_argument("--toy", action="store_true", help="参考图是玩具/商品照")

    args = parser.parse_args()
    if args.cmd == "check":
        info = validate(args.path.read_bytes())
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0
    print(image_prompt(args.name, args.name_jp, args.series, args.appearance, args.toy))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
