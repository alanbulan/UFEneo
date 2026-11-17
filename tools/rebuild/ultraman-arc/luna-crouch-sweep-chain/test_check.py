"""离线检查最终技术证据，不启动Godot、不改模拟。"""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'reports/luna-crouch-sweep-chain'
def read(p):return json.loads(p.read_text())
def check_trace_events(data,cfg):
 trace=data['trace'];kind=data['kind']
 assert len(trace)==180
 contacts=[(e['move'],e['kind']) for row in trace for e in row['events'] if e.get('player')==0 and e.get('kind') in ['hit','block']]
 expected=[('crouch_light','hit'),('crouch_light2','hit'),('sweep','hit')] if kind in ['hit','stand_guard'] else [('crouch_light','block'),('sweep','block')] if kind=='block' else []
 assert contacts==expected,('contact_sequence',contacts)
 assert trace[0]['pair'][1]['hp']-trace[-1]['pair'][1]['hp']==(195 if kind in ['hit','stand_guard'] else 0)
 assert not any(e.get('player')==1 and e.get('kind') in ['hit','block'] for row in trace for e in row['events'])
 assert all(not row['projectiles'] for row in trace)
 if kind in ['hit','stand_guard']:assert any(row['pair'][1]['state']=='down' for row in trace)
 else:assert not any(row['pair'][1]['state'] in ['down','launch','wake'] for row in trace)
 for row in trace:
  f=row['pair'][0];action=f['move_id']
  if action:
   timeline=[i for i,n in enumerate(cfg['animation_ticks'][action]) for _ in range(int(n))]
   assert f['frame_sprite']==f['animation']['index']==timeline[int(f['move_tick'])]
 expected_hp=1000
 for row in trace:
  for e in row['events']:
   if e.get('player')==0 and e.get('kind')=='hit':expected_hp-=int(cfg['definition']['moves'][e['move']]['damage'])
  assert row['pair'][1]['hp']==expected_hp,('hp_timeline',row['tick'])
  assert row['pair'][0]['hp']==1000,('attacker_hp',row['tick'])

def check(run_directory=None):
 cfg=read(R/'contract-v3.json')
 for r in cfg['bound_resources']:assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
 from PIL import Image
 manifest=read(ROOT/'art/fighters/ultraman-arc__luna/stage2/sweep-registered-20261105-v1/manifest.json')
 clip=cfg['presentation']['manifest_data']['clips']['sweep']
 assert clip['ticks']==[3,3,3,4,4,5,6]
 with Image.open(clip['texture']) as atlas:
  for row in manifest['frames']:
   with Image.open(ROOT/row['image']['path']) as image, Image.open(ROOT/row['sample']['path']) as sample:
    whole=Image.new('RGBA',(320,320));whole.paste(sample,tuple(row['translation']))
    assert image.tobytes()==whole.tobytes()==atlas.crop((320*row['phase'],0,320*(row['phase']+1),320)).tobytes()
 logic=read(R/'logic-v3.json');assert not logic['errors'] and len(logic['cases'])==8
 sem=read(R/'semantics-v3.json');assert not sem['errors'] and len(sem['cases'])==104
 for c in sem['cases']:
  assert c['final_hash']==c['replay_hash']
  for x in c['second_starts']:
   if x['is_cancel']:assert x['before']['move']=='crouch_light2' and x['before']['confirmed'] and 'sweep' in x['before']['cancel']
 for facing in [1,-1]:
  cases=[c for c in sem['cases'] if c['request']['facing']==facing and not c['request']['held'] and c['request']['second_tick']==37]
  for c in cases:
   r=c['request']
   if r['kind']=='hit' and r['gap']<=90:assert c['damage']==195 and c['second_starts'][0]['is_cancel']
   if r['kind']=='hit' and r['gap']==100:
    assert c['damage']==130 and not c['second_starts'][0]['is_cancel']
    assert c['contacts'][-1]['receiver_before']['state']=='idle'
   if r['kind']=='hit' and r['gap'] in [75,90]:
    assert c['contacts'][-1]['receiver_before']['state']=='hit'
    assert all(x['state']=='hit' for x in c['receiver_timeline'] if c['contacts'][1]['input_frame']<x['frame']<=c['contacts'][2]['input_frame'])
   if r['kind'] in ['block','whiff']:assert c['damage']==0 and not c['second_starts'][0]['is_cancel']
 for right in [c for c in sem['cases'] if c['request']['facing']==1]:
  target=dict(right['request'],facing=-1);left=next(c for c in sem['cases'] if c['request']==target)
  assert right['damage']==left['damage']
  assert [(x['input_frame'],x['is_cancel']) for x in right['second_starts']]==[(x['input_frame'],x['is_cancel']) for x in left['second_starts']]
 run_directory=Path(run_directory) if run_directory else R/'headless-v3'
 result=read(run_directory/'runner-result.json');assert result['completed'] and len(result['parts'])==(16 if all(p['headless'] for p in result['parts']) else 32)
 for part in result['parts']:
  data=read(Path(part['folder'])/'main-trace.json');trace=data['trace'];kind=part['kind']
  check_trace_events(data,cfg)
  if part['replay']:
   original=read(Path(part['folder'].replace('-replay','-original'))/'main-trace.json')['trace']
   for key in ['state_hash','events','projectiles','original_inputs','pair']:assert [r[key] for r in original]==[r[key] for r in trace]
 return {'passed':True,'parts':len(result['parts']),'semantics_cases':104,'logic_cases':8,'v3_inner_gate_repaired':False,'external_gate_required':True,'art_accepted':False}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path);a=p.parse_args();print(json.dumps(check(a.run),ensure_ascii=False))
