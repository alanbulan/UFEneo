"""已装旧循环的只读标志点标注；像素哈希绑定，不沿用到新生成帧。

初代眼框可能被白色眼内高光拆成数个暖色分量。旧的“离提示点最近
的色块重心”会在近侧眼、远侧小眼、眼框碎片之间切换。此次逐帧标注
完整近侧眼框（含眼内白色）后取框中心，供用户核实；没有标注的帧
仍由原检测器处理。标注不是质检豁免，不改变阈值或正式素材。
"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
from functools import lru_cache
from pathlib import Path
Path = _LayoutProjectPath
import json; json = _LayoutJson

ROOT=_LayoutProjectPath(_layout_root)
ANNOTATIONS=ROOT/'art/shared/production/loop-repair/marker-annotations.json'


@lru_cache(maxsize=1)
def annotations():
    if not ANNOTATIONS.exists():
        return {}
    data=json.loads(ANNOTATIONS.read_text('utf-8'))
    # 本轮新生成帧也必须重新目视核实完整近眼；仍按整帧指纹绑定，绝不继承旧坐标。
    repaired=ROOT/'art/shared/production/loop-repair/repair-v1/marker-annotations.json'
    if repaired.exists():data['frames'].extend(json.loads(repaired.read_text('utf-8'))['frames'])
    return {(r['fighter'],tuple(r['size']),r['frame_sha256']):r for r in data['frames']}


def annotation(im,fighter):
    if fighter=='ultraman-leo':
        from leo_defense_loop_feature import annotation as leo_annotation
        return leo_annotation(im)
    if fighter!='ultraman':
        return None
    key=(fighter,im.size,hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest())
    return annotations().get(key)


def marked_feature(im,fighter):
    row=annotation(im,fighter)
    if row is None:
        return None
    x,y,x1,y1=row['bounds']
    if not (0<=x<x1<=im.width and 0<=y<y1<=im.height):
        raise ValueError('循环标志点标注越界')
    return [(x+x1-1)/2,(y+y1-1)/2]
