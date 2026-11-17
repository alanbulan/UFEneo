"""欧米伽的青蓝近眼，按本角色色谱实测；不修改眼高限值。"""
import numpy as np
import cv2
import hashlib
import json
from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=1)
def delivery_hints():
    path=Path(__file__).resolve().parents[3]/'art/fighters/ultraman-omega/stage4/ground/absolute-size-codex/delivery-eye-hints.json'
    return json.loads(path.read_text(encoding='utf-8-sig'))['frames'] if path.exists() else {}

def feature(im,row):
    a=np.array(im);r,g,b=a[...,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(a.shape[:2])
    center=row.get('eye') or row.get('native_points',{}).get('eye') or row.get('hint')
    # 源QA留存原坐标；只对SHA完全一致的交付整帧迁移搜索窗口，不能把胸灯当眼。
    mapped=delivery_hints().get(hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest())
    if mapped:center=mapped['center']
    if center is None:raise ValueError('欧米伽本相缺头部提示点')
    cx,cy=center;mask=(a[...,3]>0)&(abs(xx-cx)<17)&(abs(yy-cy)<15)&(g>115)&(b>130)&(g>r*1.18)&(b>r*1.22)
    n,l,s,c=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    ids=[i for i in range(1,n) if s[i,4]>=2]
    if not ids:raise ValueError('欧米伽青蓝眼不可测量')
    i=min(ids,key=lambda i:abs(c[i,0]-cx)+abs(c[i,1]-cy))
    return c[i].astype(float).tolist()
