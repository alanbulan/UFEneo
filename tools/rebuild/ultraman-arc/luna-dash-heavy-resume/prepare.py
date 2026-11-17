"""月亮dash_heavy六相：同一1254整源缩到159方，不用旧逐相面积缩放。"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/rebuild/shared'))
from forge_backend import backend_info,binarize_alpha,_kcentroid_downscale,apply_palette,palette_mode
STAGE=ROOT/'art/fighters/ultraman-arc__luna/stage2'
OUTPUT=STAGE/'dash_heavy-registered-20261105-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def prepare():
 if OUTPUT.exists():raise ValueError('候选目录已存在，禁止覆盖')
 receipt=STAGE/'goal-closeout-20261101-v1/dash_heavy/frames.json'
 palette=ROOT/'art/fighters/ultraman-arc__luna/model/palette.json'
 old=read(receipt);rows=[]
 with palette_mode('rgb'):
  backend={k:v for k,v in backend_info().items() if k not in {"scripts","python"}}
  frozen=read(next((STAGE/'light-chain-unregistered-20261102-v1').rglob('phase-receipt.json')))['backend']['files']
  if backend['files']!=frozen:raise ValueError('Forge版本不同')
  for i,r in enumerate(old['frames']):
   source=ROOT/r['source']
   if sha(source)!=r['source_sha256']:raise ValueError('整源SHA改变')
   with Image.open(source) as im:
    if im.size!=(1254,1254) or im.mode!='RGBA':raise ValueError('整源尺寸/模式不一致')
    full=binarize_alpha(im.copy())
   sample=_kcentroid_downscale(full,159,159,detail_bias=True)
   apply_palette(sample,read(palette)['colors']);binarize_alpha(sample)
   a=np.asarray(sample);ys,xs=np.where(a[:,:,3]>0)
   if not len(xs) or xs.min()==0 or ys.min()==0 or xs.max()==158 or ys.max()==158:raise ValueError('空Alpha或碰边')
   path=OUTPUT/'samples'/f'phase-{i:02}.png';path.parent.mkdir(parents=True,exist_ok=True);sample.save(path)
   rows.append({'phase':i,'source':ref(source),'sample':ref(path),'source_size':[1254,1254],'sample_size':[159,159],
                'bbox':[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1],
                'proposed_translation':[80,127 if i in [1,2,3] else 280-int(ys.max())],'ticks':int(r['ticks'])})
 result={'schema':'ufeneo.luna.dash_heavy-source-samples.v1','fighter':'ultraman-arc__luna','action':'dash_heavy','source_receipt':ref(receipt),
         'palette':ref(palette),'backend':backend,'common_source_scale':159/1254,'per_phase_rescale':False,
         'registration_policy':'起手0与落地4/5实脚底对齐280；飞踢1–3整图共用起手0的y127，保留空中脚离地，不逐相拉到地面。模拟物理/高度不变，仅本人整帧姿势。','old_area_fit_samples_used':False,'alpha_threshold':128,'phases':rows,'generator':ref(Path(__file__).resolve()),'installed':False}
 write(OUTPUT/'samples.json',result)
 return result
if __name__=='__main__':print(json.dumps(prepare(),ensure_ascii=False,indent=2))
