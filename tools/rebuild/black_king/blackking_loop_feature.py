"""布莱克王循环只读橙红近眼；不能用通用英雄的金色面罩颜色选金角。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import cv2
import numpy as np


def feature(im,row):
    a=np.asarray(im);red,green,blue=a[:,:,:3].astype(float).transpose(2,0,1)
    yy,xx=np.indices(a.shape[:2]);x,y=row['hint']
    # hint来自高分辨率原图独立橙眼颜色读数；区域内最近眼簇，不重新启动眼鼻/耳根头尺定位。
    # 已有32色板的暗相眼色为(143,39,36)，不能只接收发亮的橙眼。
    mask=(a[:,:,3]>0)&(abs(xx-x)<13)&(abs(yy-y)<13)&(red>120)&(green>25)&(green<145)&(blue<90)&(red>green*1.7)&(red>blue*2)
    n,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    ids=[k for k in range(1,n) if stats[k,4]>=1]
    if not ids:raise ValueError('布莱克王提示点附近橙红眼不可测，不改用鼻甲或金角')
    k=min(ids,key=lambda k:np.linalg.norm(centers[k]-[x,y]))
    return centers[k].tolist()


def measure(images,rows,action):
    from loop_qa import evaluate
    result=evaluate([feature(im,row) for im,row in zip(images,rows)],action)
    factor=181.05906313645622/135
    result['limits']={k:(v*factor if k in ['vertical','adjacent','horizontal'] and v is not None else v) for k,v in result['limits'].items()}
    result['size_factor']=factor
    result['limit_policy']='AGENTS：英雄135像素为基准，按定稿头骨站高181.0591等比放大；不改其他角色'
    result['issues']=[]
    for key,value,name in [('vertical',result['vertical_range'],'眼高总幅'),('adjacent',max(result['adjacent_y']),'相邻含首尾眼高差'),('horizontal',result['horizontal_range'],'水平漂移')]:
        limit=result['limits'][key]
        if limit is not None and value>limit+1e-6:result['issues'].append(f'{name}{value:.3f}px > {limit:.3f}px')
    return dict(fighter='black_king',**result)
