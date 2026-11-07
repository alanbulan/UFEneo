"""Shared project-relative art locations. Keep creators and consumers in sync."""

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson
from pathlib import PurePosixPath
import re

KINDS = {"hero", "kaiju", "dark_ultra", "form", "story"}
LEGACY_KEYART = "art/archive/legacy-ui"
PIXEL_PORTRAITS = "assets/ui/pixel_portraits"


def asset_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        raise ValueError("Asset ID must be a lowercase identifier, never a path")
    return value


def brief_path(character, kind):
    if kind not in KINDS:
        raise ValueError("Unknown character kind: " + str(kind))
    return str(PurePosixPath("art/shared/briefs/characters", kind, asset_id(character), "base.json"))


def base_concept_dir(character):
    return PurePosixPath("art/shared/legacy/concepts/characters", asset_id(character), "base")


def base_concept_path(character, revision):
    if not re.fullmatch(r"v\d{3}", revision):
        raise ValueError("Use a version from v001 to v999")
    return base_concept_dir(character) / revision / ("base-" + revision + ".png")


def pixel_portrait_path(character):
    return PurePosixPath(PIXEL_PORTRAITS, asset_id(character), "portrait.png")


def legacy_character_dir(character):
    return PurePosixPath(LEGACY_KEYART, "characters", asset_id(character))
