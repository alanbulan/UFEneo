"""仅候选整图平移支点搜索，分开上腹支撑与后腹间隙，不安装。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np,math
from resume import ROOT,ACTOR_OUT,sha,save
base=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-midlate-20261105';out=ROOT/'reports/gomora-builtin/midlate-support';out.mkdir(parents=True,exist_ok=True)
rows=[]
for version in [1,2]:
 path=base/('candidate.png' if version==1 else 'candidate-2.png');im=Image.open(path).convert('RGBA').resize((210,105),Image.Resampling.NEAREST);a=np.asarray(im).copy();a[:,:,3]=np.where(a[:,:,3]>=128,255,0);im=Image.fromarray(a);mask=a[:,:,3]>0
 for ap,hip in [(6,[217,198]),(7,[219,196])]:
  actor=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(actor)[...,3]>=128;valid=[]
  for dx in range(-4,5):
   for dy in range(-6,4):
    p=[hip[0]-101+dx,hip[1]-74+dy];samples=[]
    for y in [64,66,68,70,72,74,76]:
     x=int(np.flatnonzero(mask[y])[-1]);cx,cy=p[0]+x,p[1]+y;upper=int(np.flatnonzero(am[:,cx])[0]);samples.append({'local':[x,y],'canvas':[cx,cy],'gap':upper-cy})
    ys,xs=np.where(mask[10:54,136:165]);ys+=10+p[1];xs+=136+p[0];worst=max(int(am[ys+sy,xs+sx].sum()) for sx in range(-2,3) for sy in range(-2,3) if sx*sx+sy*sy<=4)
    if min(s['gap'] for s in samples[:3])==0 and worst==0:
     valid.append({'shift':[dx,dy],'pelvis':[hip[0]+dx,hip[1]+dy],'head_neck_overlap_worst_radius2':worst,'edge_samples':samples,'scope':'只要求前三个上腹采样无穿入且至少一实体共点，后腹允许离背；不是全轮廓验收。'})
  rows.append({'version':version,'actor':ap,'source_sha256':sha(path),'search_dx':[-4,4],'search_dy':[-6,3],'valid_upper_abdomen_trials':valid})
  for dx,dy in [(-2,-3),(0,-4)] if ap==6 else [(0,-2)]:
   p=[hip[0]-101+dx,hip[1]-74+dy];layer=Image.new('RGBA',actor.size);layer.paste(im,tuple(p));sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
   for z in range(2):
    c=Image.alpha_composite(actor,layer) if z==0 else Image.alpha_composite(layer,actor)
    for f in range(2):
     pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f'v{version} A{ap} shift{dx},{dy} layer{z}',fill='white')
   sheet.save(out/f'v{version}-A{ap}-shift{dx},{dy}.png')
data={'schema':1,'rows':rows,'accepted':False,'installed':False,'main_tested':False,'limits':['搜索只改变离线整图平移，不改运行根点或图层。','头颈局部ROI与上腹采样是筛选，不自动构成自然承重/全扫掠通过。','腹部不必整条贴背；单一上腹承重点与腰后合理间隙须看实际姿态。']}
save(ROOT/'docs/verification/gomora-midlate-support-study.json',data)
print([(x['version'],x['actor'],[(q['shift'],[s['gap'] for s in q['edge_samples']]) for q in x['valid_upper_abdomen_trials']]) for x in rows])
