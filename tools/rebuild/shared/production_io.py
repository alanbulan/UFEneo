"""生产进程只读JSON；Windows原子替换瞬间的共享冲突短暂重试，不使用旧缓存。"""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
from functools import lru_cache
import importlib.util
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath

_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_tools = str(_layout_root / "tools")
if _layout_tools not in _layout_sys.path:
    _layout_sys.path.insert(0, _layout_tools)

from maintenance.layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
import json; json = _LayoutJson
import time
from pathlib import Path
Path = _LayoutProjectPath


@lru_cache(maxsize=None)
def load_rebuild_script(rel_path: str):
    """按相对 tools/rebuild 的路径加载角色脚本，避免向 sys.path 通配注入子目录。"""
    target = (_layout_root / "tools/rebuild" / rel_path).resolve()
    if not target.is_file():
        raise ImportError(f"Missing rebuild script: {target}")
    mod_name = "rebuild._loaded_" + rel_path.replace("/", "_").replace("-", "_").removesuffix(".py")
    if mod_name in _layout_sys.modules:
        return _layout_sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, target)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {target}")
    module = importlib.util.module_from_spec(spec)
    _layout_sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def read_json(path):
    path=Path(path)
    for attempt in range(40):
        try:return json.loads(path.read_text(encoding='utf-8-sig'))
        except PermissionError:
            if attempt==39:raise
            time.sleep(.025)
