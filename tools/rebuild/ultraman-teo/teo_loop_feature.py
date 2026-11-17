"""只服务提欧的青白眼检测；不修改既有角色的检测路径或像素限值。"""
from pathlib import Path
import json
import math
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[3]

def feature(im,row):
    model=json.loads((ROOT/'art/fighters/ultraman-teo/model/measurements.json').read_text('utf-8-sig'))
    center=row.get('hint',row.get('head_fit',{}).get('center'))
    if center is None:raise ValueError('提欧缺头部定位提示')
    head=row.get('head_fit',{});angle=math.radians(head.get('rotation',0));rot=np.array([[math.cos(angle),math.sin(angle)],[-math.sin(angle),math.cos(angle)]])
    eye=np.array(model['native_landmarks']['eye']);expected=np.asarray(center)+rot@(eye-[93,57])*float(head.get('scale',1))
    a=np.array(im.convert('RGBA'));yy,xx=np.indices(a.shape[:2]);mask=np.zeros(a.shape[:2],bool)
    for color in [[239,254,255],[184,235,242],[125,213,230]]:mask|=np.all(a[:,:,:3]==color,axis=2)
    mask&=(a[:,:,3]>127)&(abs(xx-expected[0])<=7)&(abs(yy-expected[1])<=5)
    n,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    ids=[i for i in range(1,n) if stats[i,4]>=2]
    if not ids:raise ValueError('提欧青白近侧眼不可测；不以头饰亮点代替')
    k=min(ids,key=lambda i:float(np.linalg.norm(centers[i]-expected)));return centers[k].tolist()
