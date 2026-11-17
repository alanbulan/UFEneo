"""只读核对第三版冻结合同、原输入和独立回放；不运行引擎、不签美术验收。"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'reports/gomora-builtin/main-midlate-v3-20261105'
OUT = ROOT / 'docs/verification/gomora-midlate-v3-20261105-logic.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def run_ok(folder):
    r = read(folder / 'run-result.json')
    assert r['exit'] == 0 and not r['diagnostics'] and r['sources_unchanged']
    return r

def main():
    assert not OUT.exists(), '不得覆盖已有证据'
    contract_path = BASE / 'contract.json'
    c = read(contract_path)
    old_path = Path(c['midlate_v3_plan']['base_contract'])
    old = read(old_path)
    assert sha(old_path) == c['midlate_v3_plan']['base_sha256']
    assert not c['accepted'] and not c['installed']
    for resource in c['bound_resources']:
        assert sha(Path(resource['path'])) == resource['sha256'], resource['path']
    changed = [i for i, (a, b) in enumerate(zip(old['move']['frames'], c['move']['frames'])) if a != b]
    assert changed == [27, 28]
    for key in old['move']:
        if key != 'frames': assert old['move'][key] == c['move'][key], key
    pose = 'gomora_back_lift_receiver'
    assert c['receiver_states'][pose][:-1] == old['receiver_states'][pose]
    atlas = np.array(Image.open(c['clips']['ultraman'][pose]['texture']).convert('RGBA'))
    previous = np.array(Image.open(old['clips']['ultraman'][pose]['texture']).convert('RGBA'))
    assert np.array_equal(atlas[:, :previous.shape[1]], previous)
    reg = c['chain_registration'][-1]
    full = np.array(Image.open(reg['source']).convert('RGBA').resize(tuple(reg['fixed_size']), Image.Resampling.NEAREST))
    x, y = reg['fixed_paste']; w, h = reg['fixed_size']
    cell = atlas[:, 16*256:17*256]
    assert np.array_equal(cell[y:y+h,x:x+w,:3], full[:,:,:3])
    assert np.array_equal(cell[y:y+h,x:x+w,3], np.where(full[:,:,3]>=128,255,0))
    assert np.count_nonzero(cell[:,:,3]) == np.count_nonzero(full[:,:,3]>=128)
    cases = []
    for owner in [0,1]:
        for kind in ['rear_vertical_hit','rear_vertical_tech1','rear_vertical_tech2','rear_vertical_tech3','rear_vertical_tech4','whiff']:
            name = f'owner{owner}-{kind}'
            src = BASE / name / 'search-result.json'; rp = BASE / (name+'-replay') / 'replay-result.json'
            s, r = read(src), read(rp)
            assert s['candidate_contract_sha256'] == r['candidate_contract_sha256'] == sha(contract_path)
            assert s['physical_keys'] and not s['state_injection'] and len(s['rows'])==1
            row = s['rows'][0]
            assert not r['errors'] and r['source_sha256']==sha(src)
            assert r['owner']==row['owner']==owner and r['case']==row['case']==kind
            assert not r['loads_driver'] and not r['calls_sample'] and not r['state_injection']
            tape = Path(r['format6_path']); recording=read(tape)
            assert recording['format']==6 and recording['frames']==row['original_inputs']
            assert recording['content']==row['content_fingerprint'] and recording['final_hash']==row['final_hash']
            success=kind in ['rear_vertical_hit','rear_vertical_tech4']
            assert r['damage']==(490 if success else 0) and r['slams']==int(success)
            assert r['starts']==1 and r['final_victim']['thrower']==-1 and r['final_victim']['state']!='thrown'
            if kind in ['rear_vertical_tech1','rear_vertical_tech2','rear_vertical_tech3']:
                assert r['tech_ticks'][0]-r['capture_ticks'][0]==int(kind[-1])
            assert r['not_main_visual_validation'] and r['not_release_validation']
            assert not r['contract_has_mode_release'] and r['release_transitions']==0
            run_ok(src.parent); run_ok(rp.parent)
            cases.append({'case':kind,'owner':owner,'source':str(src.relative_to(ROOT)),'source_sha256':sha(src),
                'replay':str(rp.relative_to(ROOT)),'replay_sha256':sha(rp),'format6_sha256':sha(tape),
                'original_inputs_sha256':hashlib.sha256(json.dumps(row['original_inputs'],separators=(',',':')).encode()).hexdigest(),
                **{k:r[k] for k in ['ticks','damage','captures','capture_ticks','slams','tech_ticks','whiffs','errors']}})
    feedback=BASE/'feedback-audit/audit-result.json'; f=read(feedback)
    assert not f['errors'] and len(f['rows'])==12 and f['uses_production_combat_feedback']
    assert f['same_gameplay_snapshots_except_display_event_fields'] and not f['claims_identical_content_hash']
    run_ok(feedback.parent)
    receipt={'date':'2026-11-05','reviewer':'root_delegated_by_user','status':'logic_and_original_input_replay_verified_not_art_acceptance',
      'contract':str(contract_path.relative_to(ROOT)),'contract_sha256':sha(contract_path),'bound_resources_verified':len(c['bound_resources']),
      'base_contract':str(old_path.relative_to(ROOT)),'base_sha256':sha(old_path),'changed_raw_ticks':changed,
      'registration':reg,'old_atlas_cells_rgba_unchanged':True,'new_whole_image_rgb_unchanged_alpha_threshold_only':True,
      'capture_damage_cost_and_departure_rules_unchanged':True,'cases':cases,
      'feedback_audit':{'path':str(feedback.relative_to(ROOT)),'sha256':sha(feedback),'control_scope':f['control_scope'],'errors':f['errors']},
      'result':'双向命中、拆投1/2/3/4和落空共12带：独立逐tick输入及format6二次回放通过。第三版仅替换raw27、raw28完整受方相，不改捕获、费用、唯一490伤及32以后离背。真实生产反馈模块12例审计通过。',
      'limits':['自动物理键经输入路由，不是真人键盘。','逻辑通过不代表正常或诊断画面、美术连续性、实速或声音通过。','合同使用mode=root离背，不能冒称mode=release机制已验。','反馈对照是同新姿态加原爆炸锚点，不是旧姿态整链比较；内容指纹/hash不宣称相同。'],
      'installed':False,'art_accepted':False}
    OUT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(OUT)
if __name__=='__main__': main()
