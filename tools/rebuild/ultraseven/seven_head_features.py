"""赛文旋转不变头标尺：黄色眼与封闭银色护耳；只读，不修改人物。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import math
import cv2
import numpy as np
from PIL import Image
from head_scale import ROOT

VERSION='eye-ear-v2'

def components(mask):
 n,l,s,c=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
 return [(i,s[i],c[i]) for i in range(1,n)],l

def features(im,hint=None):
 a=np.array(im);rgb=a[:,:,:3].astype(int);r,g,b=rgb.transpose(2,0,1);opaque=a[:,:,3]>127
 eyes,labels=components(opaque&(r>150)&(g>115)&(r-b>35)&(g-b>25))
 eyes=[v for v in eyes if v[1][4]>=3]
 if not eyes:return None
 eye_id,es,eye=min(eyes,key=lambda v:np.linalg.norm(v[2]-hint) if hint is not None else -v[1][4])
 eye_area=int(es[4]);lamps,_=components(opaque&(g>r*1.3)&(g>b*1.1)&(g>80))
 lamps=[v for v in lamps if np.linalg.norm(v[2]-eye)<math.sqrt(eye_area)*10]
 if not lamps:return None
 _,ls,lamp=min(lamps,key=lambda v:np.linalg.norm(v[2]-eye))
 up=lamp-eye;unit=up/max(1e-6,np.linalg.norm(up));back=np.array([-unit[1],unit[0]])*-1
 # 护耳是由深轮廓完整隔出的银色小块。不能取脸壳、肩甲或冠尾。
 silver=opaque&(rgb.max(2)-rgb.min(2)<55)&(rgb.mean(2)>85)
 candidates,sl=components(silver);choices=[]
 for i,stats,center in candidates:
  x,y,w,h,area=map(int,stats);v=center-eye;distance=np.linalg.norm(v)
  # 两三个孤立高光像素不是长方形护耳；护耳与头壳连通时回退额灯轴，
  # 不能拿下方颈甲的小亮块把实测倾角拉偏。
  if not .25*eye_area<=area<=2.1*eye_area or not 1.1*math.sqrt(eye_area)<=distance<=5*math.sqrt(eye_area):continue
  if max(w,h)/max(1,min(w,h))>3.5 or np.dot(v,back)<distance*.15:continue
  # 眼至额灯轴仅帮助找护耳，不用它截断头盔后再量长度。
  expected=eye+unit*np.linalg.norm(up)*.20+back*np.linalg.norm(up)*.86
  score=np.linalg.norm(center-expected)/distance+abs(math.log(max(.01,area/eye_area)/.45))*.12
  choices.append((score,i,stats,center))
 if not choices:
  return dict(eye=eye.tolist(),ear=None,lamp=lamp.tolist(),eye_area=eye_area,ear_area=None,eye_ear_distance=None,feature_angle_degrees=None)
 _,ei,ss,ear=min(choices,key=lambda v:v[0]);distance=float(np.linalg.norm(eye-ear))
 angle=math.degrees(math.atan2(*(eye-ear)[::-1]))
 return dict(eye=eye.tolist(),ear=ear.tolist(),lamp=lamp.tolist(),eye_area=eye_area,ear_area=int(ss[4]),
  eye_ear_distance=distance,feature_angle_degrees=angle,ear_bounds=[int(ss[0]),int(ss[1]),int(ss[0]+ss[2]),int(ss[1]+ss[3])])

def measure(im,hint=None):
 f=features(im,hint)
 if not f:return None
 base=features(Image.open(ROOT/'art/fighters/ultraseven/model/model-native.png').convert('RGBA'))
 eye=np.array(f['eye']);lamp=np.array(f['lamp'])
 if f['ear'] is not None:
  angle=f['feature_angle_degrees']-base['feature_angle_degrees'];center=(eye+f['ear'])/2
 else:
  v=lamp-eye;bv=np.array(base['lamp'])-base['eye']
  angle=math.degrees(math.atan2(v[1],v[0])-math.atan2(bv[1],bv[0]))
  center=eye-(lamp-eye)*.2
 angle=(angle+180)%360-180;theta=math.radians(angle);axis=np.array([math.sin(theta),-math.cos(theta)])
 a=np.array(im);yy,xx=np.indices(a.shape[:2]);projection=(xx-lamp[0])*axis[0]+(yy-lamp[1])*axis[1]
 # 实测倾角下的额灯平面只排除可摘冠；不再用姿势模板的头轴裁掉倾斜头壳。
 a[projection>0,3]=0
 # 冠尾或肩甲偶尔与脸壳同色连通。用眼—护耳局部坐标排除这两者，
 # 边界按同一旋转不变标尺同步放大，不采用旧检测的截断矩形。
 if f['ear'] is not None:
  ear=np.array(f['ear']);forward=eye-ear;scale=np.linalg.norm(forward)/base['eye_ear_distance'];forward/=np.linalg.norm(forward)
 else:
  scale=math.sqrt(f['eye_area']/base['eye_area']);forward=np.array([math.cos(theta+math.radians(base['feature_angle_degrees'])),math.sin(theta+math.radians(base['feature_angle_degrees']))]);ear=eye-forward*base['eye_ear_distance']*scale
 down=np.array([-forward[1],forward[0]]);u=(xx-ear[0])*forward[0]+(yy-ear[1])*forward[1];v=(xx-ear[0])*down[0]+(yy-ear[1])*down[1]
 a[(u<-2.5*scale)|(v>18.5*scale)|(v<-8*scale),3]=0
 from head_scale import measure as shell_measure
 m=shell_measure(Image.fromarray(a),'ultraman',center.tolist())
 if not m:return None
 return dict(m,method=VERSION,angle_degrees=angle,scale_ratio=m['length']/27.4197,
  eye_ear_scale_ratio=None if f['eye_ear_distance'] is None else f['eye_ear_distance']/base['eye_ear_distance'],**f)
