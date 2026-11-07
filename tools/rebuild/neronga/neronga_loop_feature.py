"""内隆嘎实际黄眼；象牙鼻角不能混入循环位置特征。只测量，不改像素。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import cv2
import numpy as np


def feature(image,row):
    pixels=np.asarray(image.convert('RGBA'));r,g,b=pixels[:,:,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(pixels.shape[:2])
    hint=row.get('native_points',{}).get('eye',row.get('hint'))
    if hint is None:raise ValueError('内隆嘎缺少原图黄眼定位提示')
    cx,cy=hint
    # 与角色已使用并核对的成品黄眼读数一致；排除象牙角和赭黄背片。
    mask=(pixels[:,:,3]>0)&(r>190)&(g>130)&(b<100)&((xx-cx)**2+(yy-cy)**2<12**2)
    n,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    choices=[i for i in range(1,n) if stats[i,4]>=2]
    if not choices:raise ValueError('内隆嘎实际黄眼不可测量，不能回退测鼻角')
    selected=min(choices,key=lambda i:np.linalg.norm(centers[i]-[cx,cy]))
    return centers[selected].tolist()
