"""反向生成晚阶段整帧的膝弧、背面与角冠诊断，不安装。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np,math
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r01-r02-late-20261105/candidate.png';im=Image.open(src).convert('RGBA');alpha=np.asarray(im)[...,3];small=im.resize((210,105),Image.Resampling.NEAREST);m=np.asarray(small)[...,3]>=128
out=ROOT/'reports/gomora-builtin/r01-r02-late-review';out.mkdir(parents=True,exist_ok=True)
point=lambda p:[round(p[0]*210/1774),round(p[1]*105/887)]
pelvis=point([840,655]);knees=[point([640,695]),point([585,575])];rows=[]
for tick,ap,world in [(26,6,[214,195]),(28,7,[219,192]),(30,7,[224,188]),('26-contact',6,[214,198]),('28-contact',7,[219,196]),('30-contact',7,[224,193])]:
 a=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(a)[...,3]>=128;p=[world[i]-pelvis[i] for i in [0,1]];layer=Image.new('RGBA',a.size);layer.paste(small,tuple(p));mask=np.asarray(layer)[...,3]>=128;head=np.zeros_like(mask);head[p[1]+10:p[1]+43,p[0]+138:p[0]+165]=mask[p[1]+10:p[1]+43,p[0]+138:p[0]+165]
 samples=[]
 for x in [114,118,122]:
  y=int(np.flatnonzero(m[:,x])[-1]);cx=x+p[0];cy=y+p[1];ay=int(np.flatnonzero(am[:,cx])[0]);samples.append({'receiver_canvas':[cx,cy],'receiver_alpha':int(np.asarray(small)[y,x,3]),'actor_upper_y':ay,'gap_down':ay-cy})
 rows.append({'tick_trial':tick,'actor':ap,'pelvis':world,'paste':p,'knees_world':[[q[i]+p[i] for i in [0,1]] for q in knees],'head_roi_overlap':int((head&am).sum()),'belly_samples':samples})
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  c=Image.alpha_composite(a,layer) if z==0 else Image.alpha_composite(layer,a)
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f'late trial t{tick} A{ap} layer{z}',fill='white')
 sheet.save(out/f'tick{tick}-A{ap:02}.png')
bg=Image.new('RGBA',im.size,(48,52,60,255));bg.alpha_composite(im);bg.convert('RGB').save(out/'true-alpha-composite.png')
rel=[[q[i]-pelvis[i] for i in [0,1]] for q in knees];r1=[[4,25],[18,28]];r2=[[-24,-3],[-28,-21]]
data={'schema':1,'source_sha256':sha(src),'size':list(im.size),'alpha':{'zero':int((alpha==0).sum()),'partial':int(((alpha>0)&(alpha<255)).sum()),'opaque':int((alpha==255).sum())},'uniform_size':[210,105],'readpoints':{'pelvis':[840,655],'pelvis_radius':50,'knees':[[640,695],[585,575]],'knee_radius':25,'abdomen':[[960,670],[1000,625],[1040,605]],'head_length':205,'head_length_radius':25},'native_pelvis':pelvis,'knees_relative':rel,'thigh_lengths':[math.hypot(*q) for q in rel],'thigh_angles_y_down_degrees':[math.degrees(math.atan2(q[1],q[0])) for q in rel],'relative_knee_gap_from_R01':[math.dist(r1[i],rel[i]) for i in [0,1]],'relative_knee_gap_to_R02':[math.dist(rel[i],r2[i]) for i in [0,1]],'trials':rows,'accepted':False,'installed':False,'main_tested':False,'conclusions':['真正改变了大腿摆向，接近R02的晚相，不是仅折小腿。','近膝左下、远膝仍左上，未实现双膝均在髋下，不能称早中相。','后接R02膝弧差缩小，但从R01前接仍大；未闭合整段。','A06整图下移3px、A07下移4或5px可以让一个真实腹边接到背缘且头ROI仍0，但邻近腹边仍有间隙；这只是接点候选，不是连续承重已通过。','头ROI、腹点与同尺度人工骨点均为诊断，不替代连续主游戏验收。','没有修改运行合同、捕获范围、图层或正式三级。']}
save(src.parent/'review.json',data);print(rel,data['relative_knee_gap_from_R01'],data['relative_knee_gap_to_R02']);print([(r['tick_trial'],r['head_roi_overlap'],r['belly_samples']) for r in rows])
