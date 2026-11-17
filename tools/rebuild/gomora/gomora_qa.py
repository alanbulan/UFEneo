"""哥莫拉分支标尺。只测量，不按区域换色；不改其他角色的质检行为。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
import json,math,sys,hashlib; json = _LayoutJson
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from functools import lru_cache

ROOT=_LayoutProjectPath(_layout_root)
WORK=ROOT/'art/fighters/gomora/stage4/pilot/gomora'
OUT=ROOT/'reports/review/2026-10-22/gomora-batch2'
MODEL=ROOT/'art/fighters/gomora/model/model-native.png'
CELL=(512,320);ANCHOR=(256,304)

def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else x.tolist())+'\n','utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def font(n=20):return ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',n)

def polyline_length(points):return sum(math.dist(a,b) for a,b in zip(points,points[1:]))

def prepare_ruler():
 WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 if (WORK/'ruler.json').exists():return read(WORK/'ruler.json')
 im=Image.open(MODEL).convert('RGBA')
 pts=dict(eye=[237,103],nose_root=[246,110],ear_root=[219,98],skull_top=[228,94],jaw=[236,120],
   hip=[190,176],knee_near=[167,207],ankle_near=[153,239],toe_near=[173,245],
   knee_far=[221,200],ankle_far=[224,238],toe_far=[251,244],shoulder=[209,118],neck=[220,115],head=[229,103])
 skull=[[218,94],[230,94],[241,99],[248,107],[240,120],[233,119],[221,106]]
 tail=[[177,178],[159,197],[141,210],[121,215],[104,209],[86,195],[70,175],[56,155],[45,140],[42,127],[44,119]]
 horns=dict(near=[[196,56],[190,70],[195,86],[211,100],[226,107],[229,100],[220,87],[204,74]],far=[[233,68],[226,83],[239,93]])
 bones={k:round(math.dist(pts[a],pts[b]),4) for k,a,b in [('thigh','hip','knee_near'),('shin','knee_near','ankle_near'),('torso','hip','shoulder'),('neck','neck','head'),('foot','ankle_near','toe_near')]}
 ruler=dict(schema=1,fighter='gomora',model=rel(MODEL),model_sha256=sha(MODEL),model_canvas=list(im.size),runtime_cell=list(CELL),runtime_anchor=list(ANCHOR),
  standing_height=192,standing_height_note='脚底248到最高近侧月牙耳角56，含耳角；不含耳角的颅骨顶94至脚底为154。直立门比较同样含角的192，不能把尾尖当头顶。',
  skull_standing_height=154,landmarks=pts,skull_polygon=skull,skull_area=float(cv2.contourArea(np.array(skull,dtype='float32'))),
  head_metric='固定颅骨面积平方根（排除耳角/鼻角/脖颈），辅以眼中心—耳角根与鼻角根距离；旋转不变。模板定位失败转人工标点，禁止按姿态外框量头。',
  head_tolerance=.08,bones=bones,tail_centerline=tail,tail_length=polyline_length(tail),tail_tolerance=.10,
  tail_policy='软门，沿尾根到尾尖中轴线实测；卷曲仍测曲线；先交真实帧人工审片，不以外框代替尾长。',horn_polygons=horns,
  horn_policy='眼睛/耳根定位后旋转校正；剪影比对只标需人工复核，不作硬拦截。',postprocess='整帧网格还原、kCentroid、二值Alpha、整图固定调色板量化；禁止区域换色')
 save(WORK/'ruler.json',ruler)
 im.crop((186,52,264,126)).resize((624,592),Image.Resampling.NEAREST).save(WORK/'head-reference-x8.png')
 ann=im.resize((1536,1024),Image.Resampling.NEAREST).convert('RGBA');d=ImageDraw.Draw(ann)
 for k,p in pts.items():
  x,y=np.array(p)*4;d.ellipse((x-4,y-4,x+4,y+4),fill='#24e6ff');d.text((x+5,y),k,font=font(14),fill='white')
 d.line([tuple(np.array(p)*4) for p in tail],fill='#ef5cf0',width=3)
 d.polygon([tuple(np.array(p)*4) for p in skull],outline='#ffff55',width=3)
 ann.save(OUT/'ruler-x4.png')
 return ruler

def eye(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
 # 眼睛金黄与腹部浅褐必须分开；不能把大片鳞甲高光当作眼。
 m=((a[:,:,3]>128)&(r>220)&(g>140)&(b<90)&(r-g>15)&(g-b>90)).astype('uint8')
 n,l,s,c=cv2.connectedComponentsWithStats(m,8)
 # 小眼睛在倾斜/低蹲的原生量化帧中可能只剩1px。它仅用于定位，
 # 头部大小仍由旋转后的完整颅骨模板量取，不能用眼像素面积定比例。
 candidates=[i for i in range(1,n) if s[i,4]>=1]
 if not candidates:return None
 i=max(candidates,key=lambda i:s[i,4]);return dict(center=c[i].tolist(),area=int(s[i,4]),box=s[i,:4].tolist())

@lru_cache(maxsize=1)
def _template():
 ruler=prepare_ruler();im=Image.open(MODEL).convert('RGBA');box=(214,90,250,122)
 p=np.array(ruler['skull_polygon'])-box[:2];mask=Image.new('L',(36,32));ImageDraw.Draw(mask).polygon([tuple(x) for x in p],fill=255)
 return np.array(im.crop(box))[:,:,:3],np.array(mask),box

def head(im,expected_scale=1.,angles=None,hint=None):
 """在眼睛附近匹配固定头壳；旋转和尺度同时搜索。匹配值仅作定位置信度。"""
 # 临时测量裁片的鼻角靠近边缘；模板的透明搜索余量不能使尺度误向小值。
 pad=round(80*expected_scale);padded=Image.new('RGBA',(im.width+2*pad,im.height+2*pad));padded.alpha_composite(im,(pad,pad));im=padded
 e=eye(im)
 detected=e is not None
 if not e and hint is not None:e=dict(center=(np.array(hint)+pad).tolist(),area=0)
 if not e:return None
 a=np.array(im);source=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2LAB).astype('float32')/255
 template,mask,box=_template();best=None
 # 在较小的临时测量图搜头，不用人物外框决定头大小。
 ex,ey=e['center'];angles=angles if angles is not None else list(range(-60,61,10))
 for angle in angles:
  for scale in sorted(set(np.r_[np.linspace(expected_scale*.72,expected_scale*1.30,25),expected_scale])):
   side=max(1,round(64*scale));mat=cv2.getRotationMatrix2D((18,16),angle,scale)
   mat[:,2]+=[side/2-18,side/2-16]
   t=cv2.warpAffine(template,mat,(side,side),flags=cv2.INTER_NEAREST)
   m=cv2.warpAffine(mask,mat,(side,side),flags=cv2.INTER_NEAREST)
   if (m>0).sum()<20:continue
   # 眼部已由金黄色材质独立定位，限定同一眼附近的模板平移。
   # 不在整张头部邻域穷举位置，也不先缩图，避免原生小头的二次采样误差。
   me=np.array([22.166666667,13.333333333,1.]);eye_in_template=mat@me;margin=max(3,math.ceil(4*scale))
   xmin=max(0,math.floor(ex-eye_in_template[0])-margin);ymin=max(0,math.floor(ey-eye_in_template[1])-margin)
   xmax=min(im.width,xmin+side+2*margin+2);ymax=min(im.height,ymin+side+2*margin+2)
   region=source[ymin:ymax,xmin:xmax]
   if min(region.shape[:2])<side:continue
   t=cv2.cvtColor(t,cv2.COLOR_RGB2LAB).astype('float32')/255
   score=cv2.matchTemplate(region,t,cv2.TM_SQDIFF_NORMED,mask=m)
   score[~np.isfinite(score)]=9
   _,_,loc,_=cv2.minMaxLoc(score);value=float(score[loc[1],loc[0]])
   pred=mat@me+np.array(loc)+[xmin,ymin]
   value+=math.dist(pred,e['center'])/max(1,scale)*.01
   if best is None or value<best[0]:best=(value,scale,angle,mat,loc,xmin,ymin)
 if best is None:return None
 val,scale,angle,mat,loc,xmin,ymin=best;ruler=prepare_ruler()
 transform=lambda p:(mat@np.r_[np.array(p)-box[:2],1]+np.array(loc)+[xmin-pad,ymin-pad]).tolist()
 polygon=[transform(p) for p in ruler['skull_polygon']]
 return dict(length=math.sqrt(ruler['skull_area'])*scale,scale=float(scale),angle=angle,score=val,eye=(np.array(e['center'])-pad).tolist(),eye_area=e['area'],polygon=polygon,
  center=np.array(polygon).mean(0).tolist(),nose_root=transform(ruler['landmarks']['nose_root']),ear_root=transform(ruler['landmarks']['ear_root']),method='rotation-corrected-fixed-skull-template-v1',eye_detected=detected,eye_locator='成品黄色眼睛' if detected else 'GPT原图眼睛经整帧统一变换定位；成品眼点不可分离，头壳仍独立匹配',needs_manual=val>.11 or not detected)

def facing_head(im,expected_scale=1.,angles=None,facing='right',hint=None):
 if facing!='left':return head(im,expected_scale,angles,hint)
 h=head(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),expected_scale,angles,[im.width-1-hint[0],hint[1]] if hint is not None else None)
 if h:
  for k in ['eye','center','nose_root','ear_root']:h[k][0]=im.width-1-h[k][0]
  h['polygon']=[[im.width-1-x,y] for x,y in h['polygon']];h['facing']='left'
 return h

def islands(im):
 a=np.array(im);n,l,s,c=cv2.connectedComponentsWithStats((a[:,:,3]>0).astype('uint8'),8)
 main=max(range(1,n),key=lambda i:s[i,4]) if n>1 else None
 return [dict(area=int(s[i,4]),bounds=s[i,:4].tolist()) for i in range(1,n) if i!=main and s[i,4]<=20]

def horn_review(im,h):
 """按头壳的旋转/倾斜对齐角的模板，只输出审片参考，不设拒收阈值。"""
 if not h:return dict(status='需人工复核：背面/遮挡，不能用纯侧面轮廓打分',parts={})
 ruler=prepare_ruler();src=np.float32([ruler['skull_polygon'][i] for i in [0,2,4]]);dst=np.float32([h['polygon'][i] for i in [0,2,4]])
 transform=cv2.getAffineTransform(src,dst);alpha=(np.array(im)[:,:,3]>0).astype('uint8');model=Image.open(MODEL).convert('RGBA');parts={}
 for name,polygon in dict(**ruler['horn_polygons'],nose=[[246,110],[260,98],[254,114],[248,117]]).items():
  mask=Image.new('L',model.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in polygon],fill=1);m=np.array(mask)*(np.array(model)[:,:,3]>0)
  target=cv2.warpAffine(m,transform,im.size,flags=cv2.INTER_NEAREST)>0
  if not target.any():parts[name]=dict(status='模板不在画布内，需人工复核');continue
  yy,xx=np.where(target);x0=max(0,int(xx.min())-3);x1=min(im.width,int(xx.max())+4);y0=max(0,int(yy.min())-3);y1=min(im.height,int(yy.max())+4)
  actual=alpha[y0:y1,x0:x1]>0;ref=target[y0:y1,x0:x1];overlap=float((actual&ref).sum()/max(1,(actual|ref).sum()))
  parts[name]=dict(roi=[x0,y0,x1,y1],tilt_corrected_iou=overlap,note='区域内含角根相邻头壳，数值只作人工定位参考，不能当身份通过结论')
 return dict(status='需人工复核，角度已按眼部/耳根模板旋转校正；没有硬阈值',angle=h['angle'],parts=parts)

def foot_origin(im,bottom=None,facing='right'):
 """脚爪标尺排除长尾；定稿同一套爪尖→脚底根的偏移，不用眼睛平移人物。"""
 a=np.array(im);r,g,b=a[:,:,:3].transpose(2,0,1);bottom=bottom if bottom is not None else im.getbbox()[3]
 yy,xx=np.where((a[:,:,3]>0)&(r>=230)&(g>=210)&(b>=170)&(np.indices(a.shape[:2])[0]>=bottom-25))
 if not len(xx):return None
 columns=np.unique(xx);groups=np.split(columns,np.where(np.diff(columns)>16)[0]+1)
 spans=[[int(v[0]),int(v[-1])] for v in groups if len(v)>=2]
 if not spans:return None
 toes=float(np.mean([(a+b)/2 for a,b in spans]));offset=12.5 if facing=='right' else -12.5
 return dict(x=toes-offset,claw_spans=spans,reference_toe_offset=offset,method='定稿双足象牙色趾爪中点减去同一12.5px根偏移；不含尾巴，不以眼部目标平移')

def tail_measure(im,root=None,side='left'):
 """Alpha内偏向中轴的最短路。软测量：根点和尖端均画出，供人工核对。"""
 import heapq
 a=np.array(im)[:,:,3]>0;h,w=a.shape
 if root is None:root=prepare_ruler()['tail_centerline'][0]
 root=np.array(root,dtype=float);yy,xx=np.where(a)
 start_index=np.argmin((xx-root[0])**2+(yy-root[1])**2);start=(int(yy[start_index]),int(xx[start_index]))
 region=(xx<root[0]-90) if side=='left' else (xx>root[0]+100)
 if not region.any():return dict(status='需人工复核：看不清独立尾尖',length=None)
 tx,ty=xx[region],yy[region]
 if side=='left':idx=int(np.argmin(ty));end=(int(ty[idx]),int(tx[idx]))
 else:idx=int(np.argmax(tx));end=(int(ty[idx]),int(tx[idx]))
 distance=cv2.distanceTransform(a.astype('uint8'),cv2.DIST_L2,5);cost=np.full((h,w),np.inf);cost[start]=0;queue=[(0,*start)];previous={};offsets=[(dy,dx,math.hypot(dx,dy)) for dy in [-1,0,1] for dx in [-1,0,1] if dx or dy]
 while queue:
  val,y,x=heapq.heappop(queue)
  if val>cost[y,x]:continue
  if (y,x)==end:break
  for dy,dx,length in offsets:
   ny,nx=y+dy,x+dx
   if not 0<=ny<h or not 0<=nx<w or not a[ny,nx]:continue
   v=val+length*(1+18/(distance[ny,nx]+1)**2)
   if v<cost[ny,nx]:cost[ny,nx]=v;previous[(ny,nx)]=(y,x);heapq.heappush(queue,(v,ny,nx))
 if end not in previous:return dict(status='需人工复核：尾部与主体路径不连通',length=None)
 path=[end]
 while path[-1]!=start:path.append(previous[path[-1]])
 path=path[::-1];length=sum(math.dist(p,q) for p,q in zip(path,path[1:]));line=[[int(x),int(y)] for y,x in path]
 return dict(status='软检查，需人工确认尾根/尾尖及中轴；不作拒收门',length=length,root=[start[1],start[0]],tip=[end[1],end[0]],centerline=line)

def validate_frame(im,h,standing=False,hidden=False,standing_target=192):
 issues=[];a=np.array(im)
 soft=head_v2_review(im,h,hidden=hidden)
 if islands(im):issues.append('island: 存在≤20px游离块')
 if len(np.unique(a[a[:,:,3]>0,:3],axis=0))>32:issues.append('palette: 超过32色')
 if not np.isin(a[:,:,3],[0,255]).all():issues.append('alpha: Alpha未二值化')
 b=im.getbbox()
 if not b or b[0]<2 or b[1]<2 or b[2]>im.width-2 or b[3]>im.height-2:issues.append('layout: 人物贴边/裁切')
 height=ANCHOR[1]-b[1] if b else 0
 if standing and abs(height/standing_target-1)>.03:issues.append(f'standing: 含耳角站高{height}px相对骨架{standing_target}px超±3%')
 return dict(issues=issues,head=h,head_v2=soft,standing_height=height,standing_target=standing_target,standing_required=standing,islands=islands(im),tail_status='尾根/尾尖标点，纯人工复核；不再自动量尾长',horn_status='需人工倾斜校正复核')

def head_v2_review(im,locator=None,facing='right',hidden=False):
 """复用第三批只读标尺；已有头壳测量仅作定位历史，不再硬判头部。"""
 import gomora_head_v2 as v2
 measured=None if hidden else v2.measure(im,facing=facing,
  angle=locator.get('angle',0) if locator else 0,
  hint=locator.get('eye') if locator else None)
 deviation=(measured['scale']-1)*100 if measured else None
 flags=[]
 if measured is None:flags.append('背面/遮挡/眼鼻角不可测，需人工复核')
 elif measured.get('needs_manual'):flags.append('眼心/鼻角定位歧义，需人工复核')
 if deviation is not None and abs(deviation)>8:flags.append('眼心—鼻角尖偏差超±8%，需人工复核')
 return dict(measurement=measured,deviation_percent=deviation,flags=flags,
  hard_gate=False,policy=v2.policy(),metric='眼心到鼻角尖的欧氏距离，v2.1',
  marker='需人工复核' if flags else '数值在±8%内，仍待用户审片')

def hard_issues(issues):
 """保留原始QA记录，只将旧头壳硬判改成v2软审片，不放宽其余门。"""
 return [issue for issue in issues if not issue.startswith('head:') and ': head:' not in issue]

def selftest():
 im=Image.open(MODEL).convert('RGBA');out=[]
 for angle in [0,30,-30,60]:
  # 只旋转测量试件，绝不是运行人物或生成输入。
  test=im.rotate(angle,resample=Image.Resampling.NEAREST,expand=True);h=head(test)
  out.append(dict(angle=angle,measurement=h));assert h and abs(h['scale']-1)<.08,(angle,h)
 save(OUT/'ruler-selftest.json',dict(tests=out,note='测量试件旋转用于验证角度不变性；绝不作为动作帧安装。'))
 print('哥莫拉标尺旋转自测完成')

if __name__=='__main__':selftest()
