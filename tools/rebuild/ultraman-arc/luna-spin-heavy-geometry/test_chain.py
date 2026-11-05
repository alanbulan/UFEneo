"""九槽诊断复核：不调用Godot，不生成时序或安装。"""
import hashlib,json
from pathlib import Path
from PIL import Image
from geometry import build_frames,read,sha,ROOT
plan=Path(__file__).with_name('plan-chain-v3.json')
sources={r['path'] for r in read(plan)['sources']}
before={s:sha(ROOT/s) for s in sources}
a,x=build_frames(plan_path=plan);b,y=build_frames(plan_path=plan)
assert x==y and len(a)==9
baseline=ROOT/'docs/verification/luna-spin-heavy-turn-mid-candidate-review.json'
old={r['key']:r for r in read(baseline)['geometry']['frames']}
old_frames,old_result=build_frames(plan_path=plan.with_name('plan-turn-v2.json'))
old_pixels={r['key']:im.tobytes() for im,r in zip(old_frames,old_result['frames'])}
for im,again,row in zip(a,b,x['frames']):
    assert im.tobytes()==again.tobytes()
    assert im.size==(320,320) and row['whole_source_preserved_no_crop']
    assert sum(im.getchannel('A').histogram()[1:255])==0
    assert row['raster_rounding_anisotropy']<0.01
    if row['key'] in old:
        o=old[row['key']]
        assert row['uniform_scale']==o['uniform_scale']
        assert row['whole_image_translation']==o['whole_image_translation']
        assert im.tobytes()==old_pixels[row['key']]
assert a[0].tobytes()==a[-1].tobytes()
assert before=={s:sha(ROOT/s) for s in sources}
assert x['physics_run'] is False and x['runtime_candidate_accepted'] is False
print('九槽重复构建逐像素一致；旧四相采样/平移/像素保持；原源SHA不变；Alpha二值/整图无裁切/栅格舍入<1%；首尾idle仅同图对照。未证明接续或支撑稳定。')
