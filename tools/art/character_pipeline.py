"""单角色「图 + 视频（I2V）双模」统一制作管线 CLI。

子命令：
- anchor        登记/对比 magpie-image 与内置 image-generator 双通道待机锚候选，择优定标
- extract-video 调用 art.video_frames 将 I2V 短片抽帧、去背、像素化到本人 ≤32 色板
- stage         调用 art.stage_cells 统一比例落格，并可选调用 art.compose_clip 拼合 clip
- derive        调用 art.derive_fighter_data 按实测 Alpha 轮廓派生招式受击框与 state_frames
- install       调用 art.install_cells 安装到 assets/fighters/<id>/animations
- check         串联 check.sprite_quality 像素硬门与 art.parity_matrix 完整度检查
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from art import stage_cells, video_frames  # noqa: E402
from check import sprite_quality  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _measure_anchor_candidate(
    label: str, path: Path, target_standing: int = 0
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"候选锚图不存在：{path}")
    with Image.open(path) as opened:
        raw_rgba = opened.convert("RGBA")
    arr = np.array(raw_rgba, dtype=np.uint8)
    raw_info = sprite_quality.analyze_frame(arr)
    visible = arr[:, :, 3] > 0
    colors_raw = int(len(np.unique(arr[:, :, :3][visible].reshape(-1, 3), axis=0))) if visible.any() else 0

    hard = stage_cells.harden_alpha(raw_rgba)
    trimmed = stage_cells.trim(hard)
    norm_h = target_standing if target_standing > 0 else trimmed.height
    scale = norm_h / max(1, trimmed.height)
    norm_w = max(1, round(trimmed.width * scale))
    normalized = stage_cells.harden_alpha(trimmed.resize((norm_w, norm_h), Image.Resampling.NEAREST))
    norm_arr = np.array(normalized, dtype=np.uint8)
    norm_mask = norm_arr[:, :, 3] > 0
    norm_info = sprite_quality.analyze_frame(norm_arr)
    norm_colors = int(len(np.unique(norm_arr[:, :, :3][norm_mask].reshape(-1, 3), axis=0))) if norm_mask.any() else 0

    head_px = stage_cells.head_height(norm_mask)
    head_ratio = round(head_px / max(1, norm_h), 4)

    # 站距/站高（取底部 10% 行带外缘宽度）
    ys, xs = np.nonzero(norm_mask)
    top_y, bot_y = int(ys.min()), int(ys.max())
    band_top = max(top_y, bot_y - max(1, round((bot_y - top_y + 1) * 0.10)))
    _, foot_xs = np.nonzero(norm_mask[band_top : bot_y + 1])
    stance_span = int(foot_xs.max() - foot_xs.min() + 1) if foot_xs.size else 0
    stance_ratio = round(stance_span / max(1, norm_h), 4)

    rel_path = path.resolve().relative_to(ROOT).as_posix() if path.resolve().is_relative_to(ROOT) else str(path)
    return {
        "label": label,
        "path": rel_path,
        "sha256": _sha256(path),
        "raw_resolution": list(raw_rgba.size),
        "bbox_size": [trimmed.width, trimmed.height],
        "normalized_standing": norm_h,
        "normalized_size": [norm_w, norm_h],
        "raw_visible_colors": colors_raw,
        "normalized_visible_colors": norm_colors,
        "binary_alpha": raw_info["binary_alpha"],
        "glow_out200": raw_info["glow_out200"],
        "glow_out16": raw_info["glow_out16"],
        "components_4conn": norm_info["components"],
        "stray_islands": len(norm_info["stray_islands"]),
        "head_height_px": head_px,
        "head_body_ratio": head_ratio,
        "stance_width_ratio": stance_ratio,
        "stance_in_range_065_080": 0.65 <= stance_ratio <= 0.80,
        "glow_gate_ok": raw_info["glow_out200"] == 0 and raw_info["glow_out16"] <= sprite_quality.MAX_OUTER_ALPHA16,
    }


def cmd_anchor(args: argparse.Namespace) -> int:
    candidates: list[tuple[str, Path]] = []
    if args.magpie is not None:
        candidates.append(("magpie-image", _resolve_repo_path(args.magpie)))
    if args.builtin is not None:
        candidates.append(("image-generator", _resolve_repo_path(args.builtin)))
    for spec in args.candidate:
        label, sep, p_text = spec.partition("=")
        if not sep or not label or not p_text:
            raise SystemExit(f"--candidate 需要 label=path 格式：{spec}")
        candidates.append((label.strip(), _resolve_repo_path(Path(p_text.strip()))))
    if args.anchor is not None:
        candidates.append(("anchor", _resolve_repo_path(args.anchor)))

    if not candidates:
        default_anchor = ROOT / f"art/fighters/{args.fighter}/stage1/anchor/identity-idle-pixel.png"
        if default_anchor.is_file():
            candidates.append(("installed-anchor", default_anchor))
        else:
            raise SystemExit("请提供至少一个候选锚图（--magpie / --builtin / --candidate / --anchor）")

    measured = [
        _measure_anchor_candidate(label, path, args.target_standing)
        for label, path in candidates
    ]

    selected_row = None
    if args.select:
        for row in measured:
            if row["label"] == args.select or row["path"] == args.select:
                selected_row = row
                break
        if selected_row is None:
            raise SystemExit(f"--select 未匹配到候选：{args.select}")
        anchor_dir = ROOT / f"art/fighters/{args.fighter}/stage1/anchor"
        anchor_dir.mkdir(parents=True, exist_ok=True)
        src_path = _resolve_repo_path(Path(selected_row["path"]))
        dest_png = anchor_dir / "identity-idle-pixel.png"
        if src_path.resolve() != dest_png.resolve():
            shutil.copy2(src_path, dest_png)
        manifest = {
            "schema": 1,
            "fighter": args.fighter,
            "selected_channel": selected_row["label"],
            "anchor_png": dest_png.relative_to(ROOT).as_posix(),
            "anchor_sha256": _sha256(dest_png),
            "metrics": selected_row,
            "candidates": measured,
        }
        (anchor_dir / "anchor-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    payload = {
        "fighter": args.fighter,
        "target_standing": args.target_standing or measured[0]["normalized_standing"],
        "candidates": measured,
        "selected": selected_row["label"] if selected_row else None,
    }
    if args.json_out is not None:
        out_path = _resolve_repo_path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_extract_video(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    if out_dir is None:
        out_dir = ROOT / f"art/fighters/{args.fighter}/stage1/video/{args.clip}"
    anchor = args.anchor
    if anchor is None:
        candidate = ROOT / f"art/fighters/{args.fighter}/stage1/anchor/identity-idle-pixel.png"
        if candidate.is_file():
            anchor = candidate

    argv = ["--video", str(args.video), "--out-dir", str(out_dir), "--clip", args.clip,
            "--count", str(args.count), "--start", str(args.start),
            "--bg-mode", args.bg_mode, "--bg-tolerance", str(args.bg_tolerance),
            "--grid-snap", args.grid_snap, "--pixel-grid-max-pitch", str(args.pixel_grid_max_pitch),
            "--palette-size", str(args.palette_size), "--scale-frame", str(args.scale_frame)]
    if anchor is not None:
        argv.extend(["--anchor", str(anchor)])
    if args.palette_json is not None:
        argv.extend(["--palette-json", str(args.palette_json)])
    if args.target_standing:
        argv.extend(["--target-standing", str(args.target_standing)])
    if args.scale:
        argv.extend(["--scale", str(args.scale)])
    if args.end is not None:
        argv.extend(["--end", str(args.end)])
    if args.fps is not None:
        argv.extend(["--fps", str(args.fps)])
    if args.timestamps:
        argv.extend(["--timestamps", args.timestamps])
    if args.chroma_key:
        argv.extend(["--chroma-key", args.chroma_key])
    if args.keep_raw:
        argv.append("--keep-raw")
    return video_frames.main(argv)


def cmd_stage(args: argparse.Namespace) -> int:
    out_dir = args.out_dir or (ROOT / f"art/fighters/{args.fighter}/stage1/cells")
    argv = [
        "--fighter", args.fighter,
        "--scale-source", str(args.scale_source),
        "--target-standing", str(args.target_standing),
        "--out-dir", str(out_dir),
        "--anchor-x", str(args.anchor_x),
        "--baseline", str(args.baseline),
        "--cell", str(args.cell),
        "--foot-band", str(args.foot_band),
    ]
    if args.scale:
        argv.extend(["--scale", str(args.scale)])
    if args.palette_json:
        argv.extend(["--palette-json", str(args.palette_json)])
    for item in args.frame:
        argv.extend(["--frame", item])
    for item in args.air:
        argv.extend(["--air", item])

    rc = stage_cells.main(argv)
    if rc != 0:
        return rc

    if args.compose_clip:
        frame_names = [f.partition("=")[0] for f in args.frame]
        compose_cmd = [
            sys.executable, str(ROOT / "tools/art/compose_clip.py"),
            "--fighter", args.fighter, "--clip", args.compose_clip,
        ]
        for name in frame_names:
            compose_cmd.extend(["--frame", str(_resolve_repo_path(out_dir) / f"{name}-cell.png")])
        if args.ticks:
            compose_cmd.extend(["--ticks", args.ticks])
        if args.loop:
            compose_cmd.append("--loop")
        return subprocess.run(compose_cmd, cwd=ROOT, check=False).returncode
    return 0


def cmd_derive(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable, str(ROOT / "tools/art/derive_fighter_data.py"),
        "--fighter", args.fighter,
        "--standing", str(args.standing),
        "--donor-standing", str(args.donor_standing),
    ]
    if args.states_only:
        cmd.append("--states-only")
    for c in args.state_clip:
        cmd.extend(["--state-clip", c])
    if args.write:
        cmd.append("--write")
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


def cmd_install(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable, str(ROOT / "tools/art/install_cells.py"),
        "--fighter", args.fighter,
        "--ticks", str(args.ticks),
    ]
    if args.only:
        cmd.extend(["--only", args.only])
    if args.merge:
        cmd.append("--merge")
    if args.dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


def cmd_check(args: argparse.Namespace) -> int:
    sq_cmd = [sys.executable, str(ROOT / "tools/check/sprite_quality.py")]
    if args.dir is not None:
        sq_cmd.extend(["--dir", str(args.dir)])
    else:
        sq_cmd.extend(["--fighter", args.fighter])
    for c in args.clip:
        sq_cmd.extend(["--clip", c])
    if args.anchor is not None:
        sq_cmd.extend(["--anchor", str(args.anchor)])
    if args.ticks:
        sq_cmd.extend(["--ticks", args.ticks])
    if args.allow_soft_alpha:
        sq_cmd.append("--allow-soft-alpha")
    if args.json_out is not None:
        sq_cmd.extend(["--json-out", str(args.json_out)])

    sq_rc = subprocess.run(sq_cmd, cwd=ROOT, check=False).returncode

    pm_cmd = [sys.executable, str(ROOT / "tools/art/parity_matrix.py"), "--fighter", args.fighter]
    if args.parity_json:
        pm_cmd.append("--json")
    pm_rc = subprocess.run(pm_cmd, cwd=ROOT, check=False).returncode
    return 1 if (sq_rc != 0 or pm_rc != 0) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_anchor = sub.add_parser("anchor", help="登记与对比双通道像素待机身份锚")
    p_anchor.add_argument("--fighter", required=True)
    p_anchor.add_argument("--magpie", type=Path, default=None, help="magpie-image MCP 生成候选")
    p_anchor.add_argument("--builtin", type=Path, default=None, help="内置 image-generator 生成候选")
    p_anchor.add_argument("--candidate", action="append", default=[], help="额外候选 label=path")
    p_anchor.add_argument("--anchor", type=Path, default=None, help="直接核验单张待机锚")
    p_anchor.add_argument("--target-standing", type=int, default=0, help="归一化比较站高（默认取首候选实际高）")
    p_anchor.add_argument("--select", default="", help="定标并晋升指定候选标签/路径为正式待机锚")
    p_anchor.add_argument("--json-out", type=Path, default=None)
    p_anchor.set_defaults(func=cmd_anchor)

    p_vid = sub.add_parser("extract-video", help="从 I2V 视频抽帧、去背并像素化")
    p_vid.add_argument("--fighter", required=True)
    p_vid.add_argument("--video", type=Path, required=True)
    p_vid.add_argument("--clip", default="clip")
    p_vid.add_argument("--out-dir", type=Path, default=None)
    p_vid.add_argument("--anchor", type=Path, default=None)
    p_vid.add_argument("--palette-json", type=Path, default=None)
    p_vid.add_argument("--target-standing", type=int, default=0)
    p_vid.add_argument("--scale", type=float, default=0.0)
    p_vid.add_argument("--scale-frame", type=int, default=0)
    p_vid.add_argument("--count", type=int, default=6)
    p_vid.add_argument("--start", type=float, default=0.0)
    p_vid.add_argument("--end", type=float, default=None)
    p_vid.add_argument("--fps", type=float, default=None)
    p_vid.add_argument("--timestamps", default="")
    p_vid.add_argument("--bg-mode", choices=("auto", "chroma-ycbcr", "chroma-rgb", "flood-lab", "alpha"), default="auto")
    p_vid.add_argument("--chroma-key", default="")
    p_vid.add_argument("--bg-tolerance", type=float, default=24.0)
    p_vid.add_argument("--grid-snap", choices=("auto", "on", "off"), default="auto")
    p_vid.add_argument("--pixel-grid-max-pitch", type=int, default=48)
    p_vid.add_argument("--palette-size", type=int, default=32)
    p_vid.add_argument("--keep-raw", action="store_true")
    p_vid.set_defaults(func=cmd_extract_video)

    p_stage = sub.add_parser("stage", help="调用 stage_cells 落格，并可选 compose_clip 拼装")
    p_stage.add_argument("--fighter", required=True)
    p_stage.add_argument("--scale-source", type=Path, required=True)
    p_stage.add_argument("--target-standing", type=int, required=True)
    p_stage.add_argument("--frame", action="append", required=True, help="名字=路径[@脚底行]")
    p_stage.add_argument("--air", action="append", default=[])
    p_stage.add_argument("--out-dir", type=Path, default=None)
    p_stage.add_argument("--anchor-x", type=int, default=stage_cells.ANCHOR_X)
    p_stage.add_argument("--baseline", type=int, default=stage_cells.BASELINE)
    p_stage.add_argument("--cell", type=int, default=stage_cells.CELL)
    p_stage.add_argument("--foot-band", type=float, default=0.08)
    p_stage.add_argument("--scale", type=float, default=0.0)
    p_stage.add_argument("--palette-json", default="")
    p_stage.add_argument("--compose-clip", default="", help="落格后立即拼装为已安装 manifest 中的指定 clip")
    p_stage.add_argument("--ticks", default="", help="compose_clip 帧时长（逗号分隔）")
    p_stage.add_argument("--loop", action="store_true")
    p_stage.set_defaults(func=cmd_stage)

    p_derive = sub.add_parser("derive", help="调用 derive_fighter_data 派生受击框与状态帧")
    p_derive.add_argument("--fighter", required=True)
    p_derive.add_argument("--standing", type=int, default=154)
    p_derive.add_argument("--donor-standing", type=int, default=188)
    p_derive.add_argument("--states-only", action="store_true")
    p_derive.add_argument("--state-clip", action="append", default=[])
    p_derive.add_argument("--write", action="store_true")
    p_derive.set_defaults(func=cmd_derive)

    p_install = sub.add_parser("install", help="调用 install_cells 安装角色图集与清单")
    p_install.add_argument("--fighter", required=True)
    p_install.add_argument("--ticks", type=int, default=10)
    p_install.add_argument("--only", default="")
    p_install.add_argument("--merge", action="store_true")
    p_install.add_argument("--dry-run", action="store_true")
    p_install.set_defaults(func=cmd_install)

    p_check = sub.add_parser("check", help="串联 sprite_quality 硬门与 parity_matrix 检查")
    p_check.add_argument("--fighter", required=True)
    p_check.add_argument("--dir", type=Path, default=None, help="可选：检查候选目录而非已装 manifest")
    p_check.add_argument("--clip", action="append", default=[])
    p_check.add_argument("--anchor", type=Path, default=None)
    p_check.add_argument("--ticks", default="")
    p_check.add_argument("--allow-soft-alpha", action="store_true")
    p_check.add_argument("--json-out", type=Path, default=None)
    p_check.add_argument("--parity-json", action="store_true")
    p_check.set_defaults(func=cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
