"""角色专属特效家族自绘：PixelFX 离线烘焙原创像素形状，并重新注册到 phase3。

与旧的“借用段重着色”不同：本工具不读取任何他人特效图集作为形状来源，只从
当前 phase3 条目取画布、锚点、rects 与逐帧有效范围（保证落点/时长/判定不变），
形状由 tools/rebuild/shared/fx_family_bake.mjs 的绘制函数原创生成。

流程：
  1. 读 phase3 条目，测现有图集逐帧 Alpha 外框，作为新形状的占位范围
  2. node fx_family_bake.mjs 烘焙到 reports/fx_redraw/<角色>/（审片用，不进库）
  3. 复制 atlas.png 到 assets/effects/<角色>/<段>/，更新条目账本字段
  4. 写 provenance.json / effect.json，生成联系表

不碰 rects、ticks、anchor、frame_boxes、frame_hitboxes、display_scale 与招式数值。

用法：
  python tools/rebuild/<角色>/phase3_family_redraw.py             # 烘焙并安装
  python tools/rebuild/<角色>/phase3_family_redraw.py --dry-run   # 只烘焙到 reports
"""
from __future__ import annotations

import sys as _layout_sys
from pathlib import Path as _LayoutNativePath

_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath  # noqa: E402

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

Path = _LayoutProjectPath

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "project.godot").is_file())
PHASE3 = ROOT / "content/presentation/phase3_projectiles.json"
BAKE = ROOT / "tools/rebuild/shared/fx_family_bake.mjs"
UPSTREAM = json.loads((ROOT / "third_party/pixelfx/UPSTREAM.json").read_text(encoding="utf-8"))
LICENSE = ROOT / "third_party/pixelfx/LICENSE"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: Path, data, newline: bool) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    Path(path).write_text(text + ("\n" if newline else ""), encoding="utf-8", newline="\n")


def measure_art_boxes(atlas: Path, entry: dict) -> list[list[int]]:
    """逐帧 Alpha 外框（相对 anchor），只用于给新形状定占位范围。"""
    import numpy as np
    from PIL import Image

    arr = np.array(Image.open(atlas).convert("RGBA"))
    ax, ay = entry["anchor"]
    boxes = []
    for x, y, w, h in entry["rects"]:
        alpha = arr[y:y + h, x:x + w, 3]
        ys, xs = np.nonzero(alpha)
        if len(xs) == 0:
            raise SystemExit(f"源图集帧为空: {atlas} rect={[x, y, w, h]}")
        boxes.append([int(xs.min()) - ax, int(ys.min()) - ay,
                      int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)])
    return boxes


def envelope_boxes(entry: dict, atlas: Path) -> list[list[int]]:
    """形状占位范围：已自绘的条目复用 provenance 里首次记录的占位框，保证重跑像素不变。"""
    prov_rel = entry.get("provenance", "")
    if entry.get("art_source") == "pixelfx_code_baked" and prov_rel.startswith("res://"):
        prov = ROOT / prov_rel.replace("res://", "")
        if prov.is_file():
            data = load_json(prov)
            boxes = data.get("art_boxes")
            if isinstance(boxes, list) and len(boxes) == len(entry["rects"]):
                return boxes
    return measure_art_boxes(atlas, entry)


def color_count(atlas: Path) -> int:
    import numpy as np
    from PIL import Image

    arr = np.array(Image.open(atlas).convert("RGBA"))
    visible = arr[arr[..., 3] > 0][:, :3]
    return int(len({tuple(int(v) for v in c) for c in visible}))


def run_bake(spec: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["node", str(BAKE), "--out", str(out_dir.relative_to(ROOT))],
        input=json.dumps(spec, ensure_ascii=False), text=True,
        capture_output=True, cwd=ROOT,
    )
    if proc.returncode != 0:
        raise SystemExit(f"烘焙失败：\n{proc.stdout}\n{proc.stderr}")
    if proc.stdout.strip():
        print(proc.stdout.rstrip())
    return load_json(out_dir / "bake.json")


def review_sheet(character: str, out_root: Path, families: list[dict], sheet: Path) -> None:
    """逐家族四帧联系表，棋盘底，便于目视核形状与相位。"""
    from PIL import Image, ImageDraw, ImageFont

    pad, label_w, max_w = 6, 210, 1600
    rows = []
    for fam in families:
        frames = [Image.open(out_root / fam["out"] / f"frame-{i}.png").convert("RGBA") for i in range(4)]
        w, h = frames[0].size
        scale = min(2.0, max(0.25, (max_w - label_w - pad * 5) / (4 * w)))
        sw, sh = max(1, int(w * scale)), max(1, int(h * scale))
        scaled = [f.resize((sw, sh), Image.NEAREST) for f in frames]
        row = Image.new("RGB", (label_w + 4 * (sw + pad) + pad, sh + pad * 2), (28, 28, 34))
        draw = ImageDraw.Draw(row)
        for yy in range(0, row.height, 8):
            for xx in range(0, label_w + 4 * (sw + pad) + pad, 8):
                if (xx // 8 + yy // 8) % 2 == 0:
                    draw.rectangle([xx, yy, xx + 7, yy + 7], fill=(38, 38, 46))
        try:
            font = ImageFont.load_default(size=13)
        except TypeError:
            font = ImageFont.load_default()
        draw.text((pad, pad), fam["name"], fill=(235, 235, 240), font=font)
        draw.text((pad, pad + 17), f"{fam['kind']} seed {fam['seed']}", fill=(150, 200, 235), font=font)
        for i, img in enumerate(scaled):
            x = label_w + i * (sw + pad)
            row.paste(img, (x, pad), img)
        rows.append(row)
    sheet.parent.mkdir(parents=True, exist_ok=True)
    total_h = sum(r.height for r in rows)
    board = Image.new("RGB", (max(r.width for r in rows), total_h), (20, 20, 24))
    y = 0
    for r in rows:
        board.paste(r, (0, y))
        y += r.height
    board.save(sheet)
    print(f"  联系表: {sheet}")


def redraw(character: str, families: list[dict], *, dry_run: bool = False) -> None:
    """families 每项：name / out / kind / palette。seed 由家族名固定派生。"""
    raw = PHASE3.read_text(encoding="utf-8")
    projectiles = json.loads(raw)
    assert json.dumps(projectiles, ensure_ascii=False, indent=2) + "\n" == raw, "phase3 往返格式不一致"

    spec_families = []
    entries = {}
    for fam in families:
        name = fam["name"]
        if name not in projectiles:
            raise SystemExit(f"phase3 缺少条目: {name}")
        entry = projectiles[name]
        atlas = ROOT / entry["texture"].replace("res://", "")
        if not atlas.is_file():
            raise SystemExit(f"图集缺失: {atlas}")
        rects = entry["rects"]
        w, h = rects[0][2], rects[0][3]
        if any(r[2] != w or r[3] != h for r in rects):
            raise SystemExit(f"{name} 帧尺寸不一致，需先人工处理")
        seed = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16) % 1000003
        spec_families.append({
            "name": name, "out": fam["out"], "kind": fam["kind"], "palette": fam["palette"],
            "seed": seed, "width": w, "height": h, "anchor": entry["anchor"], "rects": rects,
            "oneshot": not bool(entry.get("loop", True)), "fan": bool(entry.get("native_fan", False)),
            "frames": [{"art": box} for box in envelope_boxes(entry, atlas)],
        })
        entries[name] = (entry, atlas)

    staging = ROOT / "reports/fx_redraw" / character
    report = run_bake({"character": character, "families": spec_families}, staging)
    baked = {f["name"]: f for f in report["families"]}

    review_sheet(character, staging, [dict(name=f["name"], out=f["out"], kind=f["kind"], seed=f["seed"]) for f in spec_families],
                 staging / "sheet.png")

    # 形状差异记录：新图与旧（借用形状）Alpha 掩码 IoU，只为报告，不作门限。
    import numpy as np
    from PIL import Image

    for spec in spec_families:
        entry, old_atlas = entries[spec["name"]]
        new_atlas = staging / spec["out"] / "atlas.png"
        old_arr = np.array(Image.open(old_atlas).convert("RGBA"))
        new_arr = np.array(Image.open(new_atlas).convert("RGBA"))
        ious = []
        for (x, y, w, h) in entry["rects"]:
            a = old_arr[y:y + h, x:x + w, 3] > 0
            b = new_arr[y:y + h, x:x + w, 3] > 0
            union = np.logical_or(a, b).sum()
            ious.append(float(np.logical_and(a, b).sum() / union) if union else 0.0)
        print(f"  形状差异 {spec['name']}: 旧轮廓 IoU 均值 {sum(ious) / len(ious):.3f}")

    if dry_run:
        print(f"dry-run：{len(spec_families)} 段已烘焙到 {staging}，未写 assets/content")
        return

    license_dest = ROOT / f"assets/effects/{character}/PIXELFX-LICENSE.txt"
    if not license_dest.is_file():
        shutil.copyfile(LICENSE, license_dest)

    changed = 0
    for spec in spec_families:
        name = spec["name"]
        entry, _old = entries[name]
        baked_item = baked[name]
        dest_dir = ROOT / f"assets/effects/{character}/{spec['out']}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_atlas = dest_dir / "atlas.png"
        shutil.copyfile(staging / spec["out"] / "atlas.png", dest_atlas)
        new_sha = sha(dest_atlas)

        entry["texture"] = f"res://assets/effects/{character}/{spec['out']}/atlas.png"
        entry["atlas_sha256"] = new_sha
        entry["colors"] = color_count(dest_atlas)
        entry["art_source"] = "pixelfx_code_baked"
        entry["source_kind"] = "pixelfx_code_baked"
        entry["license"] = "MIT"
        entry["upstream_commit"] = UPSTREAM["commit"]
        entry["authoring_source"] = f"res://tools/rebuild/{character}/phase3_family_redraw.py"
        entry["provenance"] = f"res://assets/effects/{character}/{spec['out']}/provenance.json"
        entry["alpha_binary"] = True
        entry["dedicated_to"] = character
        for stale in ("id", "fighter_id", "action_id", "emission_core_points"):
            entry.pop(stale, None)
        for key in ("user_approved", "art_approved"):
            if key in entry:
                entry[key] = False
        entry["review_status"] = "2026-11-11 自绘原创像素特效（PixelFX 离线烘焙），待指挥目视终审"

        provenance = {
            "request": f"{character} 专属特效家族自绘：不沿用借用图集形状，按招式光色原创像素形状",
            "character": character,
            "family": name,
            "kind": spec["kind"],
            "shape_source": "原创绘制函数 tools/rebuild/shared/fx_family_bake.mjs",
            "reused_source_atlas_shape": False,
            "source_kind": "pixelfx_code_baked",
            "route": "offline",
            "upstream": UPSTREAM["repo"],
            "upstream_commit": UPSTREAM["commit"],
            "license": "MIT",
            "license_sha256": sha(LICENSE),
            "authoring_source": f"res://tools/rebuild/{character}/phase3_family_redraw.py",
            "bake_module": "res://tools/rebuild/shared/fx_family_bake.mjs",
            "seed": spec["seed"],
            "palette": spec["palette"],
            "canvas": baked_item["canvas"],
            "frame_size": baked_item["frame_size"],
            "anchor": baked_item["anchor"],
            "rects": baked_item["rects"],
            "art_boxes": [f["art"] for f in spec["frames"]],
            "ticks": entry.get("ticks"),
            "frame_sha256": baked_item["frame_sha256"],
            "atlas_sha256": new_sha,
            "frame_boxes_kept": True,
            "character_frames_modified": False,
            "review_status": entry["review_status"],
        }
        save_json(dest_dir / "provenance.json", provenance, newline=True)
        save_json(dest_dir / "effect.json", entry, newline=True)
        changed += 1

    save_json(PHASE3, projectiles, newline=True)
    print(f"  安装 {changed} 段；图集已写入 assets/effects/{character}/")


def main(character: str, families: list[dict]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    redraw(character, families, dry_run=args.dry_run)
