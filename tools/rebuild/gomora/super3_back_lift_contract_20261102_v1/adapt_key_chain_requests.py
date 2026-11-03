"""只将根点名04/09草稿适配请求目录；不POST、不改原稿/11。"""
from pathlib import Path
import hashlib,json,copy
ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-key-chain-request-review-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def write(p,value):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 rows=[];protected={};p11=ART/'phase-11/request-001/brief.json';protected[p11]=sha(p11)
 for phase in [4,9]:
  draft=ART/f'briefs-v2/phase-{phase:02d}/brief.json';protected[draft]=sha(draft);v=copy.deepcopy(read(draft))
  for reference in v['references']:
   p=ROOT/reference['path'];assert sha(p)==reference['sha256'];protected[p]=sha(p)
  v['references']=[{k:r[k] for k in ['path','sha256']} for r in v['references']]
  v['root_reviewed_draft']=rec(draft)
  v['reference_adaptation']='Only path and sha256 keys for existing root serial client; all image bytes and prompt remain unchanged.'
  target=ART/f'phase-{phase:02d}/request-001/brief.json';write(target,v)
  assert read(target)['prompt']==read(draft)['prompt']
  rows.append(dict(phase=phase,draft=rec(draft),request=rec(target),prompt_changed=False,
   review='绝对完整姿势，完整双臂/胸髋/双腿/整尾；近亮LEFT后、远暗RIGHT前明确，未链式改图。',
   specific_pose=('30度前倾上背承接，双膝/髋缓冲、双爪下胸两侧，不是最深负重或掌击。' if phase==4 else
    '双足蹬地，膝半伸、髋升高、背15–20度前倾转直、双臂不同角打开，是07深负重与11松爪之间的挺背相。')))
 v11=read(p11);assert v11['frame']==11 and len(v11['references'])==2
 rows.append(dict(phase=11,request=rec(p11),modified=False,
  review='绝对完整后抛松爪，双足不离地、双膝伸髋、上背近直轻后展、双臂不同角张开、整尾反平衡；不重复09挺背中段。',
  foot_order='未明确写近亮LEFT后/远暗RIGHT前，也未反向规定；故请求无文字冲突，但不能宣称足序已有强约束，必须实看返回整源，保持现请求字节。',
  prompt_changed=False))
 for p,digest in protected.items():assert sha(p)==digest
 write(OUT/'key-chain-review-and-request-sha.json',dict(phases=rows,post_submitted=False,
  source_images_reviewed_this_step=False,review_scope='只读请求姿势合同，不把brief审核当实际成图通过。',
  protected_files=[rec(p) for p in protected]))
 print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
