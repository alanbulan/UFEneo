"""整帧仿射同时更新抓点和框，保留动作时序/位移与特效自身大小。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import copy,sys
from pathlib import Path
Path = _LayoutProjectPath
sys.path.insert(0,str(_LayoutProjectPath(_layout_root)/'tools/rebuild'))
from head_scale_install import point,box,geometry

row=dict(old_rect=[0,0,192,192],anchor=[110,220],old_to_new={'scale':[1.25,1.25],'translation':[-10,-10]})
p=[20,60]
assert point(p,row)==[25,75]
b=box([10,20,20,40],row)
assert b==[12,25,26,50]
frame=dict(sprite=3,dx=4,dy=-2,cancel=['light2'],events=[{'kind':'sound','id':'heavy'}],hurtboxes=[[10,20,20,40]],hitboxes=[],target={'grip':p,'root':[106,0]},grab_points={'waist':p},attachments=[{'anchor':p}],shots=[{'spawn':p,'box':[-8,-8,16,16],'speed':9}])
before=copy.deepcopy(frame);after=geometry(frame,row)
assert frame==before
assert after['target']['grip']==after['grab_points']['waist']==after['attachments'][0]['anchor']==after['shots'][0]['spawn']==[25,75]
assert after['target']['root']==frame['target']['root']
assert after['shots'][0]['box']==frame['shots'][0]['box']
for key in ['sprite','dx','dy','cancel','events']:assert after[key]==frame[key]
print('HEAD_GEOMETRY PASS：根点坐标变换一致，位移/时序/世界落点与特效大小保留。')
