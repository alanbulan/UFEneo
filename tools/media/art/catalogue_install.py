"""把一张新生成的整图装进图鉴：高分红图 → 原生像素 → 按身高标尺落位。

生成图默认存到 reports/catalogue-ref/<id>/raw.png（图鉴的重采样源），再经
catalogue_native 做二值 Alpha / 32 色硬色阶，最后由 catalogue_rescale 按
catalogue_scale.json 的目标站高重新降采样并登记 SHA 与实际站高。

重画会清掉旧的 anim-strip：旧帧来自旧底图，留着会继续播玩具感的动作。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue_store  # noqa: E402 - 同目录工具

ROOT = Path(__file__).resolve().parents[3]
VENV = ROOT / ".venv/bin/python"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue_id")
    parser.add_argument("image", help="生成的整图（带真透明背景）")
    parser.add_argument("--art-source", default="mcp_image_to_image_from_official_reference")
    parser.add_argument("--keep-strip", action="store_true", help="保留旧待机动画条")
    args = parser.parse_args()

    cid = args.catalogue_id
    source = Path(args.image).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"找不到生成图：{source}")

    raw = ROOT / f"reports/catalogue-ref/{cid}/raw.png"
    raw.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, raw)

    native = ROOT / f"assets/fighters/{cid}/catalogue/model-native.png"
    native.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(VENV), str(ROOT / "tools/media/art/catalogue_native.py"),
                    str(raw), str(native)], check=True, cwd=ROOT)
    subprocess.run([str(VENV), str(ROOT / "tools/media/art/catalogue_rescale.py"),
                    "--only", cid, "--force"], check=True, cwd=ROOT)

    if not args.keep_strip:
        for suffix in (".png", ".png.import"):
            stale = ROOT / f"assets/fighters/{cid}/catalogue/anim-strip{suffix}"
            if stale.is_file():
                stale.unlink()

    fields = {
        "catalogue_id": cid,
        "image_id": cid,
        "image": "res://" + native.relative_to(ROOT).as_posix(),
        "image_sha256": sha256(native),
        "art_source": args.art_source,
        "raw_sha256": sha256(raw),
    }
    # 并行重画时多个执行者会同时改这张表，必须走带 flock 的读改写。
    catalogue_store.update_entry(cid, fields)
    entry = (catalogue_store.load()["entries"].get(cid, {}) if args.keep_strip else
             catalogue_store.remove_fields(cid, ("strip", "frames", "strip_sha256", "idle_source")))
    print(json.dumps({"id": cid, "image": entry["image"], "sha256": entry["image_sha256"],
                      "visible_height": entry.get("visible_height_including_ornaments"),
                      "strip_cleared": not args.keep_strip}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
