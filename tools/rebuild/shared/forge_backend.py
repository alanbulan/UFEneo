"""UFEneo 的 agent-sprite-forge 后端；不导入旧技能或它的解释器。

七个像素接口保留原调用签名，修改输入的两个接口也保留原地修改语义。
默认配色采用 forge 的 OKLab；需要重现历史固定色板时显式选 palette_mode('rgb')。
网格检测仅接受 forge 能证明的整数格。无网格返回 ((1.,1.),(0.,0.))。

补充算法独立实现：Astropulse kCentroid 的分块主簇思想、Lloyd 二均值，
用 NumPy 批处理实现，没有复制旧技能代码。项目的兼容约定是三轮整数中心、
亮度极值初始化、半数覆盖和暗部细节偏好；并非 forge 自带的缩放器。
出处：https://github.com/Astropulse/K-Centroid-Aseprite （kCentroid）;
Lloyd, Least squares quantization in PCM, IEEE IT 28(2), 1982。
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
import hashlib
import importlib
import math
import os
from pathlib import Path
Path = _LayoutProjectPath
from statistics import median
import sys
from typing import Any
import warnings

import numpy as np
from PIL import Image

_PALETTE_MODE = ContextVar('ufeneo_forge_palette_mode', default='oklab')
__all__ = ['detect_pixel_grid', 'grid_snap_downscale', '_kcentroid_downscale',
           '_dominant_block_color', 'build_shared_palette', 'apply_palette',
           'binarize_alpha', 'palette_mode', 'shared_source_scale', 'backend_info',
           'draw_guide', 'raw_rel', 'guide_rel', 'prompt_rel', 'take_raw_rel',
           'build_anchor_layout', 'build_layout_guide']


@lru_cache(maxsize=1)
def _scripts() -> Path:
    root = Path(os.environ.get('UFENEO_FORGE_ROOT', Path.home()/'.codex/skills/generate2dsprite'))
    for candidate in (root/'scripts', root/'skills/generate2dsprite/scripts'):
        if (candidate/'forge_palette.py').is_file() and (candidate/'pixel_reduce.py').is_file():
            return candidate.resolve()
    raise ImportError(f'未找到 agent-sprite-forge：{root}；设置 UFENEO_FORGE_ROOT 指向技能或源码根目录')


@lru_cache(maxsize=None)
def _forge(name: str):
    scripts = _scripts()
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() != scripts/f'{name}.py':
        raise ImportError(f'{name} 已从其他位置加载，拒绝混用 forge 版本')
    sys.path.insert(0, str(scripts))
    try:
        return importlib.import_module(name)
    finally:
        sys.path.remove(str(scripts))


def backend_info() -> dict[str, Any]:
    paths = [_scripts()/f'{name}.py' for name in ('forge_palette', 'pixel_reduce', 'forge_core')]
    return {'backend': 'agent-sprite-forge', 'scripts': str(_scripts()),
            'python': sys.executable, 'numpy': np.__version__,
            'palette_distance': _PALETTE_MODE.get(), 'grid': 'clean integer only',
            'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


@contextmanager
def palette_mode(mode: str):
    """oklab 调用 forge；rgb 只用于历史固定色板的距离兼容，不重新学习色板。"""
    if mode not in ('oklab', 'rgb'):
        raise ValueError('palette_mode 只能是 oklab 或 rgb')
    token = _PALETTE_MODE.set(mode)
    try:
        yield
    finally:
        _PALETTE_MODE.reset(token)


def _mask(pixels: np.ndarray) -> np.ndarray:
    fp = _forge('forge_palette')
    # 透明判定调用 forge；保留原 RGB，不通过黑色色板改变主体颜色。
    p = fp.Palette(((0, 0, 0),))
    return fp.quantize_image(pixels, p, alpha_threshold=128, orphans=0) != p.transparent_index


def binarize_alpha(image: Image.Image) -> Image.Image:
    if image.mode != 'RGBA':
        raise ValueError('原地 Alpha 接口要求 RGBA；请先 convert("RGBA")')
    pixels = np.array(image)
    visible = _mask(pixels)
    pixels[~visible] = 0
    pixels[visible, 3] = 255
    image.paste(Image.fromarray(pixels))
    return image


def build_shared_palette(frames: list, size: int) -> list:
    if not 1 <= size <= 256:
        raise ValueError('色板大小必须在 1..256 内')
    if not frames or not any(np.any(np.asarray(f.convert('RGBA'))[..., 3] >= 128) for f in frames):
        return []
    fp = _forge('forge_palette')
    return list(fp.build_palette(frames, size, seed=0, alpha_threshold=128).colors)


def apply_palette(image: Image.Image, palette: list) -> Image.Image:
    if not palette:
        return image
    if image.mode != 'RGBA':
        raise ValueError('原地色板接口要求 RGBA')
    fp = _forge('forge_palette')
    # 256 个可见色也不得牺牲一个颜色给透明槽；透明性单独保存。
    pal = fp.Palette(tuple(tuple(int(c) for c in rgb) for rgb in palette), transparent_index=None)
    pixels = np.array(image)
    visible = _mask(pixels)
    if _PALETTE_MODE.get() == 'oklab':
        opaque = pixels.copy()
        opaque[..., 3] = 255
        indices = fp.quantize_image(opaque, pal, alpha_threshold=128, orphans=0)
        result = fp.render_indices(indices, pal)
    else:
        colors = np.asarray(pal.colors, dtype=np.int32)
        unique, inverse = np.unique(pixels[..., :3].reshape(-1, 3), axis=0, return_inverse=True)
        nearest = np.empty(len(unique), dtype=np.intp)
        for start in range(0, len(unique), 8192):
            delta = unique[start:start+8192, None].astype(np.int32)-colors
            nearest[start:start+8192] = np.einsum('nki,nki->nk', delta, delta).argmin(axis=1)
        result = pixels.copy()
        result[..., :3] = colors[nearest[inverse]].reshape(pixels.shape[:2]+(3,))
        result[..., 3] = 255
    result[~visible] = 0
    image.paste(Image.fromarray(result))
    return image


def detect_pixel_grid(strip: Image.Image, max_pitch: int = 48) -> tuple[tuple[float, float], tuple[float, float]]:
    if max_pitch < 2:
        return (1., 1.), (0., 0.)
    grid = _forge('forge_palette').detect_grid(np.asarray(strip.convert('RGBA')), max_period=max_pitch)
    if grid['score'] < .5 or grid['uniformity'] < .9 or grid['period'] < 2:
        return (1., 1.), (0., 0.)
    period = float(grid['period'])
    return (period, period), tuple(float(x) for x in grid['phase'])


def _centroids(blocks: np.ndarray, detail_bias: bool) -> np.ndarray:
    """N×样本×RGBA → N×RGBA；三轮整数 Lloyd，透明样本不参与色簇。"""
    rgb = blocks[..., :3].astype(np.int32)
    valid = blocks[..., 3] >= 128
    luma = rgb @ np.array([299, 587, 114], dtype=np.int32)
    indexes = np.arange(len(blocks))
    dark = np.where(valid, luma, 10**9).argmin(axis=1)
    light = np.where(valid, luma, -1).argmax(axis=1)
    centers = np.stack((rgb[indexes, dark], rgb[indexes, light]), axis=1)
    membership = np.zeros(valid.shape, dtype=np.intp)
    counts = np.zeros((len(blocks), 2), dtype=np.int64)
    for _ in range(3):
        delta = rgb[:, :, None, :]-centers[:, None, :, :]
        membership = np.einsum('npkc,npkc->npk', delta, delta).argmin(axis=2)
        for cluster in (0, 1):
            included = valid & (membership == cluster)
            counts[:, cluster] = included.sum(axis=1)
            sums = (rgb*included[..., None]).sum(axis=1)
            centers[:, cluster] = np.where(counts[:, cluster, None] > 0,
                sums//np.maximum(counts[:, cluster, None], 1), centers[:, cluster])
    chosen = counts.argmax(axis=1)
    if detail_bias:
        luminance = centers @ np.array([299, 587, 114], dtype=np.int32)
        darkest = luminance.argmin(axis=1)
        eligible = ((counts[indexes, darkest]*5 >= valid.sum(axis=1)*2)
                    & (luminance[indexes, darkest] < 70000)
                    & (np.abs(luminance[:, 0]-luminance[:, 1]) > 50000))
        chosen = np.where(eligible, darkest, chosen)
    out = np.zeros((len(blocks), 4), dtype=np.uint8)
    out[:, :3] = centers[indexes, chosen]
    out[:, 3] = (blocks[..., 3].astype(np.int64)*valid).sum(axis=1)//np.maximum(valid.sum(axis=1), 1)
    out[valid.sum(axis=1)*2 < blocks.shape[1]] = 0
    return out


def _dominant_block_color(opaque: list, detail_bias: bool = False) -> tuple[int, int, int]:
    pixels = np.asarray(opaque, dtype=np.uint8)
    if pixels.ndim != 2 or pixels.shape[1] not in (3, 4) or not len(pixels):
        raise ValueError('需要非空 RGB/RGBA 像素列表')
    rgba = np.full((1, len(pixels), 4), 255, dtype=np.uint8)
    rgba[0, :, :3] = pixels[:, :3]
    return tuple(int(x) for x in _centroids(rgba, detail_bias)[0, :3])


def _reduce_edges(image: Image.Image, x_edges: np.ndarray, y_edges: np.ndarray, detail_bias: bool) -> Image.Image:
    pixels = np.asarray(image.convert('RGBA'))
    widths, heights = np.maximum(np.diff(x_edges), 1), np.maximum(np.diff(y_edges), 1)
    out = np.zeros((len(heights), len(widths), 4), dtype=np.uint8)
    for h in np.unique(heights):
        for w in np.unique(widths):
            yy, xx = np.meshgrid(np.flatnonzero(heights == h), np.flatnonzero(widths == w), indexing='ij')
            yy, xx = yy.ravel(), xx.ravel()
            for start in range(0, len(xx), 2048):
                yi, xi = yy[start:start+2048], xx[start:start+2048]
                blocks = pixels[y_edges[yi, None, None]+np.arange(h)[None, :, None],
                                x_edges[xi, None, None]+np.arange(w)[None, None, :]]
                out[yi, xi] = _centroids(blocks.reshape(len(xi), -1, 4), detail_bias)
    return Image.fromarray(out)


def _kcentroid_downscale(sprite: Image.Image, target_width: int, target_height: int, detail_bias: bool = False) -> Image.Image:
    if target_width <= 0 or target_height <= 0:
        raise ValueError('目标宽高必须为正整数')
    # 兼容旧接口的放大调用：重复覆盖单个源像素，不引入插值颜色。
    xe = np.arange(target_width+1, dtype=np.int64)*sprite.width//target_width
    ye = np.arange(target_height+1, dtype=np.int64)*sprite.height//target_height
    return _reduce_edges(sprite, xe, ye, detail_bias)


def grid_snap_downscale(image: Image.Image, pitch: float | tuple[float, float], detail_bias: bool = False,
                        phase: tuple[float, float] | None = None) -> Image.Image:
    px, py = (pitch, pitch) if np.isscalar(pitch) else pitch
    px, py = float(px), float(py)
    if not all(math.isfinite(x) and x > 0 for x in (px, py)):
        raise ValueError('网格周期必须为有限正数')
    if min(px, py) <= 1:
        return image.convert('RGBA').copy()
    fp = _forge('forge_palette')
    period = int(round(px))
    square_integer = px == py == period
    if phase is None:
        phase = tuple(fp.grid_score(np.asarray(image.convert('RGBA')), period)['phase']) if square_integer else (0., 0.)
    if not all(math.isfinite(x) for x in phase):
        raise ValueError('网格相位必须有限')
    if square_integer and all(float(x).is_integer() for x in phase):
        pixels = np.asarray(image.convert('RGBA'))
        score = fp.grid_score(pixels, period, phase=phase)
        if score['score'] >= .5 and score['uniformity'] >= .9:
            # 保留边缘不足一格的内容；forge 默认会裁去这些边条。
            left, top = (-int(phase[0])) % period, (-int(phase[1])) % period
            right, bottom = (-(image.width+left)) % period, (-(image.height+top)) % period
            padded = np.pad(pixels, ((top, bottom), (left, right), (0, 0)), mode='edge')
            pal = fp.build_palette(padded, 255, seed=0, alpha_threshold=128)
            idx, _, _ = _forge('pixel_reduce').reduce_image(padded, period, (0, 0), pal, 'mode', 128)
            return Image.fromarray(fp.render_indices(idx, pal))
    # forge 没有小数、非方格或脏网格还原；独立的几何格+主簇路径不假称 forge 检测通过。
    warnings.warn('forge 无干净整数方格：使用显式网格的 kCentroid 兼容还原', RuntimeWarning, stacklevel=2)
    def edges(length, spacing, offset):
        n = math.ceil(length/spacing)+2
        interior = np.rint((float(offset) % spacing)+np.arange(-1, n)*spacing).astype(np.int64)
        return np.unique(np.r_[0, interior[(interior > 0) & (interior < length)], length])
    out = _reduce_edges(image, edges(image.width, px, phase[0]), edges(image.height, py, phase[1]), detail_bias)
    return binarize_alpha(out)


def shared_source_scale(*, standing_heights: list[float] | None = None, target_standing_height: float | None = None,
                        head_readings: list[float] | None = None, target_head_reading: float | None = None) -> dict[str, Any]:
    """高分原图读数 → 一张原图的唯一比例及证据；逐帧偏差只复核，不返回逐帧缩放值。"""
    use_standing = bool(standing_heights)
    readings = standing_heights if use_standing else head_readings
    target = target_standing_height if use_standing else target_head_reading
    if not readings or target is None or not all(math.isfinite(float(v)) and v > 0 for v in [*readings, target]):
        raise ValueError('必须提供有限正数的原图站高/目标站高，或原图头标尺/目标头标尺')
    reference = median(readings)
    scale = target/reference
    checks = []
    for kind, values, native in [('standing', standing_heights, target_standing_height), ('head', head_readings, target_head_reading)]:
        if values and native is not None:
            if not all(math.isfinite(float(v)) and v > 0 for v in [*values, native]):
                raise ValueError('复核读数和目标必须为有限正数')
            tolerance = .03 if kind == 'standing' else .08
            checks.extend({'kind': kind, 'index': i, 'raw': v, 'native': v*scale,
                           'deviation': v*scale/native-1, 'needs_review': abs(v*scale/native-1) > tolerance}
                          for i, v in enumerate(values))
    return {'scale': scale, 'basis': 'upright_height_median' if use_standing else 'head_ruler_median',
            'source_median': reference, 'target_native': target, 'source_readings': list(readings),
            'checks': checks, 'policy': 'one_clean_source_one_scale; no_per_frame_rescale'}


def _relative(request: dict, state: str, prefix: str, suffix: str) -> str:
    directions = (request.get('directions') or {}).get('set', [])
    if request.get('layout') == 'taxonomy/v1':
        for direction in directions:
            if state.startswith(direction+'_'):
                return f'{prefix}/{direction}/{state[len(direction)+1:]}{suffix}'
    return f'{prefix}/{state}{suffix}'


def raw_rel(request: dict, state: str) -> str:
    return _relative(request, state, 'raw', '.png')


def guide_rel(request: dict, state: str) -> str:
    return _relative(request, state, 'references/layout-guides', '.png')


def prompt_rel(request: dict, state: str) -> str:
    return _relative(request, state, 'prompts', '.txt')


def take_raw_rel(request: dict, state: str, label: str) -> str:
    return raw_rel(request, state)[:-4]+f'.takes/{label}.png'


def build_layout_guide(*args, **kwargs) -> Image.Image:
    return _forge('make_layout_guide').build_layout_guide(*args, **kwargs)


def build_anchor_layout(*args, **kwargs) -> Image.Image:
    return _forge('make_anchor_layout').build_anchor_layout(*args, **kwargs)


def draw_guide(path: Path, state: str, frames: int, cell: dict[str, Any], motion_phase_guides: bool = False) -> None:
    if motion_phase_guides:
        raise NotImplementedError('旧技能的动作火柴人模板未迁移；请使用项目固定骨长引导图，不静默省略')
    guide = build_layout_guide(1, frames, int(cell['width']), int(cell['height']),
                               int(cell['safe_margin_x']), int(cell['safe_margin_y']))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    guide.save(path)
