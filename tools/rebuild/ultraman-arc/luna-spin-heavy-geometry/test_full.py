"""全现源双尺度敏感性重复构建；不创建运行候选。"""
from pathlib import Path
from geometry import build_frames, read, sha, ROOT
plans=[Path(__file__).with_name('plan-full-shin-v6.json'),Path(__file__).with_name('plan-full-head-v6.json')]
sources={r['path'] for p in plans for r in read(p)['sources']};before={s:sha(ROOT/s) for s in sources}
for p in plans:
    a,x=build_frames(plan_path=p);b,y=build_frames(plan_path=p)
    assert x==y and len(a)==10
    for im,other,row in zip(a,b,x['frames']):
        assert im.tobytes()==other.tobytes()
        assert row['whole_source_preserved_no_crop'] and row['raster_rounding_anisotropy']<0.01
        assert sum(im.getchannel('A').histogram()[1:255])==0
    assert a[0].tobytes()==a[-1].tobytes()
    assert x['physics_run'] is False and x['runtime_candidate_accepted'] is False
assert before=={s:sha(ROOT/s) for s in sources}
print('同胫尺/同头代理尺各十槽两次构建一致，原源不变、无裁切、Alpha二值、舍入<1%。不同尺不是相互验收，首尾同图不证明连续。')
