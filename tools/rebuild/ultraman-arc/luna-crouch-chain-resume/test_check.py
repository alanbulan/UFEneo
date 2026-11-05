"""独立离线核证，不属于已封运行依赖；不改合同和模拟。"""
import importlib.util,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('chain',HERE/'main_bundle.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def main():
 cfg=m.check(ROOT/'reports/luna-crouch-chain-resume/contract-v3.json')
 first=cfg['definition']['moves']['crouch_light'];second=cfg['definition']['moves']['crouch_light2']
 assert [first[k] for k in ['startup','active','recovery','damage','stamina_cost']]==[3,3,12,65,30]
 assert [second[k] for k in ['startup','active','recovery','damage','stamina_cost']]==[3,7,8,65,30]
 assert cfg['second_fist_boxes']=={'1':[52,69,13,14]}
 assert [i for i,f in enumerate(first['frames']) if 'crouch_light2' in f['cancel']]==list(range(3,18))
 assert [i for i,f in enumerate(second['frames']) if 'sweep' in f['cancel']]==list(range(3,18))
 for action,move in [('crouch_light',first),('crouch_light2',second)]:
  old=m.read(ROOT/f'content/fighters/ultraman-arc/moves/{action}.json')
  assert all(move[k]==old[k] for k in old if k not in ['frames','display_name','production_source'])
  assert all(all(f[k]==g[k] for k in g if k not in ['sprite','hurtboxes','hitboxes']) for f,g in zip(move['frames'],old['frames']))
 logic=m.read(ROOT/'reports/luna-crouch-chain-resume/logic-v3/result.json');assert not logic['errors'] and len(logic['cases'])==8
 for c in logic['cases']:
  assert c['damage']==(130 if c['kind'] in ['hit','stand_guard'] else 0)
  assert len(c['moves'])==(2 if c['kind'] in ['hit','stand_guard'] else 1)
 sem=m.read(ROOT/'reports/luna-crouch-chain-resume/logic-v3/semantics.json');assert not sem['errors']
 assert all(c['final_hash']==c['replay_hash'] for c in sem['cases'])
 assert any(c['request']['kind']=='whiff' and any(not s['is_cancel'] for s in c['second_starts']) for c in sem['cases'])
 assert any(c['request']['kind']=='block' and any(not s['is_cancel'] for s in c['second_starts']) for c in sem['cases'])
 assert all(not c['second_starts'] for c in sem['cases'] if c['request']['held'])
 assert all(c['second_starts'] and c['second_starts'][0]['is_cancel'] for c in sem['cases'] if c['request']['kind']=='hit' and c['request']['gap']==75 and c['request']['second_tick']==27 and not c['request']['held'])
 for trace_path in (ROOT/'reports/luna-crouch-chain-resume/headless-v3').glob('*/main-trace.json'):
  trace=m.read(trace_path)
  for action,ticks in trace['animation_ticks'].items():
   assert ticks==cfg['animation_ticks'][action]
   assert all(n==int(n) and n>0 for n in ticks)
  m.check_trace(trace)
 print(json.dumps({'passed':True,'cases':len(sem['cases']),'contract_sha256':m.sha(ROOT/'reports/luna-crouch-chain-resume/contract-v3.json'),'test_sha256':m.sha(Path(__file__))}))
if __name__=='__main__':main()
