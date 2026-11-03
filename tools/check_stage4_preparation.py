"""免费准备的资源、锁定和覆盖账本完整性检查，不评价剪影美感。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
def read(p):return json.loads(p.read_text('utf-8-sig'))

def check_completed_seven(record,cells,clips,coverage):
    """stage4-seven-complete已验收；逐格核对当前资源审批，不能只凭完成标记放行。"""
    assert record['playable_matrix'] is True,'赛文已验收，整体完成标记不得退回未完成'
    assert set(record['matrix'])==cells,'赛文生产矩阵缺格或多格'
    reviewed_rows={}
    for line in coverage.splitlines():
        if not line.strip().startswith('| ultraseven |'):continue
        row=[part.strip() for part in line.strip().split('|')[1:-1]]
        assert len(row)==10,'赛文覆盖表列数不符'
        assert row[1] not in reviewed_rows,f'赛文覆盖表重复：{row[1]}'
        reviewed_rows[row[1]]=row
    expected_rows={}
    for key,value in record['matrix'].items():
        assert all(value.get(field) is True for field in ['boxes','sound','integrated','reviewed','complete','frames_reviewed','timing_reviewed']),f'赛文格子未完成：{key}'
        assert value['move_data']['present'] is True,f'赛文缺少数据：{key}'
        animation=value['animation'];name=animation['clip']
        assert name in clips,f'赛文缺少动画：{key} / {name}'
        clip=clips[name]
        assert clip.get('motion_review',{}).get('user_approved') is True,f'赛文动画未审：{name}'
        assert clip.get('rhythm_review',{}).get('user_approved',True),f'赛文节奏未审：{name}'
        assert not clip.get('limb_color_revision',{}).get('sequence_review_pending'),f'赛文播放序颜色待审：{name}'
        assert clip['rects'] and len(clip['rects'])==len(clip['ticks']) and all(t>0 for t in clip['ticks']),f'赛文图帧或时长不合法：{name}'
        assert animation['frames']==len(clip['rects']) and animation['ticks']==clip['ticks'],f'赛文生产表与动画帧不符：{key}'
        assert animation.get('runtime_ticks',sum(clip['ticks']))==clip.get('runtime_ticks',sum(clip['ticks'])),f'赛文运行时长不符：{key}'
        label=f'{value["section"]} / {value["input"]}'
        assert label not in expected_rows,f'赛文生产矩阵输入重复：{label}'
        expected_rows[label]=['ultraseven',label,value.get('planned_name',value.get('move') or key),'是',str(len(clip['rects'])),'是','是','是','是','是']
    assert reviewed_rows.keys()==expected_rows.keys(),'赛文覆盖表缺格或多格'
    for label,expected in expected_rows.items():
        assert reviewed_rows[label]==expected,f'赛文覆盖表与实际完成状态不符：{label}'

def check_matrix_completion(fighter,record):
    if fighter!='ultraseven':
        assert not record['playable_matrix']
        return
    cells={row['id'] for row in read(ROOT/'content/roster/matrix.json')['cells']}
    clips=read(ROOT/'assets/fighters/ultraseven/animations/manifest.json')['clips']
    coverage=(ROOT/'reports/review/2026-10-22/matrix/2026-10-22-matrix.md').read_text(encoding='utf-8')
    check_completed_seven(record,cells,clips,coverage)

def main():
    prod=read(ROOT/'content/roster/production.json');prep=prod['stage4_preparation']
    ids=prep['fighters'];assert len(ids)==len(set(ids))==10
    assert prep['image_requests']==0 and prep['image_cost_authorized'] is False
    cells={r['id'] for r in read(ROOT/'content/roster/matrix.json')['cells']}
    selection={r['id']:r for r in read(ROOT/'content/roster/selection.json')['entries']}
    for fighter in ids:
        folder=ROOT/'content/fighters'/fighter;definition=read(folder/'definition.json');palette=read(folder/'palette.json')
        # 2026-10-23用户决定首批10位全部开工：任何角色都可离开prepared进入量产，不再只限赛文、哥莫拉两位试制。
        pilot=definition['production_status'] in ['model_pending_review','model_approved','pilot_partial']
        active=definition['production_status']=='pilot_partial'
        assert definition['production_status'] in ['prepared','model_pending_review','model_approved','pilot_partial']
        if definition['playable']:assert active and definition.get('pilot_manual_ready') and definition.get('walks_installed') and definition.get('selection_authorization')
        if active:
            if fighter in ['ultraseven','gomora']:assert definition.get('pilot_playable')
            if fighter=='gomora':assert (definition['playable'] and definition.get('selection_authorization') and definition.get('pilot_manual_ready')) or (not definition['playable'] and not definition.get('pilot_manual_ready')), '自由选人须明确授权与安装就绪；否则保留试制锁'
        else:assert definition['presentation']['model'] is None and definition['presentation']['manifest'] is None
        assert selection[fighter]['era']=='showa'
        assert palette['max_colors']==32
        if pilot:
            assert 0<len(palette['colors'])<=32 and palette['status'] in ['candidate_pending_review','model_candidate_pending_review','model_approved']
            assert palette['side_view_roles']['mapping']
        else:
            assert palette['colors']==[] and palette['side_view_roles']['status'].startswith('待定稿')
        plan=read(folder/'production_plan.json');assert {p['cell'] for p in plan['cells']}==cells and len(plan['cells'])==len(cells)
        # 准备快照的零完成约束只约束尚未开始试制的角色；量产中的格子可逐步完成。
        assert all(p['source_refs'] for p in plan['cells'])
        if not active:assert all(not p['completed'] for p in plan['cells'])
        record=prod['fighters'][fighter];assert set(record['matrix'])==cells
        check_matrix_completion(fighter,record)
        for value in record['matrix'].values():
            if active:
                if value['reviewed']:
                    clips=read(ROOT/f'assets/fighters/{fighter}/animations/manifest.json')['clips']
                    assert value['integrated'] and clips[value['animation']['clip']]['motion_review']['user_approved']
            else:
                assert all(value[k] is False for k in ['boxes','sound','integrated','reviewed','complete'])
                assert value['move_data']['present'] is False and value['animation']['frames']==0
        for form in definition['forms']:assert (folder/'forms'/f'{form}.json').is_file()
        refs=read(folder/'references.json');anchor=_LayoutJson.path_text(f'art/model_sheets/{fighter}/model-native.png')
        if fighter in ['ultraseven','gomora']:assert refs['approved_pixel_anchor']==(anchor if definition['production_status'] in ['model_approved','pilot_partial'] and not definition.get('model_review_pending') else None)
        elif pilot:assert refs['approved_pixel_anchor'] in [None,anchor] and (ROOT/anchor).is_file(),'量产角色须有定稿原生图；锚点只能为空或指向定稿'
        else:assert refs['approved_pixel_anchor'] is None
        assert (folder/'MOVES.md').is_file() and refs['identity_sources']
    for fighter in ['ultraman','zetton']:
        # gate-b历史已经通过；尺寸校准改变图片/框后应重新待审，不能要求新版本自动继承已审。
        assert all(r['integrated'] and r['boxes'] and r['sound'] for r in prod['fighters'][fighter]['matrix'].values() if r.get('applicable',True))
        assert next(r for r in prod['fighters'][fighter]['matrix'].values() if r['move']=='motion_41236')['animation']['frames']>=8
    root=ROOT/'content/templates/biped_tail';template=read(root/'template.json')
    assert template['extends']=='humanoid' and template['jump_speed']<14
    assert template['landing_feedback']['layer']=='presentation'
    for move in read(root/'move_manifest.json'):
        data=read(root/'moves'/f'{move}.json');assert len(data['frames'])==sum(data[k] for k in ['startup','active','recovery'])
        poses=read(ROOT/f'art/shared/poses/library/biped_tail/{move}.json')['frames']
        for i,frame in enumerate(data['frames']):
            assert 0<=frame['sprite']<len(poses)
            if data['startup']<=i<data['startup']+data['active']:assert frame['hitboxes'] and all(b is not None for b in frame['hitboxes'])
            else:assert frame['hitboxes']==[]
        for pose in poses:
            im=Image.open(ROOT/f'art/shared/poses/library/biped_tail/{move}-{pose["frame"]:02}.png')
            assert im.size==(256,256) and im.mode=='RGBA' and im.getbbox()[3]==249
            for k in ['tail_root','tail_mid','tail_tip','near_foot','far_foot']:assert len(pose[k])==2
    jump=read(ROOT/'art/shared/poses/library/biped_tail/low-jump.json');assert jump['peak_height']==55
    height=0;vy=10
    for row in jump['trajectory']:
        height=max(0,height+vy);vy=vy-1 if height>0 else 0
        # 触地当tick速度由主模拟归零，准备参考也须一致。
        assert row['height']==height and row['vy']==vy
    for sample in jump['reference_samples']:assert (ROOT/sample['texture']).is_file()
    history=read(ROOT/'art/shared/production/stage4-preparation/historical-requests.json')
    for fighter,data in history['fighters'].items():
        takes=[r['take'] for r in data['evidence']];assert len(takes)==len(set(takes))==data['requests']
        assert not any(t.endswith('/rejected') for t in takes)
    estimate=read(ROOT/'art/shared/production/stage4-preparation/request-estimate.json')
    assert estimate['new_requests_this_round']==0 and estimate['approved_requests']==0
    assert estimate['base_total']==[sum(r['low'] for r in estimate['fighters']),sum(r['high'] for r in estimate['fighters'])]
    assert estimate['total_with_conditional_form']==[a+b for a,b in zip(estimate['base_total'],estimate['conditional_super_taro'])]
    for source in read(ROOT/'art/shared/references/stage4-preparation/sources.json')['sources'].values():
        if source.get('raw'):
            assert hashlib.sha256((ROOT/source['raw']).read_bytes()).hexdigest()==source['sha256']
    print('STAGE4_PREPARATION PASS：锁定、空格、来源、请求审计与模板数据一致；不替代审片。')
if __name__=='__main__':main()
