"""共用整头刚体配准：只读运行资源，结果仅用于人工复核。

Python: .venv/bin/python
配置坐标均为 idle 第零格的原生像素；旋转沿用 OpenCV（正值逆时针）。
不导入、不改写各角色私有配准脚本，不自动批准、缩放或安装任何资源。
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
import hashlib
import io
import json; json = _LayoutJson
import math
import os
from pathlib import Path
Path = _LayoutProjectPath
import sys
import time
import types

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from .forge_backend import backend_info, binarize_alpha
except ImportError:  # 直接运行脚本时，tools/rebuild在sys.path中。
    from forge_backend import backend_info, binarize_alpha

ROOT = _LayoutProjectPath(_layout_root)
CONFIG = ROOT / 'art/production/head_fit'
DEFAULT_OUT = ROOT / 'reports/review/2026-10-23/head-fit-audit'
IDS = ('ultraman', 'ultraseven', 'zetton', 'gomora', 'ultraman-jack',
       'ultraman-ace', 'ultraman-taro', 'ultraman-leo', 'red_king',
       'neronga', 'eleking', 'black_king')
NAMES = dict(zip(IDS, ('初代', '赛文', '杰顿', '哥莫拉', '杰克', '艾斯',
                       '泰罗', '雷欧', '雷德王', '内隆嘎', '艾雷王', '布莱克王')))
cv2.setNumThreads(1)
cv2.ocl.setUseOpenCL(False)
WEIGHTS = np.array([1., .7], np.float32)


def now():
    return datetime.now().astimezone().isoformat(timespec='milliseconds')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                   allow_nan=False) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def config_for(cid):
    cfg = read_json(CONFIG / f'{cid}.json')
    assert cfg['character'] == cid
    for key in ('head_center', 'neck_cut', 'template_radius', 'background_ring', 'upsample',
                'scale_range', 'rotation_range'):
        if not np.all(np.isfinite(np.asarray(cfg[key], dtype=float))):
            raise ValueError(f'{cid}: {key} 不是有限数')
    if not (0 < cfg['scale_range'][0] < cfg['scale_range'][1]) or cfg['upsample'] < 1:
        raise ValueError('倍率范围或上采样倍数无效')
    return cfg


def crop_frame(image, rect):
    x, y, w, h = map(int, rect)
    if min(x, y) < 0 or min(w, h) <= 0 or x+w > image.width or y+h > image.height:
        raise ValueError(f'格子越界: {rect}, atlas={image.size}')
    return image.crop((x, y, x+w, y+h))


def snapshot(out, characters):
    """一次保存所有原始输入；后续校准、普查和条带只读此快照。"""
    path = out / 'snapshot.json'
    if path.exists():
        raise FileExistsError('快照已存在；使用新的输出目录，或直接校准/普查现有快照')
    result = dict(schema=1, started_at=now(), characters={}, textures={},
                  policy='逐文件双读一致性；不是全工作区同一时刻的事务快照')
    texture_dir = out / 'inputs/textures'
    texture_dir.mkdir(parents=True, exist_ok=True)
    for cid in characters:
        manifest_path = ROOT / f'assets/fighters/{cid}/animations/manifest.json'
        raw = manifest_path.read_bytes()
        if raw != manifest_path.read_bytes():
            raise RuntimeError(f'{cid} manifest 正在变动，请稍后重新快照')
        manifest = json.loads(raw)
        manifest_copy = out / f'inputs/{cid}/manifest.json'
        manifest_copy.parent.mkdir(parents=True, exist_ok=True)
        manifest_copy.write_bytes(raw)
        entry = dict(captured_at=now(), manifest_path=manifest_path.relative_to(ROOT).as_posix(),
                     manifest_sha256=sha(raw), snapshot=manifest_copy.relative_to(out).as_posix(),
                     textures={}, clips=len(manifest['clips']),
                     frames=sum(len(c['rects']) for c in manifest['clips'].values()))
        for clip in manifest['clips'].values():
            source = clip['texture'].removeprefix('res://')
            if source in entry['textures']:
                continue
            data = (ROOT / source).read_bytes()
            if data != (ROOT / source).read_bytes():
                raise RuntimeError(f'{source} 正在变动，请在新目录重新快照')
            digest = sha(data)
            with Image.open(io.BytesIO(data)) as im:
                im.verify()
            dest = texture_dir / f'{digest}.png'
            if not dest.exists():
                dest.write_bytes(data)
            entry['textures'][source] = digest
            result['textures'][digest] = dict(path=dest.relative_to(out).as_posix(),
                                            bytes=len(data), captured_at=now())
        result['characters'][cid] = entry
        print(f'快照 {cid}: {entry["clips"]} 动作 / {entry["frames"]} 帧', flush=True)
    result['finished_at'] = now()
    save_json(path, result)
    return result


@lru_cache(maxsize=128)
def snap_image(out_text, source_hash):
    out = Path(out_text)
    path = out / f'inputs/textures/{source_hash}.png'
    data = path.read_bytes()
    if sha(data) != source_hash:
        raise ValueError(f'快照哈希不符: {path}')
    return Image.open(io.BytesIO(data)).convert('RGBA')


def snap_manifest(out, cid):
    snap = read_json(out / 'snapshot.json')
    item = snap['characters'][cid]
    raw = (out / item['snapshot']).read_bytes()
    if sha(raw) != item['manifest_sha256']:
        raise ValueError(f'{cid} 清单快照哈希不符')
    return json.loads(raw), item


def snap_frame(out, item, clip, index):
    digest = item['textures'][clip['texture'].removeprefix('res://')]
    return crop_frame(snap_image(str(out), digest), clip['rects'][index]), digest


def channels(image):
    a = np.asarray(image.convert('RGBA'), dtype=np.float32) / 255.
    alpha = (a[..., 3] >= 128/255).astype(np.float32)
    lum = a[..., :3] @ np.array([.30, .59, .11], np.float32)
    dark = ((lum < .30) & (alpha > 0)).astype(np.float32)
    return np.stack((alpha, dark), axis=-1)


@dataclass
class HeadTemplate:
    features: np.ndarray
    mask: np.ndarray
    center: tuple
    origin: tuple
    image: Image.Image
    config: dict


def build_template(cfg, idle=None):
    if idle is None:
        idle = crop_frame(Image.open(ROOT / cfg['idle_texture']).convert('RGBA'), cfg['idle_rect'])
    # Forge 仅在副本上统一二值 Alpha；不回写运行帧、不做局部换色。
    idle = binarize_alpha(idle.copy())
    c = channels(idle)
    yy, xx = np.mgrid[:idle.height, :idle.width]
    cx, cy = cfg['head_center']
    (x1, y1), (x2, y2) = cfg['neck_cut']
    ref = (x2-x1)*(cy-y1) - (y2-y1)*(cx-x1)
    if ref == 0:
        raise ValueError('头中心不能落在颈部切线上')
    side = ((x2-x1)*(yy-y1) - (y2-y1)*(xx-x1))*np.sign(ref) >= 0
    near = np.hypot(xx-cx, yy-cy) <= cfg['template_radius']
    if cfg.get('include_box'):
        left, top, right, bottom = cfg['include_box']
        near &= (xx >= left) & (xx <= right) & (yy >= top) & (yy <= bottom)
    for left, top, right, bottom in cfg.get('exclude_boxes', []):
        near &= ~((xx >= left) & (xx < right) & (yy >= top) & (yy < bottom))
    head = (c[..., 0] > 0) & side & near
    # 测量掩码只取头中心所在连通域，排除切线上方的举拳等部件。
    # 这不是修图，也不删除运行资源的像素。
    _, labels = cv2.connectedComponents(head.astype(np.uint8), connectivity=8)
    ys, xs = np.where(head)
    if not len(xs):
        raise ValueError('切线和半径没有包含头部')
    nearest = int(np.argmin((xs-cx)**2+(ys-cy)**2))
    head &= labels == labels[ys[nearest], xs[nearest]]
    radius = int(cfg['background_ring'])
    ring = cv2.dilate(head.astype(np.uint8), np.ones((radius*2+1, radius*2+1), np.uint8)) > 0
    mask = ring & side & near
    ys, xs = np.where(mask)
    if len(xs) < 40:
        raise ValueError('模板掩码为空或过小')
    x0, y0, x3, y3 = int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)
    return HeadTemplate(c[y0:y3, x0:x3].copy(), mask[y0:y3, x0:x3].astype(np.float32),
                        (cx-x0, cy-y0), (x0, y0), idle, cfg)


def font(size=20):
    for name in ('/System/Library/Fonts/Hiragino Sans GB.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc'):
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default(size=size)


def jpeg_preview(image, path, max_width=768):
    im = image if image.mode == 'RGB' else image.convert('RGB')
    if im.width > max_width:
        im = im.resize((max_width, max(1, round(im.height*max_width/im.width))), Image.Resampling.LANCZOS)
    while True:
        buffer = io.BytesIO()
        im.save(buffer, 'JPEG', quality=80)
        if len(buffer.getvalue()) <= 150*1024:
            Path(path).write_bytes(buffer.getvalue())
            return
        im = im.resize((max(1, round(im.width*.85)), max(1, round(im.height*.85))), Image.Resampling.LANCZOS)


def template_plate(template):
    cfg = template.config
    x0, y0 = template.origin
    hh, ww = template.mask.shape
    margin = 4
    crop = template.image.crop((x0-margin, y0-margin, x0+ww+margin, y0+hh+margin))
    bg = Image.new('RGBA', crop.size, (47, 53, 64, 255))
    bg.alpha_composite(crop)
    panel = bg.convert('RGB').resize((crop.width*8, crop.height*8), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(panel)
    for contour in cv2.findContours(template.mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        points = [((int(p[0][0])+margin)*8+4, (int(p[0][1])+margin)*8+4) for p in contour]
        if len(points) > 1:
            draw.line(points+[points[0]], fill=(56, 245, 171), width=2)
    line = [((p[0]-x0+margin)*8+4, (p[1]-y0+margin)*8+4) for p in cfg['neck_cut']]
    draw.line(line, fill=(255, 104, 123), width=3)
    cx, cy = template.center
    xx, yy = (cx+margin)*8+4, (cy+margin)*8+4
    draw.ellipse((xx-4, yy-4, xx+4, yy+4), outline='yellow', width=2)
    full = Image.new('RGB', (panel.width, panel.height+68), (28, 32, 39))
    full.paste(panel, (0, 68))
    d = ImageDraw.Draw(full)
    d.text((8, 3), f'{NAMES[cfg["character"]]} {cfg["character"]} / idle #0 ×8', font=font(18), fill='white')
    d.text((8, 31), '绿：掩码边界  红：项背→喉  黄：搜索中心', font=font(16), fill=(200, 220, 229))
    return full


def templates(out, characters):
    directory = out / 'templates'
    directory.mkdir(exist_ok=True, parents=True)
    plates = []
    for cid in characters:
        cfg = config_for(cid)
        manifest, item = snap_manifest(out, cid)
        idle, _ = snap_frame(out, item, manifest['clips']['idle'], 0)
        tpl = build_template(cfg, idle)
        plate = template_plate(tpl)
        plate.save(directory / f'{cid}.png')
        plates.append(plate)
    for start in range(0, len(plates), 4):
        group = plates[start:start+4]
        w = max(p.width for p in group)
        h = max(p.height for p in group)
        contact = Image.new('RGB', (w*2, h*2), (28, 32, 39))
        for i, plate in enumerate(group):
            contact.paste(plate, (i%2*w, i//2*h))
        contact.save(directory / f'templates-{start//4+1}-8x.png')
        jpeg_preview(contact, directory / f'templates-{start//4+1}.jpg')
    print('模板图已写入', directory, flush=True)


def resized(array, factor):
    if factor == 1:
        return array
    return cv2.resize(array, (max(1, round(array.shape[1]*factor)),
                             max(1, round(array.shape[0]*factor))),
                      interpolation=cv2.INTER_AREA if factor < 1 else cv2.INTER_NEAREST)


def warped(template, scale, angle, resolution):
    """返回变换后的两通道、掩码和头中心；所有缩放只用于测量副本。"""
    t = resized(template.features, resolution)
    m = resized(template.mask, resolution)
    h, w = m.shape
    rotation = cv2.getRotationMatrix2D(((w-1)/2, (h-1)/2), float(angle), float(scale))
    nw = math.ceil(abs(rotation[0, 0])*w+abs(rotation[0, 1])*h)+2
    nh = math.ceil(abs(rotation[0, 1])*w+abs(rotation[0, 0])*h)+2
    rotation[:, 2] += ((nw-w)/2, (nh-h)/2)
    tw = cv2.warpAffine(t, rotation, (nw, nh), flags=cv2.INTER_LINEAR)
    mw = cv2.warpAffine(m, rotation, (nw, nh), flags=cv2.INTER_NEAREST)
    center = (np.asarray(template.center)+.5)*resolution-.5
    center = rotation @ np.array([*center, 1.])
    return tw, mw, center


def sqdiff(window, tw, mw):
    """带掩码加权 SQDIFF，除以掩码面积；适用于二值及粗搜分数通道。"""
    mw = np.ascontiguousarray(mw, dtype=np.float32)
    energy = cv2.matchTemplate(np.ascontiguousarray((window*window) @ WEIGHTS), mw, cv2.TM_CCORR)
    cross = cv2.matchTemplate(np.ascontiguousarray(window),
                             np.ascontiguousarray(tw*mw[..., None]*WEIGHTS), cv2.TM_CCORR)
    constant = float(np.sum(tw*tw*mw[..., None]*WEIGHTS))
    return np.maximum((energy-2*cross+constant)/float(mw.sum()), 0.)


@dataclass
class Match:
    error: float
    scale: float
    angle: float
    center: tuple

    def key(self):
        return (round(self.error, 9), self.scale, self.angle, *self.center)


class Matcher:
    def __init__(self, template):
        self.template = template
        self.cache = {}

    def warp(self, scale, angle, resolution):
        key = (round(float(scale), 6), round(float(angle), 4), float(resolution))
        if key not in self.cache:
            if len(self.cache) > 2500:
                self.cache.clear()
            self.cache[key] = warped(self.template, *key)
        return self.cache[key]

    def search(self, candidate, bounds, scales, angles, resolution, keep=1):
        x0, y0, x1, y1 = bounds
        # 留足透明边，保证边界头部的完整背景环也能放进搜索窗。
        window = resized(candidate[y0:y1, x0:x1], resolution)
        found = []
        for angle in angles:
            for scale in scales:
                tw, mw, tc = self.warp(scale, angle, resolution)
                if min(mw.shape) < 2 or mw.sum() < 8 or mw.shape[0] > window.shape[0] or mw.shape[1] > window.shape[1]:
                    continue
                scores = sqdiff(window, tw, mw)
                error, _, location, _ = cv2.minMaxLoc(scores)
                center = ((location[0]+tc[0]+.5)/resolution-.5+x0,
                          (location[1]+tc[1]+.5)/resolution-.5+y0)
                found.append(Match(float(error), float(scale), float(angle), center))
        found.sort(key=Match.key)
        selected = []
        for match in found:
            if all(math.dist(match.center, p.center) > 6 or abs(match.scale-p.scale) > .08
                   or abs((match.angle-p.angle+180)%360-180) > 15 for p in selected):
                selected.append(match)
                if len(selected) == keep:
                    break
        return selected

    def local_bounds(self, center, candidate, scale=1., padding=8):
        h, w = self.template.mask.shape
        tx, ty = self.template.center
        # 头中心不等于含角/冠模板的外框中心。必须覆盖离头中心最远的角，
        # 否则旋转后细搜窗会切掉模板，并偏向错误的倍率/角度。
        radius = max(math.hypot(x-tx, y-ty) for x in (0, w) for y in (0, h))*scale+padding
        cx, cy = center
        return (max(0, math.floor(cx-radius)), max(0, math.floor(cy-radius)),
                min(candidate.shape[1], math.ceil(cx+radius)), min(candidate.shape[0], math.ceil(cy+radius)))

    def fit(self, image, center=None, full_search=False):
        started = time.perf_counter()
        if center is not None and (len(center) != 2 or not all(math.isfinite(float(v)) for v in center)):
            raise ValueError('头中心必须为两个有限坐标')
        cfg = self.template.config
        a = channels(image)
        bbox = image.getbbox()
        if not bbox or not np.any(a[..., 0]):
            return dict(scale=None, rotation=None, error=None, center=None,
                        search='empty', reason='透明帧', elapsed_seconds=round(time.perf_counter()-started, 6))
        if center is None:
            idle_bbox = self.template.image.getbbox()
            relative = ((cfg['head_center'][0]-idle_bbox[0])/(idle_bbox[2]-idle_bbox[0]),
                        (cfg['head_center'][1]-idle_bbox[1])/(idle_bbox[3]-idle_bbox[1]))
            center = (bbox[0]+relative[0]*(bbox[2]-bbox[0]), bbox[1]+relative[1]*(bbox[3]-bbox[1]))
        margin = int(math.hypot(*self.template.mask.shape)*.80+10)
        # 显式透明留边是搜索域，不是给运行帧扩画布。
        padded = cv2.copyMakeBorder(a, margin, margin, margin, margin, cv2.BORDER_CONSTANT)
        center = (center[0]+margin, center[1]+margin)
        limits = cfg['scale_range']
        scales = np.round(np.arange(limits[0], limits[1]+.001, .05), 4)
        lo, hi = cfg['rotation_range']
        angles = np.arange(lo, hi, 15.)
        local = self.local_bounds(center, padded, 1.5, 24)
        coarse = self.search(padded, local, scales, angles, .5, keep=3)
        search = 'bbox_hint'
        if full_search or not coarse or coarse[0].error > .14:
            # 外框估计不准时，全帧上半部粗搜；翻转动作允许整个主体外框。
            lower = bbox[3] if full_search else max(bbox[1]+(bbox[3]-bbox[1])*.65, center[1]-margin)
            wide = (max(0, bbox[0]), max(0, bbox[1]),
                    min(padded.shape[1], bbox[2]+margin*2),
                    min(padded.shape[0], math.ceil(lower+margin*2)))
            broad = self.search(padded, wide, scales, angles, .5, keep=3)
            coarse = sorted(coarse+broad, key=Match.key)[:4]
            search = 'full_body' if full_search else 'upper_frame'
        if not coarse:
            return dict(scale=None, rotation=None, error=None, center=None, search=search,
                        reason='搜索窗不能容纳模板', elapsed_seconds=round(time.perf_counter()-started, 6))
        refined = []
        # 粗搜保留不同极小值，避免只细化一个低分假头。
        for seed in coarse[:3]:
            svalues = np.round(np.arange(max(limits[0], seed.scale-.06), min(limits[1], seed.scale+.06)+.001, .01), 4)
            avalues = np.arange(seed.angle-12, seed.angle+12.1, 3.)
            refined += self.search(padded, self.local_bounds(seed.center, padded, seed.scale, 5),
                                   svalues, avalues, 1., keep=1)
        if not refined:
            raise RuntimeError('细搜没有候选')
        seed = min(refined, key=Match.key)
        high = self.search(padded, self.local_bounds(seed.center, padded, seed.scale, 3),
                           np.round(np.arange(max(limits[0], seed.scale-.015), min(limits[1], seed.scale+.015)+.001, .005), 5),
                           np.arange(seed.angle-3, seed.angle+3.1, 1.), cfg['upsample'], keep=1)
        seed = min(high, key=Match.key)
        final = self.search(padded, self.local_bounds(seed.center, padded, seed.scale, 2),
                            np.round(np.arange(max(limits[0], seed.scale-.005), min(limits[1], seed.scale+.005)+.0001, .0025), 6),
                            np.arange(seed.angle-1, seed.angle+1.01, .5), cfg['upsample'], keep=1)
        best = min(final+high, key=Match.key)
        angle = (best.angle+180)%360-180
        reason = '搜索倍率触边' if min(abs(best.scale-limits[0]), abs(best.scale-limits[1])) < .003 else ''
        return dict(scale=round(best.scale, 6), rotation=round(float(angle), 3), error=round(best.error, 7),
                    center=[round(v-margin, 4) for v in best.center], search=search, reason=reason,
                    elapsed_seconds=round(time.perf_counter()-started, 6))


def grade(result, thresholds):
    error = result['error']
    if error is None or not math.isfinite(error) or result.get('reason'):
        return '头不可测'
    if error <= thresholds['usable']:
        return '可用'
    return '只当辅助' if error <= thresholds['auxiliary'] else '头不可测'


def result_signature(result):
    return {k: v for k, v in result.items() if k != 'elapsed_seconds'}


def code_fingerprint(function):
    """不含源码行号/文件名，避免并行添加报告代码时inspect读错旧行号。"""
    def payload(code):
        def constant(value):
            if isinstance(value, types.CodeType):
                return payload(value)
            if isinstance(value, bytes):
                return dict(bytes=value.hex())
            if value is Ellipsis:
                return dict(ellipsis=True)
            if isinstance(value, tuple):
                return [constant(v) for v in value]
            if isinstance(value, frozenset):
                return dict(frozenset=[constant(v) for v in sorted(value, key=repr)])
            return value
        return dict(bytecode=code.co_code.hex(), constants=[constant(v) for v in code.co_consts],
                    names=code.co_names, variables=code.co_varnames,
                    argcount=code.co_argcount, kwonly=code.co_kwonlyargcount,
                    posonly=code.co_posonlyargcount, freevars=code.co_freevars,
                    cellvars=code.co_cellvars)
    return dict(code=payload(function.__code__), defaults=function.__defaults__, kwdefaults=function.__kwdefaults__)


def algorithm_hash():
    functions = [channels, build_template, resized, warped, sqdiff, Match.key, Matcher.__init__,
                 Matcher.warp, Matcher.search, Matcher.local_bounds, Matcher.fit, grade]
    data = dict(functions={f.__qualname__: code_fingerprint(f) for f in functions},
                weights=WEIGHTS.tolist(), match_fields=Match.__annotations__)
    return sha(json.dumps(data, sort_keys=True, ensure_ascii=True).encode())


def config_hash(cfg):
    return sha(json.dumps(cfg, sort_keys=True, ensure_ascii=True).encode())


def calibrate_character(task):
    out_text, cid = task
    out = Path(out_text)
    cfg = config_for(cid)
    manifest, item = snap_manifest(out, cid)
    idle, _ = snap_frame(out, item, manifest['clips']['idle'], 0)
    template = build_template(cfg, idle)
    matcher = Matcher(template)
    cases = []
    for scale in (.85, 1., 1.15):
        for angle in (-30., 0., 30.):
            side = max(256, math.ceil(max(template.mask.shape)*3.8))
            transform = cv2.getRotationMatrix2D(tuple(map(float, cfg['head_center'])), angle, scale)
            transform[:, 2] += np.array([side/2-cfg['head_center'][0], side/2-cfg['head_center'][1]])
            # 对完整 RGBA 原帧施加独立变换；不使用模板 warp 生成测试答案。
            transformed = Image.fromarray(cv2.warpAffine(np.asarray(idle), transform, (side, side), flags=cv2.INTER_LINEAR))
            result = matcher.fit(transformed, (side/2, side/2))
            relative = abs(result['scale']/scale-1) if result['scale'] is not None else 1.
            angle_error = abs((result['rotation']-angle+180)%360-180) if result['rotation'] is not None else 180.
            cases.append(dict(expected_scale=scale, expected_rotation=angle,
                              relative_scale_error=round(relative, 7), rotation_error=round(angle_error, 4),
                              passed=relative <= .02+1e-9, **result))
    first = matcher.fit(idle)
    second = matcher.fit(idle)
    deterministic = result_signature(first) == result_signature(second)
    real = []
    for action in ('idle', 'walk_forward', 'walk_back'):
        clip = manifest['clips'].get(action)
        if not clip:
            continue
        for i in sorted({0, len(clip['rects'])//2, len(clip['rects'])-1}):
            frame, _ = snap_frame(out, item, clip, i)
            result = matcher.fit(frame)
            real.append(dict(action=action, frame=i, **result))
    # 缺头对照保留躯干和四肢，检验是否误把其他身体部位当作头。
    removed = np.array(idle)
    x0, y0 = template.origin
    hh, ww = template.mask.shape
    removed[max(0, y0-4):y0+hh+4, max(0, x0-4):x0+ww+4] = 0
    negatives = [dict(kind='head_removed', **matcher.fit(Image.fromarray(removed))),
                 dict(kind='transparent', **matcher.fit(Image.new('RGBA', idle.size)))]
    positive_errors = [r['error'] for r in real+cases if r['error'] is not None]
    p95 = float(np.quantile(positive_errors, .95))
    synthetic_max = max(c['error'] or 0 for c in cases)
    negative_errors = [n['error'] for n in negatives if n['error'] is not None]
    negative_min = min(negative_errors, default=1.)
    # 保留原型0.18/0.25为上界；可用阈值由本角色真实/人工正例与缺头负例决定。
    usable = round(max(.04, min(.18, max(p95+.025, synthetic_max+.015), negative_min*.72)), 6)
    auxiliary = round(max(usable, min(.25, max(p95+.08, usable+.055), negative_min*.90)), 6)
    thresholds = dict(usable=usable, auxiliary=auxiliary)
    positive_false_unknown = sum(grade(r, thresholds) == '头不可测' for r in real)
    negative_false_usable = sum(grade(r, thresholds) == '可用' for r in negatives)
    report = dict(character=cid, measured_at=now(), manifest_sha256=item['manifest_sha256'],
                  algorithm_sha256=algorithm_hash(),
                  synthetic=cases, deterministic=deterministic, idle_repeat=first,
                  real_references=real, negatives=negatives, thresholds=thresholds,
                  threshold_basis=dict(positive_p95=round(p95, 7), synthetic_max=round(synthetic_max, 7),
                                       negative_min=round(negative_min, 7), real_unmeasurable=positive_false_unknown,
                                       negative_false_usable=negative_false_usable),
                  passed=bool(deterministic and all(c['passed'] for c in cases) and
                              abs(first['scale']-1.) < .00001 and not negative_false_usable))
    save_json(out / f'calibration/{cid}.json', report)
    print(f'校准 {cid}: 最大相对误差 {max(c["relative_scale_error"] for c in cases):.2%}，'
          f'可用≤{usable:.3f} / 辅助≤{auxiliary:.3f}，{"完成" if report["passed"] else "失败"}', flush=True)
    return report


def score_oracle_test():
    rng = np.random.default_rng(20261023)
    candidate = rng.integers(0, 2, (37, 41, 2)).astype(np.float32)
    t = rng.uniform(0, 1, (13, 11, 2)).astype(np.float32)
    mask = rng.integers(0, 2, (13, 11)).astype(np.float32)
    actual = sqdiff(candidate, t, mask)
    expected = sum(float(weight)*cv2.matchTemplate(candidate[..., k].copy(), t[..., k].copy(),
                    cv2.TM_SQDIFF, mask=mask) for k, weight in enumerate(WEIGHTS))/mask.sum()
    delta = float(np.max(np.abs(actual-expected)))
    assert delta < 2e-6, delta
    assert [grade(dict(error=e, reason=''), dict(usable=.18, auxiliary=.25))
            for e in (.18, .180001, .25, .250001, None)] == ['可用', '只当辅助', '只当辅助', '头不可测', '头不可测']
    return dict(masked_sqdiff_max_error=delta, grading_boundaries=True)


def calibrate(out, characters, workers):
    started = now()
    oracle = score_oracle_test()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        reports = list(pool.map(calibrate_character, [(str(out), cid) for cid in characters]))
    passed = all(r['passed'] for r in reports)
    summary = dict(started_at=started, finished_at=now(), passed=passed, oracle=oracle,
                   algorithm_sha256=algorithm_hash(), fingerprint_scheme='python-bytecode-v1',
                   maximum_relative_scale_error=max(c['relative_scale_error'] for r in reports for c in r['synthetic']),
                   characters={r['character']: dict(passed=r['passed'], thresholds=r['thresholds'],
                               deterministic=r['deterministic'], threshold_basis=r['threshold_basis']) for r in reports})
    save_json(out / 'calibration/summary.json', summary)
    if not passed:
        raise RuntimeError('人工变换或确定性校准失败；详情见 calibration，不继续普查')
    for report in reports:
        cfg = config_for(report['character'])
        cfg['thresholds'] = report['thresholds']
        cfg['calibration'] = dict(report=f'calibration/{report["character"]}.json',
                                  manifest_sha256=report['manifest_sha256'],
                                  maximum_relative_scale_error=max(r['relative_scale_error'] for r in report['synthetic']),
                                  basis='人工缩放旋转+idle/走路实帧误差P95+缺头负例；不作为美术硬门')
        save_json(CONFIG / f'{report["character"]}.json', cfg)
    if 'ultraman-leo' in characters:
        known_positive(out)
    print('校准完成；阈值已写入专属配置', flush=True)


def known_positive(out):
    cid = 'ultraman-leo'
    cfg = config_for(cid)
    manifest, item = snap_manifest(out, cid)
    if 'dash' not in manifest['clips']:
        return
    idle, _ = snap_frame(out, item, manifest['clips']['idle'], 0)
    matcher = Matcher(build_template(cfg, idle))
    rows = []
    for i in range(len(manifest['clips']['dash']['rects'])):
        frame, _ = snap_frame(out, item, manifest['clips']['dash'], i)
        result = matcher.fit(frame)
        rows.append(dict(frame=i, grade=grade(result, cfg['thresholds']), **result))
    save_json(out / 'calibration/leo-dash-known-positive.json',
              dict(character=cid, action='dash', manifest_sha256=item['manifest_sha256'],
                   algorithm_sha256=algorithm_hash(), reference='指挥已用六倍头部并排图确认冲刺头偏大；只复核本次快照', frames=rows))


CSV_FIELDS = ['action', 'frame', 'scale', 'rotation', 'error', 'grade', 'over_8_percent', 'over_12_percent',
              'center_x', 'center_y', 'search', 'reason', 'elapsed_seconds', 'frame_sha256',
              'texture_sha256', 'duplicate_of']


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def audit_character(task):
    out_text, cid = task
    out = Path(out_text)
    cfg = config_for(cid)
    started = now()
    manifest, item = snap_manifest(out, cid)
    idle, _ = snap_frame(out, item, manifest['clips']['idle'], 0)
    template = build_template(cfg, idle)
    matcher = Matcher(template)
    cache, rows = {}, []
    for action, clip in manifest['clips'].items():
        full_search = any(word in action for word in ('flip', 'roll', 'down', 'throw', 'dive', 'air_tech'))
        for i in range(len(clip['rects'])):
            frame, source_hash = snap_frame(out, item, clip, i)
            frame_hash = sha(str(frame.size).encode()+frame.tobytes())
            cache_key = (frame_hash, full_search)
            duplicate = ''
            if cache_key in cache:
                result, duplicate = cache[cache_key]
                result = dict(result, elapsed_seconds=0.)
            else:
                result = matcher.fit(frame, full_search=full_search)
                cache[cache_key] = (result.copy(), f'{action}#{i}')
            confidence = grade(result, cfg['thresholds'])
            scale = result['scale']
            row = dict(character=cid, action=action, frame=i, **result,
                       grade=confidence, frame_sha256=frame_hash, texture_sha256=source_hash,
                       duplicate_of=duplicate,
                       center_x=result['center'][0] if result['center'] else None,
                       center_y=result['center'][1] if result['center'] else None,
                       over_8_percent=bool(abs(scale-1) > .08+1e-8) if confidence == '可用' else None,
                       over_12_percent=bool(abs(scale-1) > .12+1e-8) if confidence == '可用' else None)
            rows.append(row)
        save_json(out / f'progress/{cid}.json', dict(character=cid, last_action=action,
                                                    measured=len(rows), total=item['frames'], updated_at=now()))
    usable = [r for r in rows if r['grade'] == '可用']
    summary = dict(character=cid, name=NAMES[cid], actions=len(manifest['clips']), frames=len(rows),
                   unique_fits=len(cache), usable=len(usable), auxiliary=sum(r['grade'] == '只当辅助' for r in rows),
                   unmeasurable=sum(r['grade'] == '头不可测' for r in rows),
                   median_scale=round(float(np.median([r['scale'] for r in usable])), 6) if usable else None,
                   over_8_percent=sum(bool(r['over_8_percent']) for r in rows),
                   over_12_percent=sum(bool(r['over_12_percent']) for r in rows),
                   max_seconds=max(r['elapsed_seconds'] for r in rows),
                   over_10_seconds=sum(r['elapsed_seconds'] > 10 for r in rows),
                   started_at=started, finished_at=now(), manifest_sha256=item['manifest_sha256'],
                   config_sha256=sha((CONFIG / f'{cid}.json').read_bytes()), thresholds=cfg['thresholds'])
    summary['algorithm_sha256'] = algorithm_hash()
    summary['config_semantic_sha256'] = config_hash(cfg)
    summary['fingerprint_scheme'] = 'python-bytecode-v1'
    save_json(out / f'results/{cid}.json', dict(summary=summary, frames=rows))
    write_csv(out / f'{cid}.csv', rows, CSV_FIELDS)
    print(f'普查 {cid}: {len(rows)} 帧，可用 {len(usable)}，超±8% {summary["over_8_percent"]}，'
          f'最长 {summary["max_seconds"]:.2f} 秒', flush=True)
    return summary


def audit(out, characters, workers):
    calibration = read_json(out / 'calibration/summary.json')
    if not calibration['passed']:
        raise RuntimeError('必须先完成校准')
    if calibration.get('fingerprint_scheme') == 'python-bytecode-v1' and calibration['algorithm_sha256'] != algorithm_hash():
        raise RuntimeError('算法已变化，不能沿用旧校准')
    for cid in characters:
        result = out / f'results/{cid}.json'
        if result.exists():
            saved = read_json(result)['summary']
            config_matches = (saved['config_semantic_sha256'] == config_hash(config_for(cid))) if 'config_semantic_sha256' in saved else (saved['config_sha256'] == sha((CONFIG/f'{cid}.json').read_bytes()))
            if saved.get('algorithm_sha256') != algorithm_hash() or not config_matches:
                raise RuntimeError(f'{cid} 的旧结果与当前算法/配置不同；请使用新输出目录，不能静默复用')
    todo = [cid for cid in characters if not (out / f'results/{cid}.json').exists()]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(audit_character, [(str(out), cid) for cid in todo]))
    summaries = [read_json(out / f'results/{cid}.json')['summary'] for cid in characters]
    save_json(out / 'summary.json', summaries)
    write_csv(out / 'summary.csv', summaries, ['character', 'name', 'actions', 'frames', 'unique_fits', 'usable',
              'auxiliary', 'unmeasurable', 'median_scale', 'over_8_percent', 'over_12_percent',
              'max_seconds', 'over_10_seconds', 'manifest_sha256'])


def measure(cid, image, center=None, rect=None, full_search=False):
    frame = image.convert('RGBA') if isinstance(image, Image.Image) else Image.open(image).convert('RGBA')
    if rect:
        frame = crop_frame(frame, rect)
    cfg = config_for(cid)
    result = Matcher(build_template(cfg)).fit(frame, center, full_search)
    result['grade'] = grade(result, cfg['thresholds'])
    result['character'] = cid
    return result


def action_ranking(all_results):
    ranking = []
    for cid, document in all_results.items():
        groups = {}
        for row in document['frames']:
            groups.setdefault(row['action'], []).append(row)
        for action, rows in groups.items():
            usable = [r for r in rows if r['grade'] == '可用']
            outliers = [r for r in usable if r['over_8_percent']]
            if not outliers:
                continue
            severe = sum(bool(r['over_12_percent']) for r in usable)
            worst = max(outliers, key=lambda r: abs(r['scale']-1))
            median = float(np.median([abs(r['scale']-1) for r in outliers]))
            # 严重帧数量优先，再比较超差帧中位偏差与最坏偏差。
            ranking.append(dict(character=cid, action=action, total_frames=len(rows), usable=len(usable),
                                over_8_percent=len(outliers), over_12_percent=severe,
                                median_outlier_deviation=round(median, 6), worst_frame=worst['frame'],
                                worst_scale=worst['scale'], worst_error=worst['error'],
                                worst_deviation=round(abs(worst['scale']-1), 6),
                                frames='; '.join(f'#{r["frame"]}={r["scale"]:.4f}' for r in outliers)))
    ranking.sort(key=lambda r: (-r['over_12_percent'], -r['median_outlier_deviation'],
                                -r['worst_deviation'], -r['over_8_percent'], r['character'], r['action']))
    for i, row in enumerate(ranking):
        row['priority'] = i+1
    return ranking


def head_crop(frame, center, width, height):
    cx, cy = center
    left, top = round(cx-width/2), round(cy-height/2)
    crop = frame.crop((left, top, left+width, top+height))
    background = Image.new('RGBA', (width, height), (43, 49, 60, 255))
    background.alpha_composite(crop)
    return background.convert('RGB').resize((width*8, height*8), Image.Resampling.NEAREST)


def strip_character(out, cid, document):
    cfg = config_for(cid)
    manifest, item = snap_manifest(out, cid)
    idle, _ = snap_frame(out, item, manifest['clips']['idle'], 0)
    template = build_template(cfg, idle)
    th, tw = template.mask.shape
    tx, ty = template.center
    width = math.ceil(max(tx, tw-tx)*1.55+5)*2
    height = math.ceil(max(ty, th-ty)*1.55+5)*2
    cellw, cellh = width*8+16, height*8+80
    groups = {}
    for row in document['frames']:
        if row['scale'] is not None and row['grade'] != '头不可测' and abs(row['scale']-1) > .08+1e-8:
            groups.setdefault(row['action'], []).append(row)
    ordered = sorted(groups, key=lambda action: (-max(abs(r['scale']-1) for r in groups[action]), action))
    rows_to_draw = []
    for action in ordered:
        group = sorted(groups[action], key=lambda r: (-abs(r['scale']-1), r['frame']))
        rows_to_draw.extend(group)
    columns = max(4, math.ceil(len(rows_to_draw)*cellh/25000)+1)
    # 连续排列同动作各帧，每行首格重放idle；不为短动作留下整行空白。
    layout = [rows_to_draw[start:start+columns-1] for start in range(0, len(rows_to_draw), columns-1)]
    if not layout:
        layout = [[]]
    panel = Image.new('RGB', (cellw*columns, 120+cellh*len(layout)), (25, 29, 36))
    draw = ImageDraw.Draw(panel)
    draw.text((14, 7), f'{NAMES[cid]} / {cid}  已装帧头部超差候选 ×8', font=font(30), fill='white')
    draw.text((14, 47), f'绿字=可用，橙字=只当辅助；比例相对idle #0；同动作分组、偏差从大到小。', font=font(24), fill=(211, 218, 228))
    draw.text((14, 80), '含角/冠，保持原生比例；只当辅助不计入汇总超差数；不自动拒收或返修。', font=font(23), fill=(211, 218, 228))
    for row_index, group in enumerate(layout):
        y = 120+row_index*cellh
        panel.paste(head_crop(idle, cfg['head_center'], width, height), (8, y+72))
        draw.text((9, y+3), 'idle #0  1.0000  基准', font=font(23), fill=(170, 228, 255))
        if not group:
            draw.text((cellw+10, y+35), '没有可用/辅助的超±8%读数', font=font(24), fill='white')
        for column, record in enumerate(group, 1):
            action = record['action']
            frame, _ = snap_frame(out, item, manifest['clips'][action], record['frame'])
            x = column*cellw+8
            panel.paste(head_crop(frame, record['center'], width, height), (x, y+72))
            color = (100, 243, 171) if record['grade'] == '可用' else (255, 185, 98)
            draw.text((x, y+3), f'{action} #{record["frame"]}', font=font(22), fill='white')
            draw.text((x, y+33), f'{record["scale"]:.4f}  {record["rotation"]:+.1f}°  err {record["error"]:.3f}  {record["grade"]}', font=font(20), fill=color)
    directory = out / 'outliers'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{cid}-heads-8x.png'
    panel.save(path)
    jpeg_preview(panel, directory / f'{cid}-preview.jpg')
    print(f'条带 {cid}: {len(rows_to_draw)} 个候选（含辅助），{panel.width}×{panel.height}', flush=True)
    return dict(character=cid, frames=len(rows_to_draw), usable=sum(r['grade'] == '可用' for r in rows_to_draw),
                auxiliary=sum(r['grade'] == '只当辅助' for r in rows_to_draw),
                path=path.relative_to(out).as_posix(), dimensions=list(panel.size))


def top_action_previews(out, all_results, ranking):
    """给指挥的轻量定位图；原始8倍图仍保留在outliers目录。"""
    directory = out / 'priority-previews'
    directory.mkdir(parents=True, exist_ok=True)
    for start in range(0, min(20, len(ranking)), 4):
        panel = Image.new('RGB', (768, 4*270), (28, 32, 41))
        draw = ImageDraw.Draw(panel)
        for j, ranked in enumerate(ranking[start:start+4]):
            cid, action = ranked['character'], ranked['action']
            cfg = config_for(cid)
            manifest, item = snap_manifest(out, cid)
            idle, _ = snap_frame(out, item, manifest['clips']['idle'], 0)
            chosen = sorted([r for r in all_results[cid]['frames'] if r['action'] == action and r['grade'] == '可用' and r['over_8_percent']],
                            key=lambda r: -abs(r['scale']-1))[:2]
            y = j*270
            draw.text((10, y+3), f'{ranked["priority"]}. {NAMES[cid]} {action}：超12% {ranked["over_12_percent"]}帧，超8% {ranked["over_8_percent"]}帧', font=font(19), fill='white')
            center = cfg['head_center']
            template = build_template(cfg, idle)
            radius = math.ceil(max(template.mask.shape)*.9)
            entries = [('idle #0 1.000', idle, center)]
            for row in chosen:
                frame, _ = snap_frame(out, item, manifest['clips'][action], row['frame'])
                entries.append((f'#{row["frame"]} {row["scale"]:.4f} / err {row["error"]:.3f}', frame, row['center']))
            for column, (label, frame, head_center) in enumerate(entries):
                crop = head_crop(frame, head_center, radius*2, radius*2)
                crop = crop.resize((206, 206), Image.Resampling.NEAREST)
                panel.paste(crop, (column*254+20, y+55))
                draw.text((column*254+13, y+30), label, font=font(17), fill=(155, 231, 207))
        jpeg_preview(panel, directory / f'top-20-{start//4+1}.jpg')


def provenance(out, characters):
    snap = read_json(out / 'snapshot.json')
    drift = {}
    for cid in characters:
        item = snap['characters'][cid]
        current_manifest = ROOT / item['manifest_path']
        current_sha = sha(current_manifest.read_bytes()) if current_manifest.exists() else None
        changed = []
        for source, digest in item['textures'].items():
            path = ROOT / source
            current = sha(path.read_bytes()) if path.exists() else None
            if current != digest:
                changed.append(dict(path=source, captured_sha256=digest, current_sha256=current))
        drift[cid] = dict(manifest_changed=current_sha != item['manifest_sha256'],
                          manifest_captured_sha256=item['manifest_sha256'], manifest_current_sha256=current_sha,
                          textures_changed=changed)
        config_copy = out / f'inputs/configs/{cid}.json'
        config_copy.parent.mkdir(exist_ok=True, parents=True)
        config_copy.write_bytes((CONFIG / f'{cid}.json').read_bytes())
    result = dict(reported_at=now(), snapshot_sha256=sha((out/'snapshot.json').read_bytes()),
                   tool_sha256=sha(Path(__file__).read_bytes()), algorithm_sha256=algorithm_hash(),
                   python=sys.version, numpy=np.__version__, pillow=Image.__version__, opencv=cv2.__version__,
                   cv2_threads=cv2.getNumThreads(), opencl=False, forge=backend_info(),
                   input_art_source='existing', generation_requests=0, drift=drift)
    save_json(out / 'provenance.json', result)
    return result


def write_readme(out, all_results, ranking, origin, strips):
    snap = read_json(out / 'snapshot.json')
    calibration = read_json(out / 'calibration/summary.json')
    summaries = [doc['summary'] for doc in all_results.values()]
    totals = {key: sum(row[key] for row in summaries) for key in
              ('actions', 'frames', 'unique_fits', 'usable', 'auxiliary', 'unmeasurable', 'over_8_percent', 'over_12_percent')}
    started = min(s['started_at'] for s in summaries)
    finished = max(s['finished_at'] for s in summaries)
    maximum = max(s['max_seconds'] for s in summaries)
    changed = [NAMES[c] for c, value in origin['drift'].items() if value['manifest_changed'] or value['textures_changed']]
    lines = ['# 十二角色已装帧整头配准普查', '',
        f'快照时间：{snap["started_at"]} → {snap["finished_at"]}。配准时间：{started} → {finished}。报告时间：{origin["reported_at"]}。时间均含时区。', '',
        f'本次只读当时 manifest 中的 {totals["actions"]} 个动作、{totals["frames"]} 个帧条目；相同像素/搜索域复用结果，实际配准 {totals["unique_fits"]} 次。'
        '没有生图、重装、缩放或改写任何角色资源、manifest、content。', '',
        f'可用读数 {totals["usable"]}，只当辅助 {totals["auxiliary"]}，头不可测 {totals["unmeasurable"]}。'
        f'可用读数中超±8% {totals["over_8_percent"]} 帧，超±12% {totals["over_12_percent"]} 帧。'
        '计数按清单条目，不把共用动画条目去重成素材数。超差是复核/返修候选，不是自动美术拒收结论。', '',
        '## 怎么用', '', '从项目根目录运行，固定使用项目解释器：', '', '```bash',
        "py=.venv/bin/python",
        "out=reports/review/YYYY-MM-DD-head-fit-audit-new",
        '"$py" tools/rebuild/shared/head_fit.py snapshot --out "$out"',
        '"$py" tools/rebuild/shared/head_fit.py templates --out "$out"',
        '"$py" tools/rebuild/shared/head_fit.py calibrate --out "$out" --workers 4',
        '"$py" tools/rebuild/shared/head_fit.py audit --out "$out" --workers 4',
        '"$py" tools/rebuild/shared/head_fit.py report --out "$out"', '```', '',
        '`snapshot` 拒绝覆盖已有快照。`calibrate` 在人工变换/确定性校准成功后，仅更新 art/production/head_fit/ 下的专属配置阈值。'
        '`audit` 可从已完成角色续跑；算法或配置指纹变化时拒绝复用旧结果。各命令支持 `--characters <id...>`。'
        '工具不启动Godot；无需占用Godot锁，也不录游戏影片。', '',
        '单帧用法（rect为图集上的x、y、宽、高；center为裁出格子后的原生坐标，可省略）：', '',
        '```bash', '"$py" tools/rebuild/shared/head_fit.py measure --characters ultraman-leo --image assets/fighters/ultraman-leo/animations/idle/atlas.png --rect 0 0 192 192 --center 100 56', '```', '',
        '作为库可调用 `measure(character_id, image, center=None, rect=None, full_search=False)`，返回scale、rotation、error、center、grade。'
        '正角度是OpenCV图像坐标中的逆时针；scale=1.15表示头比idle模板大15%，不是建议的资源缩放系数。', '',
        '## 方法与配置', '',
        '每个角色用快照中已装 idle #0 的整头作刚体模板，包含角、冠、头镖；按项背→喉的切线去掉颈部。'
        '切线以上取头中心连通域，排除抬起的手；内隆嘎另排除会甩动的长须。模板保留背景环。'
        '配置包含idle贴图及格子、头中心、颈部切线、模板半径、背景圈宽、上采样倍数、搜索范围和校准阈值。', '',
        '通道为二值Alpha和亮度<0.30的暗色特征，权重1:0.7。误差为带掩码加权平方差/掩码面积，越小越接近。'
        '先在半分辨率上以0.05倍率/15°粗搜，保留多个极小值，再以原生分辨率细搜，最后在2倍上采样后以0.0025倍率/0.5°细化。'
        '搜索倍率0.65–1.50，旋转覆盖一整圈；倍率触边一律标头不可测。', '',
        '头中心先按idle头相对主体外框的位置估计。低分匹配会扩到全帧上部，翻滚/倒地/投技/俯冲/空中受身搜整个主体。'
        '外框、中心点只决定搜索域，不参与尺寸读数。搜索窗按头中心到模板最远角的距离展开，避免含角模板的中心偏置截断旋转结果。', '',
        '模板审片：[第1组](templates/templates-1.jpg) · [第2组](templates/templates-2.jpg) · [第3组](templates/templates-3.jpg)。'
        'JPEG均为质量80、宽≤768、≤150KB；每角色完整8倍PNG和3张原比例拼图保存在 templates/。', '',
        '## 校准与误差分档', '',
        f'对12个角色的完整idle RGBA帧独立施加0.85、1.00、1.15缩放与−30°、0°、+30°的全部组合。'
        f'最大相对倍率误差 {calibration["maximum_relative_scale_error"]:.2%}（要求≤2%）。'
        '每个角色重复配准结果（不含耗时）完全相同，idle自配准均为1.0000。'
        f'平方差展开与OpenCV带掩码SQDIFF的最大数值差 {calibration["oracle"]["masked_sqdiff_max_error"]:.3g}。', '',
        '真实参考取已装idle、前走、后走的首/中/末帧。这些帧用于校准匹配误差的分布，不预设它们的尺寸一定合格。'
        '另以删去头部但保留身体的副本和透明帧作负例。完整记录见 [校准总表](calibration/summary.json) 和 calibration/<角色>.json。', '',
        '阈值逐角色由正例误差P95、人工变换最大误差及缺头负例共同决定，0.18/0.25为原型上界。'
        '可用阈值=min(0.18, max(P95+0.025, 人工最大误差+0.015), 缺头误差×0.72)，最低0.04；'
        '辅助阈值=min(0.25, max(P95+0.08, 可用阈值+0.055), 缺头误差×0.90)，并不低于可用阈值。'
        '空帧、倍率触边和分数过高均为头不可测；可用/辅助按误差阈值分档。', '',
        '| 角色 | 可用误差上限 | 辅助误差上限 | 校准最大相对误差 | 真实参考不可测 |',
        '| --- | ---: | ---: | ---: | ---: |']
    for cid in all_results:
        cal = read_json(out / f'calibration/{cid}.json')
        lines.append(f'| {NAMES[cid]} | {cal["thresholds"]["usable"]:.4f} | {cal["thresholds"]["auxiliary"]:.4f} | '
                     f'{max(c["relative_scale_error"] for c in cal["synthetic"]):.2%} | {cal["threshold_basis"]["real_unmeasurable"]} |')
    positive_path = out / 'calibration/leo-dash-known-positive.json'
    if positive_path.exists():
        positive = read_json(positive_path)
        lines += ['', '雷欧冲刺的已知偏大实帧对照：'+ '、'.join(
            f'#{r["frame"]}={r["scale"]:.4f}（{r["grade"]}）' for r in positive['frames'])+
            '。指挥原型曾读到约1.20–1.27并人工确认偏大；这里报告本次快照的逐帧值，不把历史范围当成所有相位的预期值。'
            '原始读数见 [已知偏大对照](calibration/leo-dash-known-positive.json)。']
    lines += ['', '首轮校准暴露的模板中心偏置/搜索窗截断问题及失败记录保留在 calibration/initial-window-diagnostic/；'
              '修正搜索窗后才进行本次全量普查。没有修改精灵以迁就测量。', '',
              '## 每角色普查结论', '',
              '| 角色 | 清单帧数 | 可用/辅助/不可测 | 可用中位数 | 超±8% | 超±12% | 主要复核动作 | 明细与条带 |',
              '| --- | ---: | --- | ---: | ---: | ---: | --- | --- |']
    for cid, document in all_results.items():
        s = document['summary']
        med = f'{s["median_scale"]:.4f}' if s['median_scale'] is not None else '无'
        priorities = [r['action'] for r in ranking if r['character'] == cid][:3]
        top = '、'.join(priorities) or '未检出可用读数超差'
        lines.append(f'| {NAMES[cid]} | {s["frames"]} | {s["usable"]}/{s["auxiliary"]}/{s["unmeasurable"]} | {med} | '
                     f'{s["over_8_percent"]} | {s["over_12_percent"]} | {top} | [CSV]({cid}.csv) · [8倍条带](outliers/{cid}-heads-8x.png) |')
    lines += ['', '辅助及不可测帧不进入中位数和超差计数。条带另外保留辅助档的超差候选并用橙字标注，便于指挥复核；'
              '每行idle在最前，同动作放在一起，动作间及组内按绝对偏差从大到小排列。'
              '清单中即使多个动作引用相同像素也逐项报告，不改动画共用关系。', '',
              '## 最该先复核、再决定返修的前20个动作', '',
              '只从“可用且超±8%”读数排序：先看超±12%帧数，再看超差帧的中位偏差、最坏偏差和超差帧数。'
              '头饰视角变化、转背、遮挡仍可能造成刚体误配，指挥应先确认条带里的位置和姿态，再安排返修。'
              '这份排名不覆盖只有不可测读数的动作，也不代表不可测动作质量更好。', '',
              '| 优先级 | 角色/动作 | 可用/总帧 | 超±8%/±12% | 最坏帧 | 最坏比例 | 误差 |',
              '| ---: | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in ranking[:20]:
        lines.append(f'| {r["priority"]} | {NAMES[r["character"]]} / {r["action"]} | {r["usable"]}/{r["total_frames"]} | '
                     f'{r["over_8_percent"]}/{r["over_12_percent"]} | #{r["worst_frame"]} | {r["worst_scale"]:.4f} | {r["worst_error"]:.4f} |')
    lines += ['', '完整动作排名和超差帧号见 [priority-actions.csv](priority-actions.csv)。'
              '轻量定位图：'+' · '.join(f'[第{i}组](priority-previews/top-20-{i}.jpg)' for i in range(1, math.ceil(min(20,len(ranking))/4)+1))+'。', '',
              '## 时间、指纹与并行安装变化', '',
              '全部输入贴图按实际文件SHA256去重保存在 inputs/textures/，原manifest保存在 inputs/<角色>/manifest.json。'
              '每份清单和贴图在捕获时连续读取两遍并检查一致性；整个项目不加锁，因此不是跨文件的同一时刻事务快照。'
              '后续校准、配准和条带全部读取保存的字节，避免运行期间出现一半旧图、一半新图。'
              '下表是本轮普查实际使用的清单指纹；逐贴图哈希、捕获时刻见 [snapshot.json](snapshot.json)。', '',
              '| 角色 | manifest SHA256 |', '| --- | --- |']
    for cid in all_results:
        lines.append(f'| {NAMES[cid]} / {cid} | `{snap["characters"][cid]["manifest_sha256"]}` |')
    lines += ['', ('出报告时检测到并行安装已变化的角色：'+ '、'.join(changed)+'。这些新版本不在本次读数里。') if changed else '出报告时复核输入清单与贴图，未发现相对捕获快照的变化。',
              '变化的文件与新旧哈希见 [provenance.json](provenance.json) 的 drift。配置快照在 inputs/configs/，'
              '记录了配准算法、工具和配置指纹，以及Python/NumPy/Pillow/OpenCV/Forge版本。', '',
              '算法指纹使用不含文件名/行号的递归字节码、常量和默认参数，配置另有不受换行符影响的语义指纹。'
              '本轮运行期间增补了报告排版代码，旧inspect源码行号指纹不可靠；已逐函数对照首个已测试提交c9917388b确认实际配准代码完全一致。'
              '指纹订正只修改元数据，不修改读数；见 algorithm-fingerprint-proof.json 与 fingerprint-migration.json。', '',
              '## 性能与限制', '',
              f'固定OpenCV单线程、禁用OpenCL；最多4个工作进程。本机实测最慢单帧 {maximum:.3f} 秒，'
              f'超过10秒的实际配准 {sum(s["over_10_seconds"] for s in summaries)} 帧。'
              '每行elapsed_seconds为墙钟耗时；相同像素和搜索域复用结果记0并在duplicate_of标出原始条目。', '',
              '刚体模板不适合大幅转背、头部透视形变、冠角改变投影、严重遮挡或脸部表情重画。'
              '只当辅助和头不可测必须改看原图/骨长/同倍率条带，不可拿极端比例自动挡帧。'
              '即便分数可用，躯干或腿长仍可能画错；本工具只测头，不能替代身体尺寸和动作姿态审查。'
              '±8%附近还存在原生像素离散和至多约2%的合成测量误差，需要结合条带判断，不能机械截断。', '',
              '本轮素材来源为existing，生成请求为0。forge-doctor.json保留工具探测原始结果；'
              '其中通用媒体路线探测不读取本项目的独立生图配置，也不是本轮所需能力。'
              '本轮仅使用现有图像、NumPy、Pillow、OpenCV和Forge的Alpha接口。', '']
    (out / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


def report(out, characters):
    # 保留来源manifest/config原始字节与相应SHA；继承根目录PNG的LFS规则。
    (out / '.gitattributes').write_text(
        '*.json -text whitespace=cr-at-eol\n*.csv -text whitespace=cr-at-eol\ninputs/** -text -whitespace\n',
        encoding='utf-8', newline='\n')
    all_results = {cid: read_json(out / f'results/{cid}.json') for cid in characters}
    ranking = action_ranking(all_results)
    write_csv(out / 'priority-actions.csv', ranking, ['priority', 'character', 'action', 'total_frames', 'usable',
               'over_8_percent', 'over_12_percent', 'median_outlier_deviation', 'worst_frame', 'worst_scale',
               'worst_error', 'worst_deviation', 'frames'])
    strips = [strip_character(out, cid, doc) for cid, doc in all_results.items()]
    save_json(out / 'strips.json', strips)
    top_action_previews(out, all_results, ranking)
    origin = provenance(out, characters)
    write_readme(out, all_results, ranking, origin, strips)
    print('README、汇总、动作优先级和头部条带已写入', out, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['snapshot', 'templates', 'calibrate', 'audit', 'measure', 'report'])
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    ap.add_argument('--characters', nargs='+', choices=IDS, default=list(IDS))
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--image', type=Path)
    ap.add_argument('--center', nargs=2, type=float)
    ap.add_argument('--rect', nargs=4, type=int)
    ap.add_argument('--full-search', action='store_true')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.command == 'snapshot':
        snapshot(args.out, args.characters)
    elif args.command == 'templates':
        templates(args.out, args.characters)
    elif args.command == 'calibrate':
        calibrate(args.out, args.characters, args.workers)
    elif args.command == 'audit':
        audit(args.out, args.characters, args.workers)
    elif args.command == 'measure':
        if args.image is None or len(args.characters) != 1:
            ap.error('measure 需要 --image 和单个 --characters')
        print(json.dumps(measure(args.characters[0], args.image, args.center, args.rect, args.full_search),
                         ensure_ascii=False, allow_nan=False))
    elif args.command == 'report':
        report(args.out, args.characters)


if __name__ == '__main__':
    main()
