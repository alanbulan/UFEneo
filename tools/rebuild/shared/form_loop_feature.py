"""形态自己的站高和眼色；不替换本体角色既有检测/判定路径。"""
from __future__ import annotations
import json
from pathlib import Path
import cv2
import numpy as np

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'project.godot').is_file())


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def configuration(fighter):
    model=ROOT/f'art/fighters/{fighter}/model'
    mp=model/'measurements.json';cp=model/f'head-fit/{fighter}.json'
    if not mp.exists() or not cp.exists():return None
    measurements=read(mp);cfg=read(cp)
    # 现有角色完全沿用原函数；独立名册形态也可由measurements.form_of声明。
    if not (measurements.get('form_of') or fighter.startswith('ex_')):return None
    height=measurements.get('standing_height')
    if isinstance(height,dict):height=height.get('to_skull_top',height.get('including_horns_or_antennae'))
    height=height or measurements.get('standing_height_without_ornaments') or measurements.get('standing_height_with_ornaments')
    if not height or float(height)<=0:raise ValueError(f'{fighter}形态定稿没有有效站高')
    result=dict(config=cfg,measurements=measurements,scale=float(height)/135)
    if cfg.get('loop_feature'):
        result['feature']=cfg['loop_feature'];return result
    # 无显式色谱时，只从本形态已登记的定稿眼点采样，不借用本体黄色阈值。
    eye=measurements.get('native_landmarks',measurements.get('native_points',{})).get('eye')
    if eye is None:raise ValueError(f'{fighter}形态配置缺loop_feature或定稿眼点')
    from PIL import Image
    image_path=measurements.get('image',cfg['idle_texture']);im=Image.open(ROOT/image_path.removeprefix('res://')).convert('RGBA')
    x,y=map(round,eye);a=np.array(im);patch=a[max(0,y-3):y+4,max(0,x-3):x+4];rgb=patch[:,:,:3]
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV);mask=(patch[:,:,3]>0)&(hsv[:,:,1]>90)&(hsv[:,:,2]>120)
    if not mask.any():raise ValueError(f'{fighter}形态定稿眼点没有可采样的发光颜色')
    py,px=np.indices(mask.shape);distance=(px-(x-max(0,x-3)))**2+(py-(y-max(0,y-3)))**2;distance=np.where(mask,distance,999)
    yy,xx=np.unravel_index(distance.argmin(),distance.shape);hue=int(hsv[yy,xx,0])
    center=np.array(cfg['head_center'],float)
    result['feature']=dict(color=dict(hue=hue,hue_tolerance=13,saturation_min=90,value_min=120),target_offset=(np.array(eye)-center).tolist(),search_radius=[24,24],min_pixels=2,source='本形态measurements已登记眼点的当前定稿像素')
    return result


def hint(row,cfg):
    # 不要求所有历史head-qa都有hint；不以人物外框顶替真实眼点。
    for value in [row.get('hint'),row.get('head_center_native'),row.get('head_fit',{}).get('center'),row.get('head',{}).get('center'),row.get('eye_native'),cfg.get('head_center')]:
        if value is not None and len(value)==2 and np.isfinite(value).all():return np.asarray(value,float)
    raise ValueError('缺少有效头部定位提示')


def feature(im,fighter,row,config=None):
    cfg=config if config is not None else configuration(fighter)
    if cfg is None:raise ValueError(f'{fighter}不是已配置形态')
    rule=cfg['feature'];center=hint(row,cfg['config']);target=center+np.asarray(rule.get('target_offset',[0,0]),float)
    a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1);yy,xx=np.indices(a.shape[:2]);rx,ry=rule.get('search_radius',[24,24]);color=rule['color']
    mask=(a[:,:,3]>0)&(abs(xx-center[0])<rx)&(abs(yy-center[1])<ry)
    if 'hue' in color:
        hsv=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2HSV);delta=np.abs(hsv[:,:,0].astype(int)-color['hue']);delta=np.minimum(delta,180-delta)
        mask&=(delta<=color.get('hue_tolerance',13))&(hsv[:,:,1]>=color.get('saturation_min',90))&(hsv[:,:,2]>=color.get('value_min',120))
    else:
        mask&=(r>color.get('red_min',0))&(g<color.get('green_max',256))&(r>g*color.get('red_green_ratio',0))&(r>b*color.get('red_blue_ratio',0))
    n,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    ids=[i for i in range(1,n) if stats[i,4]>=rule.get('min_pixels',2)]
    if not ids:raise ValueError(f'{fighter}形态眼睛不可测量（使用本形态定稿色谱）')
    i=min(ids,key=lambda i:abs(centers[i,0]-target[0])+abs(centers[i,1]-target[1])*1.5)
    return centers[i].astype(float).tolist()
