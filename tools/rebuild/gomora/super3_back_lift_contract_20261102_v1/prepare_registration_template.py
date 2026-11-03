"""仅写未授权的18相计划模板，不调用整动作处理程序。"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'art/fighters/gomora/stage4/super3-back-lift-20261102-v1'
OUT=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-registration-v1'
KNOWN={4:[712,863],5:[700,958],7:[700,947],9:[724,894],11:[724,932]}
def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for phase in range(18):
  source=ART/f'phase-{phase:02d}/request-001/candidate.png';acceptance=source.with_name('root-actual-source-review-v1.json')
  rows.append(dict(phase=phase,request=1,source=rec(source) if source.exists() and acceptance.exists() else None,
   root_acceptance=rec(acceptance) if source.exists() and acceptance.exists() else None,
   registration_root_source=KNOWN.get(phase),support_readpoint_note=('已完成完整源宽足底读点的原型根，待根在18相中接收统一支撑读点。' if phase in KNOWN else None),
   per_phase_scale=None,area_fit=None))
 with (OUT/'registration-plan-template.json').open('x',encoding='utf8') as f:json.dump(dict(
  root_all18_sources_accepted=False,root_full_action_registration_authorized=False,root_readpoint_plan_accepted=False,
  common_scale=[1,4],cell=[512,320],anchor=[256,304],output='reports/review/2026-11-02/gomora-super3-back-lift-registration-v1/registered18-v1',
  phases=rows,template_not_runnable=True),f,ensure_ascii=False,indent=2);f.write('\n')
 print('Only incomplete plan template written; full18_registration not called')
if __name__=='__main__':main()
