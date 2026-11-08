"""哥莫拉眼心—鼻角尖标尺。只读像素；校准未全过时绝不硬拦。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse
import csv
import hashlib
import json; json = _LayoutJson
import math
from functools import lru_cache
from pathlib import Path
Path = _LayoutProjectPath

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = _LayoutProjectPath(_layout_root)
MODEL = ROOT / 'art/fighters/gomora/model/model-native.png'
WORK = ROOT / 'art/fighters/gomora/stage4/pilot/gomora/batch3'
OUT = ROOT / 'reports/review/2026-10-22/gomora-batch3/head-v2'
CALIBRATION = WORK / 'head-v2-calibration.json'
ACTIONS = 'idle dash_start dash crouch_start crouch crouch_rise light1 heavy crouch_light crouch_light2 slide'.split()


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def eye(im, hint=None):
    a = np.asarray(im.convert('RGBA'))
    r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
    mask = (a[:, :, 3] >= 128) & (r > 220) & (g > 140) & (b < 90) & (r-g > 15) & (g-b > 90)
    n, labels, stats, centers = cv2.connectedComponentsWithStats(mask.astype('uint8'), 8)
    candidates = list(range(1, n))
    if not candidates:
        return None
    k = min(candidates, key=lambda i: math.dist(centers[i], hint)) if hint is not None else max(candidates, key=lambda i: stats[i, 4])
    return dict(center=centers[k].tolist(), area=int(stats[k, 4]), box=stats[k, :4].tolist())


def locate(im, expected_scale=1., facing='right', angle=0., hint=None):
    """前方半锥内找最近象牙色连通鼻角，再取该鼻角离眼最远的真实像素。

    角度只限制搜索方向，不参与距离或尺寸计算。局部搜索上限45原生px，
    避免象牙爪；未找到或歧义均显式转人工，不把定稿距离当选尖目标。
    """
    e = eye(im, hint)
    if e is None:
        return None
    center = np.asarray(e['center'])
    a = np.asarray(im.convert('RGBA'))
    r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
    ivory = (a[:, :, 3] >= 128) & (r >= 210) & (g >= 185) & (b >= 130) & (r-b < 100) & (g-b < 90)
    yy, xx = np.indices(ivory.shape)
    delta = np.stack([xx-center[0], yy-center[1]], -1)
    radius = np.linalg.norm(delta, axis=2)
    theta = math.radians(-angle)
    direction = np.array([math.cos(theta), math.sin(theta)])
    if facing == 'left':
        direction[0] *= -1
    forward = delta @ direction
    # 旧颅骨角在真实翻滚帧会反向，不能再用它硬裁前方锥。
    # 在眼周固定半径内找完整鼻角材质块，鼻角确定后才给出前方向。
    # 最小完整面积排除耳角/鳞片的象牙高光碎斑；不是成品孤岛过滤。
    roi = (radius <= 45*expected_scale) & (radius >= 4*expected_scale)
    n, labels, stats, centers = cv2.connectedComponentsWithStats((ivory & roi).astype('uint8'), 8)
    candidates = []
    for k in range(1, n):
        ys, xs = np.where(labels == k)
        points = np.c_[xs, ys]
        distances = np.linalg.norm(points-center, axis=1)
        if stats[k, 4] < max(6, round(15*expected_scale**2)):
            continue
        near = float(distances.min())
        if near > 29*expected_scale:
            continue
        tip = points[int(np.argmax(distances))].tolist()
        candidates.append(dict(component=k, area=int(stats[k, 4]), nearest=near, tip=tip,
                               length=math.dist(center, tip), box=stats[k, :4].tolist()))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c['nearest'])
    selected = candidates[0]
    ambiguous = len(candidates) > 1 and candidates[1]['nearest']-selected['nearest'] < 2*expected_scale
    return dict(eye=e['center'], eye_area=e['area'], eye_detected=True,
                nose_tip=selected['tip'], length=selected['length'], angle=angle,
                facing=facing, search_direction=((np.array(selected['tip'])-center)/selected['length']).tolist(), orientation_hint=direction.tolist(), search_radius=45*expected_scale,
                candidates=candidates, needs_manual=ambiguous,
                method='yellow-eye-center-to-nearest-complete-ivory-nasal-horn-tip-v2.1')


@lru_cache(maxsize=1)
def reference():
    h = locate(Image.open(MODEL), 1.)
    if h is None:
        raise ValueError('定稿眼睛或鼻角不可测')
    h['model_sha256'] = hashlib.sha256(MODEL.read_bytes()).hexdigest()
    return h


def measure(im, expected_scale=1., facing='right', angle=0., hint=None):
    h = locate(im, expected_scale, facing, angle, hint)
    if h is None:
        return None
    h.update(reference_length=reference()['length'], scale=h['length']/reference()['length'],
             center=h['eye'], metric='眼心到鼻角尖欧氏距离；不含耳角、鳞片、爪子')
    return h


def policy():
    if not CALIBRATION.exists():
        return dict(hard_gate=False, reason='尚未完成第一批逐帧校准')
    return read(CALIBRATION)['policy']


def annotated(im, h, title, path):
    scale = 4
    canvas = Image.new('RGB', (im.width*scale, im.height*scale+65), '#202632')
    sprite = im.convert('RGBA').resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST)
    canvas.paste(sprite, (0, 65), sprite)
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 21)
    d.text((10, 8), title, font=font, fill='white')
    if h:
        pts = [(p[0]*scale, p[1]*scale+65) for p in [h['eye'], h['nose_tip']]]
        d.line(pts, fill='#68dfff', width=2)
        for p, color in zip(pts, ['#ff477f', '#58ff9d']):
            x, y = p
            d.ellipse((x-5, y-5, x+5, y+5), outline=color, width=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def calibrate():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = read(ROOT/'assets/fighters/gomora/animations/manifest.json')
    rows = []
    annotated(Image.open(MODEL), reference(), f'定稿 眼心—鼻角尖 {reference()["length"]:.3f}px', OUT/'model-annotated-x4.png')
    strips = []
    for action in ACTIONS:
        clip = manifest['clips'][action]
        atlas = Image.open(ROOT/clip['texture'].replace('res://', '')).convert('RGBA')
        old = read(ROOT/clip['head_qa'])['frames'] if clip.get('head_qa') else []
        heads = Image.new('RGB', (len(clip['rects'])*640, 660), '#202632')
        d = ImageDraw.Draw(heads)
        f = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 18)
        for i, (x, y, w, h) in enumerate(clip['rects']):
            im = atlas.crop((x, y, x+w, y+h))
            prior = old[i].get('measurement') if i < len(old) else None
            m = measure(im, 1., angle=prior.get('angle', 0) if prior else 0)
            deviation = (m['scale']-1)*100 if m else None
            passed = m is not None and not m['needs_manual'] and abs(deviation) <= 8
            image_path = OUT/action/f'frame-{i:02}-annotated-x4.png'
            title = f'{action} #{i}: ' + (f'{m["length"]:.3f}px / {deviation:+.2f}%' if m else '不可测')
            annotated(im, m, title, image_path)
            rows.append(dict(action=action, frame=i, measured=m, deviation_percent=deviation,
                             pass_=passed, source_texture=clip['texture'], source_rect=[x,y,w,h],
                             source_atlas_sha256=hashlib.sha256((ROOT/clip['texture'].replace('res://','')).read_bytes()).hexdigest(),
                             image_pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest(),
                             annotation=image_path.relative_to(ROOT).as_posix(),
                             points_visual_review=False))
            if m:
                cx, cy = m['eye']
                crop = im.crop((round(cx)-40,round(cy)-40,round(cx)+40,round(cy)+40))
                crop = crop.resize((640,640),Image.Resampling.NEAREST)
                heads.paste(crop,(i*640,20),crop)
                q = ImageDraw.Draw(heads)
                pts = [((p[0]-round(cx)+40)*8+i*640,(p[1]-round(cy)+40)*8+20) for p in [m['eye'],m['nose_tip']]]
                q.line(pts,fill='#68dfff',width=2)
                for px,py in pts:q.ellipse((px-4,py-4,px+4,py+4),outline='#ff4781',width=2)
            d.text((i*640+4,0),title,font=f,fill='white')
        heads.save(OUT/action/'heads-annotated-x8.png')
    all_pass = all(r['pass_'] for r in rows)
    result = dict(schema=2,reference=reference(),actions=ACTIONS,frames=rows,all_numeric_pass=all_pass,
                  policy=dict(hard_gate=False,reason='待逐帧核对标点' if all_pass else '已审第一批存在超±8%或定位歧义；按用户要求只作需人工复核软标记',tolerance=.08),
                  no_region_recolor=True,runtime_modified=False)
    save(CALIBRATION,result)
    save(OUT/'calibration.json',result)
    with (OUT/'calibration.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.writer(handle);writer.writerow(['动作','帧','定稿距离','实测距离','偏差百分比','数值合格','眼心','鼻角尖'])
        for r in rows:
            m=r['measured'];writer.writerow([r['action'],r['frame'],reference()['length'],m['length'] if m else '',r['deviation_percent'],r['pass_'],m['eye'] if m else '',m['nose_tip'] if m else ''])
    print(json.dumps(dict(reference=reference(),total=len(rows),outside=[(r['action'],r['frame'],r['deviation_percent']) for r in rows if not r['pass_']],policy=result['policy']),ensure_ascii=False))
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['calibrate']);parser.parse_args()
    calibrate()
