"""验证走路门、固定骨长和背面站高门的拒收；不替代视觉验收。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import sys,copy,math
from pathlib import Path
Path = _LayoutProjectPath
ROOT=_LayoutProjectPath(_layout_root);sys.path.insert(0,str(ROOT/'tools/rebuild'))
import walk_cycle_qa as walk,standing_size_qa as standing,seven_skeleton_walk as skeleton

def main():
    source=walk.idle_qa.feature
    try:
        walk.idle_qa.feature=lambda im,f,r:im
        eyes=[[10,y] for y in [16,14,11,14,16,14,11,14]]
        feet=[]
        for n,x in enumerate([120,108,96,84,72,84,96,108]):feet.append(dict(near=dict(x=x),far=dict(x=[72,84,96,108,120,108,96,84][n])))
        result=walk.check(eyes,'ultraseven',[{}]*8,[6]*8,feet,1);assert result['pass_'],result
        jumped=copy.deepcopy(eyes);jumped[3][1]+=9;assert not walk.check(jumped,'ultraseven',[{}]*8,[6]*8,feet,1)['pass_']
        free_phase=[[10,y] for y in [14,13,14,15,14,13,14,15]]
        assert walk.check(free_phase,'ultraseven',[{}]*8,[6]*8,feet,1,targets=[dict(eye=[99,99],feet={})]*8)['pass_'],'相位极值和骨架目标不是硬门'
        seam=[[10,y] for y in [10,12,14,14,14,14,14,15]]
        assert any('相邻' in s for s in walk.check(seam,'ultraseven',[{}]*8,[6]*8,feet,1)['issues']),'必须检查末帧到首帧'
        assert any('时长' in s for s in walk.check(eyes,'ultraseven',[{}]*8,[1,11,6,6,6,6,6,6],feet,1)['issues'])
        slipped=copy.deepcopy(feet);slipped[3]['near']['x']+=10;assert any('撑地' in s for s in walk.check(eyes,'ultraseven',[{}]*8,[6]*8,slipped,1)['issues'])
    finally:walk.idle_qa.feature=source
    for hip,ankle in [([94,125],[116,179]),([94,120],[92,179]),([94,123],[80,176])]:
        p=skeleton.knee(hip,ankle,28,33);assert abs(math.dist(hip,p)-28)<1e-8 and abs(math.dist(p,ankle)-33)<1e-8
    try:skeleton.knee([0,0],[0,100],28,33)
    except ValueError:pass
    else:raise AssertionError('不可达骨架必须拒绝')
    from PIL import Image
    from head_scale import read
    c=read(ROOT/'assets/fighters/ultraseven/animations/manifest.json')['clips']['turn'];q=read(ROOT/c['head_qa']);im=Image.open((ROOT/c['head_qa']).parent/q['frames'][1]['image']).convert('RGBA');row=q['frames'][1]
    assert row['size_policy']=='standing_height' and standing.check(im,'ultraseven',row)['pass_']
    shortened=im.resize((192,170),Image.Resampling.NEAREST);bad=copy.deepcopy(row);bad['head_region']=[[x,y*170/192] for x,y in row['head_region']];bad['foot_anchor']=[96,row['foot_anchor'][1]*170/192]
    assert not standing.check(shortened,'ultraseven',bad)['pass_'],'背面变矮必须报错，即使头宽没变'
    print('WALK_STANDING_PIPELINE PASS：固定骨长、眼高幅度与接头、撑地时长、背面站高门有效。')

if __name__=='__main__':main()
