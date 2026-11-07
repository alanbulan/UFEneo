"""空中念力头镖的来源、逐请求计数、尺度和运行清单；不评价主观造型。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib,json,sys; json = _LayoutJson
from collections import Counter
from pathlib import Path
Path = _LayoutProjectPath
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
from head_scale import read,sha,save

def main():
    work=ROOT/'art/fighters/ultraseven/stage4/revisions/seven-air-special';ledger=read(work/'ledger.json');requests=ledger['requests']
    assert ledger['limits']['per_asset']==10
    assert [r['ledger_sequence'] for r in requests]==list(range(1,len(requests)+1))
    for key,count in Counter(r['action'] for r in requests).items():assert count<=10,(key,count)
    for r in requests:
        assert r['fighter']=='ultraseven' and r['quality']=='high'
        brief=ROOT/r['brief'];assert sha(brief)==r['brief_sha256']
        b=read(brief);assert b['quality']=='high' and b['asset_key']==r['action']
        assert len(b['references'])==r['input_image_count']==len(r['inputs'])
        for p in r['inputs']:assert sha(ROOT/p['path'])==p['sha256']
        assert r['submitted_at'] and r['finished_at'] and r['result']
        raw=ROOT/r['output']
        if not raw.exists():
            assert r['result'] in ['alpha_rejected','failed_or_remote_unknown'];continue
        metadata=read(raw.with_suffix('.metadata.json'))
        assert metadata['requested_quality']=='high' and metadata['background_requested']=='transparent'
        assert metadata['image_sha256']==sha(raw)
    manifest=read(ROOT/'assets/fighters/ultraseven/animations/manifest.json')
    clip=manifest['clips']['air_special'];move=read(ROOT/'content/fighters/ultraseven/moves/air_special.json')
    assert len(clip['rects'])==14 and len(move['frames'])==sum(clip['ticks'])==clip['runtime_ticks']
    assert move['energy_cost']==1000 and move['air_allowed'] and move['finish_on_landing']
    assert move['feedback']['hitstop']>=10 and move['feedback']['flash']<=2
    path=move['projectile']['integer_path'];assert all(len(p)==2 and all(type(x)==int for x in p) for p in path)
    assert move['projectile']['max_hits']==3 and move['projectile']['hit_interval']>=4
    assert set(move['projectile']['locked_moves'])=={'ranged_forward','air_special'}
    assert move['projectile']['effect']=='seven_slugger' and move['projectile']['display_scale']==[1,1]
    assert read(ROOT/'content/fighters/ultraseven/state_frames.json')['air_special']==move['frames']
    assert 'air_special' not in read(ROOT/'content/fighters/ultraseven/definition.json')['unsupported_moves']
    atlas=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA')
    assert sha(ROOT/clip['texture'].removeprefix('res://'))==clip['atlas_sha256']
    assert set(atlas.getchannel('A').getdata())=={0,255}
    assert len({p[:3] for p in atlas.getdata() if p[3]})<=32
    for frame in move['frames']:
        index=int(frame['sprite']);assert frame['slugger_attached']==(index in [0,1,12,13])
        assert not frame['cancel']
    fx=read(ROOT/'content/presentation/phase3_projectiles.json')['seven_psychic_slugger_trail']
    assert fx['display_scale']==[1,1] and fx['visual_scale']==1
    assert sha(ROOT/fx['texture'].removeprefix('res://'))==fx['atlas_sha256']
    assert read(ROOT/fx['island_whitelist'])['atlas_sha256']==fx['atlas_sha256']
    hq=read(ROOT/clip['head_qa'])
    sizes=[r['measurement']['length']/hq['reference']['measurement']['length']-1 for r in hq['frames']]
    assert max(abs(v) for v in sizes)<=.08
    save(ROOT/'reports/review/2026-10-22/seven-air-special/resource-check.json',
        dict(requests=len(requests),by_category=dict(Counter(r['category'] for r in requests)),
            retries=sum(r['sequence']>1 for r in requests),head_deviations=sizes,display_scale=[1,1],
            approved_actions=[k for k,c in manifest['clips'].items() if c.get('motion_review',{}).get('user_approved')],
            new_action_approved=clip['motion_review']['user_approved']))
    print('SEVEN_AIR_SPECIAL_RESOURCES PASS：独立请求、14帧整帧、尺度、来源和武器状态一致；造型仍待用户审片。')

if __name__=='__main__':main()
