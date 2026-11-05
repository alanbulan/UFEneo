"""R02v5→收臂过渡→R03整数骨盆候选；只输出离线证据，禁止当已批准根轨迹安装。"""
import json,math,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from resume import ROOT,ACTOR_OUT,sha,FORGE_SHA
import sys
sys.path.insert(0,str(ROOT/"tools/rebuild/shared"))
import forge_backend as forge
assert forge.backend_info()["files"]==FORGE_SHA
parser=argparse.ArgumentParser();parser.add_argument('--width',type=int,choices=[200,210,220,230],default=220);args=parser.parse_args();width=args.width
OUT=ROOT/('reports/gomora-builtin/bridge-review/trajectory' if width==220 else f'reports/gomora-builtin/bridge-review/trajectory-{width}');OUT.mkdir(parents=True,exist_ok=True)
registration=json.loads((ACTOR_OUT/'registration.json').read_text())
actors={}
for ap in [7,2,9]:
 p=ROOT/registration['actor'][ap]['path'];assert sha(p)==registration['actor'][ap]['sha256'];actors[ap]=Image.open(p).convert('RGBA')
source_path=ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r03-bridge-20261105/candidate.png'
source=Image.open(source_path);assert source.mode=='RGBA' and source.size==(1774,887)
alpha=np.asarray(source)[...,3]
bridge_image=forge.binarize_alpha(source.copy());bridge_image=forge._kcentroid_downscale(bridge_image,width,width//2);forge.binarize_alpha(bridge_image)
bridge_image.save(OUT.parent/f'full-{width}.png')
bridge=Image.open(ROOT/f'reports/gomora-builtin/bridge-review/full-{width}.png').convert('RGBA')
assert sha(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r03-bridge-20261105/candidate.png')=='e7122bcbb7bd61a06142baf4113b3f2b271a5721dca913f22e1d9746453b7118'
local_bridge=[round(850*width/1774),round(630*width/1774)]
def whole(source_path,output_path):
 im=forge.binarize_alpha(Image.open(source_path).convert('RGBA'));im=forge._kcentroid_downscale(im,width,width//2);forge.binarize_alpha(im);im.save(output_path);return im
r02=whole(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r02-20261105/candidate-5.png',OUT.parent/f'R02-full-{width}.png')
r03=whole(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r03-20261105/candidate.png',OUT.parent/f'R03-full-{width}.png')
# 独立人工同源估计；不取最低臀缘。每图原源半径50px→原生向上取整7px。
assert sha(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r02-20261105/candidate-5.png')=='edda91826d3c7b13e7c255dd5544228224ca387d2147d81951d75488682f1ccf'
assert sha(ROOT/'art/fighters/ultraman/stage5/gomora-back-lift-receiver/builtin-r03-20261105/candidate.png')=='efd543af4e5be3dd460f36e77aa580421aa74bee6fa222df881efb33756bd340'
local2=[round(820*width/1774),round(650*width/1774)];local3=[round(835*width/1774),round(595*width/1774)]
contact_x=round(960*width/1774);contact_y=int(np.where(np.asarray(r02)[...,3][:,contact_x]>0)[0][-1]);paste2=[241-contact_x,192-contact_y];radius=math.ceil(50*width/1774);diff_radius=radius*2
start=[paste2[0]+local2[0],paste2[1]+local2[1]];ys,xs=np.where(np.asarray(r03)[...,3]>0)
def compose(ap,im,paste,title,path):
 a=actors[ap];c=Image.new('RGBA',a.size);c.paste(im,tuple(paste));assert np.count_nonzero(np.asarray(c)[...,3])==np.count_nonzero(np.asarray(im)[...,3])
 assert int(((np.asarray(a)[...,3]>0)&(np.asarray(c)[...,3]>0)).sum())==int((np.fliplr(np.asarray(a)[...,3]>0)&np.fliplr(np.asarray(c)[...,3]>0)).sum())
 sheet=Image.new('RGB',(1024,690),'#30343c');d=ImageDraw.Draw(sheet)
 for layer in range(2):
  comp=Image.alpha_composite(a,c) if layer==0 else Image.alpha_composite(c,a)
  for f in range(2):
   pic=ImageOps.mirror(comp) if f else comp;sheet.paste(pic,(512*f,345*layer+24),pic);d.text((512*f+4,345*layer+4),title+f' layer{layer}',fill='white')
 sheet.save(path)
compose(7,r02,paste2,'R02 final / nominal pelvis',OUT/'R02-final.png')
scenarios=[]
for release,bridge_ticks in [(32,1),(32,2),(31,2)]:
 case=f"release{release}-bridge{bridge_ticks}"
 pelvis=start[:];rows=[]
 for tick in range(release,40):
  n=tick-release;current=bridge if n<bridge_ticks else r03;local_current=local_bridge if n<bridge_ticks else local3;ys,xs=np.where(np.asarray(current)[...,3]>0);velocity=[-6,15-n];prior=pelvis[:];pelvis=[pelvis[0]+velocity[0],pelvis[1]-velocity[1]];paste=[pelvis[j]-local_current[j] for j in [0,1]];ap=7 if tick<32 else 2 if tick<36 else 9;a=np.asarray(actors[ap])[...,3]>0
  hit=a[ys+paste[1],xs+paste[0]];worst=(0,0,0)
  # 两图读点半径统一按当前尺度向上取整，差集圆保守覆盖；逐tick测量。
  for dx in range(-diff_radius,diff_radius+1):
   for dy in range(-diff_radius,diff_radius+1):
    if dx*dx+dy*dy>diff_radius**2:continue
    xx=xs+paste[0]+dx;yy=ys+paste[1]+dy
    assert xx.min()>=0 and xx.max()<512 and yy.min()>=0 and yy.max()<320
    count=int(a[yy,xx].sum())
    if count>worst[0]:worst=(count,dx,dy)
  rows.append({'tick':tick,'receiver':'bridge' if n<bridge_ticks else 'R03','actor':ap,'pelvis':pelvis[:],'velocity_world_y_up':velocity,'pelvis_step':math.dist(prior,pelvis),'paste':paste,'alpha_overlap':int(hit.sum()),'uncertainty_worst_alpha_overlap':worst[0],'uncertainty_worst_offset':list(worst[1:])})
  compose(ap,current,paste,f'{case} tick{tick} nominal overlap{int(hit.sum())}',OUT/f'{case}-tick{tick}.png')
  if worst[0]:compose(ap,current,[paste[0]+worst[1],paste[1]+worst[2]],f'{case} tick{tick} uncertainty {worst}',OUT/f'{case}-tick{tick}-uncertain.png')
 scenarios.append({'release_tick':release,'bridge_ticks':bridge_ticks,'frames':rows,'nominal_all_separate':all(z['alpha_overlap']==0 for z in rows),'uncertainty_all_separate':all(z['uncertainty_worst_alpha_overlap']==0 for z in rows)})
data={'schema':1,'source_sha256':sha(source_path),'alpha':{'transparent':int((alpha==0).sum()),'opaque':int((alpha==255).sum()),'partial':int(((alpha>0)&(alpha<255)).sum()),'low':int(((alpha>0)&(alpha<128)).sum()),'edge_nonzero':[int(np.count_nonzero(z)) for z in [alpha[0],alpha[-1],alpha[:,0],alpha[:,-1]]]},'reviewer':'root_delegated_by_user','accepted':False,'runtime_installed':False,'pelvis_readpoints':{'bridge_source':[850,630],'bridge_local':local_bridge,'R02_source':[820,650],'R03_source':[835,595],'each_source_radius':50,'scale':[width,1774],'R02_local':local2,'R03_local':local3,'R02_paste':paste2,'initial_world_pelvis_y_down':start,'each_native_radius_ceil':radius,'difference_radius_conservative':diff_radius},'integer_trajectory':{'vx':-6,'initial_vy':15,'gravity':1,'no_position_teleport':True,'no_root_lerp':True,'no_limb_edits':True,'actor_schedule':{'28-31':7,'32-35':2,'36-39':9},'meaning':'旧候选初速作对照，提前1/2tick释放仅候选，未批准动作时序。'},'derived_input_sha256':{'bridge':sha(ROOT/f'reports/gomora-builtin/bridge-review/full-{width}.png'),'r02':sha(OUT.parent/f'R02-full-{width}.png'),'r03':sha(OUT.parent/f'R03-full-{width}.png')},'scenarios':scenarios,'limits':['全Alpha交叠是保守诊断，需实看位置，不等于全部穿体。','名义点可行不等于不确定骨盆已验收；未按增大速度强行清交叠。','只核到tick39，未接04/05倒立、落地或主游戏。']}
(OUT/'measurement.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print([((s['release_tick'],s['bridge_ticks']),[(f['tick'],f['alpha_overlap'],f['uncertainty_worst_alpha_overlap']) for f in s['frames']]) for s in scenarios])
