"""生产进程只读JSON；Windows原子替换瞬间的共享冲突短暂重试，不使用旧缓存。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import json; json = _LayoutJson
import time
from pathlib import Path
Path = _LayoutProjectPath


def read_json(path):
    path=Path(path)
    for attempt in range(40):
        try:return json.loads(path.read_text(encoding='utf-8-sig'))
        except PermissionError:
            if attempt==39:raise
            time.sleep(.025)
