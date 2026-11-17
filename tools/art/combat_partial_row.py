"""Declared partial-body generation inputs; never a finished animation."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson

from PIL import Image


def validate(path, cell, state):
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("kind") != "ufe-partial-row" or spec.get("part") not in {"upper_body", "torso_arms"}:
        raise ValueError("Partial row must declare an upper_body or torso_arms layer")
    if spec.get("state") != state or spec.get("cell") != [cell["width"], cell["height"]]:
        raise ValueError("Partial row state/cell must match the request")
    size, crop = spec.get("identity_cell", []), spec.get("identity_crop", [])
    if len(size) != 2 or len(crop) != 4 or any(type(v) is not int for v in size + crop):
        raise ValueError("Partial row identity size/crop need integer coordinates")
    if min(size) <= 0 or not (0 <= crop[0] < crop[2] <= size[0] and 0 <= crop[1] < crop[3] <= size[1]):
        raise ValueError("Partial row crop must stay inside the accepted idle")
    if not isinstance(spec.get("seam"), str) or not spec["seam"].strip():
        raise ValueError("Partial row must describe its intended anatomical seam")
    scope = spec.get("generation_scope", "upper_body")
    if scope not in {"upper_body", "full_body_context"}:
        raise ValueError("Unknown partial row generation_scope")
    if spec["part"] == "torso_arms" and scope != "upper_body":
        raise ValueError("Atomic torso_arms cannot generate full-body context")
    if scope == "full_body_context":
        keep = spec.get("generated_keep_rect", [])
        if size != [cell["width"], cell["height"]] or len(keep) != 4 or any(type(v) is not int for v in keep):
            raise ValueError("Full-body context needs matching identity/cell size and an explicit integer keep rect")
        if not (0 <= keep[0] < keep[2] <= cell["width"] and 0 <= keep[1] < keep[3] < cell["height"]):
            raise ValueError("Full-body context must explicitly exclude its lower body")
    return spec


def adapt(identity, path, cell, state, prompt, folder):
    spec = validate(path, cell, state)
    with Image.open(identity) as source:
        if list(source.size) != spec["identity_cell"]:
            raise ValueError("Accepted idle size does not match the partial row declaration")
        reference = source.convert("RGBA").crop(spec["identity_crop"])
    folder.mkdir(parents=True, exist_ok=True)
    crop_path = folder / "accepted-upper-body-reference.png"
    reference.save(crop_path)
    # Only change the explicitly declared production unit, not upstream defaults.
    if spec.get("generation_scope") == "full_body_context":
        prompt += ("\n\n预先声明的全身上下文分层：每格仍画完整全身，保证头部、躯干、手臂的原始比例。"
                   "只有头、躯干和双臂会用作动画层；生成的腿脚仅提供比例上下文，不能进入最终人物。"
                   "最终下半身已经确定使用同一精修idle的原像素，不生成新的腿部动作。"
                   "因此腰线位置、宽度、原有衣料或体表色块边界须匹配精修idle，上半身不能放大、缩小或转身。"
                   "第1张是唯一精修idle；第2张是同图上半身裁图，仅用于腰线和原始比例。"
                   "各格保持同样的头部大小与像素格。切口约定：" + spec["seam"] +
                   "。透明背景，真正PNG Alpha。全身上下文不是可发布的完整人物动作。")
    elif spec["part"] == "torso_arms":
        prompt = prompt.replace("full-body", "torso-and-arms component")
        prompt += ("\n\n原子胸臂部件：只生成胸口、双肩、双臂与黑色手掌，禁止画头、角、颈部、髋、腿、脚或完整人物。"
                   "第1张为唯一完整像素母图，只约束杰顿身份和风格；第2张是同一母图的胸臂裁图，只约束原生比例和切口。"
                   "各个部件保持同样的胸宽与肩位，双臂按各阶段实际重画，不能复制旋转。"
                   "胸臂以外完全透明，切口约定：" + spec["seam"] + "。透明背景，真正PNG Alpha。")
    else:
        prompt = prompt.replace("full-body", "upper-body layer")
        prompt += ("\n\n分层制作的强制约定：本行只生成头部、躯干和双臂组成的完整上半身动作层。"
                   "不要画腿、脚、地面或完整人物。第1张图是唯一精修idle身份参考；"
                   "第2张是从同一idle原像素裁出的上半身范围参考，只说明比例与切口，不是另一种设计。"
                   "最后的布局图只说明格数和留白，不得照画。每格都要有真实不同的手臂姿势。"
                   "不得用固定图重复排列冒充动作。头盔、胸纹、身体宽度和像素密度保持参考。"
                   "切口约定：" + spec["seam"] + "。透明背景，真正PNG Alpha；人物之外完全透明。")
    record = {"kind": "ufe-partial-row-inputs", "purpose": "generation_input_not_runtime_animation",
              "spec_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "accepted_idle_sha256": hashlib.sha256(identity.read_bytes()).hexdigest(),
              "crop_sha256": hashlib.sha256(crop_path.read_bytes()).hexdigest(), "declaration": spec}
    (folder / "inputs.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    return prompt, crop_path
