"""强壮日冕赛罗身份锚落格：像素待机整帧 -> 256 战斗格。

站高口径与基础赛罗一致：冠顶→鞋底 188、脚底 247、根点 [128,248]。
色板从本形态待机像素整帧整图重定，强制保住金冠/黄眼/绿额灯/蓝芯计时器/
红拳套等识别色；全套动作共用该板。不做局部重涂。

用法：.venv/bin/python tools/rebuild/ultraman-zero__strong_corona/make_anchor.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/art"))
sys.path.insert(0, str(ROOT / "tools/media/art"))
import stage_cells  # noqa: E402
from catalogue_native import build_palette, harden_alpha, trim  # noqa: E402

FIGHTER = "ultraman-zero__strong_corona"
SOURCE = ROOT / f"art/fighters/{FIGHTER}/stage1/idle/frames/pixel-raw-03.png"
CELL_DIR = ROOT / f"art/fighters/{FIGHTER}/stage1/cells"
FRAME_DIR = ROOT / f"art/fighters/{FIGHTER}/stage1/idle/frames"
MODEL_DIR = ROOT / f"art/fighters/{FIGHTER}/model"
CELL = 256
ANCHOR = [128, 248]
FOOT_ROW = 247
TARGET_STANDING = 188

# 识别色：只用于检查色板是否保住，不按区域重涂；整图最近色映射。
IDENTITY_COLORS = [
    ("gold_crest", (244, 182, 28)),
    ("gold_highlight", (253, 236, 152)),
    ("eye_yellow", (253, 232, 19)),
    ("forehead_green", (2, 192, 27)),
    ("timer_blue", (0, 73, 216)),
    ("fist_red", (243, 64, 71)),
    ("suit_red", (168, 14, 23)),
    ("suit_red_deep", (132, 10, 18)),
    ("silver_light", (221, 218, 230)),
    ("silver_mid", (156, 152, 168)),
    ("armor_blue", (88, 175, 240)),
    ("outline", (0, 0, 0)),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest_distance(color, palette):
    arr = np.array(palette, dtype=np.int32)
    d = ((arr - np.array(color, dtype=np.int32)) ** 2).sum(axis=1)
    return int(np.sqrt(d.min()))


def palette_with_identity(scaled: Image.Image) -> tuple[list, list]:
    array = np.array(scaled)
    visible = array[:, :, 3] > 0
    pixels = array[:, :, :3][visible].reshape(-1, 3)
    counts = Counter(map(tuple, pixels.tolist()))
    base = build_palette(scaled, stage_cells.PALETTE_SIZE)
    palette = [tuple(int(v) for v in c) for c in base]
    forced = []
    for name, color in IDENTITY_COLORS:
        if nearest_distance(color, palette) <= 18:
            continue
        # 替换当前出现频次最低的板色；不替换前面刚补入的识别色。
        candidates = [c for c in palette if c not in forced]
        victim = min(candidates, key=lambda c: counts.get(tuple(c), 0))
        palette[palette.index(victim)] = color
        forced.append(color)
    # 去重并保序
    seen, unique = set(), []
    for c in palette:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique, forced


def foot_span(mask: np.ndarray, fraction: float = 0.08) -> tuple[int, int, int]:
    ys = np.nonzero(mask.any(axis=1))[0]
    bottom = int(ys.max())
    top = max(int(ys.min()), bottom - max(1, int((bottom - int(ys.min()) + 1) * fraction)))
    band = mask[top:bottom + 1]
    by, bx = np.nonzero(band)
    return int(bx.min()), int(bx.max()), int(bx.max() - bx.min() + 1)


def main() -> int:
    CELL_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    solid = trim(harden_alpha(Image.open(SOURCE).convert("RGBA")))
    scale = TARGET_STANDING / solid.height
    size = (max(1, round(solid.width * scale)), max(1, round(solid.height * scale)))
    scaled = harden_alpha(solid.resize(size, Image.BOX))
    palette, forced = palette_with_identity(scaled)

    out_cell = CELL_DIR / "idle-00-cell.png"
    report = stage_cells.build(
        SOURCE, out_cell, palette, scale, FOOT_ROW,
        anchor_x=ANCHOR[0], cell=CELL, foot_band=0.08,
    )

    cell_img = Image.open(out_cell).convert("RGBA")
    mask = np.array(cell_img)[:, :, 3] > 0
    x0, x1, span = foot_span(mask, 0.08)
    x0_20, x1_20, span20 = foot_span(mask, 0.20)
    ys = np.nonzero(mask.any(axis=1))[0]
    height = int(ys.max() - ys.min() + 1)
    mid = (x0 + x1) // 2
    left_rows = np.nonzero(mask[:, :mid].any(axis=1))[0]
    right_rows = np.nonzero(mask[:, mid:].any(axis=1))[0]
    sole_left = int(left_rows.max()) if len(left_rows) else -1
    sole_right = int(right_rows.max()) if len(right_rows) else -1

    x4 = cell_img.resize((CELL * 4, CELL * 4), Image.NEAREST)
    x4_cell = CELL_DIR / "idle-00-cell-x4.png"
    x4.save(x4_cell)
    shutil.copyfile(out_cell, FRAME_DIR / "identity-idle-pixel.png")
    shutil.copyfile(x4_cell, FRAME_DIR / "identity-idle-pixel-x4.png")
    shutil.copyfile(x4_cell, MODEL_DIR / "identity-anchor-x4.png")

    record = {
        "fighter": FIGHTER,
        "display_name": "强壮日冕赛罗",
        "cell": CELL,
        "anchor": ANCHOR,
        "baseline": FOOT_ROW + 1,
        "target_standing": TARGET_STANDING,
        "scale": round(scale, 6),
        "scale_source": SOURCE.relative_to(ROOT).as_posix(),
        "scale_source_sha256": sha256(SOURCE),
        "scale_source_size": list(solid.size),
        "source_photo": f"art/fighters/{FIGHTER}/stage1/idle/frames/stance-raw-01.png",
        "source_photo_sha256": sha256(ROOT / f"art/fighters/{FIGHTER}/stage1/idle/frames/stance-raw-01.png"),
        "clean_photo": f"art/fighters/{FIGHTER}/stage1/idle/frames/stance-clean-01.png",
        "clean_photo_sha256": sha256(ROOT / f"art/fighters/{FIGHTER}/stage1/idle/frames/stance-clean-01.png"),
        "diagnostic": f"art/fighters/{FIGHTER}/stage1/diagnostic/stance-reroll-2026-11-12.png",
        "palette": [list(c) for c in palette],
        "palette_size": len(palette),
        "palette_source": "本形态待机像素整帧整图重定；强制识别色见 forced_identity_colors",
        "forced_identity_colors": [{"name": n, "rgb": list(c)} for n, c in IDENTITY_COLORS
                                   if list(c) in [list(f) for f in forced]],
        "frames": [{
            **report,
            "standing": True,
            "foot_span_08": span,
            "foot_span_over_height_08": round(span / height, 4),
            "foot_span_20": span20,
            "foot_span_over_height_20": round(span20 / height, 4),
            "sole_row_left": sole_left,
            "sole_row_right": sole_right,
            "sole_difference": abs(sole_left - sole_right),
        }],
        "flags": report.get("flags", []),
        "notes": report.get("notes", []),
        "stance_review": {
            "facing": "right",
            "class": "前弓步格斗护架",
            "front_knee": "明显弯曲",
            "rear_knee": "弯曲较浅、近直",
            "foot_span_08": span,
            "foot_span_over_height_08": round(span / height, 4),
            "soles": [sole_left, sole_right],
            "sole_difference": abs(sole_left - sole_right),
            "caveat": "后膝弯曲浅，属前弓步；数值门 0.65–0.80 与双脚接地通过，但若按基础赛罗双膝深屈标准需重定站姿。",
            "authority": "root_delegated_by_user",
            "user_confirmed": False,
        },
        "known_issues": [
            "后膝弯曲浅，待用户确认是否接受前弓步待机；不接受则整锚与下游动作撤销重定。",
            "源为第三方拍摄的官方 S.H.Figuarts 测评照，玩具球关节/接缝已在生图阶段要求去除；像素锚仍以本形态官方正面图复核配色。",
        ],
        "identity_anchor": {
            "frame": out_cell.relative_to(ROOT).as_posix(),
            "sha256": sha256(out_cell),
            "x4": x4_cell.relative_to(ROOT).as_posix(),
            "x4_sha256": sha256(x4_cell),
            "standing_height": height,
            "root": ANCHOR,
            "ground_foot_row": FOOT_ROW,
            "form": "strong_corona",
            "usage": "此后全部动作帧只引此待机像素整帧；不引基础赛罗或其它形态人物帧",
        },
        "authority": "root_delegated_by_user",
        "user_approved": False,
        "review": {
            "kind": "root_delegated_by_user",
            "note": "自动评审签署；造型、头肩、手脚体量已看原生格与严格4×，但不冒称用户亲审。后膝弯曲浅已登记为 known_issue。",
        },
    }
    (CELL_DIR / "cells.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (MODEL_DIR / "identity-anchor.json").write_text(
        json.dumps(record["identity_anchor"] | {
            "palette": [list(c) for c in palette],
            "cell": CELL,
            "anchor": ANCHOR,
            "target_standing": TARGET_STANDING,
            "scale": round(scale, 6),
            "authority": "root_delegated_by_user",
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({
        "cell": record["identity_anchor"],
        "palette_size": len(palette),
        "forced": record["forced_identity_colors"],
        "frame": record["frames"][0],
        "flags": record["flags"],
        "notes": record["notes"],
    }, ensure_ascii=False, indent=1))
    return 0 if not report.get("flags") else 1


if __name__ == "__main__":
    raise SystemExit(main())
