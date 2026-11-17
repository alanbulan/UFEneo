"""把光辉赛罗的待机像素整帧确定性落成 256 身份格。

管线：
1. 源像素整帧 Alpha128 硬化并裁到主体；
2. 统一源比例 = 188 / 源站高；
3. stage_cells.build 用 BOX 缩到原生站高 188、整图映射 32 色、脚底 247、根点 [128,248]；
4. 输出 cell、严格 4× 最近邻与 cells.json。

色板：本机没有安装 agent-sprite-forge（forge_backend 报
ImportError），按项目记录的“最远色种子＋频次加权 Lloyd32，最多16轮，
整图最近色映射”同法自实现，色板取自本形态待机像素整帧本身，
保住蓝额灯/蓝眼/蓝胸核与金色甲片。脚本只读本形态素材，不改共享工具。
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/art'))
sys.path.insert(0, str(ROOT / 'tools/media/art'))
import stage_cells  # noqa: E402
from catalogue_native import harden_alpha, trim  # noqa: E402

FIGHTER = 'ultraman-zero__shining'
SOURCE = ROOT / f'art/fighters/{FIGHTER}/stage1/idle/frames/pixel-raw-04-official-side-anchor.png'
OUT_DIR = ROOT / f'art/fighters/{FIGHTER}/stage1/cells'
CELL = 256
ROOT_X = 128
FOOT_ROW = 247
TARGET_STANDING = 188
PALETTE_SIZE = 32


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lloyd_palette(image: Image.Image, size: int = PALETTE_SIZE) -> list:
    """最远色种子＋频次加权 Lloyd，最多 16 轮；返回 size 个 RGB 三元组。"""
    array = np.array(image.convert('RGBA'))
    visible = array[:, :, 3] >= 128
    pixels = array[:, :, :3][visible].reshape(-1, 3).astype(np.int64)
    colors, counts = np.unique(pixels, axis=0, return_counts=True)
    weights = counts.astype(np.float64)
    weights /= weights.sum()

    first = int(np.argmax(counts))
    centroids = [colors[first].astype(np.float64)]
    distance2 = ((colors - centroids[0]) ** 2).sum(axis=1).astype(np.float64)
    for _ in range(size - 1):
        index = int(np.argmax(distance2 * weights))
        center = colors[index].astype(np.float64)
        centroids.append(center)
        distance2 = np.minimum(distance2, ((colors - center) ** 2).sum(axis=1))
    centroids = np.array(centroids)

    for _ in range(16):
        distance = ((colors[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        assign = distance.argmin(axis=1)
        updated = centroids.copy()
        for k in range(size):
            selected = assign == k
            if selected.any():
                w = weights[selected]
                updated[k] = (colors[selected] * w[:, None]).sum(axis=0) / w.sum()
        if np.allclose(updated, centroids, atol=1e-6):
            centroids = updated
            break
        centroids = updated
    return [tuple(int(round(v)) for v in c) for c in centroids]


def main() -> int:
    raw = Image.open(SOURCE).convert('RGBA')
    solid = trim(harden_alpha(raw))
    source_standing = solid.height
    scale = TARGET_STANDING / source_standing
    palette = lloyd_palette(solid, PALETTE_SIZE)
    print('source', raw.size, 'solid', solid.size, 'scale', round(scale, 9), 'palette', len(palette))

    out = OUT_DIR / 'idle-00-cell.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    row = stage_cells.build(SOURCE, out, palette, scale, FOOT_ROW,
                            anchor_x=ROOT_X, cell=CELL, foot_band=0.08)
    row['standing'] = True
    print(json.dumps(row, ensure_ascii=False, indent=1))

    x4_path = OUT_DIR / 'idle-00-x4.png'
    Image.open(out).resize((CELL * 4, CELL * 4), Image.NEAREST).save(x4_path)

    cell_array = np.array(Image.open(out).convert('RGBA'))
    visible = cell_array[:, :, 3] > 0
    ys, xs = np.nonzero(visible)
    height = int(ys.max() - ys.min() + 1)
    band = max(2, int(height * 0.03))
    band_mask = visible[ys.max() - band + 1:ys.max() + 1]
    bys, bxs = np.nonzero(band_mask)
    foot_span = int(bxs.max() - bxs.min() + 1)
    row['foot_outer_span'] = foot_span
    row['foot_span_over_height'] = round(foot_span / height, 4)
    record = dict(row)
    record['output_sha256'] = sha256(out)
    head = row['head_height']
    cells = {
        'fighter': FIGHTER,
        'form': '光辉赛罗 / Shining Ultraman Zero',
        'stage': 'stage1',
        'date': '2026-11-12',
        'canvas': [CELL, CELL],
        'root': [ROOT_X, FOOT_ROW + 1],
        'baseline': FOOT_ROW + 1,
        'foot_row': FOOT_ROW,
        'target_standing_height': TARGET_STANDING,
        'source_scale': round(scale, 9),
        'scale_status': 'fixed_from_idle_source',
        'palette_method': '最远色种子＋频次加权Lloyd32，最多16轮，整图最近色映射（本机无 forge，按同法自实现）',
        'palette': [list(c) for c in palette],
        'palette_status': 'frozen_32_from_idle_pixel_source',
        'palette_source': {
            'path': SOURCE.relative_to(ROOT).as_posix(),
            'sha256': sha256(SOURCE),
            'method': '最远色种子＋频次加权Lloyd32，最多16轮，整图RGB最近邻映射',
        },
        'grid_detection': 'not_run',
        'frames': [record],
        'identity_anchor_for_actions': {
            'path': out.relative_to(ROOT).as_posix(),
            'sha256': sha256(out),
            'size': [CELL, CELL],
            'native_bbox': row['bbox'],
            'standing_height': height,
            'root': [ROOT_X, FOOT_ROW + 1],
            'foot_row': FOOT_ROW,
            'production_reference': {
                'path': SOURCE.relative_to(ROOT).as_posix(),
                'sha256': sha256(SOURCE),
                'note': '本形态待机像素整帧；动作帧只引这一张，不追加其它角度或角色',
            },
            'review_authority': 'root_delegated_by_user',
            'date': '2026-11-12',
        },
        'accepted_for_actions': True,
        'installed': False,
        'recording': None,
        'review_authority': 'root_delegated_by_user',
        'status': 'identity_anchor_candidate',
        'flags': [],
        'notes': [
            f'站高 {height}、头高启发式 {head}（{row["head_ratio"]}）、站距 '
            f'{row["foot_outer_span"]}/{height}={row["foot_span_over_height"]}；数值为确定性记录，不替代目视造型验收。',
            '源站高 1100、源比例 188/1100；脚底 247、根点 [128,248]。',
        ],
    }
    (OUT_DIR / 'cells.json').write_text(json.dumps(cells, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('wrote', OUT_DIR / 'cells.json', 'x4', x4_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
