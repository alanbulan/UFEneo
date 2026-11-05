"""收口第三版八条正常/诊断主游戏原输入的独立及格式6回放。"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'reports/gomora-builtin/main-midlate-v3-20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    out=ROOT/'docs/verification/gomora-midlate-v3-20261105-main-replay.json';assert not out.exists()
    cases=[]
    for mode in ['gui','diagnostic']:
        for name in ['owner0-720','owner1-720','owner0-1080','owner1-1080']:
            tp=BASE/mode/name/'main-trace.json';rp=BASE/mode/(name+'-independent-replay')/'replay-result.json'
            r=read(rp);t=read(tp);run=read(rp.with_name('run-result.json'))
            assert run['exit']==0 and not run['diagnostics'] and run['sources_unchanged']
            assert not r['errors'] and r['format6_independent_replay'] and r['trace_sha256']==sha(tp)
            assert r['observations']==760 and r['simulation_steps']==685 and r['owner']==int(name[5])
            assert not r['loads_driver'] and not r['calls_sample'] and not r['sets_states'] and not r['sets_start_positions'] and not r['adds_ticks']
            assert len(r['costs'])==len(r['captures'])==len(r['slams'])==1 and not r['techs'] and not r['whiffs']
            assert r['captures'][0]['raw']==18 and r['slams'][0]['raw']==68 and r['slams'][0]['damage']==490
            tape=Path(r['format6_path']);f=read(tape)
            assert f['format']==6 and len(f['frames'])==685
            assert r['candidate_contract_sha256']==sha(BASE/'contract.json')
            cases.append({'mode':mode,'name':name,'trace':str(tp.relative_to(ROOT)),'trace_sha256':sha(tp),'replay':str(rp.relative_to(ROOT)),'replay_sha256':sha(rp),'format6_sha256':sha(tape),**{k:r[k] for k in ['owner','case','observations','simulation_steps','costs','captures','slams','techs','whiffs','errors','format6_independent_replay']}})
    d={'date':'2026-11-05','reviewer':'root_delegated_by_user','status':'eight_main_original_input_tapes_and_format6_replay_passed','contract_sha256':sha(BASE/'contract.json'),'cases':cases,
       'result':'正常与诊断八条主游戏原InputFrame独立回放及format6二次回放通过，每带760观察/685模拟tick。实际raw18捕获、raw68唯一490伤与一次费用成立；不加载driver，不注入位置/状态，不补tick。',
       'limits':['这是本候选回放证明，不是完整美术或实速验收。','自动物理键非真人键盘，无录屏、声音验收。','mode=root离背不等于mode=release机制已验。'],'installed':False,'art_accepted':False}
    out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(out)
if __name__=='__main__':main()
