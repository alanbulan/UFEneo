"""第三版中间完整相真实膝弧、上腹支撑和头颈余量；不安装。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np,math
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-midlate-20261105/candidate-3.png';im=Image.open(src).convert('RGBA');alpha=np.asarray(im)[...,3];raw=im.resize((168,154),Image.Resampling.NEAREST);arr=np.asarray(raw).copy();arr[:,:,3]=np.where(arr[:,:,3]>=128,255,0);small=Image.fromarray(arr);m=arr[...,3]>0
point=lambda p:[round(p[0]*168/1312),round(p[1]*154/1199)]
hip=point([570,640]);knees=[point([450,830]),point([350,685])];rel=[[p[i]-hip[i] for i in (0,1)] for p in knees]
out=ROOT/'reports/gomora-builtin/midlate-review-3';out.mkdir(parents=True,exist_ok=True);bg=Image.new('RGBA',im.size,(48,52,60,255));bg.alpha_composite(im);bg.convert('RGB').save(out/'true-alpha-composite.png');rows=[]
for label,ap,world in [('t27-design',6,[216,197]),('t27-contact',6,[216,198]),('t28-comparison',7,[219,194])]:
 actor=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(actor)[...,3]>=128;p=[world[i]-hip[i] for i in (0,1)];layer=Image.new('RGBA',actor.size);layer.paste(small,tuple(p));hm=np.zeros_like(am);hm[p[1]+17:p[1]+55,p[0]+100:p[0]+132]=m[17:55,100:132];ys,xs=np.where(hm)
 worst=max(int(am[ys+dy,xs+dx].sum()) for dx in range(-2,3) for dy in range(-2,3) if dx*dx+dy*dy<=4)
 nearest=None
 for radius in range(1,9):
  if any(am[ys+dy,xs+dx].any() for dx in range(-radius,radius+1) for dy in range(-radius,radius+1) if dx*dx+dy*dy<=radius*radius):nearest=radius;break
 samples=[]
 for y in [70,72,74,76,78,80]:
  x=int(np.flatnonzero(m[y])[-1]);cx,cy=x+p[0],y+p[1];top=int(np.flatnonzero(am[:,cx])[0]);samples.append({'local':[x,y],'canvas':[cx,cy],'alpha':int(np.asarray(raw)[y,x,3]),'actor_upper_y':top,'gap_down':top-cy,'actor_alpha_at_point':int(am[cy,cx])})
 row={'trial':label,'actor':ap,'pelvis':world,'paste':p,'knees_world':[[q[i]+p[i] for i in (0,1)] for q in knees],'head_neck_roi':[100,17,132,55],'head_neck_overlap':int((hm&am).sum()),'head_neck_overlap_worst_shift_radius2':worst,'first_integer_radius_with_overlap':nearest,'belly_edge_samples':samples};rows.append(row)
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  c=Image.alpha_composite(actor,layer) if z==0 else Image.alpha_composite(layer,actor)
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f'v3 {label} A{ap} layer{z}',fill='white')
 sheet.save(out/f'{label}-A{ap:02}.png')
previous=[[199,228],[188,220]];nxt=[[201,207],[184,194]];selected=rows[0]['knees_world']
data={'schema':1,'source_sha256':sha(src),'size':list(im.size),'fixed_whole_size':[168,154],'alpha':{'zero':int((alpha==0).sum()),'partial':int(((alpha>0)&(alpha<255)).sum()),'opaque':int((alpha==255).sum())},'manual_readpoints':{'pelvis':[570,640],'pelvis_radius':45,'knees':[[450,830],[350,685]],'knee_radius':[25,25],'head_without_fin_length':195,'head_radius':25},'native_pelvis':hip,'knees_relative':rel,'trials':rows,'proposed_sequence':{'previous_t26_mid':previous,'t27_v3':selected,'next_t28_v2_A07':nxt,'near_far_steps_in':[math.dist(previous[i],selected[i]) for i in (0,1)],'near_far_steps_out':[math.dist(selected[i],nxt[i]) for i in (0,1)]},'accepted':False,'installed':False,'main_tested':False,'limits':['点位为人工名义中心，非精确骨骼或股骨长度。','真实Alpha不以255像素少否决，低Alpha杂点不用于配准。','局部头颈ROI/上腹点支持只是静态先决，不等于全角冠扫掠或原速通过。','上腹可单点承重，腰后空间不必全部贴合。','整图仅固定一次NEAREST与Alpha128，无局部改图/旋转/逐tick缩放/图层变更。','第三版名义两膝均介于mid与第二版，值得现有完整帧候选验证，尚未安装。']}
save(src.parent/'review-3.json',data);print('hip/knees',hip,rel);print([(r['trial'],r['head_neck_overlap'],r['head_neck_overlap_worst_shift_radius2'],r['first_integer_radius_with_overlap'],[q['gap_down'] for q in r['belly_edge_samples']]) for r in rows]);print(data['proposed_sequence'])
