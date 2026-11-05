"""现有完整源整链内存候选。必须提供已审逐tick配对表；不安装、不改变捕获或后段。"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'reports/gomora-builtin/main-candidate210/contract.json'
OUT = ROOT / 'reports/gomora-builtin/main-chain-20261105'
sys.path.insert(0, str(ROOT / 'tools/rebuild/shared'))
import forge_backend as forge

POSE = 'gomora_back_lift_receiver'
SOURCE = ROOT / 'art/fighters/ultraman/stage5/gomora-back-lift-receiver'
SPECS = [
    (0, 'R00v2', 'builtin-r00-20261105', 'candidate-2.png', 'review-2.json', [146, 219], [61, 122]),
    (1, 'R01', 'builtin-r01-20261105', 'candidate.png', 'review.json', [176, 193], [72, 110]),
    (12, 'early', 'builtin-r01-r02-early-20261105', 'candidate.png', 'review.json', [176, 193], [72, 113]),
    (13, 'mid', 'builtin-r01-r02-mid-20261105', 'candidate.png', 'review.json', [168, 154], [73, 82]),
    (14, 'late', 'builtin-r01-r02-late-20261105', 'candidate.png', 'review.json', [210, 105], [99, 78]),
]
LABELS = {'R00v2': 0, 'R01': 1, 'R02': 2, 'early': 12, 'mid': 13, 'late': 14}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def box_rows(im):
    alpha = np.asarray(im)[..., 3] > 0
    rows = []
    for bottom in range(320, 0, -16):
        top = max(0, bottom - 16)
        ys, xs = np.where(alpha[top:bottom])
        if len(xs):
            rows.append([int(xs.min()) - 128, 288 - (top + int(ys.max()) + 1),
                         int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)])
    return rows

def build(plan_path):
    plan = read(plan_path)
    assert not OUT.exists(), '不覆盖既有证据目录'
    assert plan['base_contract_sha256'] == sha(BASE)
    rows = plan['pairs']
    assert [row['tick'] for row in rows] == list(range(20, 32))
    original = read(BASE)
    cfg = copy.deepcopy(original)
    clip = cfg['clips']['ultraman'][POSE]
    old_atlas = Image.open(clip['texture']).convert('RGBA')
    cells = []
    for rect in clip['rects']:
        x, y, w, h = map(int, rect)
        assert [w, h] == [256, 192]
        cell = Image.new('RGBA', (256, 320))
        cell.paste(old_atlas.crop((x, y, x+w, y+h)), (0, 104))
        cells.append(cell)
    assert len(cells) == 12
    cells.extend([None] * 3)
    registrations = []
    resources = copy.deepcopy(cfg['bound_resources'])
    resources.append({'path': str(BASE), 'sha256': sha(BASE)})
    resources.append({'path': str(plan_path.resolve()), 'sha256': sha(plan_path)})
    for index, label, folder, filename, reviewname, size, pelvis in SPECS:
        path = SOURCE / folder / filename
        review_path = SOURCE / folder / reviewname
        review = read(review_path)
        assert sha(path) == review['source_sha256']
        assert review.get('uniform_size', review.get('uniform_whole_size')) == size
        assert review.get('native_pelvis', review.get('local_pelvis')) == pelvis
        im = Image.open(path).convert('RGBA').resize(tuple(size), Image.Resampling.NEAREST)
        raw_pixels = np.asarray(im).copy()
        binary = forge.binarize_alpha(im.copy())
        im.putalpha(binary.getchannel("A"))
        processed = np.asarray(im)
        assert np.array_equal(raw_pixels[..., :3], processed[..., :3]), '不改RGB'
        assert np.array_equal(processed[..., 3], np.where(raw_pixels[..., 3] >= 128, 255, 0))
        paste = [122 - pelvis[0], 214 - pelvis[1]]
        assert paste[0] >= 0 and paste[1] >= 0
        assert paste[0] + im.width <= 256 and paste[1] + im.height <= 320
        cell = Image.new('RGBA', (256, 320))
        cell.paste(im, tuple(paste))
        assert int((np.asarray(cell)[..., 3] > 0).sum()) == int((np.asarray(im)[..., 3] > 0).sum())
        cells[index] = cell
        registrations.append(dict(sprite=index, label=label, source=str(path), source_sha256=sha(path),
                                  fixed_size=size, fixed_paste=paste, cell_pelvis=[122, 214],
                                  local_pelvis=[-6, 74], alpha_threshold=128, rgb_unchanged=True,
                                  method='NEAREST whole-image resize; adopt forge_backend.binarize_alpha A channel only; retain all RGB',
                                  full_resized_rectangle_in_cell=True, thresholded_alpha_preserved=True))
        resources.extend({'path': str(p), 'sha256': sha(p)} for p in [path, review_path])
    states = cfg['receiver_states'][POSE]
    for index, label, *_ in SPECS:
        state = {'sprite': index, 'dx': 0, 'dy': 0, 'hitboxes': [], 'hurtboxes': box_rows(cells[index]),
                 'cancel': [], 'events': [], 'grab_points': {'waist': [-6, 74]}}
        if index < len(states):
            states[index] = state
        else:
            assert index == len(states)
            states.append(state)
    for row in rows:
        t = row['tick']
        frame = cfg['move']['frames'][t]
        assert row['actor'] == frame['sprite'], '不改攻击方帧时序'
        sprite = LABELS[row['receiver']]
        grip, point = row['grip'], row['hold_point']
        assert all(type(v) is int for v in grip + point) and len(grip) == len(point) == 2
        assert point[1] >= 0
        root = [grip[0]-point[0], grip[1]-point[1]]
        assert root == row['root'], '配对表root反算不一致'
        frame['target'] = {'mode': 'hold', 'pose': POSE, 'sprite': sprite, 'facing': 1,
                           'root': [0, 0], 'grip': grip,
                           'hold_point_overrides': {'ultraman': {POSE: {str(sprite): point}}}}
    assert all(abs(rows[0]['root'][i] - [-44, 45][i]) <= 14 for i in range(2))
    assert cfg['move']['frames'][:20] == original['move']['frames'][:20]
    assert cfg['move']['frames'][32:] == original['move']['frames'][32:]
    assert cfg['move']['throw_current_capture'] == original['move']['throw_current_capture']
    assert states[2:12] == original['receiver_states'][POSE][2:12]
    cfg['move']['display_name'] = '背掀完整补相链·未安装内存审查候选'
    cfg['move']['production_note'] = '仅整链内存审查，尚未美术通过，禁止安装。'
    cfg['limits'] = ['完整源固定注册，不逐tick变形；接点与膝弧未因逻辑通过而获美术验收。',
                     '捕获盒及14px入口门槛不变，t32起后段与t68唯一落地沿旧合同。',
                     '逐tick root不是mode=release机制验收，未安装正式三级。']
    cfg['pelvis_cell_readpoints'] = [[p[0], p[1]+104] for p in original['pelvis_cell_readpoints']]
    cfg['pelvis_cell_readpoints'].extend([[122, 214]] * 3)
    cfg['receiver_labels'].extend(['early', 'mid', 'late'])
    for index, label, *_ in SPECS:
        cfg['pelvis_cell_readpoints'][index] = [122, 214]
        cfg['receiver_labels'][index] = label
    atlas = Image.new('RGBA', (256 * len(cells), 320))
    for i, cell in enumerate(cells):
        atlas.paste(cell, (256*i, 0))
    OUT.mkdir(parents=True)
    atlas_path = OUT / 'receiver.png'
    atlas.save(atlas_path)
    clip.update(texture=str(atlas_path), anchor_y=288, anchors=[[128, 288]] * len(cells),
                rects=[[256*i, 0, 256, 320] for i in range(len(cells))], ticks=[4]*len(cells))
    resources.append({'path': str(atlas_path), 'sha256': sha(atlas_path)})
    cfg['bound_resources'] = resources
    cfg['chain_registration'] = registrations
    cfg['forge_backend'] = forge.backend_info()
    cfg['chain_pairs'] = rows
    cfg['base_contract_sha256'] = sha(BASE)
    cfg['accepted'] = False
    cfg['installed'] = False
    (OUT / 'contract.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'contract': str(OUT / 'contract.json'), 'sha256': sha(OUT / 'contract.json'),
                      'sprites': len(cells), 'post32_unchanged': True, 'installed': False}, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pairs', required=True, type=Path)
    build(parser.parse_args().pairs)
