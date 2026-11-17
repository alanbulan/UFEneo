"""R02v5→R03整数骨盆候选；只输出离线证据，禁止当已批准根轨迹安装。"""
import json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from resume import ROOT,ACTOR_OUT,sha
OUT=ROOT/'reports/gomora-builtin/departure-v5-r03';OUT.mkdir(parents=True,exist_ok=True)
registration=json.loads((ACTOR_OUT/'registration.json').read_text())
actors={}
for ap in [7,2,9]:
 p=ROOT/registration['actor'][ap]['path'];assert sha(p)==registration['actor'][ap]['sha256'];actors[ap]=Image.open(p).convert('RGBA')
r02=Image.open(ROOT/'reports/gomora-builtin/review-5/full-220.png').convert('RGBA');r03=Image.open(ROOT/'reports/gomora-builtin/r03-review/full-220.png').convert('RGBA')
# 独立人工同源估计；不取最低臀缘。每图原源半径50px→原生向上取整7px。
assert sha(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r02-20261105/candidate-5.png')=='edda91826d3c7b13e7c255dd5544228224ca387d2147d81951d75488682f1ccf'
assert sha(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r03-20261105/candidate.png')=='efd543af4e5be3dd460f36e77aa580421aa74bee6fa222df881efb33756bd340'
local2=[round(820*220/1774),round(650*220/1774)];local3=[round(835*220/1774),round(595*220/1774)]
start=[122+local2[0],107+local2[1]];ys,xs=np.where(np.asarray(r03)[...,3]>0)
def compose(ap,im,paste,title,path):
 a=actors[ap];c=Image.new('RGBA',a.size);c.paste(im,tuple(paste));assert np.count_nonzero(np.asarray(c)[...,3])==np.count_nonzero(np.asarray(im)[...,3])
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for layer in range(2):
  comp=Image.alpha_composite(a,c) if layer==0 else Image.alpha_composite(c,a)
  for f in range(2):
   pic=ImageOps.mirror(comp) if f else comp;sheet.paste(pic,(512*f,345*layer+24),pic);d.text((512*f+4,345*layer+4),title+f' layer{layer}',fill='white')
 sheet.save(path)
compose(7,r02,[122,107],'R02 final / nominal pelvis',OUT/'R02-final.png')
scenarios=[]
for release in [30,31,32]:
 pelvis=start[:];rows=[]
 for tick in range(release,40):
  n=tick-release;velocity=[-6,15-n];prior=pelvis[:];pelvis=[pelvis[0]+velocity[0],pelvis[1]-velocity[1]];paste=[pelvis[j]-local3[j] for j in [0,1]];ap=7 if tick<32 else 2 if tick<36 else 9;a=np.asarray(actors[ap])[...,3]>0
  hit=a[ys+paste[1],xs+paste[0]];worst=(0,0,0)
  # 两个圆形7px不确定区的差集用14px圆保守覆盖；每项逐tick测量。
  for dx in range(-14,15):
   for dy in range(-14,15):
    if dx*dx+dy*dy>196:continue
    xx=xs+paste[0]+dx;yy=ys+paste[1]+dy
    assert xx.min()>=0 and xx.max()<512 and yy.min()>=0 and yy.max()<320
    count=int(a[yy,xx].sum())
    if count>worst[0]:worst=(count,dx,dy)
  rows.append({'tick':tick,'actor':ap,'pelvis':pelvis[:],'velocity_world_y_up':velocity,'pelvis_step':math.dist(prior,pelvis),'paste':paste,'alpha_overlap':int(hit.sum()),'uncertainty_worst_alpha_overlap':worst[0],'uncertainty_worst_offset':list(worst[1:])})
  compose(ap,r03,paste,f'release{release} tick{tick} nominal overlap{int(hit.sum())}',OUT/f'release{release}-tick{tick}.png')
  if worst[0]:compose(ap,r03,[paste[0]+worst[1],paste[1]+worst[2]],f'release{release} tick{tick} uncertainty {worst}',OUT/f'release{release}-tick{tick}-uncertain.png')
 scenarios.append({'release_tick':release,'frames':rows,'nominal_all_separate':all(z['alpha_overlap']==0 for z in rows),'uncertainty_all_separate':all(z['uncertainty_worst_alpha_overlap']==0 for z in rows)})
data={'schema':1,'reviewer':'root_delegated_by_user','accepted':False,'runtime_installed':False,'pelvis_readpoints':{'R02_source':[820,650],'R03_source':[835,595],'each_source_radius':50,'scale':[220,1774],'R02_local':local2,'R03_local':local3,'R02_paste':[122,107],'initial_world_pelvis_y_down':start,'each_native_radius_ceil':7,'difference_radius_conservative':14},'integer_trajectory':{'vx':-6,'initial_vy':15,'gravity':1,'no_position_teleport':True,'no_root_lerp':True,'no_limb_edits':True,'actor_schedule':{'28-31':7,'32-35':2,'36-39':9},'meaning':'旧候选初速作对照，提前1/2tick释放仅候选，未批准动作时序。'},'derived_input_sha256':{'r02':sha(ROOT/'reports/gomora-builtin/review-5/full-220.png'),'r03':sha(ROOT/'reports/gomora-builtin/r03-review/full-220.png')},'scenarios':scenarios,'limits':['全Alpha交叠是保守诊断，需实看位置，不等于全部穿体。','名义点可行不等于不确定骨盆已验收；未按增大速度强行清交叠。','只核到tick39，未接04/05倒立、落地或主游戏。']}
(OUT/'measurement.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print([(s['release_tick'],[(f['tick'],f['alpha_overlap'],f['uncertainty_worst_alpha_overlap']) for f in s['frames']]) for s in scenarios])
