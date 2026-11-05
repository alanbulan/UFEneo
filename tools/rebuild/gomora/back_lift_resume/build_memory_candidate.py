"""仅生成主游戏内存审查合同/整帧图集，不安装正式三级。"""
import json,sys,math,argparse
from pathlib import Path
import numpy as np
from PIL import Image
from resume import ROOT,ACTOR_OUT,RECEIVER_OUT,MEASUREMENT,SURFACES,sha
parser=argparse.ArgumentParser();parser.add_argument('--air-body-subregion',action='store_true');args=parser.parse_args()
OUT=ROOT/'reports/gomora-builtin/main-candidate210';OUT.mkdir(parents=True,exist_ok=True)
POSE='gomora_back_lift_receiver'
def read(p):return json.loads(p.read_text())
def boxes(im,anchor,band=16):
 a=np.asarray(im)[...,3]>0;result=[]
 for bottom in range(im.height,0,-band):
  top=max(0,bottom-band);ys,xs=np.where(a[top:bottom]);
  if len(xs):result.append([int(xs.min())-anchor[0],anchor[1]-(top+int(ys.max())+1),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)])
 return result
reg=read(ACTOR_OUT/'registration.json');actors=[];bounds=[]
for rr in reg['actor']:
 p=ROOT/rr['path'];assert sha(p)==rr['sha256'];actors.append(Image.open(p).convert('RGBA'));bounds.append({'path':str(p),'sha256':sha(p)})
aatlas=Image.new('RGBA',(512*18,320))
for i,im in enumerate(actors):aatlas.paste(im,(512*i,0))
aatlas.save(OUT/'actor.png')
receivers=[];pelvis=[];labels=[];holds={}
def append(im,lp,label,hold=None):
 i=len(receivers);receivers.append(im);pelvis.append(lp);labels.append(label)
 if hold is not None:holds[str(i)]=hold
 return i
measure=read(MEASUREMENT)['measurements'][1:]
for rp in [0,1]:
 p=RECEIVER_OUT/f'{rp:02d}.png';im=Image.open(p).convert('RGBA');can=Image.new('RGBA',(256,192));can.paste(im,(32,0));xy=measure[rp]['points']['R']['xy'];lp=[round(xy[0]*179/1024)+38,round(xy[1]*179/1024)+6];sx,sy=SURFACES[rp];append(can,lp,f'old_R{rp:02d}_known_contact_failure',[sx+38-128,184-(sy+6)]);bounds.append({'path':str(p),'sha256':sha(p)})
for file,xy,label in [('R02-full-210.png',[97,77],'R02v5'),('full-210.png',[101,75],'bridge'),('R03-full-210.png',[99,70],'R03')]:
 p=ROOT/'reports/gomora-builtin/bridge-review'/file;im=Image.open(p).convert('RGBA');can=Image.new('RGBA',(256,192));can.paste(im,(23,40));hold=[114+23-128,184-(81+40)] if label=='R02v5' else None;append(can,[xy[0]+23,xy[1]+40],label,hold);bounds.append({'path':str(p),'sha256':sha(p)})
for rp in [4,5]:
 p=RECEIVER_OUT/f'{rp:02d}.png';im=Image.open(p).convert('RGBA');can=Image.new('RGBA',(256,192));can.paste(im,(32,0));xy=measure[rp]['points']['R']['xy'];append(can,[round(xy[0]*179/1024)+38,round(xy[1]*179/1024)+6],f'old_R{rp:02d}');bounds.append({'path':str(p),'sha256':sha(p)})
# 现有完整倒立与翻滚相，只取整格，不旋转或重拼。后四相髋点是人工候选读点，非精确骨点。
manifest=read(ROOT/'assets/fighters/ultraman/animations/manifest.json')
for key,points in [('thrown_back',[[96,95],[97,142],[90,157],[106,161]]),('down',[[105,164]])]:
 clip=manifest['clips'][key];p=ROOT/clip['texture'].removeprefix('res://');src=Image.open(p).convert('RGBA');bounds.append({'path':str(p),'sha256':sha(p)})
 for j,point in enumerate(points):
  x,y,w,h=clip['rects'][j];im=src.crop((x,y,x+w,y+h));can=Image.new('RGBA',(256,192));can.paste(im,(32,0));append(can,[point[0]+32,point[1]],f'{key}_{j}_estimated_pelvis')
ratlas=Image.new('RGBA',(256*len(receivers),192))
states=[]
for i,im in enumerate(receivers):
 ratlas.paste(im,(256*i,0));states.append({'sprite':i,'dx':0,'dy':0,'hitboxes':[],'hurtboxes':boxes(im,[128,184]),'cancel':[],'events':[],'grab_points':{'waist':holds.get(str(i),[pelvis[i][0]-128,184-pelvis[i][1]])}})
ratlas.save(OUT/'receiver.png')
order=[0,1,3,4,5,6,7,2,9,8,10,11,12,13,14,15,16,17];dur=[4,8]+[4]*16;actor_for_tick=[ap for ap,d in zip(order,dur) for _ in range(d)]
back=[]
for ap,im in enumerate(actors):
 x=reg['actor'][ap]['paste_origin'][0]+160;y=int(np.where(np.asarray(im)[...,3][:,x]>0)[0][0]);back.append([x-256,304-y])
move=read(ROOT/'content/fighters/gomora/moves/special3.json');move.update(display_name='背掀210·未安装内存审查候选',startup=16,active=4,recovery=56,damage=490,stamina_cost=50,energy_cost=3000,kind='throw',level='mid',unblockable=True,launch=False,bounce=False,knockdown=True,chip_damage=0,manual_projectiles=True,super_level=3,air_allowed=False,throw_target_air=True,throw_schema=2,whiff_branch_tick=20,whiff_recovery_tick=56,throw_current_capture={'target_ids':['ultraman'],'states':['air'],'body_hurtbox_index':1,'first_tick':16,'entry_tick':20,'max_entry_root_delta':[14,14]},production_note='仅内存主游戏审查；00/01未解决，后倒立髋点未签收，禁止安装',feedback={'spark':'impact_hit','block_spark':'impact_guard','hitstop':4,'blockstop':3,'shake':0,'flash':0,'color':[1,1,1,1]},audio={'hit':'gomora_throw_grab','block':'gomora_guard_scrape','throw_slam':'gomora_throw_slam'})
move['frames']=[];trajectory=[];world=[224,188];landed=False;impact_tick=None;landing_root=None
for t,ap in enumerate(actor_for_tick):
 frame={'sprite':ap,'dx':0,'dy':0,'hitboxes':[],'hurtboxes':boxes(actors[ap],[256,304],24),'cancel':[],'events':[]}
 if t<4:frame.update(pause_clock=True,freeze_opponent=True,cinematic_stage='portrait')
 if 16<=t<20:frame['hitboxes']=[[back[ap][0]-20,back[ap][1]-12,28,12]];frame['target']={'mode':'capture_current'}
 elif 20<=t<32:
  ri=0 if t<24 else 1 if t<28 else 2
  frame['target']={'mode':'hold','pose':POSE,'sprite':ri,'facing':1,'root':[0,0],'grip':back[ap],'hold_point_overrides':{'ultraman':{POSE:holds}}}
 elif t>=32:
  ri=3 if t<34 else 4 if t<40 else 5 if t<44 else 6 if t<48 else 7 if t<52 else 8 if t<56 else 9 if t<60 else 10 if t<68 else 11
  lp=[pelvis[ri][0]-128,184-pelvis[ri][1]]
  if not landed:
   n=t-32;world=[world[0]-6,world[1]-(15-n)];root=[world[0]-256-lp[0],304-world[1]-lp[1]]
   if root[1]<=0:
    root[1]=0;landed=True;impact_tick=t;landing_root=root[:]
  else:root=landing_root[:];ri=11
  frame['target']={'mode':'root','pose':POSE,'sprite':ri,'facing':1,'root':root,'ground':True}
  if impact_tick==t:frame['target']['impact']=True
  trajectory.append({'tick':t,'actor':ap,'receiver':ri,'label':labels[ri],'root':root,'world_pelvis_candidate':world[:],'landed':landed})
 move['frames'].append(frame)
assert impact_tick is not None
for p in [OUT/'actor.png',OUT/'receiver.png']:bounds.append({'path':str(p),'sha256':sha(p)})
clips={'gomora':{'special3':{'texture':str(OUT/'actor.png'),'cell':512,'anchor_y':304,'anchors':[[256,304]]*18,'rects':[[512*i,0,512,320] for i in range(18)],'ticks':[4]*18,'loop':False}},'ultraman':{POSE:{'texture':str(OUT/'receiver.png'),'cell':256,'anchor_y':184,'anchors':[[128,184]]*len(receivers),'rects':[[256*i,0,256,192] for i in range(len(receivers))],'ticks':[4]*len(receivers),'loop':False}}}
contract={'schema':'ufeneo.gomora.back-lift-main-candidate.v1','root_runtime_ready':True,'installed':False,'accepted':False,'opponent':'ultraman','move':move,'receiver_states':{POSE:states},'clips':clips,'bound_resources':bounds,'release_geometry':trajectory,'pelvis_cell_readpoints':pelvis,'receiver_labels':labels,'impact_tick':impact_tick,'limits':['00/01是旧失败接触帧，只用于暴露完整链缺口。','210髋点误差敏感；不是已签收人体骨点。','倒立翻滚后相髋点是新的人工估计；首轮主游戏明确检查，不默认通过。','capture不得扩判定、注入空中状态或能量。','正式三级与assets/content不改。']}
if args.air_body_subregion:
 clip=manifest['clips']['flip_forward'];p=ROOT/clip['texture'].removeprefix('res://');assert sha(p)==clip['atlas_sha256'];bounds.append({'path':str(p),'sha256':sha(p)})
 regions=[[90,82,15,18],[94,92,10,12],[88,108,18,26],[90,86,13,14]]
 air=[]
 for age in range(80):
  sprite=max(0,min(3,int((age-2)/8)));x,y,w,h=regions[sprite];body=[x-96,184-y-h,w,h];assert body[0]>=-18 and body[0]+w<=18 and body[1]>=0 and body[1]+h<=128
  air.append({'sprite':sprite,'dx':0,'dy':0,'hitboxes':[],'hurtboxes':[[-18,0,36,128],body],'cancel':[],'events':[]})
 contract['receiver_states']['diagonal_air']=air
 contract['air_body_subregion']={'jump_speed':16,'visible_clip':'flip_forward','source_rectangles_xywh':regions,'original_hurtbox_union_preserved':True,'attacker_capture_boxes_unchanged':True,'body_hurtbox_index':1,'reason':'原diagonal_air缺失导致只有fallback索引0；追加其内部可见躯干子区，非扩大总hurtbox。'}
 contract['limits'].append('仅内存补充diagonal_air躯干子区；正式缺数据未修改。')
contract_name='contract-airbody.json' if args.air_body_subregion else 'contract.json'
(OUT/contract_name).write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n');print({'contract':str(OUT/contract_name),'impact':impact_tick,'frames':len(move['frames']),'pelvis':pelvis,'first_hold':move['frames'][20]['target']})
