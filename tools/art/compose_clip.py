"""用同一角色已签的 cell 帧拼一个新 clip（不生成新图）。

用于把已有动作阶段的帧组合成缺失的过渡 clip（例如 vertical_jump 由
takeoff/air_rise/air_apex/air_fall/land 五帧组成，defeat 复用 ko）。
只复制已落格像素，不缩放、不改色。

用法：
    .venv/bin/python tools/art/compose_clip.py --fighter ultraman-justice \
        --clip vertical_jump --ticks 7,7,3,8,7 \
        --frame art/fighters/ultraman-justice/stage1/cells/takeoff-01-cell.png \
        --frame art/fighters/ultraman-justice/stage1/cells/air-rise-00-cell.png ...
    .venv/bin/python tools/art/compose_clip.py --fighter ultraman-justice \
        --clip defeat --from-clip ko
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fighter", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--from-clip", default="")
    ap.add_argument("--frame", action="append", default=[])
    ap.add_argument("--ticks", default="")
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()

    manifest_path = ROOT / f"assets/fighters/{args.fighter}/animations/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips = manifest["clips"]

    if args.from_clip:
        if args.from_clip not in clips:
            raise SystemExit(f"源 clip 不存在：{args.from_clip}")
        src = clips[args.from_clip]
        frames = [ROOT / r for r in []]
        # copy source atlas and rects as-is
        from PIL import Image
        src_atlas = Image.open(ROOT / src["texture"].replace("res://", "")).convert("RGBA")
        rects = [list(r) for r in src["rects"]]
        anchors = [list(a) for a in src["anchors"]]
        ticks = list(src["ticks"])
        cell = src["cell"]
        out_atlas = src_atlas
    else:
        if not args.frame:
            raise SystemExit("需要 --frame 或 --from-clip")
        from PIL import Image
        cells = []
        for f in args.frame:
            p = Path(f)
            p = p if p.is_absolute() else ROOT / p
            with Image.open(p) as im:
                cells.append(im.convert("RGBA"))
        cw, ch = cells[0].size
        for im in cells:
            if im.size != (cw, ch):
                raise SystemExit(f"cell 尺寸不一致：{im.size} != {(cw, ch)}")
        out_atlas = Image.new("RGBA", (cw * len(cells), ch))
        for i, im in enumerate(cells):
            out_atlas.alpha_composite(im, (cw * i, 0))
        rects = [[cw * i, 0, cw, ch] for i in range(len(cells))]
        anchor = manifest.get("anchor", [cw // 2, ch - 8])
        anchors = [list(anchor) for _ in cells]
        ticks = [int(t) for t in args.ticks.split(",")] if args.ticks else [10] * len(cells)
        cell = cw if cw == ch else [cw, ch]

    ticks = ticks if len(ticks) == len(rects) else [10] * len(rects)
    clip_dir = ROOT / f"assets/fighters/{args.fighter}/animations/{args.clip}"
    clip_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = clip_dir / "atlas.png"
    out_atlas.save(atlas_path)

    clips[args.clip] = {
        "texture": f"res://assets/fighters/{args.fighter}/animations/{args.clip}/atlas.png",
        "cell": cell,
        "anchor": list(manifest.get("anchor", [192 // 2, 192 - 8])),
        "anchor_y": int(manifest.get("anchor", [0, 184])[1]),
        "anchors": anchors,
        "rects": rects,
        "ticks": ticks,
        "loop": bool(args.loop),
        "atlas_sha256": sha256_file(atlas_path),
        "composed_from": args.from_clip or [str(Path(f).name) for f in args.frame],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{args.fighter}/{args.clip}: {len(rects)} frames " + ("from " + args.from_clip if args.from_clip else "composed"))


if __name__ == "__main__":
    main()
