"""保全v1草稿，只新增v2：按根已接07整源澄清近远足序。"""
from pathlib import Path
import json, hashlib, copy
ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
REPORT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-contract-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def read(p):return json.loads(p.read_text('utf-8-sig'))
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 original=REPORT/'remaining-16-briefs-v1.json';v1=read(original)
 source=ART/'phase-07/request-001/candidate.png';frozen={ROOT/r['path']:r['sha256'] for r in v1['briefs']}
 frozen[source]=sha(source);entries=[]
 for record in v1['briefs']:
  p=ROOT/record['path'];assert sha(p)==record['sha256'];v=copy.deepcopy(read(p));phase=v['frame']
  # Original v1 accidentally contradicted the first returned source. Retain it byte for byte.
  v['prompt']=v['prompt'].replace('Both feet remain solid, nearer foot slightly forward to RIGHT, far foot behind.',
   'Both feet remain solid: the NEAR lighter foot is behind toward LEFT, the FAR darker foot is ahead toward RIGHT.')
  v['prompt']+=' SUPPORT-FOOT ORDER: as observed in accepted phase07, the NEAR lighter thigh/leg/foot is on the rear LEFT and the FAR darker thigh/leg/foot is on the front RIGHT. Both complete broad feet remain planted in this support order; do not exchange them between phases or use foot sliding instead of knee/hip action. This is an anatomy/continuity instruction only, not an extra image attachment.'
  v['support_foot_contract']='根已接07实图：近侧亮腿/足在画面LEFT/后方，远侧暗腿/足在RIGHT/前方；完整两足保持支撑序，不逐相换腿/滑足。'
  v['draft_revision']=2;v['supersedes_unsubmitted_draft']=rec(p)
  v['first07_observation_reference_only']=rec(source)
  v['draft_correction_reason']='v1文字曾把近足写为前RIGHT，与首张根已接整源相反；仅新增v2，原v1和07/11冻结请求保持。'
  v['source_to_native_scale']=None;v['scale_policy']='共同整动作倍率待根核首07长尺/躯干；1/4仅原型，不逐相面积拟合。'
  target=ART/f'briefs-v2/phase-{phase:02d}/brief.json';save(target,v);entries.append(rec(target))
 for p,digest in frozen.items():assert sha(p)==digest
 save(REPORT/'remaining-16-briefs-v2.json',dict(briefs=entries,supersedes_index=rec(original),
  change='仅更正足序并保留首源尺度未签收；不动任何既有草稿/请求，图片附件仍只有原两张身份图。',
  first07_source=rec(source),first07_prototype=rec(ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-first07-prototype-v1/first07-readpoints-and-prototype.json'),
  post_count=0,root_owns_post=True,strict_size_passed=False,tool=rec(Path(__file__))))
 print(json.dumps(dict(index=str(REPORT/'remaining-16-briefs-v2.json'),briefs=len(entries)),ensure_ascii=False))
if __name__=='__main__':main()
