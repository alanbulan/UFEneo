"""试生产账本预算、原始请求快照、像素资源与未解锁状态检查。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import Path
Path = _LayoutProjectPath
from collections import Counter
import hashlib
import json; json = _LayoutJson
import sys
from PIL import Image
from check_stage4_preparation import check_matrix_completion
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
def read(path):return json.loads(path.read_text('utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve(path,ledger):
    local=ROOT/path
    if local.exists():return local
    for m in ledger.get('archive_mappings',[]):
        relative=Path(path)
        try:tail=relative.relative_to(m['prefix'])
        except ValueError:continue
        if tail.parts[0] not in m.get('exclude',[]):
            candidate=Path(m['destination'])/tail
            if candidate.exists():return candidate
    return local
def main(ledger_path=None):
    ledger=read(ledger_path or ROOT/'art/shared/production/stage4-pilot/ledger.json');rows=ledger['requests']
    if ledger.get('fork'):
        prefix=ledger['fork']['prefix_count'];base=read(ROOT/ledger['fork']['source'])
        assert rows[:prefix]==base['requests'][:prefix],'分会话台账不得改写历史请求'
    limits=ledger['limits'];assert limits=={'per_asset':6}
    assert [r['ledger_sequence'] for r in rows]==list(range(1,len(rows)+1))
    counts=Counter(r['fighter'] for r in rows)
    assert set(counts)<=set(['ultraseven','gomora','ultraman','zetton'])
    for fighter in ['ultraman','zetton']:
        own=[r for r in rows if r['fighter']==fighter]
        for (action,series),count in Counter((r['action'],r.get('attempt_series','original')) for r in own).items():
            assert count<=ledger.get('method_authorizations',{}).get(series,{}).get('per_asset',6)
        for row in own:
            auth=ledger.get('method_authorizations',{}).get(row.get('attempt_series'),{})
            assert fighter in auth.get('fighters',[]) and row['action'] in auth.get('assets',[])
            assert row['quality']=='high' and row['batch']=='seven-gpt-redraw'
            registry=read(ROOT/row['asset_registry'])
            assert row['action'] in registry['assets_by_fighter'][fighter]
            brief=resolve(row['brief'],ledger);assert sha(brief)==row['brief_sha256']
            request=read(brief)
            assert request['fighter']==fighter and request['asset_key']==row['action'] and request['quality']=='high'
            assert len(request['references'])==row['input_image_count'] and request['attempt_series']==row['attempt_series']
            for frozen in row['inputs']:assert sha(resolve(frozen['path'],ledger))==frozen['sha256']
            if row.get('edit_mask'):assert sha(resolve(row['edit_mask']['path'],ledger))==row['edit_mask']['sha256']
            assert row['submitted_at'] and row['finished_at'] and row['result']
            path=Path(row['output'])
            if row['result']=='alpha_rejected':path=path.parent/'rejected'/path.name
            path=resolve(path,ledger)
            if not path.exists():
                assert row['result']=='failed_or_remote_unknown';continue
            metadata=read(path.with_suffix('.metadata.json'))
            assert metadata['requested_quality']=='high' and metadata['background_requested']=='transparent'
            assert row['output_size']==metadata['dimensions'] and sha(path)==metadata['image_sha256']
    for fighter,cell,height,take in [('ultraseven',(192,192),143,5),('gomora',(384,256),192,1)]:
        own=[r for r in rows if r['fighter']==fighter]
        per_asset=Counter(r['action'] for r in own)
        assert 'model' in per_asset
        per_revision=Counter((r['action'],r.get('identity_revision','original'),r.get('attempt_series','original')) for r in own)
        for (action,revision,series),count in per_revision.items():
            assert count<=ledger.get('method_authorizations',{}).get(series,{}).get('per_asset',6)
            if series!='original':
                authorization=ledger.get('method_authorizations',{}).get(series,{})
                assert action in authorization.get('assets',[]) and authorization.get('per_asset') in [6,10],'未授权的新方法不得重计次数'
        for key in per_asset:assert [r['sequence'] for r in own if r['action']==key]==list(range(1,per_asset[key]+1))
        batch=[r for r in own if r['action']!='model']
        if batch:
            for r in batch:
                registry=read(ROOT/r.get('asset_registry','art/fighters/ultraseven/stage4/pilot/ultraseven-first/asset-registry.json'))
                assert fighter in registry.get('fighters',['ultraseven']) and r['action'] in registry['assets']
                assert r['batch']==registry.get('batch','ultraseven-first')
        for row in own:
            assert row['quality']=='high'
            if row['action']=='model':assert row['input_image_count']>=1 and row['size']=='1024x1024'
            assert row['submitted_at'] and row['finished_at'] and row['result']
            brief=resolve(row['brief'],ledger);assert sha(brief)==row['brief_sha256']
            request=read(brief);assert request['quality']=='high' and len(request['references'])==row['input_image_count']
            assert request.get('attempt_series','original')==row.get('attempt_series','original')
            if row.get('edit_mask'):assert sha(resolve(row['edit_mask']['path'],ledger))==row['edit_mask']['sha256']
            if row.get('identity_revision')=='model05':
                anchors=['art/fighters/ultraseven/model/model-reference-x4.png','art/fighters/ultraseven/model/head-reference-x8.png']
                for anchor in anchors:
                    assert anchor in request['references'],'每次请求必须附定稿5全身和头部8倍'
                    index=request['references'].index(anchor)
                    assert row['inputs'][index]['sha256']==sha(ROOT/anchor),'实际冻结附件不是定稿5'
                assert row['revision_sequence'] in range(1,ledger.get('method_authorizations',{}).get(row.get('attempt_series'),{}).get('per_asset',6)+1)
                for frozen in row['inputs']:assert sha(resolve(frozen['path'],ledger))==frozen['sha256']
            path=Path(row['output'])
            if row['result']=='alpha_rejected':path=path.parent/'rejected'/path.name
            path=resolve(path,ledger)
            if not path.exists():
                assert row['result']=='failed_or_remote_unknown';continue
            meta=read(path.with_suffix('.metadata.json'))
            assert meta['requested_quality']=='high' and meta['background_requested']=='transparent'
            assert row['output_size']==meta['dimensions'] and sha(path)==meta['image_sha256']
        folder=ROOT/'art/model_sheets'/fighter
        model=folder/'model-native.png';im=Image.open(model).convert('RGBA');qa=read(folder/'qa.json')
        pending=fighter=='ultraseven' and qa['status']=='pending_user_review'
        assert im.size==cell and (qa['candidate_take']==max(r['sequence'] for r in own if r['action']=='model') if pending else qa['candidate_take']==take)
        assert (not qa['user_approved'] and qa['body_unchanged']) if pending else (qa['height']==height and qa['status']=='user_approved' and qa['user_approved'])
        assert im.getbbox()[3]-im.getbbox()[1]==qa['height'] and im.getbbox()[3]==cell[1]-8
        if pending:
            import numpy as np
            reference=ROOT/qa.get('protected_reference','art/fighters/ultraseven/stage4/revisions/ultraseven-head-edit/before.png')
            if qa.get('protected_reference_sha256'):assert sha(reference)==qa['protected_reference_sha256']
            previous=np.array(Image.open(reference).convert('RGBA'));current=np.array(im)
            x,y,r,b=qa['edit_region'];protected=np.ones(current.shape[:2],bool);protected[y:b,x:r]=False
            assert np.array_equal(previous[protected],current[protected]),'授权头部外的身体像素改变'
        assert qa['foot_anchor']==[cell[0]//2,cell[1]-8] and qa['native_sha256']==sha(model)
        assert set(im.getchannel('A').getdata())=={0,255}
        assert len(set(p[:3] for p in im.getdata() if p[3]))<=32
        assert Image.open(folder/'model-reference-x4.png').size==tuple(n*4 for n in cell)
        palette=read(ROOT/f'content/fighters/{fighter}/palette.json')
        colors={tuple(c) for c in palette['colors']}
        for pair in palette['side_view_roles']['mapping']:
            assert tuple(pair['near']) in colors and tuple(pair['far']) in colors
            assert sum(pair['far'])<sum(pair['near'])
        definition=read(ROOT/f'content/fighters/{fighter}/definition.json')
        if definition['playable']:
            assert definition.get('pilot_manual_ready') and definition.get('walks_installed') and definition.get('selection_authorization')
            if fighter=='ultraseven':
                from walk_cycle_qa import validate_folder
                clips=read(ROOT/'assets/fighters/ultraseven/animations/manifest.json')['clips']
                for action in ['walk_forward','walk_back']:validate_folder((ROOT/clips[action]['head_qa']).parent,fighter,action)
        if definition.get('pilot_playable'):
            if fighter=='gomora':
                assert definition['production_status']=='pilot_partial'
                assert (definition['playable'] and definition.get('selection_authorization') and definition.get('pilot_manual_ready')) or (not definition['playable'] and not definition.get('pilot_manual_ready')), '自由选人须明确授权与安装就绪；否则保留试制锁'
                assert definition['presentation']['cell']==[512,320] and definition['presentation']['anchor']==[256,304]
            else:assert fighter=='ultraseven' and definition['production_status']=='pilot_partial'
            assert all((ROOT/definition['presentation'][key].removeprefix('res://')).is_file() for key in ['model','manifest'])
        else:assert definition['presentation']['model'] is None and definition['presentation']['manifest'] is None
        refs=read(ROOT/f'content/fighters/{fighter}/references.json')
        assert refs['approved_pixel_anchor']==(None if pending else model.relative_to(ROOT).as_posix()) and refs['model_candidate']==model.relative_to(ROOT).as_posix()
    prod=read(ROOT/'content/roster/production.json')
    for fighter in ['ultraseven','gomora']:
        record=prod['fighters'][fighter]
        expected='pending_user_review' if read(ROOT/_LayoutJson.path_text(f'art/model_sheets/{fighter}/qa.json'))['status']=='pending_user_review' else 'user_approved'
        assert record['model']==expected
        check_matrix_completion(fighter,record)
        manifest=ROOT/f'assets/fighters/{fighter}/animations/manifest.json'
        if manifest.exists():
            clips=read(manifest)['clips']
            for cell in record['matrix'].values():
                if cell['reviewed']:assert clips[cell['animation']['clip']]['motion_review']['user_approved']
                if cell['integrated']:assert cell['animation']['clip'] in clips and cell['boxes'] and cell['sound']
    if ledger_path is None and read(ROOT/'content/fighters/gomora/definition.json')['production_status']=='pilot_partial':
        from gomora_verify import main as verify_gomora
        verify_gomora()
    print('STAGE4_PILOT PASS：固定素材/授权方法计数、原始快照与定稿/已接入试制动作一致；未审格不算完成。')
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--ledger',type=Path)
    main(parser.parse_args().ledger)
