"""提取超差帧的干净高分原图与坐标映射，供人工量身体；不改运行资源。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
import collections
import hashlib
import math
from pathlib import Path
Path = _LayoutProjectPath

import cv2
import numpy as np
from PIL import Image, ImageDraw

import head_fit as hf
from forge_backend import backend_info, binarize_alpha
from pilot_polish_audit import ART, IDS, OLD, OUT, ROOT

AUDIT = OUT / 'audit'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frame(cid, action, index):
    manifest, item = hf.snap_manifest(AUDIT, cid)
    return hf.snap_frame(AUDIT, item, manifest['clips'][action], index)[0]


def normalized(source):
    data = {}
    for cid in IDS:
        doc = hf.read_json(source / f'results/{cid}.json')
        idle = [r['scale'] for r in doc['frames'] if r['action'] == 'idle' and r['grade'] == '可用']
        median = float(np.median(idle))
        if not idle:
            raise ValueError(f'{cid} 缺少可用idle')
        rows = []
        for original in doc['frames']:
            r = dict(original)
            r['idle_median'] = median
            r['normalized_head'] = r['scale'] / median if r['scale'] is not None else None
            r['normalized_outlier'] = (r['grade'] == '可用' and abs(r['normalized_head'] - 1) > .08 + 1e-8)
            rows.append(r)
        data[cid] = {'idle_median': median, 'frames': rows, 'summary': doc['summary']}
    return data


def record_for(cid, action, index, installed):
    manifest, _ = hf.snap_manifest(AUDIT, cid)
    clip = manifest['clips'][action]
    path = ROOT / clip['head_qa']
    if not path.is_file() and cid == 'gomora':
        fallback = ROOT / f'art/fighters/gomora/stage4/pilot/gomora/specials/ready/animations/{action}/head-qa.json'
        if fallback.is_file():
            path = fallback
    rows = hf.read_json(path)['frames']
    # 序列切片和别名先按精灵实际像素选来源，不能盲用动作内索引。
    matches = []
    for q in rows:
        image_path = path.parent / q['image']
        if not image_path.is_file():
            continue
        with Image.open(image_path) as im:
            im = im.convert('RGBA')
            if im.size == installed.size and im.tobytes() == installed.tobytes():
                matches.append(q)
    if matches:
        q = dict(matches[0])
        q['qa_native_match'] = '逐像素一致'
    elif index < len(rows):
        q = dict(rows[index])
        q['qa_native_match'] = '顺序初值；必须由整人Alpha配准复核'
    else:
        raise ValueError(f'{cid}/{action}#{index}: 无法定位来源')
    q['qa_path'] = path.relative_to(ROOT).as_posix()
    if q.get('raw'):
        # 远程/必杀旧记录的source指原生中间帧，raw才是未经后处理的GPT原图。
        q['source'] = q['raw']
        q['source_bounds'] = q.get('raw_bounds')
        metadata = hf.read_json((ROOT / q['raw']).with_name('raw.metadata.json'))
        q['source_sha256'] = metadata['image_sha256']
    return q


def mask(image):
    return (np.asarray(image.convert('RGBA'))[..., 3] >= 128).astype(np.float32)


def fit_source(source, native, initial, known=None, raw_bounds=None):
    """完整人物Alpha的等比配准，仅用来把原图量尺换算到已装帧。"""
    raw = mask(source)
    if raw_bounds:
        # 多帧原图的相邻人物不能被算作本人的配准残差；这里只限制测量域。
        sx, sy, se, sb = raw_bounds
        selected = np.zeros_like(raw)
        selected[sy:sb, sx:se] = raw[sy:sb, sx:se]
        raw = selected
    target = mask(native)
    bx, by, ex, ey = native.getchannel('A').getbbox()
    patch = target[by:ey, bx:ex]
    best = None
    for factor in initial * np.linspace(.90, 1.10, 41):
        small = cv2.resize(raw, None, fx=float(factor), fy=float(factor), interpolation=cv2.INTER_AREA)
        pad = max(patch.shape) + 8
        field = np.pad(small, pad)
        score = cv2.matchTemplate(field, patch, cv2.TM_SQDIFF)
        _, _, loc, _ = cv2.minMaxLoc(score)
        tx, ty = bx - (loc[0] - pad), by - (loc[1] - pad)
        warp = cv2.warpAffine(raw, np.array([[factor, 0, tx], [0, factor, ty]], np.float32), native.size)
        overlap = np.minimum(warp[by:ey, bx:ex], patch).sum()
        union = np.maximum(warp[by:ey, bx:ex], patch).sum()
        iou = float(overlap / max(union, 1))
        if best is None or iou > best['iou']:
            best = {'scale': float(factor), 'translation': [float(tx), float(ty)], 'iou': iou}
    if known:
        factor, tx, ty = known
        warp = cv2.warpAffine(raw, np.array([[factor, 0, tx], [0, factor, ty]], np.float32), native.size)
        iou = float(np.minimum(warp[by:ey, bx:ex], patch).sum() /
                    max(np.maximum(warp[by:ey, bx:ex], patch).sum(), 1))
        if iou >= best['iou']:
            best = {'scale': factor, 'translation': [tx, ty], 'iou': iou, 'known_transform': True}
    factor = best['scale']
    tx, ty = best['translation']
    best['source_crop'] = [max(0, math.floor((bx - tx) / factor) - 3),
                           max(0, math.floor((by - ty) / factor) - 3),
                           min(source.width, math.ceil((ex - tx) / factor) + 3),
                           min(source.height, math.ceil((ey - ty) / factor) + 3)]
    return best


def prepare(use_old=False):
    source = OLD if use_old else AUDIT
    data = normalized(source)
    cache_path = ART / 'body-source-map.json'
    previous = hf.read_json(cache_path) if cache_path.exists() else {}
    cached = {r['frame_sha256']: r for r in previous.get('entries', [])
              if previous.get('mapping_version') == 2}
    entries = []
    duplicates = {}
    for cid in IDS:
        manifest, item = hf.snap_manifest(AUDIT, cid)
        for r in data[cid]['frames']:
            if not r['normalized_outlier']:
                continue
            native, _ = hf.snap_frame(AUDIT, item, manifest['clips'][r['action']], r['frame'])
            actual = hashlib.sha256(str(native.size).encode() + native.tobytes()).hexdigest()
            if actual != r['frame_sha256']:
                raise ValueError(f'{cid} 当前像素与排程读数不同，不能沿用旧排程')
            key = (cid, actual)
            alias = f'{r["action"]}#{r["frame"]}'
            if key in duplicates:
                entries[duplicates[key]]['aliases'].append(alias)
                continue
            if actual in cached:
                row = dict(cached[actual], number=len(entries), aliases=[alias])
                entries.append(row)
                duplicates[key] = len(entries) - 1
                continue
            q = record_for(cid, r['action'], r['frame'], native)
            src = ROOT / q['source']
            if sha(src) != q['source_sha256']:
                raise ValueError(f'干净原图指纹失配: {src}')
            raw = Image.open(src).convert('RGBA')
            binarize_alpha(raw)
            factor = q.get('scale', q.get('shared_scale'))
            known = None
            if 'source_bounds' in q and 'offset' in q:
                sb, offset = q['source_bounds'], q['offset']
                known = (factor, offset[0] - sb[0] * factor, offset[1] - sb[1] * factor)
            fit = fit_source(raw, native, factor, known, q.get('source_bounds'))
            number = len(entries)
            row = {'number': number, 'character': cid, 'action': r['action'], 'frame': r['frame'],
                   'aliases': [alias], 'frame_sha256': actual, 'head_before': r['normalized_head'],
                   'source': q['source'], 'source_sha256': q['source_sha256'],
                   'source_dimensions': list(raw.size), 'source_to_installed': fit,
                   'qa_path': q['qa_path'], 'qa_native_match': q['qa_native_match']}
            entries.append(row)
            duplicates[key] = number
            hf.save_json(cache_path, {'mapping_version': 2, 'entries': entries, 'in_progress': True})
            print(f'来源 {number:03} {cid}/{alias} IoU={fit["iou"]:.3f}', flush=True)
    hf.save_json(ART / 'body-source-map.json', {'mapping_version': 2, 'art_source': 'existing', 'backend': backend_info(),
                 'scheduling_readings': str(source.relative_to(ROOT)), 'entries': entries})
    plates(entries)
    print(f'人工身体量尺排程：{len(entries)}个不同已装帧；{math.ceil(len(entries) / 6)}张轻量图')


def plates(entries):
    folder = ART / 'body-panels'
    folder.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(entries), 6):
        sheet = Image.new('RGB', (768, 680), '#242a34')
        draw = ImageDraw.Draw(sheet)
        for j, r in enumerate(entries[start:start + 6]):
            x, y = j % 3 * 256, j // 3 * 340
            draw.text((x + 4, y + 3), f'{r["number"]:03} {hf.NAMES[r["character"]]} {r["action"]} #{r["frame"]}',
                      font=hf.font(12), fill='white')
            fit = r['source_to_installed']
            draw.text((x + 4, y + 21), f'H {r["head_before"]:.3f}  原图→已装IoU {fit["iou"]:.3f}',
                      font=hf.font(12), fill='#ffdd88')
            raw = Image.open(ROOT / r['source']).convert('RGBA')
            bounds = fit['source_crop']
            cut = raw.crop(bounds)
            scale = min(244 / cut.width, 278 / cut.height)
            target = (max(1, round(cut.width * scale)), max(1, round(cut.height * scale)))
            small = cut.resize(target, Image.Resampling.LANCZOS)
            px, py = x + (256 - target[0]) // 2, y + 43 + (278 - target[1]) // 2
            sheet.paste(small, (px, py), small)
            # 图格坐标是人工输入单位；保存原图坐标的反变换，读数仍量在原图。
            r['panel'] = {'path': (folder / f'body-{start // 6:02}.jpg').relative_to(ROOT).as_posix(),
                          'tile_origin': [x, y], 'raw_crop': bounds,
                          'draw_origin': [px - x, py - y], 'draw_size': list(target),
                          'display_per_source': [target[0] / cut.width, target[1] / cut.height]}
            for xx in range(0, 256, 40):
                draw.text((x + xx, y + 322), str(xx), font=hf.font(10), fill='#b7bfcc')
            for yy in range(60, 321, 40):
                draw.text((x + 1, y + yy), str(yy), font=hf.font(10), fill='#b7bfcc')
        hf.jpeg_preview(sheet, folder / f'body-{start // 6:02}.jpg')
    record = hf.read_json(ART / 'body-source-map.json')
    record['entries'] = entries
    hf.save_json(ART / 'body-source-map.json', record)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schedule-from-old', action='store_true')
    args = parser.parse_args()
    prepare(args.schedule_from_old)
