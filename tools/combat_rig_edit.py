"""Masked generation inputs copied from canonical cutouts, never finished parts."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = _LayoutProjectPath(_layout_root)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(identity, declaration, folder):
    edit = declaration["edit_from_cutout"]
    manifest_path = (ROOT / edit["manifest"]).resolve()
    if not manifest_path.is_relative_to(ROOT / "art/rigs") or digest(manifest_path) != edit["sha256"]:
        raise ValueError("Rig edit requires the exact declared native study manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = (ROOT / manifest["source"]).resolve()
    if digest(source_path) != manifest["source_sha256"]:
        raise ValueError("Rig edit canonical source changed")
    with Image.open(source_path) as canonical, Image.open(identity) as anchor:
        if canonical.size != anchor.size or canonical.convert("RGBA").tobytes() != anchor.convert("RGBA").tobytes():
            raise ValueError("Rig edit source is not pixel-identical to accepted idle")
    scale = edit.get("input_scale", 8)
    if type(scale) is not int or not 1 <= scale <= 8:
        raise ValueError("Rig edit reference scale must be an integer from 1 to 8")
    width, height = declaration["cell"]
    canvas = Image.new("RGBA", (width * len(declaration["parts"]), height))
    mask = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
    records = []
    for index, part in enumerate(declaration["parts"]):
        source = next(p for p in manifest["parts"] if p["id"] == part["id"])
        pivot = next(b["pivot"] for b in manifest["bones"] if b["id"] == source["bone"])
        # Preserve direction, length and every seed pixel: translation only.
        if [part["tip"][i] - part["pivot"][i] for i in range(2)] != [part["source_tip"][i] - pivot[i] for i in range(2)]:
            raise ValueError("Rig edit seed cannot be rotated, stretched or resized")
        path = (manifest_path.parent / source["image"]).resolve()
        if not path.is_relative_to(manifest_path.parent) or digest(path) != source["sha256"]:
            raise ValueError("Rig edit cutout source changed")
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
        dx, dy = [part["pivot"][i] - pivot[i] + source["origin"][i] for i in range(2)]
        if min(dx, dy) < 0 or dx + image.width > width or dy + image.height > height:
            raise ValueError("Rig edit seed exceeds the declared cell")
        cell = Image.new("RGBA", (width, height))
        cell.paste(image, (dx, dy))
        canvas.paste(cell, (index * width, 0))
        alpha = cell.getchannel("A")
        editable = alpha.filter(ImageFilter.MaxFilter(13)).point(lambda a: 255 if a else 0)
        draw = ImageDraw.Draw(editable)
        for point in (part["pivot"], part["tip"]):
            x, y = point
            draw.ellipse((x-12, y-12, x+12, y+12), fill=255)
        protected_core = alpha.point(lambda a: 255 if a >= 128 else 0).filter(ImageFilter.MinFilter(5))
        draw = ImageDraw.Draw(protected_core)
        for point in (part["pivot"], part["tip"]):
            x, y = point
            draw.ellipse((x-12, y-12, x+12, y+12), fill=0)
        editable = ImageChops.subtract(editable, protected_core)
        local_mask = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        local_mask.putalpha(editable.point(lambda a: 255-a))
        mask.paste(local_mask, (index * width, 0))
        records.append({"id": part["id"], "source": str(path.relative_to(ROOT)), "source_sha256": digest(path),
                        "translation": [dx, dy], "pivot": part["pivot"], "tip": part["tip"],
                        "editable_pixels": editable.histogram()[255],
                        "protected_core_pixels": protected_core.histogram()[255]})
    folder.mkdir(parents=True, exist_ok=True)
    canvas_path, mask_path = folder / "canvas.png", folder / "mask.png"
    size = (canvas.width * scale, canvas.height * scale)
    canvas.resize(size, Image.Resampling.NEAREST).save(canvas_path)
    mask.resize(size, Image.Resampling.NEAREST).save(mask_path)
    record = {"purpose": "masked_generation_reference_not_art_or_motion", "production_eligible": False,
              "manifest": str(manifest_path.relative_to(ROOT)), "manifest_sha256": digest(manifest_path),
              "seed_geometry": "translation only; no rotation, stretch, painting or final-asset resizing",
              "integer_reference_enlargement": scale, "parts": records,
              "dimensions": list(size), "canvas_sha256": digest(canvas_path), "mask_sha256": digest(mask_path),
              "mask_zero_alpha": "editable", "mask_full_alpha": "preserve",
              "preservation_guaranteed_by_api": False}
    (folder / "inputs.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return canvas_path, mask_path
