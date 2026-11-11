"""四角色专属特效家族重着色：保留源图集像素形状，按目标光色梯度重排色板。

不新增形状、不改矩形布局、不引入外部资源；源像素逐位保留，只重映射 RGB。
亮度分层用 OKLCH 亮度（降序）线性映射到目标色板（亮→暗），alpha 原样保留。
图集输出为确定性产物：同一输入同一输出；SHA 记入 provenance.json 供审查。

用法：
  python tools/rebuild/shared/phase3_family_recolor.py --spec <json> [--out-dir <目录>]

spec 结构（按角色一份，存 tools/rebuild/<角色>/phase3_family_spec.json）：
  {
    "target": "assets/effects/mother-of-ultra",
    "source_root": "assets/effects",
    "families": [
      {
        "source": "ultraman-ace/metalium2_start/atlas.png",
        "out": "cinerama_start/atlas.png",
        "palette": ["#ffffff", "#fff5c0", "#ffd24a", "#e88a1a"]
      }
    ]
  }
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
import json
from pathlib import Path
Path = _LayoutProjectPath

import numpy as np
from PIL import Image


def _oklch_lightness(rgb: np.ndarray) -> np.ndarray:
    """OKLab 亮度通道 L，0..1；用于把源像素按明度排序。"""
    r, g, b = [rgb[..., i].astype(np.float64) / 255.0 for i in range(3)]
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = np.cbrt(l_), np.cbrt(m_), np.cbrt(s_)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    return L


def expand_stops(stops: list[str], steps: int = 16) -> list[str]:
    """关键色锚点（亮→暗）线性插值成 steps 色梯度，保持端点。"""
    if len(stops) >= steps:
        return stops
    rgb = []
    for spec in stops:
        hexv = spec.lstrip("#")
        rgb.append((int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16)))
    anchors = np.array(rgb, dtype=np.float64)
    seg = len(anchors) - 1
    out = []
    for i in range(steps):
        t = i / (steps - 1) * seg
        k = min(int(t), seg - 1)
        f = t - k
        c = anchors[k] * (1 - f) + anchors[k + 1] * f
        out.append("#%02x%02x%02x" % tuple(round(v) for v in c))
    return out


def recolor_atlas(source: Path, target_palette: list[str]) -> Image.Image:
    """把源图集按亮度映射到目标色板；alpha 原样保留。

    target_palette 是亮→暗的关键色锚点；少于 16 色时自动插值成 16 色梯度，
    与源图集的 48 色亮度分层保持足够色阶。"""
    im = Image.open(source).convert("RGBA")
    pixels = np.array(im)
    opaque = pixels[..., 3] > 0
    if not opaque.any():
        raise ValueError(f"源图集无可见像素: {source}")
    # 源可见色去重，按 OKLab 亮度降序排（亮→暗）。
    src_rgb = pixels[opaque][:, :3]
    uniq = np.unique(src_rgb, axis=0)
    uniq = uniq[np.argsort(-_oklch_lightness(uniq))]
    # 目标色板按输入顺序取（约定：亮→暗）；关键色锚点自动插值成 16 色梯度。
    dst = []
    for spec in expand_stops(target_palette):
        hexv = spec.lstrip("#")
        dst.append((int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16)))
    dst = np.array(dst, dtype=np.uint8)
    if len(dst) < 2:
        raise ValueError("目标色板至少 2 色")
    # 每个源色按其在降序亮度序列中的分位映射到目标色板的同分位色。
    lut: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    n_src = len(uniq)
    for i, rgb in enumerate(uniq):
        pos = i / max(n_src - 1, 1)
        idx = round(pos * (len(dst) - 1))
        lut[tuple(int(c) for c in rgb)] = tuple(int(c) for c in dst[idx])
    out = pixels.copy()
    for (r, g, b), (nr, ng, nb) in lut.items():
        sel = opaque & (out[..., 0] == r) & (out[..., 1] == g) & (out[..., 2] == b)
        out[sel, 0], out[sel, 1], out[sel, 2] = nr, ng, nb
    result = Image.fromarray(out)
    if result.getextrema()[3][0] < 0 or len(set(result.getchannel("A").tobytes())) > 2:
        raise ValueError("输出 alpha 必须二值")
    alphas = set(np.unique(np.array(result)[..., 3]).tolist())
    if not alphas <= {0, 255}:
        raise ValueError(f"输出 alpha 非二值: {alphas}")
    src_colors = len(uniq)
    out_colors = len(np.unique(out[opaque][:, :3], axis=0))
    return result, src_colors, out_colors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out-dir", default=None, help="覆盖 spec.target 的输出根（相对仓库根）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    root = spec_path.resolve().parents[1]
    out_root = Path(args.out_dir) if args.out_dir else Path(spec["target"])
    out_abs = (root / out_root).resolve()
    src_abs = (root / spec.get("source_root", "assets/effects")).resolve()
    for fam in spec["families"]:
        src = (src_abs / fam["source"]).resolve()
        out = (out_abs / fam["out"]).resolve()
        assert src.is_file(), f"源图集缺失: {src}"
        assert str(out).startswith(str(out_abs)), f"输出越界: {out}"
        result, n_src, n_out = recolor_atlas(src, fam["palette"])
        print(f"{fam['source']} -> {fam['out']}  {result.size}  源{n_src}色 出{n_out}色")
        if args.dry_run:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        result.save(out)
    if not args.dry_run:
        print(f"完成：{len(spec['families'])} 张图集 -> {out_abs}")


if __name__ == "__main__":
    main()
