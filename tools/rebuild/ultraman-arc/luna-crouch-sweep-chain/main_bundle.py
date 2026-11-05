"""三招只读整帧RAM技术探针。尾段美术未通过，不安装。"""
import importlib.util,json,hashlib,argparse,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent; REPORT=ROOT/'reports/luna-crouch-sweep-chain'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load('chain_bundle',HERE.parent/'luna-crouch-chain-resume/main_bundle.py')
read=base.read;sha=base.sha;write=base.write

def freeze(out,engine):
 base.REPORT=REPORT
 first=out.with_name(out.stem+'-two-punch-base.json');base.freeze(first,engine)
 cfg=read(first);manifest_path=ROOT/'art/fighters/ultraman-arc__luna/stage2/sweep-registered-20261105-v1/manifest.json';m=read(manifest_path)
 resources={Path(r['path']) for r in cfg['bound_resources']};resources.add(manifest_path)
 def checked(ref):
  p=ROOT/ref['path'];assert sha(p)==ref['sha256'];resources.add(p);return p
 for key in ['samples','registration_review','rule_reference','clip','move']:checked(m[key])
 for row in m['frames']:
  for key in ['source','sample','image']:checked(row[key])
 move=read(checked(m['move']));original=read(checked(m['rule_reference']))
 for key in original:
  if key not in ['frames','production_source','display_name']:assert move[key]==original[key],key
 assert len(move['frames'])==len(original['frames'])==28
 for a,b in zip(move['frames'],original['frames']):
  for k in b:
   if k not in ['sprite','hitboxes','hurtboxes']:assert a[k]==b[k]
 clip=read(checked(m['clip']));atlas=manifest_path.parent/'atlas.png';assert sha(atlas)==clip['atlas_sha256'];resources.add(atlas);clip['texture']=str(atlas)
 assert clip['ticks']==[3,3,3,4,4,5,6] and clip['anchors']==[[160,280]]*7
 cfg['schema']='ufeneo.luna.crouch_sweep_chain-main-candidate.v1';cfg['definition']['moves']['sweep']=move
 cfg['definition']['command_table'] += [r for r in read(ROOT/'content/fighters/ultraman-arc/command_table.json') if r['move']=='sweep' and r['states'] in [['crouch'],['crouch_light2']]]
 cfg['presentation']['manifest_data']['clips']['sweep']=clip;cfg['animation_ticks']['sweep']=clip['ticks']
 cfg['input_contract']={'light_frames':[20,27],'heavy_frame':37,'direction':[0,-1],'technical_probe_only':True}
 cfg['limitations']=['旧扫腿04落脚后05再次伸腿，视觉不通过','跨招共同尺度未签收','非实速/真人键盘/声音验收','正式资源和规则不改']
 for tree in [HERE,ROOT/'tests/review/fighters/ultraman-arc/luna_crouch_sweep_chain']:
  resources.update(p for p in tree.rglob('*') if p.suffix in ['.py','.gd','.json'])
 cfg['bound_resources']=[base.base.ref(p) for p in sorted(resources)];cfg['source_fingerprint']=hashlib.sha256(json.dumps(cfg['bound_resources'],sort_keys=True).encode()).hexdigest();write(out,cfg);print(out,sha(out))

def check_trace(data,graphical=False,size=None,idle_ticks=None):
 assert not data['failures'],data['failures'];trace=data['trace'];assert len(trace)==180
 kind=data['kind'];moves=set();contacts=[]
 for i,row in enumerate(trace):
  assert row['tick']==i+1 and row['movie_frame']==i
  assert row['original_inputs']==[[0,-1,1 if i in [20,27] else 2 if i==37 else 0],[0,-1 if kind=='block' else 0,8 if kind in ['block','stand_guard'] else 0]]
  assert not row['projectiles'] and row['training_overlay_visible']
  own=row['pair'][0]
  if own['move_id']:
   action=own['move_id'];moves.add(action);phases=[p for p,n in enumerate(data['animation_ticks'][action]) for _ in range(int(n))]
   assert own['frame_sprite']==own['animation']['index']==phases[int(own['move_tick'])]
  assert own['x']==trace[0]['pair'][0]['x'] and own['height']==0
  contacts.extend(e for e in row['events'] if e.get('kind') in ['hit','block'] and e.get('player')==0)
  for f in row['pair']:
   x,y,w,h=f['full_alpha_viewport_bounds'];assert x>=0 and y>=0 and x+w<=640 and y+h<=360
 assert moves==({'crouch_light','crouch_light2','sweep'} if kind in ['hit','stand_guard'] else {'crouch_light','sweep'})
 assert trace[-1]['pair'][0]['state']=='crouch'
 if graphical:
  expected={'before-input-crouch','returned-crouch'}
  for row in trace:
   f=row['pair'][0]
   if f['move_id'] and f['move_tick'] in [0,1,2,3,5,6,8,9,10,12,13,16,17,21,22,27]:expected.add(f"{f['move_id']}-tick-{int(f['move_tick']):02d}-phase-{int(f['frame_sprite']):02d}")
  assert {s['key'] for s in data['stills']}==expected and len(data['stills'])==len(expected)
  for still in data['stills']:
   assert still['dimensions']==still['window_dimensions']==size and not still['resized'] and sha(Path(still['path']))==still['sha256']
   req=still['request'];row=trace[still['movie_frame']]
   assert req['tick']==still['captured_tick']==row['tick'] and req['state_hash']==row['state_hash'] and still['captured_sprite']==row['pair'][0]['frame_sprite']
   assert req['pair']==row['pair'] and req['hud_visible'] and req['training_overlay_visible'] and req['final_safe_rect']==req['hud_safe_rect']
   sx,sy,sw,sh=req['hud_safe_rect']
   for x,y,w,h in req['final_render_bounds']:assert x>=sx-.1 and y>=sy-.1 and x+w<=sx+sw+.1 and y+h<=sy+sh+.1
 assert trace[-1]["pair"][1]["state"]==("crouch_guard" if kind=="block" else "guard" if kind=="stand_guard" else "idle")


def run(contract,out,headless):
 # Reuse exact current runner mechanics, not any frozen historical contract.
 source=(HERE.parent/'luna-crouch-chain-resume/main_bundle.py').read_text();fragment=source[source.index('LENGTH=180'):source.index("if __name__")]
 fragment=fragment.replace('luna_crouch_chain/','luna_crouch_sweep_chain/')
 ns=dict(base.__dict__);ns.update(REPORT=REPORT,check_trace=check_trace,base=base.base);exec(fragment,ns);ns['run'](contract,out,headless)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--out',type=Path,required=True);p.add_argument('--engine',type=Path,default=Path('/usr/local/bin/godot'));p.add_argument('--contract',type=Path);p.add_argument('--headless',action='store_true');a=p.parse_args()
 if a.command=='freeze':freeze(a.out.resolve(),a.engine.resolve())
 else:run(a.contract.resolve(),a.out.resolve(),a.headless)
