"""直立帧以脚底至头骨顶站高校验；背面不再把较窄的头宽放大成侧脸。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import numpy as np
from PIL import Image
from head_scale import ROOT,read

TOLERANCE=.03

def measure(im,fighter,row):
    import head_size
    # 明确的头骨区域只用于测量（不是调色遮罩），排除可摘冠刃。
    region=row.get('head_region')
    a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
    visible_face=fighter=='ultraseven' and bool(((a[:,:,3]>0)&(g>r*1.3)&(g>b*1.1)&(g>80)).any())
    if visible_face:
        # 正侧/侧前方继续排除额灯平面以上的可摘冠；不能把头部ROI里的冠缘算成头骨顶。
        m=head_size.head(im,fighter,row.get('hint'),direction=row.get('head_direction'),region=region)
    elif region:
        m=head_size.width_measure(im,region)
    else:m=head_size.head(im,fighter,row.get('hint'),direction=row.get('head_direction'))
    if not m:raise ValueError('直立帧头骨顶无法测量，需标注头骨区域')
    anchor=row.get('foot_anchor',[im.width//2,im.height-8])
    return dict(skull_top=float(m['bounds'][1]),foot_bottom=float(anchor[1]),height=float(anchor[1]-m['bounds'][1]),head_bounds=m['bounds'])

def reference(fighter):
    # 同角色已审待机是直立站高基准；定稿护架屈膝不同，不能拿外框强行拉直。
    c=read(ROOT/f'assets/fighters/{fighter}/animations/manifest.json')['clips']['idle']
    q=read(ROOT/c['head_qa']);a=Image.open(ROOT/c['texture'].removeprefix('res://')).convert('RGBA');values=[]
    for i,(x,y,w,h) in enumerate(c['rects']):
        values.append(measure(a.crop((x,y,x+w,y+h)),fighter,q['frames'][i])['height'])
    return float(np.median(values))

def check(im,fighter,row,peer_heights=None):
    m=measure(im,fighter,row);ref=reference(fighter);m.update(reference_height=ref,deviation=m['height']/ref-1,tolerance=TOLERANCE)
    m['peer_deviations']=[m['height']/height-1 for height in (peer_heights or [])]
    m['pass_']=abs(m['deviation'])<=TOLERANCE and all(abs(d)<=TOLERANCE for d in m['peer_deviations'])
    return m
