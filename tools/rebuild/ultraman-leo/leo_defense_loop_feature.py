"""雷欧新防御帧的完整近眼标注；只读、整帧像素哈希绑定，不改变旧循环。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import hashlib
import json; json = _LayoutJson
from functools import lru_cache
from pathlib import Path
Path = _LayoutProjectPath

ROOT = _LayoutProjectPath(_layout_root)
ANNOTATIONS = ROOT/'art/fighters/ultraman-leo/stage4/defense/marker-annotations.json'


@lru_cache(maxsize=1)
def annotations():
    if not ANNOTATIONS.exists():
        return {}
    rows = json.loads(ANNOTATIONS.read_text('utf-8'))['frames']
    return {(tuple(r['size']), r['frame_sha256']): r for r in rows}


def annotation(im):
    key = (im.size, hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest())
    return annotations().get(key)
