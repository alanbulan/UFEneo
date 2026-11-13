import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


frames = []
for i in range(4):
    src = f"art/fighters/ultraman-zero__luna_miracle/stage1/moves/jump/frames/jump-{i:02d}.png"
    p = ROOT / src
    im = Image.open(p)
    frames.append(
        {
            "clip": "jump",
            "index": i,
            "source": src,
            "source_sha256": sha256(p),
            "size": [im.width, im.height],
            "standing": False,
        }
    )

out = ROOT / "tools/rebuild/ultraman-zero__luna_miracle/jump-land.json"
out.write_text(json.dumps({"frames": frames}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("wrote", len(frames))
