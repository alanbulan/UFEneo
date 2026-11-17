"""只供迁移后的离线Python工具读取冻结证据中的历史路径。

不建立副本或文件系统链接，不改原始请求、账本与SHA；游戏资源使用改写后的路径。
"""
from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path as NativePath

ROOT = next(p for p in NativePath(__file__).resolve().parents if (p / "project.godot").is_file())
ROUTE_FILE = NativePath(__file__).with_name("layout_routes.json")
DATA = json.loads(ROUTE_FILE.read_text("utf-8")) if ROUTE_FILE.exists() else {"source_root": str(ROOT), "routes": []}
SOURCE_INDEX = ROOT / "art/source-index.json"
SOURCE_ALIASES = json.loads(SOURCE_INDEX.read_text("utf-8")).get("aliases", {}) if SOURCE_INDEX.is_file() else {}
ROUTES = sorted(DATA["routes"], key=lambda r: -len(r[0]))
ROUTE_BY_OLD = dict(ROUTES)
MAX_ROUTE_COMPONENTS = max((len(old.split("/")) for old, _ in ROUTES), default=0)


def match_route(text):
    # 接口JSON也包含很长的base64图片；其中的斜杠不是路径。
    # 只检查可能命中既有路由的前缀，避免对整张编码图片反复拼接。
    parts = text.split("/", MAX_ROUTE_COMPONENTS)
    for count in range(min(len(parts), MAX_ROUTE_COMPONENTS), 0, -1):
        prefix = "/".join(parts[:count])
        if prefix in ROUTE_BY_OLD:
            return prefix, ROUTE_BY_OLD[prefix]
    return None


def canonical_data(value):
    """路径在内存中解析到当前位置；提示词、哈希、时间等原样保留。"""
    if isinstance(value, str):
        prefix = "res://" if value.startswith("res://") else ""
        raw = value[len(prefix):]
        normal = raw.replace("\\", "/")
        known = bool(match_route(normal))
        known |= normal in SOURCE_ALIASES
        known |= any(normal.lower().startswith(p.replace("\\", "/").lower() + "/") for p in [str(ROOT), DATA["source_root"]])
        return prefix + translate(raw) if known else value
    if isinstance(value, list):
        return [canonical_data(v) for v in value]
    if isinstance(value, dict):
        return {canonical_data(k): canonical_data(v) for k, v in value.items()}
    return value


class JsonProxy:
    path_text = staticmethod(canonical_data)

    def __getattr__(self, name):
        return getattr(json, name)

    def loads(self, *args, **kwargs):
        return canonical_data(json.loads(*args, **kwargs))

    def load(self, *args, **kwargs):
        return canonical_data(json.load(*args, **kwargs))


json_proxy = JsonProxy()


def translate(value):
    return translate_string(os.fspath(value))


@lru_cache(maxsize=32768)
def translate_string(value):
    text = value.replace("\\", "/")
    base = str(ROOT).replace("\\", "/")
    original = DATA["source_root"].replace("\\", "/")
    absolute = False
    for prefix in [base, original]:
        if text.lower() == prefix.lower() or text.lower().startswith(prefix.lower() + "/"):
            text = text[len(prefix):].lstrip("/")
            absolute = True
            break
    matched = match_route(text)
    if matched:
        old, new = matched
        text = new + text[len(old):]
    # Current source files have one physical location. Frozen receipts retain
    # their original paths and bytes; resolve only their selected aliases.
    visited = set()
    while text in SOURCE_ALIASES:
        if text in visited:
            raise ValueError(f"Source alias cycle: {text}")
        visited.add(text)
        text = SOURCE_ALIASES[text]
    if absolute and not NativePath(text).is_absolute():
        return base + ("/" + text if text else "")
    return text


class ProjectPath(type(NativePath())):
    """Path的薄适配；最终完整路径形成时才迁移，支持ROOT/变量的动态拼接。"""
    def __new__(cls, *parts):
        return super().__new__(cls, translate(NativePath(*parts)))

    def __init__(self, *parts):
        # Python 3.12起pathlib在__init__保存原始参数，不能只覆盖__new__。
        if sys.version_info >= (3, 12):
            super().__init__(translate(NativePath(*parts)))

    def __truediv__(self, value):
        return type(self)(super().__truediv__(value))

    def __rtruediv__(self, value):
        return type(self)(super().__rtruediv__(value))

    def joinpath(self, *parts):
        return type(self)(super().joinpath(*parts))

    def iterdir(self):
        # 被拆散的历史批次父目录可枚举其迁移后的唯一子项。
        seen = set()
        if super().is_dir():
            for item in super().iterdir():
                resolved = type(self)(item)
                if str(resolved) not in seen:
                    seen.add(str(resolved))
                    yield resolved
        try:
            relative = NativePath(self).relative_to(ROOT).as_posix()
        except ValueError:
            relative = self.as_posix()
        for old, _ in ROUTES:
            if old.startswith(relative.rstrip("/") + "/"):
                name = old[len(relative.rstrip("/")) + 1:].split("/", 1)[0]
                item = type(self)(NativePath(self) / name)
                if str(item) not in seen:
                    seen.add(str(item))
                    yield item

    def glob(self, pattern, **kwargs):
        seen = set()
        roots = [NativePath(self)]
        try:
            relative = NativePath(self).relative_to(ROOT).as_posix()
        except ValueError:
            relative = self.as_posix()
        # 只补充位于当前目录之下的迁移根；按旧路径模式筛选，避免多收文件。
        for item in NativePath(self).glob(pattern, **kwargs):
            resolved = type(self)(item)
            if str(resolved) not in seen:
                seen.add(str(resolved))
                yield resolved
        import fnmatch
        recursive = "**" in pattern
        for old, new in ROUTES:
            if not old.startswith(relative.rstrip("/") + "/"):
                continue
            source_tail = old[len(relative.rstrip("/")) + 1:]
            target = NativePath(translate(new))
            if not target.is_absolute():
                target = ROOT / target
            options = [target] if target.is_file() else target.rglob("*") if target.is_dir() else []
            for item in options:
                suffix = "" if item == target else "/" + item.relative_to(target).as_posix()
                old_tail = source_tail + suffix
                matched = fnmatch.fnmatchcase(old_tail, pattern) if recursive else "/" not in old_tail and fnmatch.fnmatchcase(old_tail, pattern)
                if recursive and pattern.startswith("**/"):
                    matched |= fnmatch.fnmatchcase(old_tail, pattern[3:])
                if matched and str(item) not in seen:
                    seen.add(str(item))
                    yield type(self)(item)

    def rglob(self, pattern, **kwargs):
        return self.glob("**/" + pattern, **kwargs)
