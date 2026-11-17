"""R03内置完整候选：固定统一尺度、两向两层序及离背平移诊断；不安装。"""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'tools/rebuild/shared'),str(Path(__file__).parent)]
import forge_backend as forge
from resume import FORGE_SHA,ACTOR_OUT
assert forge.backend_info()['files']==FORGE_SHA
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r03-20261105/candidate.png'
assert sha(p)=='efd543af4e5be3dd460f36e77aa580421aa74bee6fa222df881efb33756bd340'
s=Image.open(p);assert s.mode=='RGBA' and s.size==(1774,887)
im=forge.binarize_alpha(s.copy());im=forge._kcentroid_downscale(im,220,110);forge.binarize_alpha(im)
out=ROOT/'reports/gomora-builtin/r03-review';out.mkdir(parents=True,exist_ok=True);im.save(out/'full-220.png')
r=json.loads((ACTOR_OUT/'registration.json').read_text());rows=[]
mask=np.asarray(im)[...,3]>0
# 与R02相同源列只作腹侧候选；不将它当精确同源解剖点。
x=119;ys=np.where(mask[:,x])[0];hold=[x,int(ys[-1])]
for ap in [7,2,9]:
 ar=r['actor'][ap];p=ROOT/ar['path'];assert sha(p)==ar['sha256'];a=Image.open(p).convert('RGBA');am=np.asarray(a)[...,3]>0;cx=ar['paste_origin'][0]+160;cy=int(np.where(am[:,cx])[0][0]);base=[cx-hold[0],cy-hold[1]]
 for dx,up in [(0,0),(-6,8),(-12,16),(-18,24)]:
  paste=[base[0]+dx,base[1]-up];can=Image.new('RGBA',a.size);can.paste(im,tuple(paste));cm=np.asarray(can)[...,3]>0;assert cm.sum()==mask.sum()
  yy,xx=np.where(mask);hit=am[yy+paste[1],xx+paste[0]]
  head=(xx>=145)&(yy<41);arm=(xx>=119)&(xx<=143)&(yy>=52)&(yy<=81)
  row={'actor':ap,'contact':[cx,cy],'source_column':960,'candidate_boundary':hold,'delta_back_up':[dx,up],'paste':paste,'alpha_overlap':int(hit.sum()),'head_roi_overlap':int(hit[head].sum()),'near_forearm_roi_overlap':int(hit[arm].sum()),'accepted':False};rows.append(row)
  sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
  for layer in range(2):
   comp=Image.alpha_composite(a,can) if layer==0 else Image.alpha_composite(can,a)
   for f in range(2):
    pic=ImageOps.mirror(comp) if f else comp;sheet.paste(pic,(512*f,345*layer+24),pic);d.text((512*f+5,345*layer+5),f'A{ap:02d} R03 delta({dx},-{up}) layer{layer}',fill='white')
  sheet.save(out/f'A{ap:02d}-back{-dx}-up{up}.png')
# 同画布原点连续性诊断：不是同骨盆，也不是已批准首tick。
same_origin=[]
for ap in [7,2,9]:
 a=np.asarray(Image.open(ROOT/r['actor'][ap]['path']))[...,3]>0
 for px,py in [(122,107),(119,99),(116,92),(113,86),(110,81)]:
  can=np.zeros(a.shape,dtype=bool);can[py:py+110,px:px+220]=mask
  same_origin.append({'actor':ap,'paste':[px,py],'alpha_overlap':int((a&can).sum()),'accepted':False})
alpha=np.asarray(s)[...,3];summary={'schema':1,'source_sha256':sha(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r03-20261105/candidate.png'),'size':list(s.size),'mode':s.mode,'alpha_levels':len(np.unique(alpha)),'transparent_pixels':int((alpha==0).sum()),'opaque_pixels':int((alpha==255).sum()),'partial_alpha_pixels':int(((alpha>0)&(alpha<255)).sum()),'low_alpha_pixels':int(((alpha>0)&(alpha<128)).sum()),'edge_nonzero':[int(np.count_nonzero(z)) for z in [alpha[0],alpha[-1],alpha[:,0],alpha[:,-1]]],'forge_files':FORGE_SHA,'whole_frame_size':[220,110],'palette_applied':False,'runtime_installed':False,'accepted':False,'pairs':rows,'shared_origin_probe':same_origin,'limits':['腹缘点只作待审几何候选，不是已批准同源骨点。','后上位移仅静态空间比较，未批准速度或瞬移。','ROI为矩形近似，全Alpha相交不自动等价穿体。']}
(out/'measurement.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
