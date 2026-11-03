"""Declared GPT component-row inputs for native rig parts, never an animation."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson
import re

from PIL import Image, ImageDraw


def validate(path, cell, state, frames):
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("kind") != "ufe-rig-parts-row" or spec.get("production_eligible") is not False:
        raise ValueError("Rig parts must explicitly declare a non-production parts row")
    if spec.get("state") != state or spec.get("cell") != [cell["width"], cell["height"]]:
        raise ValueError("Rig parts state/cell must match the request")
    parts = spec.get("parts", [])
    if len(parts) != frames or not parts:
        raise ValueError("Rig parts need one declared component per row slot")
    if spec.get("masked_completion_only") and (len(parts) != 1 or not spec.get("edit_from_cutout")):
        raise ValueError("Focused completion needs exactly one component and a canonical cutout edit")
    ids = [part.get("id", "") for part in parts]
    if len(set(ids)) != len(ids) or not all(re.fullmatch(r"[a-z][a-z0-9_]*", value) for value in ids):
        raise ValueError("Rig parts need unique safe component IDs")
    for part in parts:
        if not isinstance(part.get("description"), str) or not part["description"].strip():
            raise ValueError("Each rig part must describe anatomy and hidden joint surfaces")
        for key in ("pivot", "tip"):
            point = part.get(key, [])
            if len(point) != 2 or any(type(v) is not int for v in point) or not (0 <= point[0] < cell["width"] and 0 <= point[1] < cell["height"]):
                raise ValueError("Rig landmarks must stay inside the request cell")
        if part["pivot"] == part["tip"]:
            raise ValueError("Rig segments need distinct pivot and tip landmarks")
    size, crop = spec.get("identity_cell", []), spec.get("identity_crop", [])
    if len(size) != 2 or len(crop) != 4 or any(type(v) is not int for v in size + crop):
        raise ValueError("Rig identity size/crop need integer coordinates")
    if min(size) <= 0 or not (0 <= crop[0] < crop[2] <= size[0] and 0 <= crop[1] < crop[3] <= size[1]):
        raise ValueError("Rig reference crop must stay inside accepted idle")
    if not re.fullmatch(r"[0-9a-f]{64}", spec.get("identity_sha256", "")):
        raise ValueError("Rig parts must pin the accepted idle hash")
    scale = spec.get("reference_scale", 1)
    if type(scale) is not int or not 1 <= scale <= 8:
        raise ValueError("Rig reference enlargement must be an integer from 1 to 8")
    return spec


def adapt(identity, path, cell, state, frames, prompt, guide, folder):
    spec = validate(path, cell, state, frames)
    if hashlib.sha256(identity.read_bytes()).hexdigest() != spec["identity_sha256"]:
        raise ValueError("Rig identity differs from the declared accepted idle")
    with Image.open(identity) as source:
        if list(source.size) != spec["identity_cell"]:
            raise ValueError("Rig identity size differs from accepted idle")
        reference = source.convert("RGBA").crop(spec["identity_crop"])
    folder.mkdir(parents=True, exist_ok=True)
    crop_path = folder / "accepted-arm-reference.png"
    # Integer NEAREST enlargement of a generation reference, never final art.
    scale = spec.get("reference_scale", 1)
    reference = reference.resize((reference.width * scale, reference.height * scale), Image.Resampling.NEAREST)
    reference.save(crop_path)
    # Geometry guides constrain generation only; they never enter an art output.
    with Image.open(guide) as opened:
        layout = opened.convert("RGBA")
    draw = ImageDraw.Draw(layout)
    for index, part in enumerate(spec["parts"]):
        x = index * cell["width"]
        a, b = part["pivot"], part["tip"]
        draw.line((x+a[0], a[1], x+b[0], b[1]), fill=(25, 150, 225, 255), width=1)
        for point in (a, b):
            px, py = x+point[0], point[1]
            draw.line((px-2, py, px+2, py), fill=(25, 150, 225, 255), width=1)
            draw.line((px, py-2, px, py+2), fill=(25, 150, 225, 255), width=1)
    guide_path = folder / "component-landmarks.png"
    layout.save(guide_path)
    prompt = prompt.replace("full-body frames", "detached anatomical components").replace("full-body pose", "detached anatomical component").replace("full-body", "detached anatomical component")
    prompt = prompt.replace("Generate distinct animation poses that create a readable cycle or action.",
                            "Generate the two declared independent anatomical components.")
    prompt = "\n".join(line for line in prompt.splitlines() if not any(phrase in line for phrase in (
        "This row owns motion only.", "For cyclic locomotion,", "Prefer a subtler animation",
        "Preserve the same silhouette, face, proportions, palette, material, and props across every frame.")))
    prompt = prompt.replace("or creates a separate disconnected component that is not attached to the character",
                            "or splits the declared part into disconnected fragments")
    prompt += ("\n\n独立骨骼部件制作约定：这是一行静态部件，不是两个完整人物，也不是动作的两帧。"
               "第1张是唯一精修idle身份与像素画风锚点；第2张是它的手臂原像素裁剪，"
               "只说明红银色块和粗细，不是新的设计。最后的线段图只说明顺序、关节中心和长度，"
               "不画蓝线、圆圈、编号、网格或任何引导标记。每格仅画声明的一个完整部件。"
               "保持初代C型真实服装，红色是衣料，不要新增机械装甲、黑手套或肘部铰链。"
               "所有切口需有完整圆润的关节遮挡面，不能复制待机中缺失隐藏表面的尖角裁片。"
               "保持同一调色板、相同硬边像素格，不能加入平滑渐变和抗锯齿。")
    for index, part in enumerate(spec["parts"], 1):
        prompt += f"\n从左至右第{index}格：{part['description']}。每格{cell['width']}×{cell['height']}，关节中心{part['pivot']}→{part['tip']}。"
    if spec.get("corrections"):
        prompt += "\n本次制作修正：" + spec["corrections"]
    prompt += "\n透明背景，真正PNG Alpha。主体之外全透明，不要红底、品红底、白底、棋盘格、影子、文字和特效。"
    record = {"kind": "ufe-rig-parts-inputs", "production_eligible": False,
              "purpose": "native_rig_components_not_motion_or_fighter",
              "spec_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "accepted_idle_sha256": hashlib.sha256(identity.read_bytes()).hexdigest(),
              "generation_reference_integer_scale": scale,
              "crop_sha256": hashlib.sha256(crop_path.read_bytes()).hexdigest(), "declaration": spec}
    (folder / "inputs.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    return prompt, crop_path, guide_path
