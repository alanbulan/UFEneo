"""R01整图同体尺配对及名义髋轨迹；仅离线，不安装。"""
from PIL import Image,ImageDraw,ImageOps
import numpy as np
from resume import ROOT,ACTOR_OUT,sha,save
src=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r01-20261105/candidate.png';im=Image.open(src).convert('RGBA');alpha=np.asarray(im)[...,3]
out=ROOT/'reports/gomora-builtin/r01-review';out.mkdir(parents=True,exist_ok=True)
# 按头长170缩至25，只整图等比，不把不同画布硬缩成相同宽度。
size=(176,193);small=im.resize(size,Image.Resampling.NEAREST);m=np.asarray(small)[...,3]>=128
pelvis=[round(490*176/1199),round(745*193/1312)]
rows=[]
for tick,ap,world in [(20,5,[204,196]),(24,6,[204,202]),(25,6,[209,199]),(26,6,[214,195]),(27,6,[219,192]),(28,7,[224,188])]:
 a=Image.open(ACTOR_OUT/f'{ap:02}.png').convert('RGBA');am=np.asarray(a)[...,3]>=128;paste=[world[i]-pelvis[i] for i in [0,1]];layer=Image.new('RGBA',a.size);layer.paste(small,tuple(paste));mask=np.asarray(layer)[...,3]>=128
 head=np.zeros_like(mask);head[paste[1]+45:paste[1]+80,paste[0]+109:paste[0]+135]=mask[paste[1]+45:paste[1]+80,paste[0]+109:paste[0]+135]
 samples=[]
 for y in [102,104,106,108,110]:
  x=int(np.flatnonzero(m[y])[-1]);cx=x+paste[0];cy=y+paste[1];ay=int(np.flatnonzero(am[:,cx])[0]);samples.append({'receiver':[cx,cy],'receiver_alpha':int(np.asarray(small)[y,x,3]),'actor_y':ay,'signed_gap_down':ay-cy})
 row={'tick':tick,'actor':ap,'pelvis':world,'paste':paste,'head_roi_overlap':int((head&am).sum()),'all_overlap_not_automatically_penetration':int((mask&am).sum()),'abdomen_edge_samples':samples};rows.append(row)
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for z in range(2):
  c=Image.alpha_composite(a,layer) if z==0 else Image.alpha_composite(layer,a)
  for f in range(2):
   pic=ImageOps.mirror(c) if f else c;sheet.paste(pic,(512*f,345*z+24),pic);d.text((512*f+4,345*z+4),f'R01 t{tick} A{ap:02} pelvis{world} layer{z}',fill='white')
 sheet.save(out/f'tick{tick}-A{ap:02}.png')
bg=Image.new('RGBA',im.size,(48,52,60,255));bg.alpha_composite(im);bg.convert('RGB').save(out/'true-alpha-composite.png')
data={'schema':1,'source_sha256':sha(src),'original_size':list(im.size),'alpha':{'zero':int((alpha==0).sum()),'partial':int(((alpha>0)&(alpha<255)).sum()),'opaque':int((alpha==255).sum())},'uniform_size':list(size),'source_readpoints':{'pelvis':[490,745],'pelvis_radius':45,'abdomen':[[565,750],[620,725],[680,704]],'edge_radius':15,'head_length':170,'head_length_radius':25},'native_pelvis':pelvis,'pair_trials':rows,'accepted':False,'installed':False,'main_game_tested':False,'notes':['两臂两腿可辨，确有更前折躯干和向后收小腿的中间变化。','按头长统一体尺，原图画布不同不代表角色缩放异常。','各点是名义人工估计，未签收骨骼。','tick20是错位对照；tick28是同R01几何对照，不冒称实际R02帧。','头ROI是诊断，不能替代全头颈掩模与实看；全Alpha相交也不自动等于穿体。','没有运行或修改合同，没有正式安装。']}
data['knee_transition']={'meaning':'t27 R01到t28真实R02v5的同侧人工膝点，不以髋连续替代。','each_source_radius':25,'R01_source':[[520,920],[615,940]],'R02_source':[[620,625],[580,470]],'R01_size':[176,193],'R02_size':[210,105],'R01_paste':[147,82],'R02_paste':[127,111],'source_R02_sha256':sha(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r02-20261105/candidate-5.png'),'rows':[]}
for p1,p2 in zip(data['knee_transition']['R01_source'],data['knee_transition']['R02_source']):
 w1=[round(p1[0]*176/1199)+147,round(p1[1]*193/1312)+82];w2=[round(p2[0]*210/1774)+127,round(p2[1]*105/887)+111];delta=[w2[i]-w1[i] for i in [0,1]];data['knee_transition']['rows'].append({'R01_world':w1,'R02_world':w2,'delta':delta,'distance':round((delta[0]**2+delta[1]**2)**.5,2)})
data['knee_transition']['conclusion']='近侧约40px、远侧约68px，读点误差不足以消除此跳变；静帧不能断言必须生成，但不能签收连续收腿。'
save(src.parent/'review.json',data);print([(r['tick'],r['head_roi_overlap'],[(x['receiver'],x['signed_gap_down']) for x in r['abdomen_edge_samples']]) for r in rows])
