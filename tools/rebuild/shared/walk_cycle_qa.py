"""走路头部相位、脚底世界坐标与时长约束；只读测量，不修改动画。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import numpy as np
from head_scale import read,save
import idle_qa,walk_rhythm

def check(images,fighter,heads,ticks,feet,sign,targets=None):
    eyes=[idle_qa.feature(im,fighter,h) for im,h in zip(images,heads)]
    ey=np.array([p[1] for p in eyes]);n=len(images);adj=np.abs(np.roll(ey,-1)-ey);issues=[]
    if np.ptp(ey)>8:issues.append('眼睛高度总幅度>8px')
    if max(adj)>4:issues.append('眼睛相邻帧含接头变化>4px')
    phase='只查幅度与含首尾相邻差；相位目标仅作姿势引导，不作硬门'
    average=sum(ticks)/n
    if min(ticks)<average*.6 or max(ticks)>average*1.5:issues.append('帧时长超出均值0.6–1.5倍')
    stance=walk_rhythm.deviations(feet,ticks,sign)
    if max(abs(r['deviation']) for r in stance)>8:issues.append('撑地世界坐标偏差>±8px')
    return dict(fighter=fighter,eyes=eyes,eye_range=float(np.ptp(ey)),adjacent_eye_y=adj.tolist(),phase_rule=phase,
        ticks=ticks,average_tick=average,stance=stance,max_foot_deviation=max(abs(r['deviation']) for r in stance),issues=issues,pass_=not issues)

def validate_folder(folder,fighter,action):
    if action not in ['walk_forward','walk_back']:return None
    import pathlib
    from PIL import Image
    folder=pathlib.Path(folder);p=folder/'walk-measurements.json'
    if not p.exists():raise ValueError('走路缺少真实脚步逐帧测量及目标曲线')
    q=read(folder/'head-qa.json');d=read(p);images=[Image.open(folder/r['image']).convert('RGBA') for r in q['frames']]
    r=check(images,fighter,q['frames'],d['ticks'],d['feet'],d['sign'],d.get('targets'))
    save(folder/'walk-cycle-qa.json',r)
    if r['issues']:raise ValueError('; '.join(r['issues']))
    return r
