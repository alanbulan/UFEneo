"""临时只读：打印 JSON 指定键的内容。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = ROOT / path
    data = json.loads(path.read_text(encoding="utf-8"))
    keys = sys.argv[2:]
    if not keys:
        print(list(data))
        return 0
    for key in keys:
        print("==", key)
        print(json.dumps(data.get(key), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
