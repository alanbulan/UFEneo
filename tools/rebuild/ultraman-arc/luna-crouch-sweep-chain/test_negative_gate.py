"""真实v3 trace只读基线+内存变造负例，不启动Godot、不覆盖历史。"""
import copy,hashlib,json
from pathlib import Path
import test_check as gate
R=gate.R
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 cfg=gate.read(R/'contract-v3.json');run=R/'headless-v3'
 baseline_paths=[R/'contract-v3.json',*(Path(x['path']) for x in cfg['bound_resources']),*run.rglob('*.json')]
 before={str(p):sha(p) for p in baseline_paths}
 positive=gate.check(run)
 def source(kind):return gate.read(run/('1280x720-right-'+kind+'-original')/'main-trace.json')
 trials=[]
 def attempt(name,kind,mutate):
  data=copy.deepcopy(source(kind));mutate(data)
  try:gate.check_trace_events(data,cfg)
  except AssertionError as e:trials.append({'name':name,'rejected':True,'reason':str(e)})
  else:trials.append({'name':name,'rejected':False})
 def clear(d):
  for row in d['trace']:row['events']=[]
 def hp(d):
  for row in d['trace']:row['pair'][1]['hp']=1000
 def both(d):clear(d);hp(d)
 def duplicate(d):
  row=next(r for r in d['trace'] if any(e.get('kind')=='hit' for e in r['events']))
  row['events'].append(copy.deepcopy(next(e for e in row['events'] if e.get('kind')=='hit')))
 def drop_block(d):
  for row in d['trace']:
   for i,e in enumerate(row['events']):
    if e.get('kind')=='block' and e.get('move')=='sweep':row['events'].pop(i);return
  raise RuntimeError('baseline sweep block absent')
 attempt('clear_events','hit',clear)
 attempt('restore_hp_to_1000','hit',hp)
 attempt('clear_events_and_restore_hp','hit',both)
 attempt('duplicate_contact','hit',duplicate)
 attempt('remove_sweep_block','block',drop_block)
 attempt('alter_intermediate_hp','hit',lambda d:d['trace'][80]['pair'][1].update(hp=999))
 after={str(p):sha(p) for p in baseline_paths}
 assert before==after,'read-only baseline changed'
 assert all(t['rejected'] for t in trials),trials
 result={'schema':'ufeneo.luna.external-gate-negative-tests.v1','positive':positive,'negative_cases':trials,'read_only_baseline':{'file_count':len(before),'before_digest':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'after_digest':hashlib.sha256(json.dumps(after,sort_keys=True).encode()).hexdigest(),'unchanged':before==after},'checker_sha256':sha(Path(gate.__file__)),'test_sha256':sha(Path(__file__)),'v3_inner_gate_repaired':False,'godot_started':False}
 out=R/'external-gate-negative-v1.json';assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(out,sha(out))
if __name__=='__main__':run()
