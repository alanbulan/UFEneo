"""中阶段完整相的真实双膝弧与配对；不按提示词推定成功。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np, math
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r01-r02-mid-20261105/candidate.png';im=Image.open(src).convert('RGBA');alpha=np.asarray(im)[...,3];small=im.resize((168,154),Image.Resampling.NEAREST);m=np.asarray(small)[...,3]>=128
out=ROOT/'reports/gomora-builtin/r01-r02-mid-review';out.mkdir(parents=True,exist_ok=True)
point=lambda xy:[round(xy[0]*168/1312),round(xy[1]*154/1199)]
pelvis=point([570,640]);knees=[point([455,865]),point([365,805])];rows=[]
for tick,ap,world in [(26,6,[214,195]),(28,7,[219,192]),('26-contact',6,[214,200]),('26-contact4',6,[214,199])]:
 actor=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(actor)[...,3]>=128;paste=[world[i]-pelvis[i] for i in [0,1]];layer=Image.new('RGBA',actor.size);layer.paste(small,tuple(paste));mask=np.asarray(layer)[...,3]>=128
 head=np.zeros_like(mask);head[paste[1]+47:paste[1]+81,paste[0]+106:paste[0]+134]=mask[paste[1]+47:paste[1]+81,paste[0]+106:paste[0]+134]
 samples=[]
 for y in [74,76,78,80]:
  x=int(np.flatnonzero(m[y])[-1]);cx=x+paste[0];cy=y+paste[1];ay=int(np.flatnonzero(am[:,cx])[0]);samples.append({'receiver_canvas':[cx,cy],'receiver_alpha':int(np.asarray(small)[y,x,3]),'actor_upper_y':ay,'gap_down':ay-cy})
 rows.append({'tick_trial':tick,'actor':ap,'pelvis':world,'paste':paste,'knees_world':[[p[i]+paste[i] for i in [0,1]] for p in knees],'head_roi_overlap':int((head&am).sum()),'belly_samples':samples})
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  c=Image.alpha_composite(actor,layer) if z==0 else Image.alpha_composite(layer,actor)
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f'mid trial t{tick} A{ap} layer{z}',fill='white')
 sheet.save(out/f'tick{tick}-A{ap:02}.png')
bg=Image.new('RGBA',im.size,(48,52,60,255));bg.alpha_composite(im);bg.convert('RGB').save(out/'true-alpha-composite.png')
r02=[[200,185],[196,167]];last=rows[1]['knees_world'];delta=[[r02[j][i]-last[j][i] for i in [0,1]] for j in [0,1]]
data={'schema':1,'source_sha256':sha(src),'size':list(im.size),'alpha':{'zero':int((alpha==0).sum()),'partial':int(((alpha>0)&(alpha<255)).sum()),'opaque':int((alpha==255).sum())},'uniform_size':[168,154],'readpoints':{'pelvis':[570,640],'pelvis_radius':45,'knees':[[455,865],[365,805]],'knee_radius':[25,30],'abdomen':[[670,625],[720,602],[775,580]],'head_length':195,'head_length_radius':25},'native_pelvis':pelvis,'knees_relative':[[p[i]-pelvis[i] for i in [0,1]] for p in knees],'trials':rows,'to_R02':{'knees':r02,'delta':delta,'distance':[math.hypot(*v) for v in delta],'meaning':'不同完整姿态相邻切换的剩余跳变，不能除以静帧持有tick宣称平滑。'},'accepted':False,'installed':False,'main_tested':False,'conclusions':['真实Alpha合成可见完整两臂两腿，没有按预览黑底否决。','近远双膝都在髋左下，远侧大腿确实较早相后摆；近腿仍较向下伸展。','同髋双膝弧已分段，但前后肩髋脚及实际接触、速度仍须整链验证。','A06完整图下移4px有实体腹边接点且头ROI为0；多下1px时头ROI交叠2，余量敏感，不能签全头颈安全。','头ROI/腹点仅诊断，不能替代全头颈轮廓或动态承重验收。','未改运行合同、捕获范围、素材层级或正式三级。']}
rel=data['knees_relative'];r1=[[-15,26],[0,31]];late=[[-23,4],[-30,-10]]
data['relative_transition_gaps']={'from_early':[math.dist(rel[i],r1[i]) for i in [0,1]],'to_late':[math.dist(rel[i],late[i]) for i in [0,1]],'meaning':'同髋相对膝差，不含实际根运动；骨盆和膝关节有人工读点误差。'}
data['leg_length_limit']='不能用共用骨盆中心到膝的距离冒称精确股骨长度；隐藏近远髋关节不同，源骨点误差需保留。'
save(src.parent/'review.json',data);print(data['knees_relative'],data['to_R02']);print([(r['tick_trial'],r['head_roi_overlap'],r['belly_samples']) for r in rows])
