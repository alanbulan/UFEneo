"""只在开发目录生成完整人物等比缩放试算，并重新配准候选头部。"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

from concurrent.futures import ProcessPoolExecutor
import hashlib
import math

import numpy as np
from PIL import Image

import head_fit as hf
from forge_backend import backend_info, binarize_alpha
from pilot_polish_audit import ART, IDS, OUT, ROOT
from pilot_polish_prepare import normalized

AUDIT = OUT / 'audit'


def anchor(manifest, clip, i):
    if 'anchors' in clip:
        return list(clip['anchors'][i])
    if 'anchor' in clip:
        return list(clip['anchor'])
    w, h = clip['rects'][i][2:]
    return [w / 2, clip.get('anchor_y', manifest.get('anchor', [w / 2, h - 8])[1])]


def pixel_sha(im):
    return hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest()


def task_measure(task):
    cid, path, center, full, median = task
    result = hf.measure(cid, ROOT / path, center=center, full_search=full)
    result['normalized_head'] = result['scale'] / median if result['scale'] is not None else None
    return result


def main():
    readings = normalized(AUDIT)
    plan = {'schema': 1, 'art_source': 'existing', 'generated_requests': 0,
            'installed': False, 'approval': '待指挥审查；不构成安装授权',
            'method': '仅对可用且归一头超±8%帧按1/归一读数整帧等比缩放；最近邻；保留根点；不改部件或颜色',
            'backend': backend_info(), 'characters': {}}
    jobs, targets = [], []
    for cid in IDS:
        manifest, item = hf.snap_manifest(AUDIT, cid)
        records = {(r['action'], r['frame']): r for r in readings[cid]['frames']}
        idle_frames = [hf.snap_frame(AUDIT, item, manifest['clips']['idle'], i)[0]
                       for i in range(len(manifest['clips']['idle']['rects']))]
        idle_area = float(np.median([np.count_nonzero(np.asarray(f)[..., 3]) for f in idle_frames]))
        character = {'idle_median': readings[cid]['idle_median'], 'idle_median_area': idle_area, 'actions': {}}
        for action, clip in manifest['clips'].items():
            rows = [records[action, i] for i in range(len(clip['rects']))]
            if not any(r['normalized_outlier'] for r in rows):
                continue
            frames = [hf.snap_frame(AUDIT, item, clip, i)[0] for i in range(len(rows))]
            factors = [1 / r['normalized_head'] if r['normalized_outlier'] else 1. for r in rows]
            # 一个动作只使用一种画布；扩大透明边，绝不缩人以塞回旧画布。
            left = top = right = bottom = 0
            for i, (im, f) in enumerate(zip(frames, factors)):
                ax, ay = anchor(manifest, clip, i)
                x, y, ex, ey = im.getchannel('A').getbbox()
                left = max(left, math.ceil(8 - (ax + (x - ax) * f)))
                top = max(top, math.ceil(8 - (ay + (y - ay) * f)))
                right = max(right, math.ceil(ax + (ex - ax) * f + 8 - im.width))
                bottom = max(bottom, math.ceil(ay + (ey - ay) * f + 8 - im.height))
            size = (max(im.width for im in frames) + left + right,
                    max(im.height for im in frames) + top + bottom)
            out_action = {'canvas': list(size), 'padding': [left, top, right, bottom],
                          'ticks': clip['ticks'], 'loop': clip['loop'], 'frames': []}
            for i, (im, f, r) in enumerate(zip(frames, factors, rows)):
                ax, ay = anchor(manifest, clip, i)
                new_anchor = [ax + left, ay + top]
                tx, ty = new_anchor[0] - ax * f, new_anchor[1] - ay * f
                if f == 1.:
                    candidate = Image.new('RGBA', size)
                    candidate.paste(im, (left, top))
                else:
                    candidate = im.transform(size, Image.Transform.AFFINE,
                        (1 / f, 0, -tx / f, 0, 1 / f, -ty / f), Image.Resampling.NEAREST)
                binarize_alpha(candidate)
                path = ART / f'candidates/{cid}/{action}/frame-{i:02}.png'
                path.parent.mkdir(parents=True, exist_ok=True)
                candidate.save(path)
                area = int(np.count_nonzero(np.asarray(candidate)[..., 3]))
                before_area = int(np.count_nonzero(np.asarray(im)[..., 3]))
                row = {'frame': i, 'changed': r['normalized_outlier'], 'factor': f,
                       'source_texture': clip['texture'], 'source_rect': clip['rects'][i],
                       'source_pixel_sha256': r['frame_sha256'],
                       'candidate': path.relative_to(ROOT).as_posix(), 'candidate_pixel_sha256': pixel_sha(candidate),
                       'source_anchor': [ax, ay], 'anchor': new_anchor, 'translation': [tx, ty],
                       'head_before': r, 'head_after': r if not r['normalized_outlier'] else None,
                       'silhouette_sqrt_before': math.sqrt(before_area / idle_area),
                       'silhouette_sqrt_after': math.sqrt(area / idle_area)}
                if row['changed']:
                    center = [r['center'][0] * f + tx, r['center'][1] * f + ty]
                    full = any(word in action for word in ('flip', 'roll', 'down', 'throw', 'dive', 'air_tech'))
                    jobs.append((cid, row['candidate'], center, full, readings[cid]['idle_median']))
                    targets.append(row)
                out_action['frames'].append(row)
            character['actions'][action] = out_action
        plan['characters'][cid] = character
    hf.save_json(ART / 'scale-plan-pending.json', plan)
    with ProcessPoolExecutor(max_workers=4) as pool:
        for row, result in zip(targets, pool.map(task_measure, jobs)):
            row['head_after'] = result
    hf.save_json(ART / 'scale-plan.json', plan)
    print('整帧试算与候选头部复测已完成；未安装', flush=True)


if __name__ == '__main__':
    main()
