"""循环整帧的头部特征连续性；含最后一帧到第一帧。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import numpy as np
from PIL import Image
from head_scale import ROOT,read,save
from idle_qa import feature as legacy_feature
from loop_repair_landmarks import marked_feature
import hashlib


def feature(im,fighter,row):
    if fighter=='ultraman-teo':
        from teo_loop_feature import feature as teo_feature
        return teo_feature(im,row)
    if fighter=='ultraman-omega':
        from omega_loop_feature import feature as omega_feature
        return omega_feature(im,row)
    if fighter=='ultraman-blazar':
        from blazar_loop_feature import feature as blazar_feature
        return blazar_feature(im,row)
    if fighter=='neronga':
        from neronga_loop_feature import feature as neronga_feature
        return neronga_feature(im,row)
    # 初代已装旧循环有逐帧完整近侧眼框标注：避免跳选远眼/眼框碎片。
    # 精确像素哈希绑定；无标注的新帧、杰顿、赛文继续原有检测路径。
    point=marked_feature(im,fighter)
    return point if point is not None else legacy_feature(im,fighter,row)


def limits(action):
    if action in ['walk_forward','walk_back']:return dict(vertical=8,adjacent=4,horizontal=None,kind='步行独立规则')
    if action=='stun':return dict(vertical=12,adjacent=4,horizontal=None,kind='眩晕连续摇晃')
    if action.startswith('flip_'):return dict(vertical=None,adjacent=None,horizontal=None,kind='翻转运动循环，报告轨迹，不套用静止呼吸门')
    return dict(vertical=6,adjacent=3,horizontal=3,kind='静止保持/待机/蓄能')


# AGENTS：比英雄（站高135）高大的怪兽，循环像素限值按“定稿站高÷135”等比放大。
# 雷德王、布莱克王在各自的loop_feature里自行换算，这里只登记走通用路径的角色。
BODY_SCALE={'eleking':184/135,'neronga':196/135}


def evaluate(centers,action,factor=1.0):
    points=np.asarray(centers,dtype=float);x,y=points.T
    dy=np.abs(np.roll(y,-1)-y);dx=np.abs(np.roll(x,-1)-x);issues=[]
    rule={k:(v*factor if k in ['vertical','adjacent','horizontal'] and v is not None else v) for k,v in limits(action).items()}
    if factor!=1.0:rule['body_scale']=factor
    for key,value,description in [('vertical',float(np.ptp(y)),'眼高总幅'),('adjacent',float(max(dy)),'相邻含首尾眼高差'),('horizontal',float(np.ptp(x)),'水平漂移')]:
        if rule[key] is not None and value>rule[key]+1e-6:issues.append(f'{description}{value:.3f}px > {rule[key]}px')
    return dict(action=action,centers=points.tolist(),vertical_range=float(np.ptp(y)),horizontal_range=float(np.ptp(x)),adjacent_y=dy.tolist(),adjacent_x=dx.tolist(),limits=rule,issues=issues)


def measure(images,fighter,heads,action):
    from form_loop_feature import configuration, feature as form_feature
    form=configuration(fighter)
    if form is not None:
        return dict(fighter=fighter,**evaluate([form_feature(im,fighter,h,form) for im,h in zip(images,heads)],action,form['scale']))
    if fighter=='red_king':
        from redking_loop_feature import measure as redking_measure
        return redking_measure(images,heads,action)
    if fighter=='black_king':
        from blackking_loop_feature import measure as blackking_measure
        return blackking_measure(images,heads,action)
    if any(h.get('loop_motion_reference') in ['head_shell_center','head_center'] for h in heads):
        if not action.startswith('flip_'):raise ValueError('头壳中心只可用于翻转轨迹报告，不可替代待机或走路眼高')
        centers=[]
        for im,h in zip(images,heads):
            if not h.get('loop_motion_only') or hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()!=h.get('rgba_sha256'):
                raise ValueError('翻转轨迹标点与当前完整帧像素不符')
            points=h.get('native_points',{})
            if h.get('loop_motion_reference')=='head_shell_center':
                center=[(float(points['skull_top'][i])+float(points['chin'][i]))/2 for i in [0,1]]
            elif h.get('loop_motion_reference')=='head_center':center=points['head_center']
            else:raise ValueError('翻转轨迹缺少明确头部参照')
            if not all(np.isfinite(center))or not(0<=center[0]<im.width and 0<=center[1]<im.height):raise ValueError('翻转轨迹头部参照越界')
            centers.append(center)
        return dict(fighter=fighter,feature_reference='rigid_head_motion_only',**evaluate(centers,action))
    return dict(fighter=fighter,**evaluate([feature(im,fighter,h) for im,h in zip(images,heads)],action,BODY_SCALE.get(fighter,1.0)))


def validate_folder(folder,fighter,action,loop=None):
    folder=Path(folder)
    if loop is None:
        policy=folder/'clip-policy.json'
        if policy.exists():loop=read(policy).get('loop',False)
        else:
            mp=ROOT/f'assets/fighters/{fighter}/animations/manifest.json'
            loop=read(mp)['clips'].get(action,{}).get('loop',False) if mp.exists() else False
    if not loop:return None
    q=read(folder/'head-qa.json');images=[Image.open(folder/r['image']).convert('RGBA') for r in q['frames']]
    result=measure(images,fighter,q['frames'],action);save(folder/'loop-qa.json',result)
    if result['issues']:raise ValueError(action+'循环不平滑：'+'；'.join(result['issues']))
    return result


def installed(output=None):
    from check.limb_idle import frame_row
    results=[];errors=[]
    for manifest in sorted((ROOT/'assets/fighters').glob('*/animations/manifest.json')):
        fighter=manifest.parent.parent.name
        for action,clip in read(manifest)['clips'].items():
            if not clip.get('loop'):continue
            hq=read(ROOT/clip['head_qa']);atlas=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA')
            images=[atlas.crop((x,y,x+w,y+h)) for x,y,w,h in clip['rects']];heads=[frame_row(hq['frames'],clip,i) for i in range(len(images))]
            try:r=measure(images,fighter,heads,action)
            except ValueError as exc:r=dict(fighter=fighter,action=action,issues=[str(exc)])
            r['report_only']=fighter in ['ultraman','zetton'];results.append(r)
            if r['issues'] and not r['report_only']:errors.extend(f'{fighter}/{action}: {s}' for s in r['issues'])
    save(Path(output) if output else ROOT/'reports/loop-quality-scan.json',dict(clips=results,errors=errors,policy='初代/杰顿全部旧循环仅报告不改；步行沿用已审专门规则；翻转运动列轨迹不按静止呼吸限制。'))
    return results,errors
