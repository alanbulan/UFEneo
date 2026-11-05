"""绑定月亮dash_heavy候选与当前主游戏代码，仅生成reports中的内存验收合同。"""
import argparse
import copy
from pathlib import Path
import prepare as P
import numpy as np
from PIL import Image

MOVEMENT_ACTIONS = ["idle", "turn", "walk_forward", "walk_back"]
DASH_ACTIONS = ["dash_start", "dash", "dash_stop"]

def checked(ref):
 p=P.ROOT/ref['path']
 if P.sha(p)!=ref['sha256']:raise ValueError('SHA改变：'+str(p))
 return p

def alpha_state_frames(atlas, clip):
 frames=[]
 with Image.open(atlas) as image:
  for phase,(rect,ticks) in enumerate(zip(clip["rects"],clip["ticks"])):
   x,y,w,h=rect;alpha=np.asarray(image.crop((x,y,x+w,y+h)))[:,:,3]>0
   ys,_=np.where(alpha);top,bottom=int(ys.min()),int(ys.max())+1;boxes=[]
   for n in range(3):
    y0,y1=top+(bottom-top)*n//3,top+(bottom-top)*(n+1)//3;_,xs=np.where(alpha[y0:y1])
    if len(xs):boxes.append([int(xs.min())-160,280-y1,int(xs.max()-xs.min()+1),y1-y0])
   for _ in range(ticks):frames.append({"sprite":phase+int(clip.get('simulation_sprite_offset',0)),"dx":0,"dy":0,"hitboxes":[],"hurtboxes":copy.deepcopy(boxes),"cancel":[],"events":[]})
 return frames

def checked_dash_sources(prior, clips):
 import hashlib
 receipt_path=prior/'frames.json';receipt=P.read(receipt_path)
 if receipt['fighter']!='ultraman-arc__luna' or receipt['action']!='dash_sequence' or len(receipt['frames'])!=9:raise ValueError('本人dash九相清单不符')
 index_path=P.ROOT/'art/source-index.json';aliases=P.read(index_path)['aliases'];resources={receipt_path,index_path,prior/'candidate-clips.json',prior/'atlas.png'}
 with Image.open(prior/'atlas.png') as atlas:
  for phase,row in enumerate(receipt['frames']):
   if row['strict_size_passed'] or row['installed']:raise ValueError('不得虚构dash尺寸或安装验收')
   for key in ['source','image']:
    relative=row[key];visited=set()
    while relative in aliases:
     if relative in visited:raise ValueError('原源别名循环')
     visited.add(relative);relative=aliases[relative]
    path=P.ROOT/relative
    if P.sha(path)!=row[key+'_sha256']:raise ValueError('dash原源或成品SHA改变')
    resources.add(path)
    if key=='image':
     with Image.open(path) as image:
      if image.size!=(320,320) or image.mode!='RGBA':raise ValueError('dash整帧尺寸/模式错误')
      if hashlib.sha256(image.tobytes()).hexdigest()!=row['RGBA_sha256']:raise ValueError('dash整帧像素改变')
      if atlas.crop((320*phase,0,320*(phase+1),320)).tobytes()!=image.tobytes():raise ValueError('dash图集与逐相整帧不符')
  for action in DASH_ACTIONS:
   clip=clips[action]
   if clip['source_fighter']!='ultraman-arc__luna' or P.sha(prior/'atlas.png')!=clip['atlas_sha256']:raise ValueError('dash本人图集变化')
   if clip['anchors']!=[[160,280]]*len(clip['rects']):raise ValueError('dash根点改变')
 return resources

def build(out):
 out=out.resolve();out.relative_to(P.ROOT/'reports/luna-dash-heavy-resume')
 if out.exists():raise ValueError('输出已存在')
 manifest_path=P.OUTPUT/'manifest.json';manifest=P.read(manifest_path);resources={manifest_path,Path(__file__).resolve()}
 for k in ['samples','registration_review','rule_reference','clip','move']:resources.add(checked(manifest[k]))
 resources.update(checked(r) for r in manifest['processing_tools'].values())
 for row in manifest['frames']:
  for k in ['source','sample','image']:resources.add(checked(row[k]))
 samples=P.read(P.OUTPUT/'samples.json');resources.add(checked(samples['palette']));resources.add(checked(samples['source_receipt']))
 clips={'dash_heavy':P.read(checked(manifest['clip']))};moves={'dash_heavy':P.read(checked(manifest['move']))}
 prior=P.STAGE/'movement-contract-20261101-v1';bundle=P.read(prior/'bundle.json');states=P.read(prior/'state_frames.json')
 resources.update([prior/'bundle.json',prior/'state_frames.json'])
 for action in MOVEMENT_ACTIONS:
  clips[action]=copy.deepcopy(bundle['clips'][action]);clips[action]['source_fighter']='ultraman-arc__luna'
  atlas=P.STAGE/'goal-closeout-20261101-v1'/action/'atlas.png'
  if P.sha(atlas)!=clips[action]['atlas_sha256']:raise ValueError('本人idle/turn图集变化')
  clips[action]['texture']=atlas.as_posix();resources.add(atlas)
 dash_prior=P.STAGE/'dash-repair-20261102-v1/offline-nine-registered-v1'
 dash_clips=P.read(dash_prior/'candidate-clips.json');resources.update(checked_dash_sources(dash_prior,dash_clips));states['dash']=[]
 for action in DASH_ACTIONS:
  clip=copy.deepcopy(dash_clips[action]);clip['texture']=(dash_prior/'atlas.png').as_posix();clips[action]=clip
  states['dash'].extend(alpha_state_frames(dash_prior/'atlas.png',clip))
 atlas=P.OUTPUT/'atlas.png'
 if P.sha(atlas)!=clips['dash_heavy']['atlas_sha256']:raise ValueError('dash_heavy图集变化')
 clips['dash_heavy']['texture']=atlas.as_posix();resources.add(atlas)
 flags=P.ROOT/'content/fighters/ultraman-arc__luna/definition.json'
 if any(P.read(flags)[k] for k in ['implemented','playable','select_visible']):raise ValueError('禁止开放未齐装甲')
 model=P.ROOT/'art/fighters/ultraman-arc__luna/model/model-native.png';resources.update([flags,model])
 command_path=P.ROOT/'content/fighters/ultraman-arc/command_table.json';commands=[r for r in P.read(command_path) if r['move']=='dash_heavy' and r['states']==['dash']];resources.add(command_path)
 for folder in ['core','input','content','presentation','app','ui','third_party/shoto','tests/review/fighters/ultraman-arc/luna_dash_heavy','tests/review/fighters/ultraman-arc/luna_light_chain','tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1']:
  resources.update(p for p in (P.ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tres','.tscn','.gdshader'})
 cfg={'schema':'ufeneo.luna.dash_heavy-main-candidate.v1','root_runtime_ready':True,'fighter':'ultraman-arc__luna','opponent':'zetton',
      'playable':False,'implemented':False,'transform_enabled':False,'select_visible':False,
      'definition':{'id':'ultraman-arc__luna','display_name':'亚刻奥特曼 · 月亮装甲 · 冲刺飞踢候选','max_health':1000,'walk_speed':2,'jump_speed':16,'body_radius':18,
                    'moves':moves,'command_table':commands,'state_frames':{a:states[a] for a in MOVEMENT_ACTIONS+['dash']}},
      'presentation':{'model':model.as_posix(),'native':True,'anchor_y':280,'manifest_data':{'fighter':'ultraman-arc__luna','clips':clips}},
      'dependency_review':{'dash':'existing_own_nine_phase_candidate','strict_size_accepted':False,'new_registration_claimed':False,'state_hurtboxes':'derived_from_bound_own_atlas_alpha','complete_dash_cycle_accepted':False,'exercised_dash_phases':[0,1,2,3,4],'unexercised_dash_phases':[5,6,7,8],'initial_gap':{'hit':140,'block':140,'whiff':320},'input_plan':{'forward_taps':[20,22],'heavy_tick':34},'distance_basis':'首步2 + dash十一帧66 + 招式35 = 103；输入前间距72，起跳原规则不变，不扩大实体脚框' },
      'bound_resources':[{'path':p.as_posix(),'sha256':P.sha(p)} for p in sorted(resources)],'manifest':P.ref(manifest_path),'main_game_accepted':False,'replay_accepted':False}
 P.write(out,cfg)
 return out
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();print(build(args.output))
