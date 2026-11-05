"""R02第五版和旧相邻帧整图静态配对，不安装、不冒称动作验收。"""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
sys.path.insert(0,str(Path(__file__).resolve().parent))
from resume import ROOT,ACTOR_OUT,SURFACES,sha
r=json.loads((ACTOR_OUT/'registration.json').read_text());out=ROOT/'reports/gomora-builtin/review-5/neighbors';out.mkdir(exist_ok=True)
v=Image.open(ROOT/'reports/gomora-builtin/review-5/full-220.png').convert('RGBA'); rows=[]
for ap,rp in [(6,1),(7,2),(2,3),(9,3),(8,4)]:
 ar=r['actor'][ap];a=Image.open(ROOT/ar['path']).convert('RGBA');am=np.asarray(a)[...,3]>0;x=ar['paste_origin'][0]+160;y=int(np.where(am[:,x])[0][0]); sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 assert sha(ROOT/ar['path'])==ar['sha256']
 assert sha(ROOT/r['receiver'][rp]['path'])==r['receiver'][rp]['sha256']
 old=Image.open(ROOT/r['receiver'][rp]['path']).convert('RGBA')
 for typ,(im,hold) in enumerate([(old,[z+6 for z in SURFACES[rp]]),(v,[119,85])]):
  paste=(x-hold[0],y-hold[1]); c=Image.new('RGBA',a.size);c.paste(im,paste);over=int((am&(np.asarray(c)[...,3]>0)).sum()); rows.append(dict(actor=ap,receiver=rp,kind='old' if typ==0 else 'v5_static',contact=[x,y],paste=list(paste),overlap=over))
  for layer in range(2):
   comp=Image.alpha_composite(a,c) if layer==0 else Image.alpha_composite(c,a);sheet.paste(comp,(layer*512,typ*345+24),comp);d.text((layer*512+5,typ*345+5),f'A{ap:02d} {"old R"+str(rp) if typ==0 else "V5 static only"} layer{layer} overlap{over}',fill='white')
 sheet.save(out/f'A{ap:02d}.png')
(out/'measurements.json').write_text(json.dumps(rows,indent=2));print(rows)
