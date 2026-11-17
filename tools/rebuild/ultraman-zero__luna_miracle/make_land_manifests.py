"""生成已切分帧的落格清单。"""
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
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/form_switch-land.json",
        [frame("form_switch", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/form_switch/frames/form_switch-{i:02d}.png")
         for i in range(6)],
    )
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/idle-05-land.json",
        [frame("idle", 5, "art/fighters/ultraman-zero__luna_miracle/stage1/idle/frames/idle-05.png")],
    )
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/walk_forward-2-land.json",
        [frame("walk_forward", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/walk_forward/frames/walk_forward-{i:02d}.png")
         for i in range(4, 8)],
    )
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/walk_back-land.json",
        [frame("walk_back", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/walk_back/frames/walk_back-{i:02d}.png")
         for i in range(4)],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
