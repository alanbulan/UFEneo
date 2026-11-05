"""完整收腿中间候选的真实膝弧与配对；不按提示词推定成功。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np, math
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r01-r02-bridge-20261105/candidate.png';im=Image.open(src).convert('RGBA');alpha=np.asarray(im)[...,3];small=im.resize((176,193),Image.Resampling.NEAREST);m=np.asarray(small)[...,3]>=128
out=ROOT/'reports/gomora-builtin/r01-r02-bridge-review';out.mkdir(parents=True,exist_ok=True)
point=lambda xy:[round(xy[0]*176/1199),round(xy[1]*193/1312)]
pelvis=point([490,755]);knees=[point([455,900]),point([585,940])];rows=[]
for tick,ap,world in [(26,6,[214,195]),(28,7,[219,192])]:
 actor=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(actor)[...,3]>=128;paste=[world[i]-pelvis[i] for i in [0,1]];layer=Image.new('RGBA',actor.size);layer.paste(small,tuple(paste));mask=np.asarray(layer)[...,3]>=128
 head=np.zeros_like(mask);head[paste[1]+47:paste[1]+81,paste[0]+106:paste[0]+134]=mask[paste[1]+47:paste[1]+81,paste[0]+106:paste[0]+134]
 samples=[]
 for y in [102,104,106,108,110]:
  x=int(np.flatnonzero(m[y])[-1]);cx=x+paste[0];cy=y+paste[1];ay=int(np.flatnonzero(am[:,cx])[0]);samples.append({'receiver_canvas':[cx,cy],'receiver_alpha':int(np.asarray(small)[y,x,3]),'actor_upper_y':ay,'gap_down':ay-cy})
 rows.append({'tick_trial':tick,'actor':ap,'pelvis':world,'paste':paste,'knees_world':[[p[i]+paste[i] for i in [0,1]] for p in knees],'head_roi_overlap':int((head&am).sum()),'belly_samples':samples})
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  c=Image.alpha_composite(actor,layer) if z==0 else Image.alpha_composite(layer,actor)
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f'bridge trial t{tick} A{ap} layer{z}',fill='white')
 sheet.save(out/f'tick{tick}-A{ap:02}.png')
bg=Image.new('RGBA',im.size,(48,52,60,255));bg.alpha_composite(im);bg.convert('RGB').save(out/'true-alpha-composite.png')
r02=[[200,185],[196,167]];last=rows[-1]['knees_world'];delta=[[r02[j][i]-last[j][i] for i in [0,1]] for j in [0,1]]
data={'schema':1,'source_sha256':sha(src),'size':list(im.size),'alpha':{'zero':int((alpha==0).sum()),'partial':int(((alpha>0)&(alpha<255)).sum()),'opaque':int((alpha==255).sum())},'uniform_size':[176,193],'readpoints':{'pelvis':[490,755],'pelvis_radius':45,'knees':[[455,900],[585,940]],'knee_radius':[25,30],'abdomen':[[570,754],[620,725],[675,700]],'head_length':170,'head_length_radius':25},'native_pelvis':pelvis,'knees_relative':[[p[i]-pelvis[i] for i in [0,1]] for p in knees],'trials':rows,'to_R02':{'knees':r02,'delta':delta,'distance':[math.hypot(*v) for v in delta],'meaning':'不同完整姿态相邻切换的剩余跳变，不能除以静帧持有tick宣称平滑。'},'accepted':False,'installed':False,'main_tested':False,'conclusions':['真实Alpha合成可见完整两臂两腿，没有按预览黑底否决。','近膝略左、远膝仍右下；主要是小腿向后折，未实现要求的双大腿后摆。','名义髋可小步衔接但不能替代膝弧；远膝接R02的大跳仍在。','头ROI/腹点仅诊断，不能替代全头颈轮廓或动态承重验收。','未改运行合同、捕获范围、素材层级或正式三级。']}
save(src.parent/'review.json',data);print(data['knees_relative'],data['to_R02']);print([(r['tick_trial'],r['head_roi_overlap'],r['belly_samples']) for r in rows])
