"""Build masked GPT edit inputs from accepted idle; never runtime animation."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson

from PIL import Image, ImageDraw


def validate(path, cell, count):
    spec = json.loads(path.read_text(encoding="utf-8"))
    width, height = cell["width"], cell["height"]
    if spec.get("kind") != "ufe-anchor-edit" or spec.get("cell") != [width, height]:
        raise ValueError("Anchor edit kind/cell must match this row")
    scale = spec.get("input_scale", 2)
    if type(scale) is not int or not 1 <= scale <= 4:
        raise ValueError("Anchor edit scale must be an integer from 1 to 4")
    if len(spec.get("frames", [])) != count:
        raise ValueError("Anchor edit must match the declared row/take frame count")
    editable = 0
    for frame in spec["frames"]:
        for rect in frame.get("editable_rects", []):
            if len(rect) != 4 or any(type(v) is not int for v in rect):
                raise ValueError("Edit rectangles need four integer coordinates")
            x0, y0, x1, y1 = rect
            if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                raise ValueError("Edit rectangle must stay inside its frame")
            editable += 1
    if not editable:
        raise ValueError("An action edit needs at least one editable region")
    return spec


def build(identity, spec_path, cell, count, folder):
    spec = validate(spec_path, cell, count)
    width, height = cell["width"], cell["height"]
    scale = spec.get("input_scale", 2)
    with Image.open(identity) as source:
        if source.size != (width, height):
            raise ValueError("Accepted idle dimensions disagree with edit cell")
        anchor = source.convert("RGBA")
    canvas = Image.new("RGBA", (width * count, height))
    mask = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(mask)
    for index, frame in enumerate(spec["frames"]):
        canvas.paste(anchor, (index * width, 0))
        for x0, y0, x1, y1 in frame.get("editable_rects", []):
            draw.rectangle((index * width + x0, y0, index * width + x1 - 1, y1 - 1), fill=(0, 0, 0, 0))
    # Integer enlargement of an identity reference, never final sprite output.
    size = (canvas.width * scale, canvas.height * scale)
    folder.mkdir(parents=True, exist_ok=True)
    canvas_path, mask_path = folder / "canvas.png", folder / "mask.png"
    canvas.resize(size, Image.Resampling.NEAREST).save(canvas_path)
    mask.resize(size, Image.Resampling.NEAREST).save(mask_path)
    record = {"purpose": "masked_generation_input_not_animation_or_runtime_art",
              "spec": str(spec_path), "spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
              "accepted_idle_sha256": hashlib.sha256(identity.read_bytes()).hexdigest(),
              "dimensions": list(size), "mask_zero_alpha": "editable", "mask_full_alpha": "preserve",
              "canvas_sha256": hashlib.sha256(canvas_path.read_bytes()).hexdigest(),
              "mask_sha256": hashlib.sha256(mask_path.read_bytes()).hexdigest()}
    (folder / "inputs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return canvas_path, mask_path
