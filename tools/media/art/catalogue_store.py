"""图鉴展示表的并发安全读改写。

多个批处理进程会同时往 content/roster/catalogue_display.json 写条目，
直接 read-modify-write 会互相覆盖。这里用 flock 串行化，并且先写临时文件
再原子替换，避免读到写了一半的 JSON。
"""
from __future__ import annotations

import fcntl
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DISPLAY_PATH = ROOT / "content/roster/catalogue_display.json"
LOCK_PATH = ROOT / "reports/catalogue-display.lock"


def load() -> dict:
    return json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))


def update_entry(catalogue_id: str, fields: dict) -> dict:
    """给单个条目合并字段，返回合并后的条目。"""
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_PATH, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            data = json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))
            entry = data["entries"].setdefault(catalogue_id, {})
            entry.update(fields)
            temporary = DISPLAY_PATH.with_name(DISPLAY_PATH.name + ".tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
            temporary.replace(DISPLAY_PATH)
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    return entry


def remove_fields(catalogue_id: str, fields: tuple[str, ...]) -> dict:
    """删除条目里的若干字段（同样走 flock）。"""
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_PATH, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            data = json.loads(DISPLAY_PATH.read_text(encoding="utf-8"))
            entry = data["entries"].setdefault(catalogue_id, {})
            for field in fields:
                entry.pop(field, None)
            temporary = DISPLAY_PATH.with_name(DISPLAY_PATH.name + ".tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
            temporary.replace(DISPLAY_PATH)
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    return entry


def animated_ids() -> set[str]:
    return {cid for cid, entry in load()["entries"].items() if entry.get("strip")}
