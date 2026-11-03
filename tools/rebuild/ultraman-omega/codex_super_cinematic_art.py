"""欧米伽三级背景与独立特写：官方单张生成、Forge整图处理；不自动安装。"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import time
import shutil

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "art/fighters/ultraman-omega/stage6/super-cinematic-20261101-v1"
OUT = ROOT / "reports/review/2026-11-01/omega-super-cinematic-v1"
UNKNOWN = "011ff77710ed49c9b441ed80f91733be"
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/rebuild/shared")]
from forge_backend import _kcentroid_downscale, apply_palette, binarize_alpha, build_shared_palette, palette_mode, backend_info


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return dict(path=Path(path).resolve().relative_to(ROOT).as_posix(), sha256=sha(path))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def official():
    import art_pipeline
    config = art_pipeline.local_image_config()
    assert art_pipeline.image_route(config) == "api"
    assert config["base_url"].rstrip("/") == "https://api.openai.com/v1"
    assert Decimal(str(config["official_budget"]["limit_usd"])) == 60
    return art_pipeline, config, Path(config["official_budget"]["ledger_path"])


def prepare():
    _, _, ledger = official()
    entries = read(ledger)["entries"]
    old = next(item for item in entries if item["id"] == UNKNOWN)
    assert Decimal(old["committed_usd"]) == 10
    ART.mkdir(parents=True, exist_ok=False)
    OUT.mkdir(parents=True, exist_ok=True)
    (ART / ".gitattributes").write_text("*.json -text\n*.md -text\n*.txt -text\n", encoding="utf-8")
    references = []
    for name, source in [
        ("identity", ROOT / "art/fighters/ultraman-omega/model/clean-model-source.png"),
        ("pixel-identity", ROOT / "art/fighters/ultraman-omega/model/model-reference-x4.png"),
        ("peer-style", ROOT / "assets/effects/ultraman-blazar/special3_cut_in/atlas.png"),
    ]:
        image = Image.open(source).convert("RGBA")
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        destination = ART / "references" / (name + ".png")
        destination.parent.mkdir(exist_ok=True)
        image.save(destination)
        references.append(dict(name=name, source=ref(source), reference=ref(destination), whole_image=True))
    prompts = {
        "portrait": (
            "透明背景，真正RGBA透明PNG。为2D像素街机格斗游戏画一张欧米伽奥特曼本人独立大招定格特写插画，只有一人一相，固定侧视朝右，头顶至腰部的完整上半身，包括两手。"
            "输入1、2只确定同一个本人的外形、头部、配色与红银皮套花纹，不能画成别的奥特曼。输入3只参照像素画风和上半身特写的构图，不复制布莱泽身份、蓝色头饰、手势或胸部结构。"
            "欧米伽的高红色弯曲头刃必须完整保留、向后上方延伸；单一青蓝眼、本人银色耳侧与下颌、银色胸部纹理和中央青蓝胸灯都准确。身体主要深红配银色，远侧身体适度暗色。"
            "画原创的准备连斩的蓄势特写：近侧红手握拳置胸前偏下、另一臂收至腰侧，挺胸凝神看向右侧，脸和高头刃读得清晰。不得画交掌、十字光线、光束、任何发光拖尾或脱手武器。"
            "两手、双肩、完整高头刃和胸部均须在画内，四周至少8%透明安全边；人物上半身在中央，不接触画边；下腹以自然皮套曲线完整收边，不用直线截断。"
            "用与现装角色相同的清晰像素色块、阶梯轮廓、有限色阶，不要照片纹理、柔焦、平滑矢量、3D、玩具球关节、螺丝、活动轴、拼接缝。人体皮套连续。"
            "没有场景、文字、边框、字母、UI、棋盘、灰底。透明背景。本图是单张定格特写，不能拼小格、不能用待机图简单放大。"
        ),
        "background": (
            "为2D像素街机格斗游戏画一张欧米伽奥特曼三级大招的静止背景画板。只有背景，没有人物、头像、地面、武器、建筑、文字或UI。"
            "画面是深黑藏蓝宇宙与低亮暗红星云，中央向右有数条纤细青蓝色星光丝带，少量红色和青色晶体星屑由深处向两侧展开；亮度克制、主色深暗、对比明确，人物叠上去必须清晰。"
            "不要满屏白闪、白底、高亮蓝色大片、耀眼白色爆心、全屏太阳、同心圆或魔法阵。能量只以细碎像素星纹和短光丝体现，背景主要暗色。"
            "统一项目既有硬朗2D像素街机美术，清楚方形色块与阶梯星纹，细节丰富，非照片、非平滑渐变、非矢量。"
            "输出1024×1024完整不透明方图；本作会保留中央横向1024×576区域作为640×360背景。所有主要纹理在中央这条横幅中完整构图，上下只作连续暗星云余边。"
            "左右上下来到画边都应是连续暗宇宙，不能有边框、镂空、透明洞、棋盘或拼贴格。纯背景一张。"
        ),
    }
    save(ART / "plan.json", dict(
        user_request="大招是不是少了那个背景定格帧？看其他奥特曼大招。",
        authority="root_delegated_by_user", stage=6, fighter="ultraman-omega",
        art_source="api", route="tools/art_pipeline.py(generate_image), https://api.openai.com/v1",
        references=references, old_unknown_entry=old,
        committed_before_usd=str(sum(Decimal(item["committed_usd"]) for item in entries)),
        limit_usd="60", serial=True, no_auto_retry=True,
        portrait_canvas=[256, 256], portrait_center=[148, 158], background_canvas=[640, 360],
        background_crop_source=[0, 224, 1024, 800],
        note="独立整幅像素特写；背景原画裁中心横幅等比缩小。不是动作帧复用，不改招式时长。"
    ))
    for name, prompt in prompts.items():
        folder = ART / "requests" / name / "request-001"
        folder.mkdir(parents=True)
        selected = references if name == "portrait" else []
        save(folder / "brief.json", dict(id="omega_special3_" + name, fighter="ultraman-omega", stage=6,
            asset_kind="effect" if name == "portrait" else "background", kind="cinematic",
            size="1024x1024", quality="high", background="transparent" if name == "portrait" else "opaque",
            prompt=prompt, references=[item["reference"] for item in selected], not_installed=True))
    print("专属背景与特写的两个独立单张合同已准备；未POST。")


def generate(name):
    folder = ART / "requests" / name / "request-001"
    plan = read(ART / "plan.json")
    brief = read(folder / "brief.json")
    client, config, ledger = official()
    entries = read(ledger)["entries"]
    assert next(item for item in entries if item["id"] == UNKNOWN) == plan["old_unknown_entry"]
    assert not any(item["id"] != UNKNOWN and any(token in str(item.get("status", "")).lower()
                   for token in ["unknown", "reserved"]) for item in entries), "先恢复新未决请求"
    assert sum(Decimal(item["committed_usd"]) for item in entries) + Decimal(str(config["official_budget"]["reserve_usd"])) <= 60
    references = []
    for item in brief["references"]:
        path = ROOT / item["path"]
        assert ref(path) == item
        references.append(path)
    save(folder / "before-submit.json", dict(brief=ref(folder / "brief.json"), references=brief["references"],
        started_unix=int(time.time()), no_auto_retry=True, old_unknown=plan["old_unknown_entry"]))
    error = None
    try:
        client.generate_image(SimpleNamespace(model=None, reference=references, out=folder / "candidate.png",
            mask=None, pose_guide=None, dry_run=False), brief, "欧米伽三级独立专属背景/定格特写")
    except Exception as exc:
        error = type(exc).__name__
    metadata = next((path for path in [folder / "candidate.metadata.json", folder / "rejected/candidate.metadata.json"] if path.is_file()), None)
    result = dict(error_type=error, returned=bool(metadata), no_retry=True)
    if metadata:
        result.update(metadata=ref(metadata), official_billing=read(metadata).get("official_billing"))
    save(folder / "submission-result.json", result)
    print(json.dumps(result, ensure_ascii=False))
    if not metadata:
        raise SystemExit(1)


def process(name):
    folder = ART / "requests" / name / "request-001"
    metadata = next(path for path in [folder / "candidate.metadata.json", folder / "rejected/candidate.metadata.json"] if path.is_file())
    source = metadata.with_suffix("").with_suffix(".png")
    image = Image.open(source).convert("RGBA")
    before = np.asarray(image)[..., 3]
    output = ART / "native" / name
    output.mkdir(parents=True, exist_ok=False)
    if name == "portrait":
        review = read(ART / "portrait-source-review-v1.json")
        assert review["source"] == ref(source) and review["allow_binary_alpha"] is True
        assert before.min() == 0 and before.max() >= 128 and np.mean(before == 0) > .12
        # 全相统一缩小并留十像素外边，不裁接或拼任何人物部位。
        scaled = binarize_alpha(_kcentroid_downscale(image, 236, 236))
        frame = Image.new("RGBA", (256, 256))
        frame.paste(scaled, (10, 10))
    else:
        assert image.size == (1024, 1024) and before.min() == 255
        frame = _kcentroid_downscale(image.crop((0, 224, 1024, 800)), 640, 360)
    with palette_mode("rgb"):
        palette = build_shared_palette([frame], 64)
        frame = apply_palette(frame, palette)
    frame = binarize_alpha(frame)
    frame.save(output / "atlas.png")
    alpha = np.asarray(frame)[..., 3]
    save(output / "provenance.json", dict(source=ref(source), metadata=ref(metadata), atlas=ref(output / "atlas.png"),
        whole_frame_processing=True, no_body_parts=True, backend=backend_info(), palette_colors=64,
        native_size=list(frame.size), alpha_values=[int(value) for value in np.unique(alpha)],
        alpha_bbox=frame.getbbox(), source_alpha_values=len(np.unique(before)), source_transparency_accepted=read(metadata)["transparency_accepted"],
        transform="整张1024方图等比缩至236后置256画布中央留十像素透明边" if name == "portrait" else "原1024方图中央1024x576裁片等比缩至640x360",
        native_alpha=bool(before.min() == 0) if name == "portrait" else None,
        generation_route="official project generate_image", visual_review_pending=True))
    for color, tag in [("#202632", "dark"), ("#ded8c7", "light")]:
        page = Image.new("RGB", frame.size, color)
        page.paste(frame, (0, 0), frame)
        page.save(output / (tag + ".jpg"), quality=90, optimize=True)
    print(json.dumps(dict(name=name, native=ref(output / "atlas.png"), dimensions=frame.size), ensure_ascii=False))


def install():
    contract = read(OUT / "original-contract.json")
    move_path = ROOT / "content/fighters/ultraman-omega/moves/special3.json"
    registry_path = ROOT / "content/presentation/supers.json"
    assert sha(move_path) == contract["original_files"]["content/fighters/ultraman-omega/moves/special3.json"]["sha256"]
    sources = []
    for name, asset in [("portrait", "special3_cut_in"), ("background", "special3_background")]:
        source = ART / "native" / name / "atlas.png"
        target = ROOT / "assets/effects/ultraman-omega" / asset / "atlas.png"
        target.parent.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(source, target)
        sources.append(dict(source=ref(source), installed=ref(target)))
    registry = read(registry_path)
    assert "ultraman-omega" not in registry
    registry["ultraman-omega"] = dict(portrait="res://assets/effects/ultraman-omega/special3_cut_in/atlas.png",
        background="res://assets/effects/ultraman-omega/special3_background/atlas.png", background_z_index=0)
    move = read(move_path)
    for tick, frame in enumerate(move["frames"]):
        frame["cinematic_stage"] = "portrait" if tick < 12 else "action" if tick < 36 else "beam" if tick < 52 else "recovery"
        if tick < 12:
            frame["pause_clock"] = True
            frame["freeze_opponent"] = True
    for path, data in [(move_path, move), (registry_path, registry)]:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    save(OUT / "root-install-v1.json", dict(sources=sources, special3=ref(move_path), registry=ref(registry_path),
        only_frame_fields=["cinematic_stage", "pause_clock", "freeze_opponent"],
        actual_freeze_pre_ticks=list(range(1,12)), no_change_to_body_or_combat=True, authority="root_delegated_by_user"))
    print("欧米伽本人背景/特写及三级短定格已接入，原战斗机制保持。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "generate", "process", "install"])
    parser.add_argument("--name", choices=["portrait", "background"])
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "install":
        install()
    else:
        assert args.name
        {"generate": generate, "process": process}[args.command](args.name)
