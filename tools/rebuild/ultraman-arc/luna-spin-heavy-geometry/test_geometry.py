"""只读重复构建核验，不运行Godot，不写游戏文件。"""
import hashlib
from geometry import build_frames, ROOT, read
from pathlib import Path
plan=read(Path(__file__).with_name('plan.json'))
before={r['path']:hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest() for r in plan['sources']}
a,x=build_frames();b,y=build_frames()
assert x==y
assert len(a)==len(b)==3
for p,q,row in zip(a,b,x['frames']):
    assert p.tobytes()==q.tobytes()
    hist=p.getchannel('A').histogram()
    assert sum(hist[1:255])==0
    assert p.size==(320,320)
    assert row['whole_source_preserved_no_crop']
    assert row['raster_rounding_anisotropy']<0.01
    assert abs(row['alpha_bbox'][3]-280)<=1
assert x['runtime_candidate_accepted'] is False and x['physics_run'] is False
assert before=={r['path']:hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest() for r in plan['sources']}
print('三完整帧重复构建逐像素相等；原源SHA不变；Alpha二值/无裁切/栅格舍入/支撑末行≤1像素通过。未运行物理或宣称动作通过。')
