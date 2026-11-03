"""仅适配尚未POST的14相，冻结原v2 prompt和两身份附件。"""
from pathlib import Path
import json,hashlib,copy
ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-remaining14-request-review-v1'
ORDER=[0,1,2,3,5,6,8,10,12,13,14,15,16,17]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 protected={ART/f'phase-{p:02d}/request-001/brief.json':sha(ART/f'phase-{p:02d}/request-001/brief.json') for p in [4,7,9,11]}
 rows=[]
 for i,phase in enumerate(ORDER):
  draft=ART/f'briefs-v2/phase-{phase:02d}/brief.json';protected[draft]=sha(draft);v=copy.deepcopy(read(draft))
  assert v['frame']==phase and v['submitted'] is False
  for r in v['references']:
   p=ROOT/r['path'];assert sha(p)==r['sha256'];protected[p]=sha(p)
  v['references']=[{k:r[k] for k in ['path','sha256']} for r in v['references']]
  v['root_reviewed_draft']=rec(draft)
  v['reference_adaptation']='Only path and sha256 keys for existing root serial client; all image bytes and prompt remain unchanged.'
  target=ART/f'phase-{phase:02d}/request-001/brief.json';save(target,v)
  assert read(target)['prompt'].encode('utf8')==read(draft)['prompt'].encode('utf8')
  rows.append(dict(order=i+1,phase=phase,phase_name=v['phase_name'],request=rec(target),draft=rec(draft),
   prompt_utf8_sha256=hashlib.sha256(v['prompt'].encode('utf8')).hexdigest(),prompt_preserved=True,
   references_only_path_sha256=all(set(r)=={'path','sha256'} for r in v['references'])))
 for p,digest in protected.items():assert sha(p)==digest
 save(OUT/'remaining14-request-order-sha.json',dict(order=ORDER,requests=rows,post_submitted=False,
  root_owns_serial_post=True,source_actual_review_required_per_return=True,protected_files_unchanged=[rec(p) for p in protected]))
 lines=['# 余14张未提交请求顺序与SHA','', '仅适配请求目录；原v2 prompt UTF-8内容及两个身份附件保持，未POST。根逐张审原brief与回图后串行推进。04/07/09/11请求完全未动。','', '| 顺序 | 相 | 动作 | request-001/brief.json SHA-256 |','| --- | --- | --- | --- |']
 lines += [f"| {r['order']} | {r['phase']:02d} | {r['phase_name']} | `{r['request']['sha256']}` |" for r in rows]
 lines += ['', '完整路径、草稿SHA和prompt SHA见`remaining14-request-order-sha.json`。']
 with (OUT/'README.md').open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
 print(json.dumps(dict(index=str(OUT/'remaining14-request-order-sha.json'),order=ORDER),ensure_ascii=False))
if __name__=='__main__':main()
