"""生成 jump 落格清单。"""
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


def main() -> int:
    frames = [frame("jump", i, f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/jump/frames/jump-{i:02d}.png")
              for i in range(4)]
    out = ROOT / "tools/rebuild/ultraman-zero__luna_miracle/jump-land.json"
    out.write_text(json.dumps({"frames": frames}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(out, len(frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
