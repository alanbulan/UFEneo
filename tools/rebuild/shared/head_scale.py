"""头部尺度审计：保留原图来源与测量标记，不用姿势外框代替头部。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from collections import defaultdict
import argparse, hashlib, json, math, sys; json = _LayoutJson
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from production_io import read_json

ROOT=_LayoutProjectPath(_layout_root)
WORK=ROOT/'art/shared/production/head-scale'
OUT=ROOT/'reports/review/2026-10-22-head-scale'
def read(p):return read_json(p)
def save(p,v):
 # 原子写入：并行会话读同一JSON时不会读到半截内容。
 import art_phase2
 art_phase2.save(Path(p),v)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def font(n=16):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)

def measure(im,fighter,hint=None,direction=None,region=None):
 """初代测银色头壳长轴；杰顿测独立脸部发光体长轴。后脑/遮挡必须人工标注。"""
 a=np.asarray(im);rgb=a[:,:,:3].astype(int);r,g,b=rgb.transpose(2,0,1);opaque=a[:,:,3]>0
 if region is not None:
  # 标注只限制测量区域，不改任何人物像素；同一标注须映射到成品再次复测。
  selection=Image.new('1',im.size);ImageDraw.Draw(selection).polygon([tuple(p) for p in region],fill=1)
  opaque=opaque&np.asarray(selection)
 if fighter=='ultraman':
  mask=opaque&(rgb.max(2)-rgb.min(2)<48)&(rgb.mean(2)>105)
  mask=mask.astype('uint8')
 else:mask=(opaque&(r>150)&(g>60)&(r>g*1.05)&(b<110)).astype('uint8')
 n,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
 candidates=[]
 for i in range(1,n):
  x,y,w,h,area=map(int,stats[i]);pts=np.column_stack(np.where(labels==i)[::-1]).astype('float32')
  if area<(max(20,int(opaque.sum()*.007)) if fighter=='ultraman' else max(6,int(opaque.sum()*.002))):continue
  rect=cv2.minAreaRect(pts);dims=sorted([v+1 for v in rect[1]])
  if dims[0]<=1:continue
  hull=cv2.convexHull(pts).reshape(-1,2);diameter=float(np.sqrt(((hull[:,None,:]-hull[None,:,:])**2).sum(2)).max())+1
  aspect=dims[1]/dims[0]
  if fighter=='ultraman':
   # 银色头壳接近椭圆；躯干/长靴的长宽比通常更大。眼色邻域仅用于挑头，不测眼睛面积。
   near=(opaque&(r-b>35)&(g-b>25)&(r>160)&(g>130)).astype('uint8')
   grown=cv2.dilate((labels==i).astype('uint8'),np.ones((7,7),np.uint8))
   eyes=int((grown&near).sum());score=(100 if eyes else 0)+min(eyes,20)-abs(aspect-1.5)*5-y/im.height*8+min(area,500)*.015
  else:
   direction=direction or [0,-1]
   score=float(np.dot(centers[i],direction))/max(im.size)*100+min(aspect,4)*.1
  if hint is not None:score=-math.dist(centers[i],hint)/max(im.size)*500+min(area,500)*.003
  if region is not None:score=area  # 人工头部选区内取主要头壳，不能把眼内白块当头。
  candidates.append((score,{'length':round(diameter,4),'width':round(dims[0],4),'center':centers[i].tolist(),'polygon':cv2.boxPoints(rect).tolist(),'bounds':[x,y,x+w,y+h],'area':area,'aspect':aspect}))
 return max(candidates,key=lambda v:v[0])[1] if candidates else None

def pose_hint(request,index,size):
 guide=request.get('guide')
 if not guide:return None
 path=(ROOT/guide).parent/'poses.json'
 if not path.exists():return None
 data=read(path);frames=data.get('frames',[])
 if index>=len(frames) or 'joints' not in frames[index]:return None
 p=frames[index]['joints'];pts=np.array(list(p.values()));margin=request.get('pose_head_margin',29 if request.get('fighter')=='zetton' else 13)
 left=pts[:,0].min()-10;right=pts[:,0].max()+15;top=min(pts[:,1].min()-3,p['head'][1]-margin);bottom=pts[:,1].max()+3
 return [(p['head'][0]-left)/(right-left)*size[0],(p['head'][1]+4-top)/(bottom-top)*size[1]]

def pose_direction(request,index):
 guide=request.get('guide')
 if guide and ((ROOT/guide).parent/'poses.json').exists():
  frames=read((ROOT/guide).parent/'poses.json').get('frames',[])
  if index<len(frames) and 'joints' in frames[index]:
   p=frames[index]['joints'];v=np.array(p['head'])-np.array(p['neck']);return (v/max(1,np.linalg.norm(v))).tolist()
 return [0,-1]

def inventory():
 requests=[]
 for p in (ROOT/'art/fighters/ultraman/stage2/legacy/requests').glob('*.json'):
  q=read(p)
  requests.append((q.get('generation_dir',f'art/fighters/ultraman/stage2/generation/{p.stem}'),q,p))
 # 原始SHA索引也覆盖曾经外移的phase2质量记录。
 raw_by_sha={}
 for f in ['ultraman','zetton']:
  for p in (ROOT/'art/generation'/f).rglob('raw.png'):raw_by_sha[sha(p)]=p
 result=[]
 for f in ['ultraman','zetton']:
  m=read(ROOT/f'assets/fighters/{f}/animations/manifest.json')
  for action,c in m['clips'].items():
   cur=read(ROOT/c['curation']) if c.get('curation') else None
   atlas=Image.open(ROOT/c['texture'].removeprefix('res://')).convert('RGBA')
   source_set=read(ROOT/c['source_set'])['sources'] if c.get('source_set') else None
   for i,rect in enumerate(c['rects']):
    x,y,w,h=rect;im=atlas.crop((x,y,x+w,y+h));rec={}
    if cur:
     ci=c.get('sequence_frames',list(range(len(c['rects']))))[i]
     # 杰顿dash三段保存整条curation，rect索引即原atlas索引。
     if 'frames' not in cur:
      origin=cur['sources'][i];rec=read(ROOT/origin['curation'])['frames'][origin['sprite']]
     else:
      if len(cur['frames'])>len(c['rects']):ci=x//w
      rec=cur['frames'][ci]
    elif source_set:
     ci=c.get('sequence_frames',list(range(len(c['rects']))))[i]
     rec=next((r for r in source_set if r.get('sequence_frame',r['frame'])==ci),{})
    raw=rec.get('raw',rec.get('source_take'))
    source=rec.get('source','')
    if not source and f=='ultraman':
     legacy=ROOT/f'art/fighters/ultraman/stage2/legacy/gate_a_final/before/{action}/frame-{i}.png'
     if legacy.exists():source=legacy.relative_to(ROOT).as_posix()
    if not raw and source_set:raw=source
    if not raw and source:
     qp=ROOT/source;qp=qp.parent/'qa.json'
     if qp.exists():raw=read(qp).get('source')
    if not raw or not (ROOT/raw).exists():
     digest=rec.get('raw_sha256',c.get('source_sha256'))
     if digest in raw_by_sha:raw=raw_by_sha[digest].relative_to(ROOT).as_posix()
    if action=='crouch' and f=='ultraman':
     candidates=sorted((ROOT/f'art/fighters/ultraman/stage2/generation/phase3_crouch/frame-{i:02}').glob('[0-9][0-9]/raw.png'))
     if candidates:raw=candidates[-1].relative_to(ROOT).as_posix()
    matched=[(q,p) for gd,q,p in requests if raw and raw.startswith(gd+'/')]
    q,p=matched[0] if matched else ({},None)
    if source_set:source_i=0
    else:source_i=rec.get('source_frame')
    if source_i is None:
     try:source_i=int(Path(source).stem.split('-')[-1])
     except ValueError:source_i=i
    if int(q.get('frames',99))==1:source_i=0
    result.append({'fighter':f,'action':action,'frame':i,'raw':raw,'raw_exists':bool(raw and (ROOT/raw).is_file()),'request':p.relative_to(ROOT).as_posix() if p else None,'raw_frame':source_i,'source':source,'old_atlas':c['texture'].removeprefix('res://'),'old_rect':rect,'old_head':measure(im,f)})
 save(WORK/'inventory.json',result)
 print('frames',len(result),'missing raw',sum(not r['raw_exists'] for r in result),'missing request',sum(not r['request'] for r in result),'missing head',sum(not r['old_head'] for r in result))
 for r in result:
  if not r['raw_exists'] or not r['request']:print(r['fighter'],r['action'],r['frame'],r['raw'],r['request'])
 return result

def audit(probe=False,fresh=False,fighter_filter=None,resume=False):
 """先在开发目录重处理；超差绝不安装，也不逐帧修比例。"""
 sys.path.insert(0,str(Path(__file__).resolve().parent));import process_phase2 as proc
 rows=read(WORK/'inventory.json');groups=defaultdict(list)
 for row in rows:
  if row['raw_exists']:groups[(row['fighter'],row['raw'])].append(row)
 baselines={f:measure(Image.open(ROOT/f'assets/fighters/{f}/model-native.png').convert('RGBA'),f) for f in ['ultraman','zetton']}
 if not fighter_filter:save(WORK/'baselines.json',baselines)
 results=[];atlas_cache={};converted={}
 annotations=read(WORK/'measurement-regions.json') if (WORK/'measurement-regions.json').exists() else []
 regions={(r['fighter'],r['raw'],r['raw_frame']):r['region'] for r in annotations}
 probe_data=read(WORK/'probe.json') if not fresh and not probe and (WORK/'probe.json').exists() else None
 probe_rows={(r['fighter'],r['action'],r['frame']):r for r in probe_data['rows']} if probe_data else {}
 suffix='-'+fighter_filter if fighter_filter else ''
 progress=WORK/f'audit-in-progress{suffix}.json'
 prior_path=progress if progress.exists() else WORK/'audit-in-progress.json'
 prior=read(prior_path)['rows'] if (resume or not fresh) and not probe and prior_path.exists() else []
 cached={(r['fighter'],r['action'],r['frame']):r for r in prior}
 for (f,rawpath),members in groups.items():
  if fighter_filter and f!=fighter_filter:continue
  if resume and all((f,r['action'],r['frame']) in cached and cached[(f,r['action'],r['frame'])].get('head_region') and cached[(f,r['action'],r['frame'])].get('output') and cached[(f,r['action'],r['frame'])]['source_sha256']==sha(ROOT/rawpath) for r in members):
   results.extend(cached[(f,r['action'],r['frame'])] for r in members);continue
  raw=Image.open(ROOT/rawpath).convert('RGBA');request=read(ROOT/members[0]['request']) if members[0]['request'] else {'columns':1,'rows':1,'frames':1}
  if probe_data:
   selected_rows=[probe_rows[(f,r['action'],r['frame'])] for r in members]
   if all((f,r['action'],r['frame']) in cached and r.get('source')==cached[(f,r['action'],r['frame'])].get('source') and r.get('shared_scale')==cached[(f,r['action'],r['frame'])].get('shared_scale') and r.get('raw_head')==cached[(f,r['action'],r['frame'])].get('raw_head') and cached[(f,r['action'],r['frame'])].get('output') and (ROOT/cached[(f,r['action'],r['frame'])]['output']).is_file() for r in selected_rows):
    results.extend(cached[(f,r['action'],r['frame'])] for r in selected_rows);continue
  try:cells=proc.grid_figures(raw,request['columns'],request['rows'],request['frames'])
  except ValueError as e:
   for r in members:results.append(dict(**r,status='blocked',reason=str(e)))
   continue
  heads=[]
  for ci,crop in enumerate(cells):
   # 仅检测用缩图；正式转换仍用完整原图和sprite-gen。
   h=measure(crop,f,direction=pose_direction(request,ci),region=regions.get((f,rawpath,ci)))
   heads.append(h)
  selected={r['raw_frame'] for r in members}
  lengths=[h['length'] for ci,h in enumerate(heads) if h and ci in selected]
  # 选择最大与最小测量的中点，使同一原图最大绝对相对偏差最小；不分别缩帧。
  factor=2*baselines[f]['length']/(min(lengths)+max(lengths)) if lengths else None
  if probe_data:
   for r in members:
    pr=probe_rows[(f,r['action'],r['frame'])]
    if pr.get('raw_head') is not None:heads[r['raw_frame']]=pr['raw_head']
   factor=selected_rows[0].get('shared_scale',factor)
  for r in members:
   i=r['raw_frame']
   if i>=len(cells):results.append(dict(**r,status='blocked',reason='来源帧序超出原图，需核对'));continue
   head=heads[i]
   if head is None or factor is None:results.append(dict(**r,status='blocked',reason='头部未可靠识别，需人工标注'));continue
   if probe:
    dev=(head['length']*factor/baselines[f]['length']-1)*100
    results.append(dict(**r,raw_head=head,shared_scale=factor,raw_head_deviation_percent=dev,status='blocked' if abs(dev)>8 else 'candidate_pending_review'))
    continue
   crop=cells[i];width=round(crop.width*factor);height=round(crop.height*factor)
   cache_key=(rawpath,i,width,height)
   if cache_key not in converted:
    snapped,pitch,phase=proc.snap_for_scale(crop,factor)
    im=proc._kcentroid_downscale(snapped,width,height);proc.binarize_alpha(im);im=proc.apply_palette(im,read(ROOT/f'content/fighters/{f}/palette.json')['colors'])
    converted[cache_key]=im
   im=converted[cache_key].copy()
   fragments=[]
   for component in proc.components(im)[1:]:
    if len(component)<=2:
     for xy in component:im.putpixel(xy,(0,0,0,0))
    else:fragments.append(len(component))
   # 先按旧成品整帧仿射登记新图；不拆肢体，保留根点与原有空中摆位。
   if r['old_atlas'] not in atlas_cache:atlas_cache[r['old_atlas']]=Image.open(ROOT/r['old_atlas']).convert('RGBA')
   x,y,w,h=r['old_rect'];old=atlas_cache[r['old_atlas']].crop((x,y,x+w,y+h));bounds=old.getbbox();sx=width/(bounds[2]-bounds[0]);sy=height/(bounds[3]-bounds[1]);ox,oy=w/2,h-8
   # 只保留GPT原生色；永久禁止迁移旧区域调色差值或颜色标签。
   left=round(ox+(bounds[0]-ox)*sx);top=round(oy+(bounds[1]-oy)*sy)
   # 开发候选可扩透明画布，原点用显式anchor保存；不裁人物、不放大像素。
   pad_x=max(0,-left,left+width-w);pad_y=max(0,-top,top+height-h)
   canvas=Image.new('RGBA',(w+2*pad_x,h+2*pad_y));canvas.alpha_composite(im,(left+pad_x,top+pad_y))
   dest=WORK/'candidates'/f/r['action']/f'frame-{r["frame"]}.png';dest.parent.mkdir(parents=True,exist_ok=True);canvas.save(dest)
   native_hint=[left+pad_x+head['center'][0]*factor,top+pad_y+head['center'][1]*factor]
   raw_region=regions.get((f,rawpath,i),head['polygon'])
   native_region=[[left+pad_x+x*factor,top+pad_y+y*factor] for x,y in raw_region]
   measured=measure(canvas,f,native_hint,region=native_region);deviation=(measured['length']/baselines[f]['length']-1)*100 if measured else None
   raw_deviation=(head['length']*factor/baselines[f]['length']-1)*100
   issues=[]
   if fragments:issues.append('存在游离身体碎片，禁止安装')
   if deviation is None or abs(deviation)>8:issues.append('成品头部尺寸超出±8%或未可靠识别')
   results.append(dict(**r,status='blocked' if issues else 'candidate_pending_review',issues=issues,raw_head=head,head_region=native_region,shared_scale=factor,new_head=measured,head_deviation_percent=deviation,raw_head_deviation_percent=raw_deviation,output=dest.relative_to(ROOT).as_posix(),anchor=[ox+pad_x,oy+pad_y],old_to_new={'scale':[sx,sy],'translation':[left-bounds[0]*sx+pad_x,top-bounds[1]*sy+pad_y]},source_sha256=sha(ROOT/rawpath),image_sha256=sha(dest)))
  if not probe:save(progress,{'baseline':baselines,'rows':results,'installed':False})
  print(f,Path(rawpath).parent.as_posix(),flush=True)
 save(WORK/('probe.json' if probe else f'audit{suffix}.json'),{'schema':1,'baseline':baselines,'rows':results,'missing_raw':[r for r in rows if not r['raw_exists']],'installed':False,'generation_requests':0})
def probe():audit(True)

def gallery():
 rows=read(WORK/'inventory.json');OUT.mkdir(parents=True,exist_ok=True)
 for f in ['ultraman','zetton']:
  group=[r for r in rows if r['fighter']==f]
  for page in range(math.ceil(len(group)/80)):
   selected=group[page*80:(page+1)*80];sheet=Image.new('RGB',(1600,math.ceil(len(selected)/10)*200),'#242e3b');d=ImageDraw.Draw(sheet)
   for j,r in enumerate(selected):
    x,y,w,h=r['old_rect'];im=Image.open(ROOT/r['old_atlas']).crop((x,y,x+w,y+h)).convert('RGBA')
    # 仅预览缩至128x128；坐标/测量一律仍取原生帧。
    scale=128/im.height;shown=im.resize((round(im.width*scale),128),Image.Resampling.NEAREST);ox=j%10*160;oy=j//10*200;sheet.paste(shown,(ox,oy+50),shown)
    head=r['old_head']
    if head:
     pts=[(ox+p[0]*scale,oy+50+p[1]*scale) for p in head['polygon']];d.line(pts+[pts[0]],fill='#50ff80',width=2)
    d.text((ox+2,oy+2),f'{r["action"]}\n#{r["frame"]} '+(str(round(head['length'],1)) if head else 'MISSING'),font=font(12),fill='white')
   sheet.save(OUT/f'{f}-head-detection-{page}.png')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['inventory','gallery','audit','probe']);p.add_argument('--fresh',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--fighter',choices=['ultraman','zetton']);args=p.parse_args()
 audit(fresh=args.fresh,fighter_filter=args.fighter,resume=args.resume) if args.command=='audit' else globals()[args.command]()
