"""中晚补相完整源及A06/A07静态配对；未达标不安装。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np,math
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-midlate-20261105/candidate.png';im=Image.open(src).convert('RGBA');alpha=np.asarray(im)[...,3];size=(210,105);small=im.resize(size,Image.Resampling.NEAREST);arr=np.asarray(small).copy();arr[:,:,3]=np.where(arr[:,:,3]>=128,255,0);small=Image.fromarray(arr);m=arr[...,3]>0
out=ROOT/'reports/gomora-builtin/midlate-review';out.mkdir(parents=True,exist_ok=True)
point=lambda xy:[round(xy[0]*210/1774),round(xy[1]*105/887)]
pelvis=point([850,625]);knees=[point([700,735]),point([615,585])];rows=[]
for label,ap,world in [('t27',6,[217,198]),('t28',7,[219,196])]:
 actor=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(actor)[...,3]>=128;p=[world[i]-pelvis[i] for i in [0,1]];layer=Image.new('RGBA',actor.size);layer.paste(small,tuple(p));mask=np.asarray(layer)[...,3]>0
 head=np.zeros_like(mask);head[p[1]+10:p[1]+49,p[0]+136:p[0]+165]=mask[p[1]+10:p[1]+49,p[0]+136:p[0]+165]
 ys,xs=np.where(head);worst=0
 for dx in range(-2,3):
  for dy in range(-2,3):
   if dx*dx+dy*dy<=4:worst=max(worst,int(am[ys+dy,xs+dx].sum()))
 samples=[]
 for y in range(64,78,2):
  x=int(np.flatnonzero(m[y])[-1]);cx=x+p[0];cy=y+p[1];ys=np.flatnonzero(am[:,cx]);ay=int(ys[0]) if len(ys) else None
  samples.append({'receiver_canvas':[cx,cy],'receiver_local':[x,y],'actor_upper_y':ay,'gap_down':None if ay is None else ay-cy,'actor_alpha_at_point':int(am[cy,cx])})
 row={'trial':label,'actor':ap,'pelvis':world,'paste':p,'knees_world':[[q[i]+p[i] for i in [0,1]] for q in knees],'head_neck_roi_overlap':int((head&am).sum()),'head_neck_overlap_worst_shift_radius2':worst,'belly_edge_samples':samples};rows.append(row)
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  c=Image.alpha_composite(actor,layer) if z==0 else Image.alpha_composite(layer,actor)
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f'midlate {label} A{ap} layer{z}',fill='white')
 sheet.save(out/f'{label}-A{ap:02}.png')
rel=[[q[i]-pelvis[i] for i in [0,1]] for q in knees];mid=[[-15,29],[-26,21]];late=[[-23,4],[-30,-10]]
data={'schema':1,'sha256':sha(src),'size':list(im.size),'alpha':{'zero':int((alpha==0).sum()),'partial':int(((alpha>0)&(alpha<255)).sum()),'opaque':int((alpha==255).sum())},'fixed_whole_size':list(size),'manual_readpoints':{'pelvis':[850,625],'pelvis_radius':50,'knees':[[700,735],[615,585]],'knee_radius':[25,25],'head_without_fin_length':205,'head_radius':25},'native_pelvis':pelvis,'knees_relative':rel,'desired_knees_relative':[[-23,17],[-32,6]],'relative_distance_from_mid':[math.dist(mid[i],rel[i]) for i in (0,1)],'relative_distance_to_late':[math.dist(rel[i],late[i]) for i in (0,1)],'trials':rows,'accepted':False,'installed':False,'main_tested':False,'limits':['共用髋中心与人工膝点不是精确股骨，保留取点误差。','右缘按行采样只诊断腹侧与背面，不等于合法承重。','头颈ROI为局部诊断，不等于全扫掠净空验收。','新相近膝介于mid/late，远膝名义上已高于髋，未清楚达到略低于髋要求。','主体Alpha≥128完整，极少255不构成透明失败；低Alpha杂点不能用于注册。','不旋转/切肢/逐tick缩放/改层，不改合同或正式三级。']}
previous=[[199,228],[188,220]];nxt=[[196,200],[189,186]];k=rows[0]['knees_world'];data['proposed_t27_transition']={'previous_t26_mid':previous,'new_t27':k,'next_t28_late':nxt,'from_previous_distances':[math.dist(previous[i],k[i]) for i in (0,1)],'to_next_distances':[math.dist(k[i],nxt[i]) for i in (0,1)],'meaning':'人工名义膝点，远膝从mid到新相仍约27像素；不以总跳差减少冒称连续。'}
save(src.parent/'review.json',data);print(rel);print(rows)
