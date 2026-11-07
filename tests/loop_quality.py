"""循环门的接头与阈值逻辑，不评判像素美术观感。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import sys
from pathlib import Path
Path = _LayoutProjectPath
sys.path.insert(0,str(_LayoutProjectPath(_layout_root)/'tools/rebuild'))
from loop_qa import evaluate
assert not evaluate([[0,0],[1,3],[2,6],[1,3]],'charge')['issues']
assert evaluate([[0,0],[0,2],[0,4]],'charge')['issues'] # 末尾回开头4px
assert evaluate([[0,0],[4,1]],'idle')['issues'] # 水平漂移
assert not evaluate([[0,0],[0,4],[0,8],[0,12],[0,8],[0,4]],'stun')['issues']
assert evaluate([[0,0],[0,4],[0,9],[0,4]],'stun')['issues']
assert not evaluate([[0,0],[0,4],[0,8],[0,4]],'walk_forward')['issues']
print('LOOP_QUALITY PASS')
