"""补充已切分帧的落格清单（按 state sprite 索引映射）。"""
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
    # walk_back: 4 sprites [0,1,2,3]
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/walk_back-land.json",
        [frame("walk_back", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/walk_back/frames/walk_back-{i:02d}.png")
         for i in range(4)],
    )
    # dash: 4 sprites [0,1,2,3]
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/dash-land.json",
        [frame("dash", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/dash/frames/dash-{i:02d}.png")
         for i in range(4)],
    )
    # crouch: 2 sprites [0,1] -> use 00,01
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/crouch-land.json",
        [frame("crouch", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/crouch/frames/crouch-{i:02d}.png", standing=False)
         for i in range(2)],
    )
    # guard: 2 sprites [0,1]
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/guard-land.json",
        [frame("guard", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/guard/frames/guard-{i:02d}.png")
         for i in range(2)],
    )
    # hit: 2 sprites [0,1]
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/hit-land.json",
        [frame("hit", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/hit/frames/hit-{i:02d}.png")
         for i in range(2)],
    )
    # down/getup: map strip frames by visual (down-02 prone, down-03 getting up) to states
    # down needs 2 sprites [0,1]; getup needs 2 [0,1]
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/down-land.json",
        [
            frame("down", 0, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-02.png", standing=False),
            frame("down", 1, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-03.png", standing=False),
        ],
    )
    write_manifest(
        "tools/rebuild/ultraman-zero__luna_miracle/getup-land.json",
        [
            frame("getup", 0, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-01.png", standing=False),
            frame("getup", 1, "art/fighters/ultraman-zero__luna_miracle/stage1/moves/down/frames/down-00.png", standing=True),
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
