"""正式走路的真实像素测量门；初代/杰顿按用户授权只报告，不改素材。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import argparse,sys
from pathlib import Path
Path = _LayoutProjectPath
from PIL import Image
ROOT=_LayoutProjectPath(_layout_root)
sys.path.insert(0,str(ROOT/'tools/rebuild'))
from head_scale import read,save,sha
import walk_cycle_qa
from current_walk_measurement import refresh

def main(output=None):
    reports=[];errors=[]
    # 已审旧角色使用本轮只读复测，核对图集指纹，避免把旧测量当成当前图集。
    old=ROOT/'reports/review/2026-10-22/seven-gate-revision/old-walks-read-only-audit.json'
    if not old.exists():errors.append('缺少初代/杰顿已安装走路的本轮只读测量')
    else:
        for row in read(old):
            # 始终实测当前像素；旧报告指纹只作对照，允许量产中的新图集。
            row=refresh(row)
            assert sha(ROOT/row['atlas'])==row['atlas_sha256'],'测量期间图集再次改变，请等待安装完成后重跑'
            reports.append(dict(fighter=row['fighter'],action=row['action'],report_only=True,issues=row['issues'],
                eye_range=row['eye_range'],adjacent_eye_y=row.get('adjacent_eye_y'),max_foot_deviation=row['max_foot_deviation'],
                atlas=row['atlas'],atlas_sha256=row['atlas_sha256'],previous_atlas_sha256=row.get('previous_atlas_sha256'),
                measurement_refreshed=row.get('measurement_refreshed',False),atlas_or_timing_changed=row.get('atlas_or_timing_changed')))
            print(row['fighter']+'/'+row['action']+'（只报告）：'+('；'.join(row['issues']) or '数值门通过'))
    path=ROOT/'assets/fighters/ultraseven/animations/manifest.json'
    if path.exists():
        for action,clip in read(path)['clips'].items():
            if action not in ['walk_forward','walk_back']:continue
            folder=(ROOT/clip['head_qa']).parent
            try:
                hq=read(folder/'head-qa.json');a=Image.open(ROOT/clip['texture'].removeprefix('res://')).convert('RGBA')
                for i,(x,y,w,h) in enumerate(clip['rects']):
                    actual=a.crop((x,y,x+w,y+h));expected=Image.open(folder/hq['frames'][i]['image']).convert('RGBA')
                    if actual.size!=expected.size or actual.tobytes()!=expected.tobytes():raise ValueError('正式图集和测量源不一致')
                measured=read(folder/'walk-measurements.json')
                if measured['ticks']!=clip['ticks']:raise ValueError('测量时长与manifest不一致')
                # 检查器只读，不在角色生产目录写回派生报告。
                result=walk_cycle_qa.check([a.crop((x,y,x+w,y+h)) for x,y,w,h in clip['rects']],
                    'ultraseven',hq['frames'],measured['ticks'],measured['feet'],measured['sign'],measured.get('targets'))
                if result['issues']:raise ValueError('; '.join(result['issues']))
                reports.append(dict(result,fighter='ultraseven',action=action,report_only=False))
            except (ValueError,FileNotFoundError) as exc:
                reason='缺少固定骨架生成后的真实脚/眼测量' if isinstance(exc,FileNotFoundError) else str(exc)
                errors.append('ultraseven/'+action+': '+reason)
    save(Path(output) if output else ROOT/'reports/walk-standing-resources.json',dict(reports=reports,errors=errors,rule='走路眼幅≤8/相邻含接头≤4；撑地±8；均值0.6–1.5；无极值相位硬门；旧角色只报告'))
    if errors:print('\n'.join(errors));raise SystemExit(1)
    print('WALK_STANDING_RESOURCES PASS：已安装的新走路与真实测量一致；旧角色问题仅报告。')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);main(parser.parse_args().output)
