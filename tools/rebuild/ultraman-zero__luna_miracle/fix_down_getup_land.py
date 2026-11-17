"""修正 down/getup 落格映射。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame(clip: str, index: int, source: str, standing: bool = True) -> dict:
    path = ROOT / source
    im = Image.open(path)
    return {
        "clip": clip,
        "index": index,
        "source": source,
        "source_sha256": sha256(path),
        "size": [im.width, im.height],
        "standing": standing,
    }


def write_manifest(rel: str, frames: list[dict]) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"frames": frames}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(rel, len(frames))


def main() -> int:
    # down: 两帧倒地保持（仰卧/俯卧）
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/down-land.json",
        [
            frame("down", 0, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-00.png", standing=False),
            frame("down", 1, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-02.png", standing=False),
        ],
    )
    # getup: 过渡起身 -> 单膝起身
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/getup-land.json",
        [
            frame("getup", 0, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-01.png", standing=False),
            frame("getup", 1, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-03.png", standing=False),
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
