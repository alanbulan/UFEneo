"""从 URL 下载参考图并落盘到 art/fighters/<id>/sources/。

只做确定性校验与保存；搜索由执行者用 WebSearch/WebFetch 完成。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue_reference as CR

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def download(url: str, timeout: int = 30) -> bytes:
    # Fandom 的 static.wikia 直链会校验 Referer，缺了返回 403。
    headers = {"User-Agent": UA, "Referer": "https://ultra.fandom.com/"}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue_id")
    parser.add_argument("url")
    parser.add_argument("--index", type=int, default=1)
    parser.add_argument("--toy", action="store_true", help="来源是玩具/商品页")
    args = parser.parse_args()

    try:
        data = download(args.url)
    except Exception as error:  # noqa: BLE001
        print(f"下载失败：{error}", file=sys.stderr)
        return 1
    try:
        info = CR.validate(data)
    except ValueError as error:
        print(f"校验失败：{error}", file=sys.stderr)
        return 1

    # 按真实格式命名：生图 MCP 靠扩展名判断解码器。
    path = CR.reference_path(args.catalogue_id, args.index, CR.suffix_for(info["format"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    meta = {
        **info,
        "source_url": args.url,
        "toy_reference": bool(args.toy or CR.looks_like_toy(args.url)),
        "saved": path.relative_to(CR.ROOT).as_posix(),
    }
    path.with_suffix(".json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
