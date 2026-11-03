"""人物整帧的微小游离连通块检查；合法道具只接受逐帧、逐块指纹白名单。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import cv2
import numpy as np
from PIL import Image
from head_scale import ROOT,read,save

WHITELIST=ROOT/'content/presentation/detached-parts.json'

def components(im):
 a=np.array(im.getchannel('A'))>0
 n,labels,stats,_=cv2.connectedComponentsWithStats(a.astype('uint8'),8)
 if n<=2:return []
 main=1+int(stats[1:,cv2.CC_STAT_AREA].argmax());result=[]
 for k in range(1,n):
  if k==main or stats[k,cv2.CC_STAT_AREA]>20:continue
  x,y,w,h,area=map(int,stats[k]);mask=labels[y:y+h,x:x+w]==k
  result.append(dict(bounds=[x,y,x+w,y+h],area=area,mask_sha256=hashlib.sha256(mask.tobytes()).hexdigest()))
 return result

def check(im,fighter,action,index):
 allow=read(WHITELIST).get('parts',[]) if WHITELIST.exists() else []
 result=[]
 for c in components(im):
  approved=next((p for p in allow if p['fighter']==fighter and p['action']==action and p['frame']==index and p['bounds']==c['bounds'] and p['area']==c['area'] and p['mask_sha256']==c['mask_sha256'] and p.get('reason')),None)
  result.append(dict(c,allowed=approved is not None,reason=approved.get('reason') if approved else None))
 return result

def validate_folder(folder,fighter,action):
 folder=ROOT/folder;hq=read(folder/'head-qa.json');rows=[];issues=[]
 for r in hq['frames']:
  found=check(Image.open(folder/r['image']).convert('RGBA'),fighter,action,r['frame'])
  rows.append(dict(frame=r['frame'],components=found))
  if any(not c['allowed'] for c in found):issues.append(f'frame {r["frame"]}: 面积≤20像素的游离块未登记')
 save(folder/'island-qa.json',dict(connectivity=8,maximum_area=20,frames=rows,issues=issues))
 if issues:raise ValueError('; '.join(issues))
 return rows
