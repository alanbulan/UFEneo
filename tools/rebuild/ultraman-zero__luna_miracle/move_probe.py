"""只读：打印基础赛罗各招的非帧字段与引用到的 effect/audio id。"""
from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MOVES = ROOT / "content/fighters/ultraman-zero/moves"

SKIP = {"frames"}


def collect(value, path, out):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"spark", "block_spark", "effect", "impact_effect", "block_effect"} \
                    and isinstance(item, str):
                out.setdefault(key, set()).add(item)
            collect(item, f"{path}.{key}", out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            collect(item, f"{path}[{index}]", out)


def main() -> int:
    effects = {}
    audios = set()
    shots = {}
    for path in sorted(glob.glob(str(MOVES / "*.json"))):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        found = {}
        collect({k: v for k, v in data.items() if k not in SKIP}, "", found)
        for key, values in found.items():
            effects.setdefault(key, set()).update(values)
        audio = data.get("audio", {})
        audios.update(v for v in audio.values() if isinstance(v, str))
        for frame in data["frames"]:
            for event in frame.get("events", []):
                if event.get("kind") == "sound":
                    audios.add(str(event.get("id")))
                if event.get("kind") == "shot":
                    shots.setdefault(data["id"], set()).add(str(event.get("id")))
        if data.get("shots"):
            for shot in data["shots"]:
                shots.setdefault(data["id"], set()).add(str(shot.get("effect")))
        print("==", data["id"], data.get("kind"), "frames", len(data["frames"]),
              "startup/active/recovery", data.get("startup"), data.get("active"), data.get("recovery"))
        print("  audio", json.dumps(audio, ensure_ascii=False))
        if data.get("shots"):
            print("  shots", json.dumps(data["shots"], ensure_ascii=False))
        if data.get("projectile"):
            print("  projectile", json.dumps(data["projectile"], ensure_ascii=False))
        if data.get("target"):
            print("  target", json.dumps(data["target"], ensure_ascii=False))
    print("== effects")
    for key in sorted(effects):
        print(key, sorted(effects[key]))
    print("== audio ids")
    print(sorted(audios))
    print("== shot ids")
    for key in sorted(shots):
        print(key, sorted(shots[key]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
