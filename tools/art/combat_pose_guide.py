"""Draw abstract motion constraints on an upstream layout, never character art."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath

from PIL import Image, ImageDraw

COLORS = {"body": "#65778b", "front_arm": "#f0a235", "rear_arm": "#25a6be", "legs": "#65778b"}


def validate(spec_path, cell, count):
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    width, height = cell["width"], cell["height"]
    if spec.get("kind") != "ufe-combat-pose-guide" or spec.get("cell") != [width, height]:
        raise ValueError("Pose guide kind/cell must match this row")
    if len(spec.get("frames", [])) != count:
        raise ValueError("Pose guide must have exactly the declared row/take frame count")
    # Validate the complete guide before touching the input or calling the API.
    for frame in spec["frames"]:
        if not frame.get("paths"):
            raise ValueError("Every pose needs abstract joint paths")
        for line in frame["paths"]:
            if line.get("role") not in COLORS or len(line.get("points", [])) < 2:
                raise ValueError("Unknown pose path role or missing joints")
            for point in line["points"]:
                if len(point) != 2 or any(type(v) is not int for v in point) or not (0 <= point[0] < width and 0 <= point[1] < height):
                    raise ValueError("Pose joint coordinates must stay inside their frame")
    return spec


def overlay(path, spec_path, cell, count):
    spec = validate(spec_path, cell, count)
    width, height = cell["width"], cell["height"]
    with Image.open(path) as source:
        if source.size != (width * count, height):
            raise ValueError("Upstream layout dimensions disagree with pose guide")
        guide = source.convert("RGB")
    draw = ImageDraw.Draw(guide)
    for i, frame in enumerate(spec["frames"]):
        for line in frame["paths"]:
            points = [(x + i * width, y) for x, y in line["points"]]
            color = COLORS[line["role"]]
            draw.line(points, fill=color, width=6, joint="curve")
            for x, y in points:
                draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
    guide.save(path)
