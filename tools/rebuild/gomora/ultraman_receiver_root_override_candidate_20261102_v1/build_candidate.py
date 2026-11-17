"""离线构建：完整源码、受方固定透明外边距、数据/差异/安装计划；不改共享产品。"""
from __future__ import annotations
import copy
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[4]
TOOL=Path(__file__).resolve().parent
REPORT=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-root-override-candidate-v1'
OLD=ROOT/'reports/review/2026-11-02/gomora-super3-resume-front-v1'
CONTACT=ROOT/'reports/review/2026-11-02/gomora-back-lift-ultraman-contact-proposal-v1'
PROPOSED=REPORT/'proposed'
POSE='gomora_back_lift_receiver'
GATE_SHA='c20d72dab1fe4b29bd7994b0b8c745590678754526a9397893ca0dddddf6ed1f'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text('utf-8-sig'))
def rec(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
def text(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(data)
def replace(text_,old,new):
    assert text_.count(old)==1,(old,text_.count(old))
    return text_.replace(old,new,1)
def diff(before,after,rel):
    return ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))


ROOT_HELPER='''extends RefCounted
## 可选受方root offset。缺字段/身份沿原默认；不会把非法覆盖静默换成零点。
const REVISION := 1

static func integer(value: Variant) -> bool:
\t# JSON数值可能是float；只接受有限且数学上为整数的值，bool不属于数值。
\treturn (value is int or value is float) and is_finite(float(value)) and value==int(value)

static func valid(table: Variant) -> bool:
\tif not table is Dictionary:return false
\t# 空表等同没有匹配身份，仍走原root；存在的每个键/点都必须合法。
\tfor identity in table:
\t\tif not identity is String or identity.strip_edges().is_empty() or identity!=identity.strip_edges():return false
\t\tvar point: Variant=table[identity]
\t\tif not point is Array or point.size()!=2:return false
\t\tif not integer(point[0]) or not integer(point[1]):return false
\treturn true

static func offset(victim: UfeFighter, target: Dictionary) -> Array:
\tif not target.has("root_overrides"):return target.get("root",[0,0])
\tvar table: Variant=target.root_overrides
\tif not valid(table):return []
\treturn table.get(victim.definition.id,target.get("root",[0,0]))
'''


def core_candidates():
    source=lambda rel:(OLD/'product'/rel).read_text('utf-8-sig')
    outputs={'core/combat/throw_root_offsets.gd':ROOT_HELPER}
    rel='core/combat/throw_resolver.gd';s=source(rel)
    s=replace(s,'const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")\n',
        'const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")\nconst RootOffsets = preload("res://core/combat/throw_root_offsets.gd")\nconst ROOT_OVERRIDE_RULE_REVISION = RootOffsets.REVISION\n')
    s=replace(s,'static func abort_hold(sim: UfeMatchDirector, owner: int, victim: UfeFighter) -> void:',
        'static func abort_hold(sim: UfeMatchDirector, owner: int, victim: UfeFighter, reason: String="missing_hold_point") -> void:')
    s=replace(s,'"reason":"missing_hold_point"','"reason":reason')
    assert s.count('var offset: Array=target.get("root",[0,0])')==2
    s=s.replace('var offset: Array=target.get("root",[0,0])','var offset: Array=RootOffsets.offset(b,target)')
    s=replace(s,'\tvar available:=a.height+int(target.grip[1])+int(offset[1])',
        '\tif offset.is_empty():return preferred # sync已在选相前拒绝非法覆盖。\n\tvar available:=a.height+int(target.grip[1])+int(offset[1])')
    # 在高度、姿势、floor-safe及任何release写状态前只解析一次。
    s=replace(s,'\t\tif CurrentCapture.preserve(b,target):continue\n',
        '\t\tif CurrentCapture.preserve(b,target):continue\n\t\tvar offset: Array=RootOffsets.offset(b,target)\n\t\tif offset.is_empty():\n\t\t\tabort_hold(sim,owner,b,"invalid_root_override")\n\t\t\tcontinue\n')
    s=replace(s,'\t\tb.facing=a.facing*int(target.get("facing",-1))\n\t\tvar offset: Array=RootOffsets.offset(b,target)\n',
        '\t\tb.facing=a.facing*int(target.get("facing",-1))\n')
    outputs[rel]=s
    rel='core/combat/move_data.gd';s=source(rel)
    s=replace(s,'const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")\n',
        'const CurrentCapture = preload("res://core/combat/throw_current_capture.gd")\nconst RootOffsets = preload("res://core/combat/throw_root_offsets.gd")\n')
    s=replace(s,'\t\tvar target: Dictionary=frame.get("target",{})\n',
        '\t\tvar target: Dictionary=frame.get("target",{})\n\t\tif target.has("root_overrides") and not RootOffsets.valid(target.root_overrides):return false\n')
    outputs[rel]=s
    rel='core/combat/match_director.gd';s=source(rel)
    s=replace(s,'["body_pushbox_2d", BODY_PUSHBOX_2D_REVISION]], "", true).sha256_text()',
        '["body_pushbox_2d", BODY_PUSHBOX_2D_REVISION], ["throw_root_overrides", UfeThrowResolver.ROOT_OVERRIDE_RULE_REVISION]], "", true).sha256_text()')
    outputs[rel]=s
    rel='core/combat/throw_current_capture.gd';s=source(rel)
    s=replace(s,'const HoldPoints = preload("res://core/combat/throw_hold_points.gd")\n',
        'const HoldPoints = preload("res://core/combat/throw_hold_points.gd")\nconst RootOffsets = preload("res://core/combat/throw_root_offsets.gd")\n')
    s=replace(s,'\tvar offset: Array = next.get("root",[0,0])\n',
        '\tvar offset: Array = RootOffsets.offset(b,next)\n\tif offset.is_empty():return false\n')
    outputs[rel]=s
    return outputs


def main():
    assert not PROPOSED.exists()
    gate=CONTACT/'root-provisional-geometry-review-v1.json';assert sha(gate)==GATE_SHA
    approval=read(gate);assert approval['accept_for_offline_materialization_and_main_candidate_preparation']
    assert approval['preserve_actor_scale_anchor_and_existing_default_grips']
    previous=read(CONTACT/'closeout-owned-paths.json')
    assert all(sha(ROOT/q['path'])==q['sha256'] for q in previous['paths'])
    plan=read(OLD/'install-plan.json');old_entries={q['path']:q for q in plan['entries']}
    before={}
    for rel,q in old_entries.items():
        src=ROOT/q['candidate']['path'];assert sha(src)==q['after_sha256']
        current=ROOT/rel;actual=sha(current) if current.exists() else None
        assert actual==q['before_sha256'],f'共享基线已变：{rel}'
        before[rel]=actual
    for rel in ['assets/fighters/ultraman/animations/manifest.json','content/fighters/ultraman/state_frames.json']:
        before[rel]=sha(ROOT/rel)
    before['assets/fighters/ultraman/animations/gomora-back-lift-receiver/atlas.png']=None
    before['core/combat/throw_root_offsets.gd']=None
    assert not (ROOT/'core/combat/throw_root_offsets.gd').exists()
    assert not (ROOT/'assets/fighters/ultraman/animations/gomora-back-lift-receiver/atlas.png').exists()
    PROPOSED.mkdir(parents=True)
    save(REPORT/'shared-product-baseline.json',{'root_approval':rec(gate),'paths':before,'godot_or_product_writes':0})
    outputs=core_candidates()
    entries=[];core_diffs=[]
    for rel,content in outputs.items():
        out=PROPOSED/rel;text(out,content)
        old=OLD/'product'/rel
        baseline=old.read_text('utf-8-sig') if old.exists() else ''
        patch=REPORT/'diffs/root-extension'/Path(rel.replace('/','__')).with_suffix('.diff')
        text(patch,diff(baseline,content,rel))
        core_diffs.append({'path':rel,'existing_back_lift_baseline':rec(old) if old.exists() else None,'proposed':rec(out),'extension_diff':rec(patch)})
    proposal=read(CONTACT/'proposal-v1/precise-contact-and-canvas-proposal.json')
    assert proposal['fixed_outer_canvas']==[192,192] and proposal['fixed_paste_origin']==[6,6] and proposal['fixed_anchor']==[96,184]
    native=REPORT/'materialized192/native';native.mkdir(parents=True)
    images=[];material=[];atlas=Image.new('RGBA',(192*6,192),(0,0,0,0))
    for q in proposal['pairs']:
        src=ROOT/q['receiver']['path'];assert sha(src)==q['receiver']['sha256']
        with Image.open(src) as opened:opened.load();im=opened.copy()
        assert im.mode=='RGBA' and im.size==(179,179)
        canvas=Image.new('RGBA',(192,192),(0,0,0,0));canvas.paste(im,(6,6))
        a=np.asarray(canvas);original=np.asarray(im)
        assert np.array_equal(a[6:185,6:185],original)
        outside=a.copy();outside[6:185,6:185]=0;assert not outside.any()
        assert set(np.unique(a[...,3]))=={0,255}
        path=native/f"{q['phase']:02d}.png";canvas.save(path)
        with Image.open(path) as check:assert np.array_equal(np.asarray(check),a)
        images.append(canvas);atlas.paste(canvas,(192*q['phase'],0))
        material.append({'phase':q['phase'],'source179':rec(src),'candidate192':rec(path),'fixed_paste_origin':[6,6],
            'dimensions':[192,192],'anchor':[96,184],'whole_inner_rgba_byte_array_identical':True,
            'outside_padding_all_zero_rgba':True,'scale_or_resample_operations':0,'crop_or_component_filter':False,
            'source_scale_stays_179_over_1024':True,'root_registration_provisional_not_runtime_accepted':True})
    texture_rel='assets/fighters/ultraman/animations/gomora-back-lift-receiver/atlas.png'
    atlas_path=PROPOSED/texture_rel;atlas_path.parent.mkdir(parents=True);atlas.save(atlas_path)
    # 几何数据复用既有免费离线Alpha分带方法；图片本身不重采样或改色。
    script=ROOT/'tools/rebuild/gomora/super3_back_lift_contract_20261102_v1/prepare_main_candidate.py'
    spec=importlib.util.spec_from_file_location('frozen_back_lift_geometry',script);geom=importlib.util.module_from_spec(spec);spec.loader.exec_module(geom)
    state_frames=[]
    for i,im in enumerate(images):state_frames.append({'sprite':i,'dx':0,'dy':0,'hitboxes':[],'hurtboxes':geom.boxes(im,[96,184]),'cancel':[],'events':[]})
    order=[0,1,4,5,2,3];pose_frames=[copy.deepcopy(state_frames[i]) for i in order]
    pose_frames[1]['throw_hold_variants']=[1,4,5]
    state=read(ROOT/'content/fighters/ultraman/state_frames.json');assert POSE not in state
    state[POSE]=pose_frames;save(PROPOSED/'content/fighters/ultraman/state_frames.json',state)
    manifest=read(ROOT/'assets/fighters/ultraman/animations/manifest.json');assert POSE not in manifest['clips']
    manifest['clips'][POSE]={'texture':'res://'+texture_rel,'cell':192,'anchor_y':184,
        'rects':[[192*i,0,192,192] for i in range(6)],'ticks':[4]*6,'anchors':[[96,184]]*6,'loop':False,
        'atlas_sha256':sha(atlas_path),'source_scale':'179/1024 complete image; fixed transparent padding [6,6]',
        'review':{'reviewer':'root_delegated_by_user','offline_materialization_authorized_by':str(gate.relative_to(ROOT)).replace('\\','/'),
                  'runtime_contact_accepted':False,'full_pose_continuation_accepted':False,'strict_size_accepted':False}}
    save(PROPOSED/'assets/fighters/ultraman/animations/manifest.json',manifest)
    move_rel='content/fighters/gomora/moves/special3.json';old_move=read(OLD/'product'/move_rel);move=copy.deepcopy(old_move)
    assert move['throw_current_capture']['target_ids']==['zetton']
    move['throw_current_capture']['target_ids'].append('ultraman')
    points={str(q['phase']):q['proposed_receiver_hold_point'] for q in proposal['pairs'][:4]}
    computed=[]
    for q in proposal['pairs']:
        start,end=q['raw_ticks'];expected_mode='hold' if q['phase']<4 else 'root'
        for raw in range(start,end+1):
            target=move['frames'][raw]['target'];old_target=old_move['frames'][raw]['target']
            assert target['mode']==expected_mode and target['facing']==1 and target['pose']==POSE
            if expected_mode=='hold':
                measured=q['proposed_actor_grip'];G=old_target['grip']
                offset=[measured[i]-G[i] for i in range(2)]
                target['hold_point_overrides']['ultraman']={POSE:copy.deepcopy(points)}
            else:offset=q['proposed_receiver_root_relative_actor']
            target['root_overrides']={'ultraman':offset}
            assert target.get('grip')==old_target.get('grip') and target['root']==old_target['root']
            if raw==start:computed.append({'phase':q['phase'],'raw_ticks':[start,end],'mode':expected_mode,
                'unchanged_existing_grip_G':old_target.get('grip'),'independent_actor_C_local':q['proposed_actor_grip'],
                'actual_receiver_A_or_E_local':q['proposed_receiver_hold_point'],'new_root_offset':offset,
                'resulting_receiver_root_relative_actor':q['proposed_receiver_root_relative_actor']})
    assert all(move['frames'][i]==old_move['frames'][i] for i in list(range(20))+list(range(44,72)))
    stripped=copy.deepcopy(move);stripped['throw_current_capture']['target_ids'].remove('ultraman')
    for f in stripped['frames']:
        t=f.get('target',{});t.pop('root_overrides',None)
        if 'hold_point_overrides' in t:t['hold_point_overrides'].pop('ultraman',None)
    assert stripped==old_move
    save(PROPOSED/move_rel,move)
    save(REPORT/'materialized192/receipt.json',{'art_source':'existing','generation_route_invoked':False,'root_gate':rec(gate),
        'whole_frames':material,'atlas':rec(atlas_path),'free_geometry_authoring_tool':rec(script),
        'runtime_png_root_path':texture_rel,'state_index_to_actual_sprite':order,'index1_hold_variants':[1,4,5],
        'state_hurtboxes_from_complete_fixed_canvas_alpha_bands':True,'post_requests':0,'product_writes':0,'godot_runs':0,'git_writes':0})
    save(REPORT/'ultraman-data-contract.json',{'pose':POSE,'phase_geometry':computed,
        'state_index_to_actual_sprite':order,'state1_hold_variants':[1,4,5],
        'hold_variants_expected_consumption':{'20-23':0,'24-27':1,'28-31':2,'32-35':3,'36-39':4,'40-43':5},
        'all_existing_shared_grips_default_roots_and_zetton_overrides_unchanged':True,
        'frame0_to19_and44_to71_complete_dictionaries_unchanged':True,
        'raw44_actual_target':old_move['frames'][44]['target'],'static_ideal_root_minus33_99_not_applied':True,
        'ordinary_runtime_product_not_modified':True,'runtime_acceptance_pending':True})
    # 原已审候选的未变更文件只引用其正式冻结归属，不复制为本任务新文件。
    proposed_files={q.relative_to(PROPOSED).as_posix():q for q in PROPOSED.rglob('*') if q.is_file()}
    for rel in sorted(set(old_entries)|set(proposed_files)):
        candidate=proposed_files.get(rel) or ROOT/old_entries[rel]['candidate']['path']
        current=ROOT/rel;current_sha=sha(current) if current.exists() else None
        entry={'path':rel,'before_sha256':current_sha,'after_sha256':sha(candidate),'candidate':rec(candidate),
            'new_file':not current.exists(),'new_task_owned_candidate':rel in proposed_files}
        if rel in old_entries:entry['previous_back_lift_candidate']=old_entries[rel]['candidate']
        entries.append(entry)
        if candidate.suffix.lower() in ['.gd','.json','.md']:
            base_text=current.read_text('utf-8-sig') if current.exists() else ''
            out=REPORT/'diffs/current-product'/Path(rel.replace('/','__')).with_suffix('.diff')
            text(out,diff(base_text,candidate.read_text('utf-8-sig'),rel))
    save(REPORT/'core-root-extension-review.json',{'complete_core_sources_and_exact_extension_diffs':core_diffs,
        'central_resolution_consumers':['throw_resolver.sync','throw_resolver.floor_safe_hold_sprite','throw_resolver release branch via sync offset','throw_current_capture.eligible'],
        'schema':'Optional Dictionary; string identity keys nonblank/no outer whitespace; 2 finite mathematical integers; JSON integral floats accepted; empty map falls back.',
        'legacy_default_path':'No field or missing identity returns existing target.root or [0,0]. Invalid present map rejected by MoveData; midhold invalid map aborts with invalid_root_override.',
        'explicit_semantic_fingerprint':['throw_root_overrides',1],'existing_actor_and_zetton_data_grips_unchanged':True,
        'old_prerequisites_referenced_not_recopied':True,'gdscript_compiled':False,'godot_executed':False})
    save(REPORT/'candidate-install-plan.NOT-EXECUTED.json',{'schema':1,'status':'offline_only_root_code_data_review_and_serial_godot_window_required',
        'root_offline_gate':rec(gate),'entries':entries,'source_old_prerequisite_plan':rec(OLD/'install-plan.json'),
        'no_install_function_in_this_tool':True,'must_restore_original_bytes_stats_sidecars_and_user_data_after_later_temporary_main':True,
        'runtime_acceptance_pending':True,'post_requests':0,'budget_writes':0,'shared_product_writes':0,'godot_runs':0,'git_writes':0})
    after={rel:(sha(ROOT/rel) if (ROOT/rel).exists() else None) for rel in before};assert before==after
    save(REPORT/'readonly-byte-verification-build.json',{'before':before,'after':after,'unchanged':True,
        'all_frozen_contact_owned_rows_unchanged':True,'old_prerequisite_candidate_sha_verified':True,
        'post_requests':0,'budget_writes':0,'shared_product_writes':0,'godot_runs':0,'git_writes':0})
    print(json.dumps({'report':str(REPORT),'plan':rec(REPORT/'candidate-install-plan.NOT-EXECUTED.json'),
        'hold_root_offsets':[q['new_root_offset'] for q in computed[:4]],'release44_71_unchanged':True,'godot_runs':0,'shared_product_writes':0},ensure_ascii=False))

if __name__=='__main__':main()
