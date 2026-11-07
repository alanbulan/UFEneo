"""躺姿身长使用定稿真实骨长；只读测量，绝不据此外框缩放人物。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import math
import numpy as np
from PIL import Image,ImageDraw
from head_scale import ROOT,read,save,sha
import head_size

REFERENCES=ROOT/'art/fighters/ultraseven/stage4/revisions/seven-body-fix/body-references.json'
JOINTS=['head_top','neck','hip','knee','ankle','toe']
TOLERANCE=.08

def reference(fighter):
 data=read(REFERENCES)['fighters'][fighter]
 if sha(ROOT/data['image'])!=data['image_sha256']:raise ValueError(fighter+'定稿变化，须重新标真实骨长')
 points=[data['joints'][k] for k in JOINTS]
 segments=[math.dist(a,b) for a,b in zip(points,points[1:])]
 return dict(**data,length=sum(segments),segments=dict(zip(['head','torso','thigh','shin','foot'],segments)),method='定稿实测头顶→颈→胯→膝→踝→脚尖的中心骨链总长；不使用站姿外框高度')

def measure(im,headrow,fighter='ultraseven',landmarks=None):
 if landmarks:
  points=landmarks.get('path') or [landmarks['head_top'],landmarks['foot']]
  return dict(head_top=points[0],foot=points[-1],path=points,length=sum(math.dist(a,b) for a,b in zip(points,points[1:])),method=landmarks['reason'])
 m=head_size.head(im,fighter,headrow.get('hint'),direction=headrow.get('direction'),region=headrow.get('region'),method='eye-ear-v2' if fighter=='ultraseven' else None)
 if not m:return None
 a=np.array(im);rgb=a[:,:,:3].astype(int);opaque=a[:,:,3]>0;yy,xx=np.where(opaque);center=np.array(m['center'])
 # 初代银靴、杰顿黑靴不能沿用赛文红靴的颜色筛选；先找远离头部的身体端点。
 body=opaque if fighter!='ultraseven' else opaque&(rgb[:,:,0]>60)&(rgb[:,:,0]>rgb[:,:,1]*1.7)&(rgb[:,:,0]>rgb[:,:,2]*1.5)
 ry,rx=np.where(body)
 if not len(rx):return None
 pts=np.c_[rx,ry];foot=pts[np.linalg.norm(pts-center,axis=1).argmax()];axis=(foot-center)/np.linalg.norm(foot-center)
 # 固定头壳和外置冠/触角必须分开。旧尺会抓住头镖后尾或杰顿横伸触角，
 # 也会把初代举起的手当脚；明示关节标注优先，绝不反推参考长度。
 if fighter in ['ultraman','ultraseven']:
  from PIL import ImageDraw
  sel=Image.new('1',im.size);ImageDraw.Draw(sel).polygon([tuple(p) for p in m['polygon']],fill=1)
  fixed=opaque&np.asarray(sel)&(rgb.max(2)-rgb.min(2)<55)&(rgb.mean(2)>85)
  hy,hx=np.where(fixed);headpoints=np.c_[hx,hy]
 else:
  headpoints=np.c_[xx,yy];headpoints=headpoints[np.linalg.norm(headpoints-center,axis=1)<m['length']*.65]
 if not len(headpoints):return None
 projection=(headpoints-center)@axis
 # 头顶细鳍/冠尾的单一极值不是头骨；头壳前10%边缘像素取稳健端点。
 limit=np.quantile(projection,.10)
 top=headpoints[np.abs(projection-limit).argmin()]
 return dict(head_top=top.tolist(),foot=foot.tolist(),length=float(np.linalg.norm(foot-top)),head_center=center.tolist(),method='伸展躺姿头部轴向端点至脚尖；弯曲/抬头/足尖回勾须显式标注中心骨链，不能拿手或外框代替')

def validate_folder(folder,fighter,action):
 folder=ROOT/folder;config=folder/'body-length-policy.json'
 if not config.exists():
  if fighter=='ultraseven' and action=='down':raise ValueError('躺倒帧缺少强制身长校验配置')
  return []
 policy=read(config);q=read(folder/'head-qa.json');ref=reference(fighter)
 rows=[];issues=[];annotated=read(folder/'body-landmarks.json') if (folder/'body-landmarks.json').exists() else {}
 for i in policy['frames']:
  row=q['frames'][i];p=folder/row['image'];im=Image.open(p).convert('RGBA');mark=annotated.get(str(i))
  if mark and mark.get('image_sha256')!=sha(p):raise ValueError(f'frame {i}: 身长关节点与像素指纹不符')
  m=measure(im,row,fighter,mark);good=m is not None and abs(m['length']/ref['length']-1)<=TOLERANCE
  rows.append(dict(frame=i,reference_length=ref['length'],measurement=m,deviation_percent=None if m is None else (m['length']/ref['length']-1)*100,pass_=good))
  if not good:issues.append(f'frame {i}: 躺倒身长相对定稿伸直骨长超±8%或不可测')
 save(folder/'body-length-qa.json',dict(reference=ref,frames=rows,issues=issues))
 if issues:raise ValueError('; '.join(issues))
 return rows
