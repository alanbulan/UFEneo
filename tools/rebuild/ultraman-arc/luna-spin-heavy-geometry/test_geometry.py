"""只读重复构建核验，不运行Godot，不写游戏文件。"""
import hashlib
from geometry import build_frames, ROOT, read
from pathlib import Path
recipes=[Path(__file__).with_name('plan.json'),Path(__file__).with_name('plan-turn-v2.json')]
all_sources={r['path'] for p in recipes for r in read(p)['sources']}
before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in all_sources}
old={}
for recipe in recipes:
    a,x=build_frames(plan_path=recipe);b,y=build_frames(plan_path=recipe)
    assert x==y and len(a)==len(read(recipe)['sources'])
    for p,q,row in zip(a,b,x['frames']):
        assert p.tobytes()==q.tobytes()
        hist=p.getchannel('A').histogram();assert sum(hist[1:255])==0
        assert p.size==(320,320) and row['whole_source_preserved_no_crop']
        assert row['raster_rounding_anisotropy']<0.01
        assert abs(row['alpha_bbox'][3]-280)<=1
        if row['key'] in old:assert old[row['key']]==p.tobytes(), '增加新相不应改变旧三相'
        old[row['key']]=p.tobytes()
    assert x['runtime_candidate_accepted'] is False and x['physics_run'] is False
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in all_sources}
print('三相/四相均重复构建逐像素相等；原源SHA不变，旧三帧不受插入新相影响；Alpha二值/无裁切/栅格舍入/支撑末行≤1像素通过。未运行物理或宣称动作通过。')
