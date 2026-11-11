"""把单帧生成图落进战斗格：全套共用一个源像素比例。

art/STYLE.md：同一动作整帧统一尺度和根点；不得按姿势外框归一身高。
本工具只做确定性后处理，不改造型：

1. 色板取自本人已批准图鉴定稿 `assets/fighters/<id>/catalogue/model-native.png`
   的 32 色，与身份锚同源，动作帧与定稿同色；
2. 用一张**直立参考帧**（通常是待机第 0 帧）的站高定出"源像素→原生像素"
   的唯一比例，全部帧乘同一比例。屈膝、腾空收腿因此保留真实压低/腾空高度，
   不会被拉直；
3. 缩放后二值 Alpha、量化到 32 色、水平按脚底段重心对到 anchor x，
   脚底贴 baseline-1，腾空帧由 `@脚底行` 指定；
4. 逐帧核：头高与参考帧偏差 ≤±8%（身份比例）、直立帧站高 ≤±3%、
   连通块 1、Alpha 二值、色数 ≤32。任一项不过就报红并要求重生成，
   不用硬拉或换色掩盖。

用法：
    .venv/bin/python tools/art/stage_cells.py --fighter ultraman-nice \
        --scale-source art/fighters/ultraman-nice/stage1/idle/frames/raw-00.png \
        --target-standing 150 \
        --frame idle-00=art/fighters/ultraman-nice/stage1/idle/frames/raw-00.png \
        --frame walk-00=art/fighters/ultraman-nice/stage1/walk/frames/raw-00.png \
        --frame jump-00=art/fighters/ultraman-nice/stage1/jump/frames/raw-00.png --air jump-00

`--frame 名字=路径[@脚底行]`：脚底行省略时贴地（baseline-1）；腾空帧给脚底行。
`--air 名字`：该帧不是直立姿势，跳过站高门（头高门仍然生效）。
默认输出 reports/<id>/stage1/<名字>-cell.png，`--out-dir` 可改。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/media/art"))
from catalogue_native import (  # noqa: E402
    apply_palette, build_palette, harden_alpha, trim,
)

CELL = 192
ANCHOR_X = 96
BASELINE = 184
PALETTE_SIZE = 32
HEAD_TOLERANCE = 0.08
STANDING_TOLERANCE = 0.03


def approved_path(fighter: str) -> Path:
    path = ROOT / f"assets/fighters/{fighter}/catalogue/model-native.png"
    if not path.exists():
        raise SystemExit(f"缺少已批准图鉴定稿：{path}")
    return path


def head_height(mask: np.ndarray) -> int:
    """头顶到颈线的行数。

    侧视整帧的行宽曲线：头壳先增到最宽，再收到颈，然后在肩/护架手臂处
    突然变宽。颈线因此取"站高 8%–40% 区间内第一次明显变宽的那一行"
    （相对上一行 ≥1.35 倍且绝对增宽 ≥2% 站高）。不能用整段最窄行：
    格斗护架的手臂常比脖子更窄，会把头高量成半个身子。
    """
    ys = np.nonzero(mask.any(axis=1))[0]
    if not len(ys):
        return 0
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    rows = [int(mask[y].sum()) for y in range(top, bottom + 1)]
    low, high = int(height * 0.08), int(height * 0.40)
    for offset in range(max(1, low), min(high, len(rows) - 1)):
        previous = rows[offset - 1]
        if previous and rows[offset] >= previous * 1.35 \
                and rows[offset] - previous >= height * 0.02:
            return offset
    window = [(i, rows[i]) for i in range(low, max(low + 1, high))]
    return min(window, key=lambda item: item[1])[0] if window else 0


def foot_center(mask: np.ndarray, fraction: float = 0.08) -> float:
    """脚底带重心：取底部 fraction 带内全部像素的横向重心。

    默认 0.08 只覆盖鞋底与小腿下缘，适合待机/屈膝这类重心在两脚之间的帧。
    迈步、前跨、腾空收腿这类后脚留原位、前脚伸远的姿势，鞋底一带几乎只有
    后脚，重心会贴到后脚、把整帧推向右缘（奥王 walk_forward-00 2026-11-10：
    0.08 得 offset 114、右端 253；0.20 得 80、右端 219）。这类角色改用
    `--foot-band 0.20`（覆盖髋以下整条腿部轮廓），并**连同身份锚一起**用
    同一带宽落格，保证全套横向基准一致。
    """
    ys = np.nonzero(mask.any(axis=1))[0]
    bottom = int(ys.max())
    top = max(int(ys.min()), bottom - max(1, int((bottom - int(ys.min()) + 1) * fraction)))
    band = mask[top:bottom + 1]
    total = band.sum()
    if total == 0:
        return mask.shape[1] / 2.0
    return float((band.sum(axis=0) * np.arange(band.shape[1])).sum() / total)


def components(mask: np.ndarray) -> int:
    seen = np.zeros_like(mask, bool)
    count = 0
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x] and not seen[y, x]:
                count += 1
                queue = deque([(y, x)])
                seen[y, x] = True
                while queue:
                    cy, cx = queue.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                                and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
    return count


def solid_source(path: Path) -> Image.Image:
    return trim(harden_alpha(Image.open(path).convert("RGBA")))


def parse_frame(text: str) -> tuple[str, Path, int | None]:
    name, _, rest = text.partition("=")
    if not name or not rest:
        raise SystemExit(f"--frame 需要 名字=路径[@脚底行]：{text}")
    path_text, _, foot = rest.partition("@")
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise SystemExit(f"帧文件不存在：{path}")
    return name, path, (int(foot) if foot else None)


def build(source: Path, out: Path, palette: list, scale: float, foot_row: int,
          anchor_x: int = ANCHOR_X, cell: int = CELL,
          foot_band: float = 0.08) -> dict:
    solid = solid_source(source)
    size = (max(1, round(solid.width * scale)), max(1, round(solid.height * scale)))
    scaled = harden_alpha(solid.resize(size, Image.BOX))
    scaled = apply_palette(scaled, palette)
    mask = np.array(scaled)[:, :, 3] > 0
    center = foot_center(mask, foot_band)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, (round(anchor_x - center), foot_row + 1 - scaled.height))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)

    array = np.array(canvas)
    visible = array[:, :, 3] > 0
    ys, xs = np.where(visible)
    height = int(ys.max() - ys.min() + 1)
    head = head_height(visible)
    return {
        "frame": out.stem,
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output": out.relative_to(ROOT).as_posix(),
        "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "scale": round(scale, 6),
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "height": height,
        "width": int(xs.max() - xs.min() + 1),
        "head_height": head,
        "head_ratio": round(head / height, 4) if height else 0.0,
        "colors": int(len(np.unique(array[:, :, :3][visible].reshape(-1, 3), axis=0))),
        "components": components(visible),
        "foot_row": int(ys.max()),
        "alpha": sorted({int(v) for v in np.unique(array[:, :, 3])}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="单帧落格：全套共用一个源像素比例")
    parser.add_argument("--fighter", required=True)
    parser.add_argument("--scale-source", required=True, help="直立参考帧（定比例用）")
    parser.add_argument("--target-standing", type=int, required=True,
                        help="参考帧在屏站高（与已装战斗帧同档）")
    parser.add_argument("--frame", action="append", required=True,
                        help="名字=路径[@脚底行]，可重复")
    parser.add_argument("--air", action="append", default=[],
                        help="非直立帧名字，跳过站高门")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--anchor-x", type=int, default=ANCHOR_X)
    parser.add_argument("--baseline", type=int, default=BASELINE)
    parser.add_argument("--cell", type=int, default=CELL,
                        help="制作格边长；默认 192，原生体量容不下时按角色统一增大")
    parser.add_argument("--foot-band", type=float, default=0.08,
                        help="横向对位用的底部带宽（占站高比例）；迈步/前跨角色连同锚一起用 0.20")
    parser.add_argument("--scale", type=float, default=0.0,
                        help="显式源→原生比例；默认按参考帧站高与目标站高换算")
    args = parser.parse_args(argv)

    reference_path = Path(args.scale_source)
    if not reference_path.is_absolute():
        reference_path = ROOT / reference_path
    reference = solid_source(reference_path)
    reference_mask = np.array(reference)[:, :, 3] > 0
    reference_head = head_height(reference_mask)
    if not reference_head:
        raise SystemExit(f"参考帧头部无法测量：{reference_path}")
    scale = args.scale or (args.target_standing / reference.height)

    approved = solid_source(approved_path(args.fighter))
    palette = build_palette(approved, PALETTE_SIZE)

    out_dir = Path(args.out_dir) if args.out_dir else Path(f"reports/{args.fighter}/stage1")
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    air = set(args.air)
    reports, flags, notes = [], [], []
    target_head = max(1, round(reference_head * scale))
    for text in args.frame:
        name, path, foot = parse_frame(text)
        row = build(path, out_dir / f"{name}-cell.png", palette, scale,
                    foot if foot is not None else args.baseline - 1,
                    anchor_x=args.anchor_x, cell=args.cell,
                    foot_band=args.foot_band)
        row["standing"] = name not in air
        reports.append(row)

        # 硬门：只放机器能确定的项，失败即拒收。
        if row["components"] != 1:
            flags.append(f"{name}: 连通块 {row['components']}（应 1）")
        if row["alpha"] != [0, 255]:
            flags.append(f"{name}: Alpha 不是二值 {row['alpha']}")
        if row["colors"] > PALETTE_SIZE:
            flags.append(f"{name}: 色数 {row['colors']} 超过 {PALETTE_SIZE}")

        # 比例项：前倾、腾空、护架摆臂都会让自动头高失真，只报数值，
        # 由人工看联系表判定，不冒充自动通过。
        if name in air:
            notes.append(f"{name}: 非直立帧，头高 {row['head_height']}、站高 "
                         f"{row['height']} 仅供参考，需目视核对比例")
            continue
        if not row["head_height"]:
            notes.append(f"{name}: 头部自动测量失败，须目视核对")
        elif abs(row["head_height"] - target_head) > target_head * HEAD_TOLERANCE:
            notes.append(f"{name}: 头高 {row['head_height']} 偏离参考帧换算的 {target_head} "
                         f"超过 ±8%，须目视核对")
        drift = abs(row["height"] - args.target_standing) / args.target_standing
        if drift > STANDING_TOLERANCE:
            notes.append(f"{name}: 站高 {row['height']} 偏离目标 {args.target_standing} "
                         f"达 {drift:.0%}，若为屈膝压低可保留，否则须目视核对")

    report = {
        "fighter": args.fighter,
        "approved": approved_path(args.fighter).relative_to(ROOT).as_posix(),
        "approved_sha256": hashlib.sha256(approved_path(args.fighter).read_bytes()).hexdigest(),
        "scale": round(scale, 6),
        "scale_source": reference_path.relative_to(ROOT).as_posix(),
        "scale_source_head": reference_head,
        "target_standing": args.target_standing,
        "target_head": target_head,
        "cell": args.cell,
        "anchor": [args.anchor_x, args.baseline],
        "head_tolerance": HEAD_TOLERANCE,
        "standing_tolerance": STANDING_TOLERANCE,
        "frames": reports,
        "flags": flags,
        "notes": notes,
    }
    current_report = report
    # 同一目录可能先后落多批帧：只合并本批 frame，不丢已有身份锚/签收/批次记录。
    # 旧版直接覆盖会让后续批次抹掉 identity_anchor 与既有帧 SHA。
    existing_path = out_dir / "cells.json"
    if existing_path.is_file():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        if isinstance(existing, dict):
            merged = dict(existing)
            merged.update({k: v for k, v in report.items() if k != "frames"})
            # 既有记录有的批次用 frame、有的用 name 作键；只认 frame 会把
            # 全部 name 行压成同一个 "None" 并吞掉历史。两种键都保留。
            def row_key(row: dict) -> str:
                return str(row.get("frame") or row.get("name") or "")

            by_name = {row_key(row): row for row in existing.get("frames", [])
                       if isinstance(row, dict)}
            for row in report["frames"]:
                by_name[row_key(row)] = row
            merged["frames"] = list(by_name.values())
            report = merged
    (out_dir / "cells.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if not flags else 1


if __name__ == "__main__":
    raise SystemExit(main())
