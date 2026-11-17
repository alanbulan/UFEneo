"""绑定月亮sweep候选与当前主游戏代码，仅生成reports中的内存验收合同。"""
import argparse
import copy
from pathlib import Path
import prepare as P
import numpy as np
from PIL import Image

CROUCH_ACTIONS = ["crouch_start", "crouch", "crouch_rise"]

def alpha_state_frames(atlas, clip):
 frames=[]
 with Image.open(atlas) as image:
  for phase,(rect,ticks) in enumerate(zip(clip["rects"],clip["ticks"])):
   x,y,w,h=rect;alpha=np.asarray(image.crop((x,y,x+w,y+h)))[:,:,3]>0
   ys,_=np.where(alpha);top,bottom=int(ys.min()),int(ys.max())+1;boxes=[]
   for n in range(3):
    y0,y1=top+(bottom-top)*n//3,top+(bottom-top)*(n+1)//3;_,xs=np.where(alpha[y0:y1])
    if len(xs):boxes.append([int(xs.min())-160,280-y1,int(xs.max()-xs.min()+1),y1-y0])
   for _ in range(ticks):frames.append({"sprite":phase,"dx":0,"dy":0,"hitboxes":[],"hurtboxes":copy.deepcopy(boxes),"cancel":[],"events":[]})
 return frames

def checked(ref):
 p=P.ROOT/ref['path']
 if P.sha(p)!=ref['sha256']:raise ValueError('SHA改变：'+str(p))
 return p

def checked_crouch_sources(prior, action, clip):
 receipt_path=prior/action/'frames.json';receipt=P.read(receipt_path)
 if receipt['fighter']!='ultraman-arc__luna' or receipt['action']!=action or len(receipt['frames'])!=2:raise ValueError('蹲族帧清单不符')
 if clip['anchors']!=[[160,280]]*2 or len(clip['rects'])!=2:raise ValueError('蹲族必须两相同根点')
 index_path=P.ROOT/'art/source-index.json';aliases=P.read(index_path)['aliases'];resources={receipt_path,index_path}
 resources.add(checked(receipt['palette']));resources.add(checked(receipt['atlas']))
 with Image.open(prior/action/'atlas.png') as atlas:
  for phase,row in enumerate(receipt['frames']):
   for key in ['source','image']:
    relative=row[key];visited=set()
    while relative in aliases:
     if relative in visited:raise ValueError('原源别名循环')
     visited.add(relative);relative=aliases[relative]
    path=P.ROOT/relative
    if P.sha(path)!=row[key+'_sha256']:raise ValueError('蹲族原源或成品SHA改变')
    resources.add(path)
    if key=='image':
     with Image.open(path) as image:
      x,y,w,h=clip['rects'][phase]
      if atlas.crop((x,y,x+w,y+h)).tobytes()!=image.tobytes():raise ValueError('蹲族图集与逐相图不符')
 return resources

def build(out):
 out=out.resolve();out.relative_to(P.ROOT/'reports/luna-sweep-resume')
 if out.exists():raise ValueError('输出已存在')
 manifest_path=P.OUTPUT/'manifest.json';manifest=P.read(manifest_path);resources={manifest_path,Path(__file__).resolve()}
 for k in ['samples','registration_review','rule_reference','clip','move']:resources.add(checked(manifest[k]))
 resources.update(checked(r) for r in manifest['processing_tools'].values())
 for row in manifest['frames']:
  for k in ['source','sample','image']:resources.add(checked(row[k]))
 samples=P.read(P.OUTPUT/'samples.json');resources.add(checked(samples['palette']));resources.add(checked(samples['source_receipt']))
 clips={'sweep':P.read(checked(manifest['clip']))};moves={'sweep':P.read(checked(manifest['move']))}
 prior=P.STAGE/'movement-contract-20261101-v1';bundle=P.read(prior/'bundle.json');states=P.read(prior/'state_frames.json')
 resources.update([prior/'bundle.json',prior/'state_frames.json'])
 for action in ['idle','turn']:
  clips[action]=copy.deepcopy(bundle['clips'][action]);clips[action]['source_fighter']='ultraman-arc__luna'
  atlas=P.STAGE/'goal-closeout-20261101-v1'/action/'atlas.png'
  if P.sha(atlas)!=clips[action]['atlas_sha256']:raise ValueError('本人idle/turn图集变化')
  clips[action]['texture']=atlas.as_posix();resources.add(atlas)
 crouch_prior=P.STAGE/'crouch-family-repair-20261102-v1/offline-nine-registered-v1'
 for action in CROUCH_ACTIONS:
  clip_path=crouch_prior/action/'candidate-clip.json';clip=copy.deepcopy(P.read(clip_path));atlas=crouch_prior/action/'atlas.png'
  if clip['source_fighter']!='ultraman-arc__luna' or P.sha(atlas)!=clip['atlas_sha256']:raise ValueError('本人蹲族来源变化')
  clip['texture']=atlas.as_posix();clips[action]=clip;states[action]=alpha_state_frames(atlas,clip)
  resources.update([clip_path,atlas]);resources.update(checked_crouch_sources(crouch_prior,action,clip))
 atlas=P.OUTPUT/'atlas.png'
 if P.sha(atlas)!=clips['sweep']['atlas_sha256']:raise ValueError('sweep图集变化')
 clips['sweep']['texture']=atlas.as_posix();resources.add(atlas)
 flags=P.ROOT/'content/fighters/ultraman-arc__luna/definition.json'
 if any(P.read(flags)[k] for k in ['implemented','playable','select_visible']):raise ValueError('禁止开放未齐装甲')
 model=P.ROOT/'art/fighters/ultraman-arc__luna/model/model-native.png';resources.update([flags,model])
 command_path=P.ROOT/'content/fighters/ultraman-arc/command_table.json';commands=[r for r in P.read(command_path) if r['move']=='sweep' and r['states']==['crouch']];resources.add(command_path)
 for folder in ['core','input','content','presentation','app','ui','third_party/shoto','tests/review/fighters/ultraman-arc/luna_sweep','tests/review/fighters/ultraman-arc/luna_light_chain','tools/rebuild/ultraman-arc/armor_s2_walk_source_review_20261102_v1']:
  resources.update(p for p in (P.ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.gd','.json','.tres','.tscn','.gdshader'})
 cfg={'schema':'ufeneo.luna.sweep-main-candidate.v1','root_runtime_ready':True,'fighter':'ultraman-arc__luna','opponent':'zetton',
      'playable':False,'implemented':False,'transform_enabled':False,'select_visible':False,
      'definition':{'id':'ultraman-arc__luna','display_name':'亚刻奥特曼 · 月亮装甲 · 扫腿候选','max_health':1000,'walk_speed':2,'jump_speed':16,'body_radius':18,
                    'moves':moves,'command_table':commands,'state_frames':{a:states[a] for a in ['idle','turn']+CROUCH_ACTIONS}},
      'presentation':{'model':model.as_posix(),'native':True,'anchor_y':280,'manifest_data':{'fighter':'ultraman-arc__luna','clips':clips}},
      'dependency_review':{'crouch_family':'existing_own_candidate','strict_size_accepted':False,'new_registration_claimed':False,'state_hurtboxes':'derived_from_bound_own_atlas_alpha'},
      'bound_resources':[{'path':p.as_posix(),'sha256':P.sha(p)} for p in sorted(resources)],'manifest':P.ref(manifest_path),'main_game_accepted':False,'replay_accepted':False}
 P.write(out,cfg)
 return out
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();print(build(args.output))
