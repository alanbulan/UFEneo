"""冻结本任务唯一新增目录并复核上游旧冻结字节；不执行产品/版本库修改。"""
from pathlib import Path
import json
import propose as p

TOOL=Path(__file__).resolve().parent
REPORT=p.REPORT


def main():
    assert not (REPORT/'closeout-owned-paths.json').exists()
    old_guards=[]
    old=[('gomora-back-lift-ultraman-scale-proposal-v1','b14b2ed3c8fda2e95698af80d29692d8bf7c2dcebfeb3cb35bde5315bb6f9c3a'),
         ('gomora-back-lift-ultraman-179-unregistered-v1','1997675610c1887c95bf5154dc1183faaa3c8b689b90fa5a6dad726f18673e18')]
    for dirname,expected in old:
        manifest=REPORT.parent/dirname/'closeout-owned-paths.json';assert p.sha(manifest)==expected
        rows=p.read(manifest)['paths']
        assert all(p.sha(p.ROOT/r['path'])==r['sha256'] for r in rows)
        old_guards.append({'manifest':p.rec(manifest),'frozen_rows_verified_unchanged':rows,'reference_only_not_owned':True})
    receipt=p.read(p.PREVIOUS/'candidate-01/processing-receipt.json')
    source_guards=[]
    for row in receipt['outputs']:
        for key in ['source','source_provider','source_metadata','root_source_review','candidate']:
            guard=row[key];assert p.sha(p.ROOT/guard['path'])==guard['sha256']
            source_guards.append({'phase':row['phase'],'kind':key,**guard})
    p.save(REPORT/'upstream-frozen-verification.json',{'old_frozen_directory_manifests':old_guards,
        'original_png_provider_metadata_root_reviews_and_179_candidates':source_guards,'all_expected_sha256_match':True,
        'old_directories_and_tools_not_owned_or_written':True,'root_commit_reference':'490f74e76f'})
    base=p.read(REPORT/'proposal-v1/precise-contact-and-canvas-proposal.json')
    index=p.read(REPORT/'continuation-and-dependency-v1/complete-pages-index.json')
    opened=base['point_pages']+[r['clean_pair_page'] for r in base['pairs']]+index['complete_2x_pair_pages']
    opened+=[r for r in index['complete_continuation_pages'] if '-marked.' not in r['path']]
    assert all(p.sha(p.ROOT/r['path'])==r['sha256'] for r in opened)
    p.save(REPORT/'actual-visual-review.json',{
        'reviewer':'gomora_super3_resume','role':'subagent_readonly_proposal_not_root_acceptance',
        'actually_opened_complete_final_pages':opened,
        'preparation_complete_views_also_opened':True,'native179_and_caster_complete_canvas_content_not_modified':True,
        'findings':[
            '最终独立C/A/E均在既定表面误差门内；03–05 H0推定/肩髋差及严格骨尺false继承，未改体尺。',
            '腹腰/卸重面按点对到本人背缘；05已翻胸腹向上，接触E为背侧卸重面，不能误称腹侧。',
            '头与角根/颈侧及双手与肩胸在平面配对上邻接或重叠；须根看实际层序/双向，不能以Alpha交集或点重合签自然接触。',
            '05到本人倒立0的R几何连续；头和双臂/腿向有明显转换，R零差不等于整人连续通过。',
            '完整场景/坐标页未裁人物；该离线页不是main画面，不替代实际相序、双向、空中和回放。'],
        'natural_contact_accepted':False,'full_pose_continuation_accepted':False,'runtime_registration_accepted':False,
        'strict_size_accepted':False,'root_grip_override_accepted':False,
        'marked_pair_pages_generated_for_root_not_claimed_opened_here':True,
        'failed_first_measurement_retained':p.rec(REPORT/'measurement-diagnostic-v1/surface-gate-failure.json')})
    critical=[REPORT/'manual-native-contact-points-v2.json',REPORT/'proposal-v1/precise-contact-and-canvas-proposal.json',
        REPORT/'continuation-and-dependency-v1/minimal-generic-root-override-dependency.json',
        REPORT/'continuation-and-dependency-v1/non-target-raw43-to44-timing.json',REPORT/'actual-visual-review.json']
    p.save(REPORT/'delivery-freeze-v1.json',{'status':'readonly_proposal_ready_for_root_actual_review',
        'critical_documents':[p.rec(q) for q in critical],'tools':[p.rec(q) for q in sorted(TOOL.glob('*.py'))],
        'exclusive_new_scope':[REPORT.relative_to(p.ROOT).as_posix(),TOOL.relative_to(p.ROOT).as_posix()],
        'previous_frozen_tasks_reference_only':old_guards,
        'supersedes_only_early_outer_canvas':{'old_cell':[256,256],'old_anchor':[128,248],'new_cell':[192,192],'new_anchor':[96,184],'fixed_paste_origin':[6,6]},
        'candidate179_whole_scale_unchanged':True,'strict_size_accepted':False,'root_actual_contact_review_pending':True,
        'png_writes':0,'post_requests':0,'budget_writes':0,'product_writes':0,'godot_runs':0,'git_writes':0,'videos':0})
    manifest=REPORT/'closeout-owned-paths.json';textlist=REPORT/'incremental-precise-file-list.txt'
    files=[q for folder in [REPORT,TOOL] for q in folder.rglob('*') if q.is_file()]
    assert all(q.suffix.lower()!='.png' for q in files)
    names=sorted({q.relative_to(p.ROOT).as_posix() for q in files+[manifest,textlist]})
    with textlist.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(names)+'\n')
    files=[q for folder in [REPORT,TOOL] for q in folder.rglob('*') if q.is_file()]
    p.save(manifest,{'paths':[p.rec(q) for q in sorted(files)],'manifest_itself_in_precise_file_list':True,
        'only_new_task_directories_owned':True,'previous_frozen_tasks_and_sources_not_owned':True,
        'registrations':0,'png_writes':0,'post_requests':0,'budget_writes':0,'product_writes':0,'godot_runs':0,'git_writes':0})
    print(json.dumps({'manifest':p.rec(manifest),'freeze':p.rec(REPORT/'delivery-freeze-v1.json'),
        'precise_incremental_paths':p.rec(textlist),'runtime_accepted':False},ensure_ascii=False))

if __name__=='__main__':main()
